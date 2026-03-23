from __future__ import annotations

from datetime import date

from .database import BookkeepingDB
from .role_mapping import (
    is_financial_role,
    list_group_num_role_rules,
    list_role_alias_rules,
    resolve_business_role,
    resolve_role_source,
)


class ReportingService:
    def __init__(self, db: BookkeepingDB) -> None:
        self.db = db

    def get_current_group_rows(self) -> list[dict]:
        rows: list[dict] = []
        for group in self.db.get_all_groups():
            adjustment_total = self.db.get_manual_adjustment_total(str(group["group_key"]))
            tx_balance = float(group["tx_balance"] or 0)
            business_role = resolve_business_role(
                business_role=group["business_role"],
                group_num=int(group["group_num"]) if group["group_num"] is not None else None,
            )
            rows.append(
                {
                    "group_key": str(group["group_key"]),
                    "platform": str(group["platform"]),
                    "chat_id": str(group["chat_id"]),
                    "chat_name": str(group["chat_name"]),
                    "group_num": int(group["group_num"]) if group["group_num"] is not None else None,
                    "business_role": business_role,
                    "role_source": resolve_role_source(
                        business_role=group["business_role"],
                        group_num=int(group["group_num"]) if group["group_num"] is not None else None,
                    ),
                    "current_balance": tx_balance + adjustment_total,
                }
            )
        return rows

    def get_period_group_rows(self, period_id: int) -> list[dict]:
        period = self.db.conn.execute(
            "SELECT * FROM accounting_periods WHERE id = ?",
            (period_id,),
        ).fetchone()
        if period is None:
            return []
        snapshot_rows = self.db.list_period_group_snapshots(period_id)
        if not snapshot_rows:
            return []
        return self._get_period_snapshot_rows(period_id, period, snapshot_rows)

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
        from .analytics import AnalyticsService

        current_rows = self.get_current_group_rows()
        recent_periods = []
        period_rows = self.db.conn.execute(
            "SELECT id FROM accounting_periods ORDER BY closed_at DESC, id DESC LIMIT 20"
        ).fetchall()
        for item in period_rows:
            rows = self.get_period_group_rows(int(item["id"]))
            if rows:
                recent_periods.extend(rows)
        return {
            "summary": AnalyticsService(self.db).build_dashboard_summary(today=date.today().isoformat()),
            "current_groups": current_rows,
            "combinations": self.list_combination_summaries(),
            "recent_periods": recent_periods,
            "latest_transactions": AnalyticsService(self.db).build_latest_transactions(),
        }

    def build_role_mapping_payload(self) -> dict:
        from .analytics import AnalyticsService

        current_rows = self.get_current_group_rows()
        counts_by_role = {
            "customer": 0,
            "vendor": 0,
            "internal": 0,
            "unassigned": 0,
        }
        for row in current_rows:
            resolved_role = str(row["business_role"] or "unassigned")
            if resolved_role not in counts_by_role:
                resolved_role = "unassigned"
            counts_by_role[resolved_role] += 1

        financial_summary = AnalyticsService(self.db).build_dashboard_summary(today=date.today().isoformat())
        resolved_group_count = sum(1 for row in current_rows if row["business_role"] not in {None, "unassigned"})
        return {
            "summary": {
                "resolved_group_count": resolved_group_count,
                "financial_group_count": sum(
                    1 for row in current_rows if is_financial_role(str(row["business_role"] or ""))
                ),
                "unassigned_group_count": counts_by_role["unassigned"],
                "financial_total_balance": float(financial_summary["current_total_balance"] or 0),
                "current_estimated_profit": float(financial_summary["current_estimated_profit"] or 0),
                "counts_by_role": counts_by_role,
            },
            "current_groups": current_rows,
            "mapping_rules": list_group_num_role_rules(),
            "role_aliases": list_role_alias_rules(),
        }

    def _get_period_snapshot_rows(self, period_id: int, period_row, snapshot_rows) -> list[dict]:
        closed_at = str(period_row["closed_at"])
        return [
            {
                "period_id": period_id,
                "group_key": str(snapshot["group_key"]),
                "platform": str(snapshot["platform"]),
                "chat_name": str(snapshot["chat_name"]),
                "group_num": int(snapshot["group_num"]) if snapshot["group_num"] is not None else None,
                "business_role": resolve_business_role(
                    business_role=snapshot["business_role"],
                    group_num=int(snapshot["group_num"]) if snapshot["group_num"] is not None else None,
                ),
                "opening_balance": float(snapshot["opening_balance"]),
                "income": float(snapshot["income"]),
                "expense": float(snapshot["expense"]),
                "closing_balance": float(snapshot["closing_balance"]),
                "settled_at": closed_at,
                "closed_at": closed_at,
                "adjustment_count": self._count_snapshot_adjustments(period_id, str(snapshot["group_key"])),
            }
            for snapshot in snapshot_rows
        ]

    def _count_snapshot_adjustments(self, period_id: int, group_key: str) -> int:
        row = self.db.conn.execute(
            """
            SELECT COUNT(*) AS cnt
            FROM manual_adjustments
            WHERE period_id = ?
              AND group_key = ?
            """,
            (period_id, group_key),
        ).fetchone()
        return int(row["cnt"] or 0)
