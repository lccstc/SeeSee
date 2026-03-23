from __future__ import annotations

from datetime import datetime, timedelta

from .database import BookkeepingDB
from .role_mapping import resolve_business_role


class AccountingPeriodService:
    def __init__(self, db: BookkeepingDB) -> None:
        self.db = db

    def settle_group_with_receipts(self, *, group_key: str, closed_by: str, note: str | None = None) -> dict | None:
        period_id = self.close_group_unsettled(
            group_key=group_key,
            closed_by=closed_by,
            note=note,
        )
        if period_id is None:
            return None
        summary = self.build_period_close_summary(period_id)
        receipt_actions = self.build_period_group_receipt_actions(period_id)
        return {
            "period_id": period_id,
            "summary": summary,
            "receipt_actions": receipt_actions,
        }

    def settle_all_with_receipts(self, *, closed_by: str, note: str | None = None) -> dict | None:
        period_id = self.close_all_unsettled(
            closed_by=closed_by,
            note=note,
        )
        if period_id is None:
            return None
        summary = self.build_period_close_summary(period_id)
        receipt_actions = self.build_period_group_receipt_actions(period_id)
        return {
            "period_id": period_id,
            "summary": summary,
            "receipt_actions": receipt_actions,
        }

    def build_period_group_receipt_actions(self, period_id: int) -> list[dict[str, object]]:
        actions: list[dict[str, object]] = []
        for snapshot in self.db.list_period_group_snapshots(period_id):
            transaction_count = int(snapshot["transaction_count"] or 0)
            if transaction_count <= 0:
                continue
            group_row = self.db.get_group_by_key(str(snapshot["group_key"]))
            chat_id = str(group_row["chat_id"] or "").strip() if group_row is not None else ""
            if not chat_id:
                continue
            actions.append(
                {
                    "action_type": "send_text",
                    "chat_id": chat_id,
                    "text": self._format_group_close_receipt(snapshot),
                }
            )
        return actions

    def close_group_unsettled(self, *, group_key: str, closed_by: str, note: str | None = None) -> int | None:
        txs = self.db.get_unsettled_transactions(group_key)
        if not txs:
            return None
        start_at = self._resolve_period_start_at(txs)
        end_at = max(str(tx["created_at"]) for tx in txs)
        return self.close_period(
            start_at=start_at,
            end_at=end_at,
            closed_by=closed_by,
            note=note,
        )

    def close_all_unsettled(self, *, closed_by: str, note: str | None = None) -> int | None:
        rows = self.db.get_groups_with_unsettled_transactions()
        if not rows:
            return None
        txs = []
        for row in rows:
            txs.extend(self.db.get_unsettled_transactions(str(row["group_key"])))
        if not txs:
            return None
        start_at = self._resolve_period_start_at(txs)
        end_at = max(str(tx["created_at"]) for tx in txs)
        return self.close_period(
            start_at=start_at,
            end_at=end_at,
            closed_by=closed_by,
            note=note,
        )

    def build_period_close_summary(self, period_id: int) -> dict[str, float | int]:
        rows = self.db.list_period_group_snapshots(period_id)
        active_rows = [row for row in rows if int(row["transaction_count"] or 0) > 0]
        total_rmb = sum(float(row["income"] or 0) - float(row["expense"] or 0) for row in active_rows)
        transaction_count = sum(int(row["transaction_count"] or 0) for row in active_rows)
        return {
            "period_id": period_id,
            "group_count": len(active_rows),
            "transaction_count": transaction_count,
            "total_rmb": total_rmb,
        }

    def close_period(self, *, start_at: str, end_at: str, closed_by: str, note: str | None = None) -> int:
        groups = self.db.list_groups()
        transaction_ids_to_close: list[int] = []
        self.db.conn.execute("BEGIN")
        try:
            period_id = self.db.insert_accounting_period(
                start_at=start_at,
                end_at=end_at,
                closed_at=end_at,
                closed_by=closed_by,
                note=note,
                has_adjustment=0,
                snapshot_version=1,
            )
            card_stats_rows: list[dict] = []
            for group in groups:
                group_key = str(group["group_key"])
                business_role = resolve_business_role(
                    business_role=group["business_role"],
                    group_num=int(group["group_num"]) if group["group_num"] is not None else None,
                )
                opening_balance = self.db.get_group_balance_before(group_key, start_at)
                txs = self.db.list_group_transactions_between(group_key, start_at, end_at)
                transaction_ids_to_close.extend(
                    int(tx["id"])
                    for tx in txs
                    if int(tx["deleted"] or 0) == 0 and int(tx["settled"] or 0) == 0
                )
                income = sum(float(tx["rmb_value"]) for tx in txs if float(tx["rmb_value"]) > 0)
                expense = sum(abs(float(tx["rmb_value"])) for tx in txs if float(tx["rmb_value"]) < 0)
                closing_balance = opening_balance + income - expense
                self.db.insert_period_group_snapshot(
                    period_id=period_id,
                    group_key=group_key,
                    platform=str(group["platform"]),
                    chat_name=str(group["chat_name"]),
                    group_num=int(group["group_num"]) if group["group_num"] is not None else None,
                    business_role=business_role,
                    opening_balance=opening_balance,
                    income=income,
                    expense=expense,
                    closing_balance=closing_balance,
                    transaction_count=len(txs),
                )
                card_stats_rows.extend(self._build_card_stats(period_id, group_key, group, txs))
            self.db.replace_period_card_stats(period_id, card_stats_rows)
            self.db.mark_transactions_closed(transaction_ids_to_close, settled_at=end_at, commit=False)
            self.db.conn.commit()
            return period_id
        except Exception:
            self.db.conn.rollback()
            raise

    @staticmethod
    def _build_card_stats(
        period_id: int,
        group_key: str,
        group_row,
        txs,
    ) -> list[dict]:
        buckets: dict[tuple[str, float | None, float | None], dict] = {}
        for tx in txs:
            category = str(tx["category"] or "rmb")
            card_type = "rmb" if category == "rmb" else category
            rate = float(tx["rate"]) if tx["rate"] is not None else None
            unit_face_value = float(tx["unit_face_value"]) if tx["unit_face_value"] is not None else None
            key = (card_type, rate, unit_face_value)
            bucket = buckets.setdefault(
                key,
                {
                    "group_key": group_key,
                    "business_role": resolve_business_role(
                        business_role=group_row["business_role"] if group_row is not None else None,
                        group_num=int(group_row["group_num"]) if group_row is not None and group_row["group_num"] is not None else None,
                    ),
                    "card_type": card_type,
                    "usd_amount": 0.0,
                    "rate": rate,
                    "rmb_amount": 0.0,
                    "unit_face_value": unit_face_value,
                    "unit_count": 0.0,
                    "sample_raw": str(tx["raw"]),
                },
            )
            bucket["usd_amount"] += (
                float(tx["usd_amount"])
                if tx["usd_amount"] is not None
                else (0.0 if card_type == "rmb" else float(tx["amount"] or 0))
            )
            bucket["rmb_amount"] += float(tx["rmb_value"])
            if tx["unit_count"] is not None:
                bucket["unit_count"] += float(tx["unit_count"])
        return [
            {
                "period_id": period_id,
                **row,
            }
            for row in buckets.values()
        ]

    def _resolve_period_start_at(self, txs) -> str:
        periods = self.db.list_accounting_periods()
        if periods:
            latest = max(
                periods,
                key=lambda row: (str(row["closed_at"]), int(row["id"])),
            )
            return str(latest["end_at"])
        earliest_created_at = min(str(tx["created_at"]) for tx in txs)
        earliest_dt = self._parse_db_timestamp(earliest_created_at) - timedelta(seconds=1)
        return earliest_dt.strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def _parse_db_timestamp(value) -> datetime:
        if isinstance(value, datetime):
            return value
        text = str(value).strip()
        return datetime.fromisoformat(text.replace("Z", "+00:00")).replace(tzinfo=None)

    @staticmethod
    def _format_group_close_receipt(snapshot) -> str:
        opening_balance = float(snapshot["opening_balance"] or 0)
        income = float(snapshot["income"] or 0)
        expense = float(snapshot["expense"] or 0)
        closing_balance = float(snapshot["closing_balance"] or 0)
        transaction_count = int(snapshot["transaction_count"] or 0)
        return (
            "✅ Group settled\n"
            f"📘 Period ID: {int(snapshot['period_id'])}\n"
            f"📝 Transactions: {transaction_count}\n"
            f"📂 Opening Balance: {AccountingPeriodService._signed_amount(opening_balance)}\n"
            f"💵 Income: {AccountingPeriodService._signed_amount(income)}\n"
            f"💸 Expense: -{abs(expense):.2f}\n"
            f"💰 Closing Balance: {AccountingPeriodService._signed_amount(closing_balance)}"
        )

    @staticmethod
    def _signed_amount(value: float) -> str:
        sign = "+" if value >= 0 else "-"
        return f"{sign}{abs(value):.2f}"
