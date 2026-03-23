from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from .periods import AccountingPeriodService


class _NullActionCollector:
    def send_text(self, chat_id: str, text: str) -> bool:
        return False

    def send_file(self, chat_id: str, file_path: str, caption: str | None = None) -> bool:
        return False


class CommandHandler:
    def __init__(self, db, master_users: list[str], export_dir: str | Path) -> None:
        self.db = db
        self.action_collector = _NullActionCollector()
        self.bootstrap_masters = set(master_users)
        self.export_dir = Path(export_dir)
        self.last_undo_group_key: str | None = None

    def set_action_collector(self, action_collector) -> None:
        self.action_collector = action_collector or _NullActionCollector()

    def handle_command(
        self,
        *,
        platform: str,
        group_key: str,
        chat_id: str,
        chat_name: str,
        sender_id: str,
        sender_name: str,
        command_text: str,
        observed_id: str | None = None,
    ) -> None:
        parts = command_text[1:].split(" ", 1)
        name = parts[0].lower()
        args = parts[1].strip() if len(parts) > 1 else ""
        observed_id = str(observed_id or sender_id or "").strip()
        dispatch = {
            "bal": lambda: self.handle_balance(group_key, chat_id),
            "history": lambda: self.handle_history(group_key, chat_id, args),
            "undo": lambda: self.handle_undo(group_key, chat_id, sender_id),
            "clear": lambda: self.handle_clear(group_key, chat_id, sender_id),
            "adduser": lambda: self.handle_add_user(chat_id, sender_id, args),
            "rmuser": lambda: self.handle_remove_user(chat_id, sender_id, args),
            "addmaster": lambda: self.handle_add_master(chat_id, sender_id, args),
            "rmmaster": lambda: self.handle_remove_master(chat_id, sender_id, args),
            "users": lambda: self.handle_users(chat_id, sender_id),
            "bkstats": lambda: self.handle_stats(chat_id, sender_id),
            "export": lambda: self.handle_export(group_key, chat_id, sender_id),
            "js": lambda: self.handle_settle(platform, group_key, chat_id, sender_id),
            "alljs": lambda: self.handle_all_settle(platform, chat_id, sender_id),
            "mx": lambda: self.handle_mingxi(group_key, chat_id, args),
            "set": lambda: self.handle_set_group(platform, group_key, chat_id, chat_name, sender_id, args),
            "diy": lambda: self.handle_diy_send(chat_id, sender_id, args),
            "ngn": lambda: self.handle_ngn(chat_id, sender_id, args),
            "whoami": lambda: self.handle_whoami(chat_id, sender_id, sender_name, observed_id),
            "bind": lambda: self.handle_bind(platform, chat_id, sender_name, observed_id, sender_id, args, command_name="bind"),
            "bindid": lambda: self.handle_bind(platform, chat_id, sender_name, observed_id, sender_id, args, command_name="bindid"),
        }
        action = dispatch.get(name)
        if action:
            action()

    def can_manage(self, sender_id: str) -> bool:
        return self.is_master(sender_id) or self.db.is_whitelisted(sender_id)

    def is_master(self, sender_id: str) -> bool:
        return sender_id in self.bootstrap_masters or self.db.is_admin(sender_id)

    def clear_undo_lock(self, group_key: str) -> None:
        if self.last_undo_group_key == group_key:
            self.last_undo_group_key = None

    def _group_num_display(self, group_key: str) -> str:
        group_num = self.db.get_group_num(group_key)
        return f"Group {group_num}" if group_num is not None else "Ungrouped"

    def _is_group2(self, group_key: str) -> bool:
        return self.db.get_group_num(group_key) == 2

    def handle_balance(self, group_key: str, chat_id: str) -> None:
        bal = self.db.get_balance(group_key)
        ngn_rate = self.db.get_ngn_rate()
        group_display = self._group_num_display(group_key)
        is_group2 = self._is_group2(group_key)

        if bal["count"] == 0:
            msg = f"📊 Current Balance: 0.00\n📝 No transactions\n📋 Group: {group_display}"
        else:
            sign = "+" if bal["total"] >= 0 else "-"
            msg = f"📊 Balance: {sign}{abs(bal['total']):.2f}\n📋 Group: {group_display}\n"
            categories = self.db.get_category_mingxi(group_key)
            if categories:
                unsettled_count = sum(rate_group["count"] for cat in categories for rate_group in cat["rate_groups"])
                msg += f"📝 Unsettled: {unsettled_count}\n\nDetails:\n"
                grand_total_amount = 0.0
                for cat in categories:
                    cat_total_amount = sum(rate_group["total_amount"] for rate_group in cat["rate_groups"])
                    amt_sign = "+" if cat_total_amount >= 0 else "-"
                    msg += f"{cat['category'].upper()}: {amt_sign}{abs(cat_total_amount):.0f}\n"
                    grand_total_amount += cat_total_amount
                grand_sign = "+" if grand_total_amount >= 0 else "-"
                msg += f"────────\nTotal: {grand_sign}{abs(grand_total_amount):.0f}\n"
            else:
                msg += "✅ All transactions settled\n"

        if ngn_rate is not None and is_group2:
            msg += f"\n🥛₦ {ngn_rate:g}"
        self.action_collector.send_text(chat_id, msg.rstrip())

    def handle_history(self, group_key: str, chat_id: str, args: str) -> None:
        if args and args.isdigit():
            rows = self.db.get_history(group_key, int(args))
        elif args and len(args) <= 10:
            rows = self.db.get_history_by_category(group_key, args.lower())
        else:
            rows = self.db.get_history(group_key, 20)
        if not rows:
            self.action_collector.send_text(chat_id, "📝 No transactions")
            return

        lines = [f"📝 Last {len(rows)} transactions:"]
        for row in reversed(rows):
            created = self._parse_db_timestamp(row["created_at"]) + timedelta(hours=7)
            time_text = created.strftime("%m-%d %H:%M")
            if row["category"] == "rmb":
                sign = "+" if row["rmb_value"] >= 0 else "-"
                lines.append(f"{time_text} | {sign}{abs(row['rmb_value']):.2f}")
            else:
                rmb_sign = "+" if row["rmb_value"] >= 0 else "-"
                input_sign = "+" if row["input_sign"] > 0 else "-"
                lines.append(f"{time_text} | {input_sign}{row['amount']:g}{row['category'].upper()} ×{row['rate']:g} = {rmb_sign}{abs(row['rmb_value']):.2f}")
        self.action_collector.send_text(chat_id, "\n".join(lines))

    def handle_undo(self, group_key: str, chat_id: str, sender_id: str) -> None:
        if not self.can_manage(sender_id):
            self.action_collector.send_text(chat_id, "❌ Permission denied")
            return
        if self.last_undo_group_key == group_key:
            self.action_collector.send_text(chat_id, "⚠️ Consecutive undo blocked\nPlease record a new transaction first")
            return
        deleted = self.db.undo_last(group_key)
        if deleted is None:
            self.action_collector.send_text(chat_id, "❌ No transaction to undo")
            return
        self.last_undo_group_key = group_key
        sign = "+" if deleted["rmb_value"] >= 0 else "-"
        self.action_collector.send_text(chat_id, f"↩️ Undone: {deleted['raw']} ({sign}{abs(deleted['rmb_value']):.2f})\n⚠️ To continue undoing, please record a new transaction first")

    def handle_clear(self, group_key: str, chat_id: str, sender_id: str) -> None:
        if not self.is_master(sender_id):
            self.action_collector.send_text(chat_id, "❌ Admin only")
            return
        count = self.db.clear_group(group_key)
        self.action_collector.send_text(chat_id, f"🗑️ Cleared {count} transactions")

    def handle_add_user(self, chat_id: str, sender_id: str, args: str) -> None:
        if not self.is_master(sender_id):
            self.action_collector.send_text(chat_id, "❌ Admin only")
            return
        user_key = args.strip()
        if not user_key:
            self.action_collector.send_text(chat_id, "❌ Format: /adduser 微信号")
            return
        self.db.add_to_whitelist(user_key, sender_id)
        self.action_collector.send_text(chat_id, f"✅ Added user: {user_key}")

    def handle_remove_user(self, chat_id: str, sender_id: str, args: str) -> None:
        if not self.is_master(sender_id):
            self.action_collector.send_text(chat_id, "❌ Admin only")
            return
        user_key = args.strip()
        if not user_key:
            self.action_collector.send_text(chat_id, "❌ Format: /rmuser 微信号")
            return
        if self.is_master(user_key):
            self.action_collector.send_text(chat_id, "❌ Cannot remove admin by /rmuser")
            return
        removed = self.db.remove_from_whitelist(user_key)
        self.action_collector.send_text(chat_id, f"{'✅ Removed user' if removed else '❌ User not found'}: {user_key}")

    def handle_add_master(self, chat_id: str, sender_id: str, args: str) -> None:
        if not self.is_master(sender_id):
            self.action_collector.send_text(chat_id, "❌ Admin only")
            return
        user_key = args.strip()
        if not user_key:
            self.action_collector.send_text(chat_id, "❌ Format: /addmaster 微信号")
            return
        self.db.add_admin(user_key, sender_id)
        self.action_collector.send_text(chat_id, f"✅ Added admin: {user_key}")

    def handle_remove_master(self, chat_id: str, sender_id: str, args: str) -> None:
        if not self.is_master(sender_id):
            self.action_collector.send_text(chat_id, "❌ Admin only")
            return
        user_key = args.strip()
        if not user_key:
            self.action_collector.send_text(chat_id, "❌ Format: /rmmaster 微信号")
            return
        if user_key in self.bootstrap_masters:
            self.action_collector.send_text(chat_id, "❌ Cannot remove bootstrap admin")
            return
        removed = self.db.remove_admin(user_key)
        self.action_collector.send_text(chat_id, f"{'✅ Removed admin' if removed else '❌ Admin not found'}: {user_key}")

    def handle_users(self, chat_id: str, sender_id: str) -> None:
        if not self.is_master(sender_id):
            self.action_collector.send_text(chat_id, "❌ Admin only")
            return
        admins = self.db.get_admins()
        users = self.db.get_whitelist()
        lines = ["📋 Roles:"]
        bootstrap_lines = sorted(self.bootstrap_masters)
        if bootstrap_lines:
            lines.append("Admins (bootstrap):")
            lines.extend(f"  {item}" for item in bootstrap_lines)
        if admins:
            lines.append("Admins (database):")
            lines.extend(f"  {row['user_key']}" for row in admins)
        if users:
            lines.append("Users:")
            lines.extend(f"  {row['user_key']}" for row in users)
        if len(lines) == 1:
            lines.append("  No roles configured")
        self.action_collector.send_text(chat_id, "\n".join(lines))

    def handle_stats(self, chat_id: str, sender_id: str) -> None:
        if not self.is_master(sender_id):
            self.action_collector.send_text(chat_id, "❌ Admin only")
            return
        lines = [
            "📈 Bookkeeping Stats",
            f"Groups: {self.db.get_group_count()}",
            f"Transactions: {self.db.get_total_transaction_count()}",
            f"Admins: {len(self.bootstrap_masters) + len(self.db.get_admins())}",
            f"Users: {len(self.db.get_whitelist())}",
            "",
            "📊 Group Stats:",
        ]
        for num, count in self.db.get_group_number_stats().items():
            if count:
                lines.append(f"  Group {num}: {count} groups")
        self.action_collector.send_text(chat_id, "\n".join(lines))

    def handle_export(self, group_key: str, chat_id: str, sender_id: str) -> None:
        if not self.is_master(sender_id):
            self.action_collector.send_text(chat_id, "❌ Admin only")
            return
        path = self.db.export_group_csv(group_key, self.export_dir)
        if path is None:
            self.action_collector.send_text(chat_id, "❌ No data to export")
            return
        if not self.action_collector.send_file(chat_id, str(path)):
            self.action_collector.send_text(chat_id, f"Exported file ready: {path}")

    def handle_settle(self, platform: str, group_key: str, chat_id: str, sender_id: str) -> None:
        if not self.can_manage(sender_id):
            self.action_collector.send_text(chat_id, "❌ Permission denied")
            return
        period_service = AccountingPeriodService(self.db)
        result = period_service.settle_group_with_receipts(
            group_key=group_key,
            closed_by=sender_id,
            note=f"/js from {group_key}",
        )
        if result is None:
            self.action_collector.send_text(chat_id, "✅ No unsettled transactions")
            return
        summary = result["summary"]
        self.action_collector.send_text(chat_id, self._format_period_close_message(summary))

    def handle_all_settle(self, platform: str, chat_id: str, sender_id: str) -> None:
        if not self.can_manage(sender_id):
            self.action_collector.send_text(chat_id, "❌ Permission denied")
            return
        period_service = AccountingPeriodService(self.db)
        result = period_service.settle_all_with_receipts(
            closed_by=sender_id,
            note="/alljs",
        )
        if result is None:
            self.action_collector.send_text(chat_id, "✅ No unsettled transactions in any group")
            return
        summary = result["summary"]
        self.action_collector.send_text(chat_id, self._format_period_close_message(summary))

    def handle_mingxi(self, group_key: str, chat_id: str, args: str) -> None:
        bal = self.db.get_balance(group_key)
        ngn_rate = self.db.get_ngn_rate()
        is_group2 = self._is_group2(group_key)
        categories = self.db.get_category_mingxi(group_key)

        if not args:
            bal_sign = "+" if bal["total"] >= 0 else ""
            msg = f"📊 Details:\n💰 Balance: {bal_sign}{bal['total']:.2f}"
            if ngn_rate is not None and is_group2:
                msg += f"\n🥛₦ {ngn_rate:g}"
            if not categories:
                msg += "\n📝 No transactions" if bal["count"] == 0 else "\n✅ All transactions settled"
                self.action_collector.send_text(chat_id, msg.rstrip())
                return
            msg += "\n"
            grand_total_amount = 0.0
            grand_total_rmb = 0.0
            for cat in categories:
                msg += f"{cat['category'].upper()}:\n"
                cat_total_amount = 0.0
                cat_total_rmb = 0.0
                for rate_group in cat["rate_groups"]:
                    rmb_sign = "+" if rate_group["total_rmb"] >= 0 else "-"
                    if rate_group["rate"] is None or cat["category"] == "rmb":
                        msg += f"  {rate_group['count']} txs {rmb_sign}{abs(rate_group['total_rmb']):.2f}\n"
                        cat_total_rmb += rate_group["total_rmb"]
                    else:
                        cat_total_amount += rate_group["total_amount"]
                        cat_total_rmb += rate_group["total_rmb"]
                        if is_group2 and rate_group["total_ngn"] is not None:
                            ngn_sign = "+" if rate_group["total_ngn"] >= 0 else "-"
                            msg += f"  x{rate_group['rate']:g}: {rate_group['total_amount']:.0f} = {rmb_sign}{abs(rate_group['total_rmb']):.2f} ({ngn_sign}{abs(rate_group['total_ngn']):.0f} NGN)\n"
                        else:
                            msg += f"  x{rate_group['rate']:g}: {rate_group['total_amount']:.0f} = {rmb_sign}{abs(rate_group['total_rmb']):.2f}\n"
                msg += "--------\n"
                if cat["category"] == "rmb":
                    rmb_sign = "+" if cat_total_rmb >= 0 else "-"
                    msg += f"  Subtotal: {rmb_sign}{abs(cat_total_rmb):.2f}\n"
                else:
                    amt_sign = "+" if cat_total_amount >= 0 else "-"
                    rmb_sign = "+" if cat_total_rmb >= 0 else "-"
                    msg += f"  Subtotal: {amt_sign}{abs(cat_total_amount):.0f} = {rmb_sign}{abs(cat_total_rmb):.2f}\n"
                    grand_total_amount += cat_total_amount
                    grand_total_rmb += cat_total_rmb
            grand_amt_sign = "+" if grand_total_amount >= 0 else "-"
            grand_rmb_sign = "+" if grand_total_rmb >= 0 else "-"
            msg += f"==========\nTotal: {grand_amt_sign}{abs(grand_total_amount):.0f} = {grand_rmb_sign}{abs(grand_total_rmb):.2f}"
            self.action_collector.send_text(chat_id, msg.rstrip())
            return

        category = args.strip().lower()
        cat_data = next((item for item in categories if item["category"] == category), None)
        if cat_data is None or not cat_data["rate_groups"]:
            self.action_collector.send_text(chat_id, f"📝 No transactions for {category.upper()}")
            return
        bal_sign = "+" if bal["total"] >= 0 else ""
        msg = f"📋 {category.upper()}:\n💰 Balance: {bal_sign}{bal['total']:.2f}"
        if ngn_rate is not None and is_group2:
            msg += f"\n🥛₦ {ngn_rate:g}"
        msg += "\n"
        net_amount = 0.0
        total_rmb = 0.0
        total_ngn = 0.0
        for rate_group in cat_data["rate_groups"]:
            sign = "+" if rate_group["total_rmb"] >= 0 else "-"
            net_amount += rate_group["total_amount"]
            total_rmb += rate_group["total_rmb"]
            total_ngn += rate_group["total_ngn"] or 0.0
            if rate_group["rate"] is None or category == "rmb":
                msg += f"  {rate_group['count']} txs {sign}{abs(rate_group['total_rmb']):.2f}\n"
            elif is_group2 and rate_group["total_ngn"] is not None:
                ngn_sign = "+" if rate_group["total_ngn"] >= 0 else "-"
                msg += f"  x{rate_group['rate']:g}: {rate_group['total_amount']:.0f} = {sign}{abs(rate_group['total_rmb']):.2f} ({ngn_sign}{abs(rate_group['total_ngn']):.0f} NGN)\n"
            else:
                msg += f"  x{rate_group['rate']:g}: {rate_group['total_amount']:.0f} = {sign}{abs(rate_group['total_rmb']):.2f}\n"
        total_rmb_sign = "+" if total_rmb >= 0 else "-"
        if category == "rmb":
            msg += f"\nTotal: {total_rmb_sign}{abs(total_rmb):.2f}"
        else:
            net_sign = "+" if net_amount >= 0 else "-"
            if is_group2:
                ngn_sign = "+" if total_ngn >= 0 else "-"
                msg += f"\nTotal: {net_sign}{abs(net_amount):.0f} {total_rmb_sign}{abs(total_rmb):.2f} ({ngn_sign}{abs(total_ngn):.0f} NGN)"
            else:
                msg += f"\nTotal: {net_sign}{abs(net_amount):.0f} {total_rmb_sign}{abs(total_rmb):.2f}"
        self.action_collector.send_text(chat_id, msg.rstrip())

    def handle_set_group(self, platform: str, group_key: str, chat_id: str, chat_name: str, sender_id: str, args: str) -> None:
        if not self.can_manage(sender_id):
            self.action_collector.send_text(chat_id, "❌ Admin only")
            return
        if not args or not args.isdigit() or len(args) != 1:
            self.action_collector.send_text(chat_id, "❌ Format: /set number (0-9)\nEx: /set 1")
            return
        group_num = int(args)
        if not self.db.set_group(platform=platform, group_key=group_key, chat_id=chat_id, chat_name=chat_name, group_num=group_num):
            self.action_collector.send_text(chat_id, "❌ Failed, please retry")
            return
        self.action_collector.send_text(chat_id, f"✅ This group assigned to Group {group_num}\nOnly groups with numbers can use bookkeeping")

    def handle_diy_send(self, chat_id: str, sender_id: str, args: str) -> None:
        if not self.can_manage(sender_id):
            self.action_collector.send_text(chat_id, "Admin only")
            return
        parts = args.split(" ", 1)
        if len(parts) != 2 or not parts[0].isdigit():
            self.action_collector.send_text(chat_id, "Format: /diy number message\nEx: /diy 1 Hello everyone")
            return
        group_num = int(parts[0])
        message = parts[1].strip()
        groups = self.db.get_groups_by_num(group_num)
        if not groups:
            self.action_collector.send_text(chat_id, f"Group {group_num} has no groups")
            return
        total_groups = len(groups)
        estimated_time = max(1, int((total_groups / 5) * 1.5 + 0.999))
        self.action_collector.send_text(chat_id, f"Starting broadcast...\nGroup: {group_num}\nTarget: {total_groups} groups\nEst. time: {estimated_time}s")
        results: list[tuple[dict, bool]] = []
        for index, group in enumerate(groups, start=1):
            ok = self.action_collector.send_text(group["chat_id"], message)
            results.append((group, ok))
            if index % 10 == 0:
                success = sum(1 for _, sent in results if sent)
                self.action_collector.send_text(chat_id, f"Progress: {index}/{total_groups} (Success: {success})")
        success_count = sum(1 for _, sent in results if sent)
        fail_groups = [group["chat_name"] for group, sent in results if not sent]
        lines = ["Broadcast complete!", "----------------", f"Group: {group_num}", f"Total: {total_groups} groups", f"Success: {success_count} groups"]
        if fail_groups:
            lines.append(f"Failed: {len(fail_groups)} groups")
        lines.extend(["----------------", f"Content: {message[:40]}{'...' if len(message) > 40 else ''}"])
        if fail_groups:
            lines.append("Failed groups:")
            lines.extend(f"{index}. {name}" for index, name in enumerate(fail_groups, start=1))
        self.action_collector.send_text(chat_id, "\n".join(lines))

    def handle_ngn(self, chat_id: str, sender_id: str, args: str) -> None:
        if not self.can_manage(sender_id):
            self.action_collector.send_text(chat_id, "❌ Admin only")
            return
        try:
            rate = float(args)
        except ValueError:
            self.action_collector.send_text(chat_id, "❌ Format: /ngn number\nEx: /ngn 194.2")
            return
        self.db.set_ngn_rate(str(rate))
        self.action_collector.send_text(chat_id, f"✅ NGN rate updated: 🥛₦ {rate:g}")

    def handle_whoami(self, chat_id: str, sender_id: str, sender_name: str, observed_id: str) -> None:
        self.action_collector.send_text(
            chat_id,
            (
                f"name={sender_name or '-'}\n"
                f"observed_id={observed_id or '-'}\n"
                f"id={sender_id or '-'}\n"
                f"is_master={'true' if self.is_master(sender_id) else 'false'}"
            ),
        )

    def handle_bind(
        self,
        platform: str,
        chat_id: str,
        sender_name: str,
        observed_id: str,
        sender_id: str,
        args: str,
        *,
        command_name: str,
    ) -> None:
        canonical_id = args.strip()
        if command_name == "bind":
            if not canonical_id or not canonical_id.startswith("+"):
                self.action_collector.send_text(chat_id, "格式: /bind +国家区号手机号\n例: /bind +85212345678")
                return
        elif not canonical_id:
            self.action_collector.send_text(chat_id, "格式: /bindid 真实微信号\n例: /bindid Button-Leo")
            return

        if not (self.is_master(canonical_id) or self.db.is_whitelisted(canonical_id)):
            self.action_collector.send_text(chat_id, f"目标ID未在管理员或白名单中: {canonical_id}")
            return

        self.db.bind_identity(
            platform=platform,
            chat_id=chat_id,
            observed_id=observed_id,
            observed_name=sender_name or observed_id,
            canonical_id=canonical_id,
        )
        self.action_collector.send_text(
            chat_id,
            (
                f"绑定成功\n"
                f"name={sender_name or '-'}\n"
                f"observed_id={observed_id or '-'}\n"
                f"canonical_id={canonical_id}"
            ),
        )

    @staticmethod
    def _format_period_close_message(summary: dict[str, float | int]) -> str:
        total_rmb = float(summary["total_rmb"])
        sign = "+" if total_rmb >= 0 else "-"
        return (
            "✅ Accounting period closed!\n"
            f"📘 Period ID: {int(summary['period_id'])}\n"
            f"📊 Groups: {int(summary['group_count'])}\n"
            f"📝 Transactions: {int(summary['transaction_count'])}\n"
            f"💰 Total: {sign}{abs(total_rmb):.2f}"
        )

    @staticmethod
    def _parse_db_timestamp(value) -> datetime:
        if isinstance(value, datetime):
            return value
        text = str(value).strip()
        return datetime.fromisoformat(text.replace("Z", "+00:00")).replace(tzinfo=None)
