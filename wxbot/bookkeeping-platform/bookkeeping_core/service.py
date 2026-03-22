from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta

from .commands import CommandHandler
from .contracts import CoreAction, CoreActionCollector, NormalizedMessageEnvelope
from .ingestion import build_runtime_record, persist_transaction_record
from .parser import format_confirmation, looks_like_transaction, parse_transaction


class BookkeepingService:
    def __init__(self, *, db, master_users: list[str], export_dir) -> None:
        self.db = db
        self.commands = CommandHandler(db, master_users, export_dir)
        self.logger = logging.getLogger("bookkeeping-core")
        self.processed_message_ids: set[str] = set()
        self.last_transaction_map: dict[tuple[str, str], dict] = {}
        for master in master_users:
            self.db.add_admin(master, "system", "bootstrap")
            self.db.add_to_whitelist(master, "system", "bootstrap")

    def process_envelope(self, msg: NormalizedMessageEnvelope) -> list[CoreAction]:
        collector = CoreActionCollector()
        self.commands.set_action_collector(collector)
        try:
            return self._process_envelope(msg, collector)
        finally:
            self.commands.set_action_collector(None)

    def handle_message(self, msg: NormalizedMessageEnvelope) -> list[CoreAction]:
        return self.process_envelope(msg)

    def _process_envelope(self, msg: NormalizedMessageEnvelope, collector: CoreActionCollector) -> list[CoreAction]:
        if not msg.message_id or msg.message_id in self.processed_message_ids:
            return collector.actions
        self.processed_message_ids.add(msg.message_id)
        if len(self.processed_message_ids) > 4000:
            self.processed_message_ids = set(list(self.processed_message_ids)[-2000:])

        if not msg.is_group or not msg.content:
            return collector.actions
        if msg.content_type != "text":
            return collector.actions
        if msg.sender_kind not in ("user", "self"):
            return collector.actions

        group_key = self._group_key(msg.platform, msg.chat_id)
        sender_name = msg.sender_name or msg.sender_id
        observed_id = msg.sender_id or sender_name
        sender_id = self.db.resolve_identity(
            platform=msg.platform,
            chat_id=msg.chat_id,
            observed_id=observed_id,
            observed_name=sender_name,
        )
        text = msg.content.strip()
        self.logger.info("[%s] %s (%s): %s", group_key, sender_name, sender_id, text)

        if text.startswith("/"):
            command_name = text[1:].split(" ", 1)[0].lower()
            if command_name in {"set", "bind", "bindid", "whoami"} or self.db.is_group_active(group_key):
                self.commands.handle_command(
                    platform=msg.platform,
                    group_key=group_key,
                    chat_id=msg.chat_id,
                    chat_name=msg.chat_name,
                    sender_id=sender_id,
                    sender_name=sender_name,
                    command_text=text,
                    observed_id=observed_id,
                )
            return collector.actions

        if not self.db.is_group_active(group_key):
            return collector.actions

        ngn_expr = self._parse_ngn_expression(text)
        if ngn_expr is not None:
            if self.db.get_group_num(group_key) == 2 and self.commands.can_manage(sender_id):
                ngn_rate = self.db.get_ngn_rate()
                if ngn_rate is None:
                    collector.send_text(msg.chat_id, "Please set NGN rate first (use /ngn command)")
                else:
                    num1, num2 = ngn_expr
                    intermediate = int(num2 * ngn_rate)
                    result = int(num1 * intermediate)
                    collector.send_text(msg.chat_id, f"{num1:g}*{intermediate}=NGN {result}")
            return collector.actions

        timer_minutes = self._parse_timer(text)
        if timer_minutes is not None:
            self._create_reminder_if_needed(msg, group_key, sender_id, timer_minutes)
            return collector.actions

        if not looks_like_transaction(text):
            return collector.actions
        if not self.commands.can_manage(sender_id):
            return collector.actions

        tx = parse_transaction(text)
        if tx is None:
            collector.send_text(msg.chat_id, f"Invalid transaction format: {text}")
            return collector.actions
        if tx.category != "rmb" and (tx.rate is None or tx.rate <= 0 or tx.rate > 10):
            collector.send_text(msg.chat_id, f"Rate error: Rate must be between 0-10\nCurrent: {tx.rate}")
            return collector.actions

        group_num = self.db.get_group_num(group_key)
        record = build_runtime_record(
            platform=msg.platform,
            group_key=group_key,
            group_num=group_num,
            chat_id=msg.chat_id,
            chat_name=msg.chat_name,
            sender_id=sender_id,
            sender_name=sender_name,
            message_id=msg.message_id,
            created_at=None,
            parsed=tx,
        )
        persist_transaction_record(self.db, record)
        self.commands.clear_undo_lock(group_key)
        balance = self.db.get_balance(group_key)
        collector.send_text(msg.chat_id, self._confirmation_text(group_key, tx, balance["total"]))

        ngn_rate = self.db.get_ngn_rate()
        ngn_value = tx.rmb_value * ngn_rate if (group_num == 2 and ngn_rate is not None) else None
        self.last_transaction_map[(group_key, sender_id)] = {
            "platform": msg.platform,
            "chat_id": msg.chat_id,
            "sender_id": sender_id,
            "message": f"{'+' if tx.input_sign > 0 else '-'}{tx.amount:g} {tx.category.upper()} x{tx.rate:g}" if tx.rate else tx.raw,
            "amount": tx.amount,
            "category": tx.category,
            "rate": tx.rate,
            "rmb_value": tx.rmb_value,
            "ngn_value": ngn_value,
            "timestamp": time.time(),
        }
        return collector.actions

    def flush_due_actions(self) -> list[CoreAction]:
        collector = CoreActionCollector()
        now_text = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        for reminder in self.db.get_due_reminders(now_text):
            text = f"Payment Reminder!\n{reminder.message}"
            if reminder.ngn_value is not None:
                text += f" = {'+' if reminder.ngn_value >= 0 else '-'}{abs(reminder.ngn_value):.0f} NGN"
            text += f"\n{reminder.duration_minutes} minutes elapsed"
            if collector.send_text(reminder.chat_id, text):
                self.db.mark_reminder_sent(reminder.id)
        return collector.actions

    def flush_due_reminders(self) -> list[CoreAction]:
        return self.flush_due_actions()

    def _create_reminder_if_needed(self, msg: NormalizedMessageEnvelope, group_key: str, sender_id: str, minutes: int) -> None:
        last_tx = self.last_transaction_map.get((group_key, sender_id))
        if not last_tx or time.time() - last_tx["timestamp"] > 5 * 60:
            return
        remind_at = (datetime.utcnow() + timedelta(minutes=minutes)).strftime("%Y-%m-%d %H:%M:%S")
        self.db.create_reminder(
            platform=msg.platform,
            chat_id=msg.chat_id,
            sender_id=sender_id,
            message=last_tx["message"],
            amount=last_tx["amount"],
            category=last_tx["category"],
            rate=last_tx["rate"],
            rmb_value=last_tx["rmb_value"],
            ngn_value=last_tx["ngn_value"],
            duration_minutes=minutes,
            remind_at=remind_at,
        )
        # timer 功能仍保留在 core 内部，但动作会在统一 runtime 边界外执行
        self.last_transaction_map.pop((group_key, sender_id), None)

    def _confirmation_text(self, group_key: str, tx, balance_total: float) -> str:
        group_num = self.db.get_group_num(group_key)
        ngn_rate = self.db.get_ngn_rate()
        if group_num == 2 and ngn_rate is not None:
            ngn_amount = tx.rmb_value * ngn_rate
            rmb_sign = "+" if tx.rmb_value >= 0 else "-"
            ngn_sign = "+" if ngn_amount >= 0 else "-"
            if tx.category == "rmb":
                body = f"✅ {rmb_sign}{abs(tx.rmb_value):.2f} ({ngn_sign}{abs(ngn_amount):.0f} NGN)"
            else:
                body = (
                    f"✅ {'+' if tx.input_sign > 0 else '-'}{tx.amount:g} {tx.category.upper()} ×{tx.rate:g} = "
                    f"{rmb_sign}{abs(tx.rmb_value):.2f} ({ngn_sign}{abs(ngn_amount):.0f} NGN)"
                )
            return body + f"\n📊 Balance: {'+' if balance_total >= 0 else '-'}{abs(balance_total):.2f}\n🥛₦ {ngn_rate:g}"
        return format_confirmation(tx) + f"\n📊 Balance: {'+' if balance_total >= 0 else '-'}{abs(balance_total):.2f}"

    @staticmethod
    def _group_key(platform: str, chat_id: str) -> str:
        return f"{platform}:{chat_id}"

    @staticmethod
    def _parse_timer(text: str) -> int | None:
        if text.endswith("mins") and text[:-4].isdigit():
            return int(text[:-4])
        return None

    @staticmethod
    def _parse_ngn_expression(text: str) -> tuple[float, float] | None:
        parts = text.split("*")
        if len(parts) != 2:
            return None
        try:
            return float(parts[0]), float(parts[1])
        except ValueError:
            return None
