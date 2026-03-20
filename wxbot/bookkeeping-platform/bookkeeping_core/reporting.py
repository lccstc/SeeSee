from __future__ import annotations

from collections import defaultdict

from .database import BookkeepingDB


class ReportingService:
    def __init__(self, db: BookkeepingDB) -> None:
        self.db = db

    def get_current_group_rows(self) -> list[dict]:
        rows: list[dict] = []
        for group in self.db.get_all_groups():
            adjustment_total = self.db.get_manual_adjustment_total(str(group["group_key"]))
            tx_balance = float(group["tx_balance"] or 0)
            rows.append(
                {
                    "group_key": str(group["group_key"]),
                    "platform": str(group["platform"]),
                    "chat_id": str(group["chat_id"]),
                    "chat_name": str(group["chat_name"]),
                    "group_num": int(group["group_num"]) if group["group_num"] is not None else None,
                    "current_balance": tx_balance + adjustment_total,
                }
            )
        return rows

    def get_period_group_rows(self, settlement_id: int) -> list[dict]:
        settlement = self.db.get_settlement_by_id(settlement_id)
        if settlement is None:
            return []
        group_key = str(settlement["group_key"])
        previous = self.db.get_previous_settlement(group_key, settlement_id)

        opening_cutoff = str(previous["settled_at"]) if previous is not None else None
        opening_balance = self._sum_balance_before(group_key, opening_cutoff)
        opening_balance += self.db.get_manual_adjustment_total(group_key, int(previous["id"])) if previous is not None else 0.0

        txs = self.db.conn.execute(
            """
            SELECT *
            FROM transactions
            WHERE settlement_id = ? AND deleted = 0
            ORDER BY created_at ASC, id ASC
            """,
            (settlement_id,),
        ).fetchall()
        if not txs:
            return []

        income = sum(float(tx["rmb_value"]) for tx in txs if float(tx["rmb_value"]) > 0)
        expense = sum(abs(float(tx["rmb_value"])) for tx in txs if float(tx["rmb_value"]) < 0)
        base_closing = opening_balance + income - expense

        adjustments = self.db.get_manual_adjustments(settlement_id)
        grouped_adjustments: dict[str, dict[str, float]] = defaultdict(
            lambda: {"opening_delta": 0.0, "income_delta": 0.0, "expense_delta": 0.0, "closing_delta": 0.0}
        )
        for item in adjustments:
            target = grouped_adjustments[str(item["group_key"])]
            target["opening_delta"] += float(item["opening_delta"])
            target["income_delta"] += float(item["income_delta"])
            target["expense_delta"] += float(item["expense_delta"])
            target["closing_delta"] += float(item["closing_delta"])

        group_row = self.db.conn.execute(
            "SELECT * FROM groups WHERE group_key = ?",
            (group_key,),
        ).fetchone()
        adj = grouped_adjustments[group_key]
        return [
            {
                "settlement_id": settlement_id,
                "group_key": group_key,
                "platform": str(group_row["platform"]) if group_row is not None else str(settlement["platform"]),
                "chat_name": str(group_row["chat_name"]) if group_row is not None else group_key,
                "group_num": int(group_row["group_num"]) if group_row is not None and group_row["group_num"] is not None else None,
                "opening_balance": opening_balance + adj["opening_delta"],
                "income": income + adj["income_delta"],
                "expense": expense + adj["expense_delta"],
                "closing_balance": base_closing + adj["closing_delta"],
                "settled_at": str(settlement["settled_at"]),
                "adjustment_count": sum(1 for item in adjustments if str(item["group_key"]) == group_key),
            }
        ]

    def get_combination_summary(self, group_numbers: list[int], label: str) -> dict:
        selected = {int(num) for num in group_numbers}
        rows = [row for row in self.get_current_group_rows() if row["group_num"] in selected]
        return {
            "label": label,
            "group_numbers": sorted(selected),
            "group_count": len(rows),
            "current_balance": sum(float(row["current_balance"]) for row in rows),
            "rows": rows,
        }

    def list_combination_summaries(self) -> list[dict]:
        summaries: list[dict] = []
        for row in self.db.list_group_combinations():
            numbers = [
                int(item)
                for item in str(row["group_numbers"] or "").split(",")
                if str(item).strip()
            ]
            summaries.append(self.get_combination_summary(numbers, label=str(row["name"])))
        return summaries

    def build_dashboard_payload(self) -> dict:
        current_rows = self.get_current_group_rows()
        settlements = self.db.conn.execute(
            "SELECT id, group_key, settled_at, total_rmb, detail FROM settlements ORDER BY settled_at DESC, id DESC LIMIT 20"
        ).fetchall()
        recent_periods = []
        for item in settlements:
            rows = self.get_period_group_rows(int(item["id"]))
            if rows:
                recent_periods.append(rows[0])
        return {
            "current_groups": current_rows,
            "combinations": self.list_combination_summaries(),
            "recent_periods": recent_periods,
        }

    def _sum_balance_before(self, group_key: str, cutoff: str | None) -> float:
        if cutoff is None:
            return 0.0
        row = self.db.conn.execute(
            """
            SELECT COALESCE(SUM(rmb_value), 0) AS total
            FROM transactions
            WHERE group_key = ?
              AND deleted = 0
              AND created_at <= ?
            """,
            (group_key, cutoff),
        ).fetchone()
        return float(row["total"] or 0)
