from __future__ import annotations

from datetime import date, datetime

from .database import BookkeepingDB


class AnalyticsService:
    def __init__(self, db: BookkeepingDB) -> None:
        self.db = db

    def build_dashboard_summary(self, *, today: str) -> dict:
        from .reporting import ReportingService

        current_rows = ReportingService(self.db).get_current_group_rows()
        today_periods = [
            row for row in self.db.list_accounting_periods() if self._date_text(row["closed_at"]) == today
        ]
        today_card_rows = [
            card_row
            for period in today_periods
            for card_row in self.db.list_period_card_stats(int(period["id"]))
        ]
        return {
            "range_label": f"{today} 已关账账期",
            "current_total_balance": self._sum_values(current_rows, "current_balance"),
            "today_realized_profit": sum(
                self._period_profit(self.db.list_period_group_snapshots(int(period["id"])))
                for period in today_periods
            ),
            "today_total_usd_amount": self._sum_values(today_card_rows, "usd_amount"),
            "unassigned_group_count": self._count_unassigned_groups(),
            "today_period_count": len(today_periods),
        }

    def build_period_workbench(self, *, period_id: int | None) -> dict:
        periods = self._list_recent_periods()
        selected = self._pick_selected_period(periods, period_id)
        selected_period_id = int(selected["id"]) if selected is not None else None
        snapshot_rows = self.db.list_period_group_snapshots(selected_period_id) if selected_period_id is not None else []
        card_rows = self.db.list_period_card_stats(selected_period_id) if selected_period_id is not None else []
        group_rows = [self._serialize_snapshot(row) for row in snapshot_rows]
        card_stats = [self._serialize_card_stat(row) for row in card_rows]
        return {
            "periods": periods,
            "selected_period": selected,
            "summary": self._summarize_period(group_rows, card_stats),
            "group_rows": group_rows,
            "card_stats": card_stats,
        }

    def build_history_analysis(
        self,
        *,
        start_date: str,
        end_date: str,
        card_keyword: str = "",
        sort_by: str = "profit",
    ) -> dict:
        periods = self._select_periods_in_range(start_date, end_date)
        period_rows: list[dict] = []
        card_rankings_by_type: dict[str, dict] = {}
        normalized_keyword = card_keyword.strip().lower()

        for period in periods:
            period_id = int(period["id"])
            snapshot_rows = [self._serialize_snapshot(row) for row in self.db.list_period_group_snapshots(period_id)]
            card_rows = [self._serialize_card_stat(row) for row in self.db.list_period_card_stats(period_id)]
            period_rows.append(self._serialize_period(period, snapshot_rows, card_rows))
            for card_row in card_rows:
                if normalized_keyword and normalized_keyword not in str(card_row["card_type"]).lower():
                    continue
                ranking = card_rankings_by_type.setdefault(
                    str(card_row["card_type"]),
                    {
                        "card_type": str(card_row["card_type"]),
                        "usd_amount": 0.0,
                        "rmb_amount": 0.0,
                        "unit_count": 0.0,
                        "row_count": 0,
                        "period_count": 0,
                    },
                )
                ranking["usd_amount"] += float(card_row["usd_amount"])
                ranking["rmb_amount"] += float(card_row["rmb_amount"])
                ranking["unit_count"] += float(card_row["unit_count"])
                ranking["row_count"] += 1
                ranking["period_count"] += 1

        card_rankings = self._sort_card_rankings(list(card_rankings_by_type.values()), sort_by=sort_by)
        return {
            "range": {
                "start_date": start_date,
                "end_date": end_date,
                "label": f"{start_date} 至 {end_date}",
            },
            "period_rows": period_rows,
            "summary": self._summarize_history(period_rows, card_rankings),
            "card_rankings": card_rankings,
        }

    def _list_recent_periods(self) -> list[dict]:
        periods = sorted(
            self.db.list_accounting_periods(),
            key=lambda row: (self._normalize_value(row["closed_at"]), int(row["id"])),
            reverse=True,
        )[:20]
        return [self._serialize_period(period) for period in periods]

    def _pick_selected_period(self, periods: list[dict], period_id: int | None) -> dict | None:
        if not periods:
            return None
        if period_id is None:
            return periods[0]
        for period in periods:
            if int(period["id"]) == int(period_id):
                return period
        return periods[0]

    def _select_periods_in_range(self, start_date: str, end_date: str):
        return [
            row
            for row in sorted(
                self.db.list_accounting_periods(),
                key=lambda period: (self._normalize_value(period["closed_at"]), int(period["id"])),
                reverse=True,
            )
            if start_date <= self._date_text(row["closed_at"]) <= end_date
        ]

    def _serialize_period(self, row, snapshot_rows: list[dict] | None = None, card_rows: list[dict] | None = None) -> dict:
        snapshots = snapshot_rows if snapshot_rows is not None else [
            self._serialize_snapshot(item) for item in self.db.list_period_group_snapshots(int(row["id"]))
        ]
        cards = card_rows if card_rows is not None else [
            self._serialize_card_stat(item) for item in self.db.list_period_card_stats(int(row["id"]))
        ]
        return {
            "id": int(row["id"]),
            "start_at": self._normalize_value(row["start_at"]),
            "end_at": self._normalize_value(row["end_at"]),
            "closed_at": self._normalize_value(row["closed_at"]),
            "closed_by": self._normalize_value(row["closed_by"]),
            "note": self._normalize_value(row["note"]),
            "has_adjustment": int(row["has_adjustment"] or 0),
            "snapshot_version": int(row["snapshot_version"] or 1),
            "group_count": len(snapshots),
            "transaction_count": sum(int(item["transaction_count"]) for item in snapshots),
            "profit": self._period_profit(snapshots),
            "total_usd_amount": self._sum_values(cards, "usd_amount"),
        }

    def _serialize_snapshot(self, row) -> dict:
        return {
            "id": self._int_or_none(row["id"]),
            "period_id": int(row["period_id"]),
            "group_key": str(row["group_key"]),
            "platform": str(row["platform"]),
            "chat_name": str(row["chat_name"]),
            "group_num": int(row["group_num"]) if row["group_num"] is not None else None,
            "business_role": self._normalize_value(row["business_role"]),
            "opening_balance": float(row["opening_balance"] or 0),
            "income": float(row["income"] or 0),
            "expense": float(row["expense"] or 0),
            "closing_balance": float(row["closing_balance"] or 0),
            "transaction_count": int(row["transaction_count"] or 0),
            "anomaly_flags_json": str(row["anomaly_flags_json"] or "[]"),
        }

    def _serialize_card_stat(self, row) -> dict:
        return {
            "id": self._int_or_none(row["id"]),
            "period_id": int(row["period_id"]),
            "group_key": str(row["group_key"]),
            "business_role": self._normalize_value(row["business_role"]),
            "card_type": str(row["card_type"]),
            "usd_amount": float(row["usd_amount"] or 0),
            "rate": float(row["rate"]) if row["rate"] is not None else None,
            "rmb_amount": float(row["rmb_amount"] or 0),
            "unit_face_value": float(row["unit_face_value"]) if row["unit_face_value"] is not None else None,
            "unit_count": float(row["unit_count"] or 0),
            "sample_raw": self._normalize_value(row["sample_raw"]),
        }

    def _summarize_period(self, group_rows: list[dict], card_rows: list[dict]) -> dict:
        return {
            "group_count": len(group_rows),
            "transaction_count": sum(int(row["transaction_count"]) for row in group_rows),
            "opening_balance": self._sum_values(group_rows, "opening_balance"),
            "income": self._sum_values(group_rows, "income"),
            "expense": self._sum_values(group_rows, "expense"),
            "closing_balance": self._sum_values(group_rows, "closing_balance"),
            "profit": self._period_profit(group_rows),
            "total_usd_amount": self._sum_values(card_rows, "usd_amount"),
        }

    def _summarize_history(self, period_rows: list[dict], card_rankings: list[dict]) -> dict:
        return {
            "period_count": len(period_rows),
            "total_profit": self._sum_values(period_rows, "profit"),
            "total_usd_amount": self._sum_values(card_rankings, "usd_amount"),
            "card_type_count": len(card_rankings),
        }

    def _sort_card_rankings(self, rows: list[dict], *, sort_by: str) -> list[dict]:
        allowed = {"usd_amount", "rmb_amount", "unit_count", "row_count", "period_count"}
        sort_key = sort_by if sort_by in allowed else "rmb_amount"
        return sorted(
            rows,
            key=lambda row: (float(row[sort_key]), str(row["card_type"])),
            reverse=True,
        )

    def _count_unassigned_groups(self) -> int:
        return sum(
            1
            for row in self.db.get_all_groups()
            if not str(self._normalize_value(row["business_role"]) or "").strip()
        )

    @staticmethod
    def _period_profit(rows: list[dict]) -> float:
        return sum(float(row["income"]) - float(row["expense"]) for row in rows)

    @staticmethod
    def _sum_values(rows: list[dict], key: str) -> float:
        return sum(float(AnalyticsService._read_value(row, key) or 0) for row in rows)

    @staticmethod
    def _read_value(row, key: str):
        if hasattr(row, "keys"):
            return row[key]
        return row.get(key)

    @staticmethod
    def _int_or_none(value) -> int | None:
        return int(value) if value is not None else None

    @staticmethod
    def _date_text(value) -> str:
        normalized = AnalyticsService._normalize_value(value)
        return str(normalized or "")[:10]

    @staticmethod
    def _normalize_value(value):
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, datetime):
            return value.isoformat(sep=" ")
        if isinstance(value, date):
            return value.isoformat()
        if hasattr(value, "isoformat"):
            try:
                return value.isoformat()
            except TypeError:
                pass
        if hasattr(value, "__float__"):
            try:
                return float(value)
            except (TypeError, ValueError):
                pass
        return str(value)
