from __future__ import annotations

from collections import defaultdict

from .database import BookkeepingDB


class AccountingPeriodService:
    def __init__(self, db: BookkeepingDB) -> None:
        self.db = db

    def close_period(self, *, start_at: str, end_at: str, closed_by: str, note: str | None = None) -> int:
        groups = self.db.list_groups()
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
                opening_balance = self.db.get_group_balance_before(group_key, start_at)
                txs = self.db.list_group_transactions_between(group_key, start_at, end_at)
                income = sum(float(tx["rmb_value"]) for tx in txs if float(tx["rmb_value"]) > 0)
                expense = sum(abs(float(tx["rmb_value"])) for tx in txs if float(tx["rmb_value"]) < 0)
                closing_balance = opening_balance + income - expense
                self.db.insert_period_group_snapshot(
                    period_id=period_id,
                    group_key=group_key,
                    platform=str(group["platform"]),
                    chat_name=str(group["chat_name"]),
                    group_num=int(group["group_num"]) if group["group_num"] is not None else None,
                    business_role=str(group["business_role"]) if group["business_role"] is not None else None,
                    opening_balance=opening_balance,
                    income=income,
                    expense=expense,
                    closing_balance=closing_balance,
                    transaction_count=len(txs),
                )
                card_stats_rows.extend(self._build_card_stats(period_id, group_key, group, txs))
            self.db.replace_period_card_stats(period_id, card_stats_rows)
            self.db.conn.commit()
            return period_id
        except Exception:
            self.db.conn.rollback()
            raise

    def backfill_legacy_periods(self) -> int:
        settlements = self.db.list_settlements()
        if not settlements:
            return 0

        created = 0
        running_balance_by_group: dict[str, float] = defaultdict(float)
        previous_closed_at_by_group: dict[str, str] = {}
        existing_rows = self.db.list_accounting_period_snapshots()
        existing_snapshots_by_key = {
            (str(row["group_key"]), str(row["closed_at"])): row
            for row in existing_rows
        }

        self.db.conn.execute("BEGIN")
        try:
            for settlement in settlements:
                settlement_id = int(settlement["id"])
                group_key = str(settlement["group_key"])
                settled_at = str(settlement["settled_at"])
                existing_snapshot = existing_snapshots_by_key.get((group_key, settled_at))
                if existing_snapshot is not None:
                    running_balance_by_group[group_key] = float(existing_snapshot["closing_balance"])
                    previous_closed_at_by_group[group_key] = settled_at
                    continue

                txs = self.db.list_settlement_transactions(settlement_id)
                if not txs:
                    continue

                opening_balance = float(running_balance_by_group[group_key])
                income = sum(float(tx["rmb_value"]) for tx in txs if float(tx["rmb_value"]) > 0)
                expense = sum(abs(float(tx["rmb_value"])) for tx in txs if float(tx["rmb_value"]) < 0)
                closing_balance = opening_balance + income - expense

                group_row = self.db.get_group_by_key(group_key)
                start_at = previous_closed_at_by_group.get(group_key) or str(txs[0]["created_at"])
                adjustments = [
                    row
                    for row in self.db.get_manual_adjustments(settlement_id)
                    if str(row["group_key"]) == group_key
                ]
                adjustment_totals = defaultdict(float)
                for item in adjustments:
                    adjustment_totals["opening_delta"] += float(item["opening_delta"])
                    adjustment_totals["income_delta"] += float(item["income_delta"])
                    adjustment_totals["expense_delta"] += float(item["expense_delta"])
                    adjustment_totals["closing_delta"] += float(item["closing_delta"])
                if adjustments:
                    opening_balance += adjustment_totals["opening_delta"]
                    income += adjustment_totals["income_delta"]
                    expense += adjustment_totals["expense_delta"]
                    closing_balance += adjustment_totals["closing_delta"]
                period_id = self.db.insert_accounting_period(
                    start_at=start_at,
                    end_at=settled_at,
                    closed_at=settled_at,
                    closed_by=str(settlement["settled_by"]),
                    note=str(settlement["detail"]) if settlement["detail"] is not None else None,
                    has_adjustment=1 if adjustments else 0,
                    snapshot_version=1,
                )
                self.db.insert_period_group_snapshot(
                    period_id=period_id,
                    group_key=group_key,
                    platform=str(group_row["platform"]) if group_row is not None else str(settlement["platform"]),
                    chat_name=str(group_row["chat_name"]) if group_row is not None else group_key,
                    group_num=int(group_row["group_num"]) if group_row is not None and group_row["group_num"] is not None else None,
                    business_role=str(group_row["business_role"]) if group_row is not None and group_row["business_role"] is not None else None,
                    opening_balance=opening_balance,
                    income=income,
                    expense=expense,
                    closing_balance=closing_balance,
                    transaction_count=len(txs),
                )
                running_balance_by_group[group_key] = closing_balance
                previous_closed_at_by_group[group_key] = settled_at
                created += 1

            self.db.conn.commit()
        except Exception:
            self.db.conn.rollback()
            raise

        return created

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
                    "business_role": str(group_row["business_role"]) if group_row is not None and group_row["business_role"] is not None else None,
                    "card_type": card_type,
                    "usd_amount": 0.0,
                    "rate": rate,
                    "rmb_amount": 0.0,
                    "unit_face_value": unit_face_value,
                    "unit_count": 0.0,
                    "sample_raw": str(tx["raw"]),
                },
            )
            bucket["usd_amount"] += float(tx["usd_amount"]) if tx["usd_amount"] is not None else 0.0
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
