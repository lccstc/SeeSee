from __future__ import annotations

from datetime import date, datetime

from .database import BookkeepingDB
from .role_mapping import (
    is_financial_role,
    is_unassigned_role,
    resolve_business_role,
    resolve_role_source,
)


class AnalyticsService:
    def __init__(self, db: BookkeepingDB) -> None:
        self.db = db

    def build_latest_transactions(self, *, limit: int = 8) -> list[dict]:
        periods = self.db.list_accounting_periods()
        return [
            self._serialize_transaction(row, period_status=self._resolve_period_status(row, periods=periods))
            for row in self.db.list_latest_transactions(limit)
        ]

    def build_dashboard_summary(self, *, today: str) -> dict:
        from .reporting import ReportingService

        periods = self._list_recent_periods()
        current_rows = ReportingService(self.db).get_current_group_rows()
        financial_current_rows = self._financial_rows(current_rows)
        live_window_start_at = self._resolve_live_window_start_at(periods)
        current_window_rows = [
            self._serialize_transaction(row, period_status="unsettled")
            for row in self.db.list_current_window_transactions(live_window_start_at)
        ]
        current_window_summary = self._summarize_live_window(current_window_rows)
        current_window_role_card_breakdown = self._build_role_card_breakdown(current_window_rows)
        today_periods = [
            row for row in self.db.list_accounting_periods() if self._date_text(row["closed_at"]) == today
        ]
        today_period_rows: list[dict] = []
        today_card_rows: list[dict] = []
        for period in today_periods:
            period_card_rows = [
                self._serialize_card_stat(item)
                for item in self.db.list_period_card_stats(int(period["id"]))
            ]
            today_card_rows.extend(period_card_rows)
            today_period_rows.append(self._serialize_period(period, card_rows=period_card_rows))
        today_role_card_breakdown = self._build_role_card_breakdown(today_card_rows)
        return {
            "range_label": f"{today} 结算账期",
            "current_total_balance": self._sum_values(financial_current_rows, "current_balance"),
            "today_realized_profit": self._sum_values(today_period_rows, "profit"),
            "today_total_usd_amount": float(today_role_card_breakdown["total_usd_amount"] or 0),
            "today_customer_card_rmb_amount": float(today_role_card_breakdown["customer"]["total_display_rmb_amount"] or 0),
            "today_customer_card_usd_amount": float(today_role_card_breakdown["customer"]["total_usd_amount"] or 0),
            "today_vendor_card_rmb_amount": float(today_role_card_breakdown["vendor"]["total_display_rmb_amount"] or 0),
            "today_vendor_card_usd_amount": float(today_role_card_breakdown["vendor"]["total_usd_amount"] or 0),
            "current_estimated_profit": float(current_window_summary["profit"] or 0),
            "current_estimated_usd_amount": float(current_window_role_card_breakdown["total_usd_amount"] or 0),
            "current_customer_card_rmb_amount": float(current_window_role_card_breakdown["customer"]["total_display_rmb_amount"] or 0),
            "current_customer_card_usd_amount": float(current_window_role_card_breakdown["customer"]["total_usd_amount"] or 0),
            "current_vendor_card_rmb_amount": float(current_window_role_card_breakdown["vendor"]["total_display_rmb_amount"] or 0),
            "current_vendor_card_usd_amount": float(current_window_role_card_breakdown["vendor"]["total_usd_amount"] or 0),
            "current_window_transaction_count": int(current_window_summary["transaction_count"] or 0),
            "mapped_group_count": len(financial_current_rows),
            "unassigned_group_count": self._count_unassigned_groups(),
            "today_period_count": len(today_periods),
            "today_role_card_breakdown": today_role_card_breakdown,
            "current_role_card_breakdown": current_window_role_card_breakdown,
        }

    def build_period_workbench(self, *, period_id: int | None, use_live_period: bool = False) -> dict:
        periods = self._list_recent_periods()
        selected = None if use_live_period else self._pick_selected_period(periods, period_id)
        selected_period_id = int(selected["id"]) if selected is not None else None
        live_window_start_at = self._resolve_live_window_start_at(periods)
        current_window_rows = self.db.list_current_window_transactions(live_window_start_at)
        snapshot_rows = self.db.list_period_group_snapshots(selected_period_id) if selected_period_id is not None else []
        card_rows = self.db.list_period_card_stats(selected_period_id) if selected_period_id is not None else []
        transactions = [
            self._serialize_transaction(row, period_status="unsettled")
            for row in current_window_rows
        ]
        if selected_period_id is not None:
            group_rows = [self._serialize_snapshot(row) for row in snapshot_rows]
            group_rows = self._apply_workbench_adjustments(selected_period_id, group_rows)
            card_stats = self._card_rows([self._serialize_card_stat(row) for row in card_rows])
            group_rows = self._attach_group_usd_amounts(group_rows, card_stats)
            summary = self._summarize_period(group_rows, card_stats)
            role_card_breakdown = self._build_role_card_breakdown(card_stats)
        else:
            group_rows = self._build_live_group_rows(transactions)
            card_stats = self._build_live_card_stats(transactions)
            summary = self._summarize_live_window(transactions)
            role_card_breakdown = self._build_role_card_breakdown(transactions)
        role_rows = self._build_role_rows(group_rows=group_rows, transactions=transactions)
        return {
            "periods": periods,
            "selected_period": selected,
            "live_window": self._serialize_live_window(live_window_start_at, transactions),
            "summary": summary,
            "transactions": transactions,
            "group_rows": group_rows,
            "card_stats": card_stats,
            "role_rows": role_rows,
            "role_card_breakdown": role_card_breakdown,
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
        all_card_rows: list[dict] = []

        for period in periods:
            period_id = int(period["id"])
            snapshot_rows = [self._serialize_snapshot(row) for row in self.db.list_period_group_snapshots(period_id)]
            card_rows = [self._serialize_card_stat(row) for row in self.db.list_period_card_stats(period_id)]
            all_card_rows.extend(card_rows)
            period_rows.append(self._serialize_period(period, snapshot_rows, card_rows))
        role_card_breakdown = self._build_role_card_breakdown(all_card_rows, card_keyword=card_keyword)
        card_rankings = self._build_card_rankings(
            self._vendor_rows(all_card_rows),
            card_keyword=card_keyword,
            sort_by=sort_by,
        )
        return {
            "range": {
                "start_date": start_date,
                "end_date": end_date,
                "label": f"{start_date} 至 {end_date}",
            },
            "period_rows": period_rows,
            "summary": self._summarize_history(period_rows, card_rankings, role_card_breakdown),
            "card_rankings": card_rankings,
            "customer_card_rankings": role_card_breakdown["customer"]["rows"],
            "vendor_card_rankings": role_card_breakdown["vendor"]["rows"],
            "role_card_breakdown": role_card_breakdown,
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
        financial_snapshots = self._financial_rows(snapshots)
        role_card_breakdown = self._build_role_card_breakdown(cards)
        return {
            "id": int(row["id"]),
            "start_at": self._normalize_value(row["start_at"]),
            "end_at": self._normalize_value(row["end_at"]),
            "closed_at": self._normalize_value(row["closed_at"]),
            "closed_by": self._normalize_value(row["closed_by"]),
            "note": self._normalize_value(row["note"]),
            "has_adjustment": int(row["has_adjustment"] or 0),
            "snapshot_version": int(row["snapshot_version"] or 1),
            "group_count": len(financial_snapshots),
            "transaction_count": sum(int(item["transaction_count"]) for item in financial_snapshots),
            "vendor_transaction_count": self._sum_role_transaction_count(financial_snapshots, "vendor"),
            "profit": float(role_card_breakdown["profit"] or 0),
            "total_usd_amount": float(role_card_breakdown["total_usd_amount"] or 0),
            "customer_card_rmb_amount": float(role_card_breakdown["customer"]["total_display_rmb_amount"] or 0),
            "customer_card_usd_amount": float(role_card_breakdown["customer"]["total_usd_amount"] or 0),
            "vendor_card_rmb_amount": float(role_card_breakdown["vendor"]["total_display_rmb_amount"] or 0),
            "vendor_card_usd_amount": float(role_card_breakdown["vendor"]["total_usd_amount"] or 0),
        }

    def _serialize_snapshot(self, row) -> dict:
        group_num = int(row["group_num"]) if row["group_num"] is not None else None
        return {
            "id": self._int_or_none(row["id"]),
            "period_id": int(row["period_id"]),
            "group_key": str(row["group_key"]),
            "platform": str(row["platform"]),
            "chat_name": str(row["chat_name"]),
            "group_num": group_num,
            "business_role": resolve_business_role(
                business_role=row["business_role"],
                group_num=group_num,
            ),
            "opening_balance": float(row["opening_balance"] or 0),
            "income": float(row["income"] or 0),
            "expense": float(row["expense"] or 0),
            "closing_balance": float(row["closing_balance"] or 0),
            "transaction_count": int(row["transaction_count"] or 0),
            "total_usd_amount": 0.0,
            "anomaly_flags_json": str(row["anomaly_flags_json"] or "[]"),
        }

    def _serialize_card_stat(self, row) -> dict:
        business_role = resolve_business_role(
            business_role=row["business_role"],
            group_num=None,
        )
        raw_rmb_amount = float(row["rmb_amount"] or 0)
        return {
            "id": self._int_or_none(row["id"]),
            "period_id": int(row["period_id"]),
            "group_key": str(row["group_key"]),
            "business_role": business_role,
            "card_type": str(row["card_type"]),
            "usd_amount": float(row["usd_amount"] or 0),
            "rate": float(row["rate"]) if row["rate"] is not None else None,
            "rmb_amount": raw_rmb_amount,
            "display_rmb_amount": self._normalize_role_card_rmb_amount(raw_rmb_amount, business_role),
            "unit_face_value": float(row["unit_face_value"]) if row["unit_face_value"] is not None else None,
            "unit_count": float(row["unit_count"] or 0),
            "sample_raw": self._normalize_value(row["sample_raw"]),
        }

    def _serialize_transaction(self, row, *, period_status: str) -> dict:
        settled_flag = int(row["settled"] or 0)
        normalized_status = "settled" if period_status == "settled" or settled_flag else "unsettled"
        display_usd_amount = self._display_usd_amount(row)
        transaction_group_num = int(row["group_num"]) if row["group_num"] is not None else None
        mapped_group_num = self._read_optional_value(row, "mapped_group_num")
        group_num = int(mapped_group_num) if mapped_group_num is not None else transaction_group_num
        business_role = resolve_business_role(
            business_role=self._read_value(row, "business_role"),
            group_num=group_num,
        )
        raw_rmb_value = float(row["rmb_value"] or 0)
        return {
            "id": int(row["id"]),
            "platform": str(row["platform"]),
            "group_key": str(row["group_key"]),
            "group_num": group_num,
            "chat_id": str(row["chat_id"]),
            "chat_name": str(row["chat_name"]),
            "sender_id": str(row["sender_id"]),
            "sender_name": str(row["sender_name"]),
            "business_role": business_role,
            "message_id": self._normalize_value(row["message_id"]),
            "input_sign": int(row["input_sign"] or 0),
            "amount": float(row["amount"] or 0),
            "category": str(row["category"]),
            "rate": float(row["rate"]) if row["rate"] is not None else None,
            "rmb_value": raw_rmb_value,
            "display_rmb_amount": self._normalize_role_card_rmb_amount(raw_rmb_value, business_role),
            "raw": str(row["raw"]),
            "parse_version": str(row["parse_version"] or "1"),
            "usd_amount": float(row["usd_amount"] or 0),
            "display_usd_amount": display_usd_amount,
            "unit_face_value": float(row["unit_face_value"]) if row["unit_face_value"] is not None else None,
            "unit_count": float(row["unit_count"]) if row["unit_count"] is not None else None,
            "created_at": self._normalize_value(row["created_at"]),
            "edited_by": self._normalize_value(self._read_optional_value(row, "edited_by")),
            "edited_at": self._normalize_value(self._read_optional_value(row, "edited_at")),
            "is_edited": self._read_optional_value(row, "edited_at") is not None,
            "settled": normalized_status == "settled",
            "period_status": normalized_status,
        }

    def _summarize_period(self, group_rows: list[dict], card_rows: list[dict]) -> dict:
        financial_group_rows = self._financial_rows(group_rows)
        role_card_breakdown = self._build_role_card_breakdown(card_rows)
        return {
            "group_count": len(financial_group_rows),
            "transaction_count": sum(int(row["transaction_count"]) for row in financial_group_rows),
            "opening_balance": self._sum_values(financial_group_rows, "opening_balance"),
            "income": self._sum_values(financial_group_rows, "income"),
            "expense": self._sum_values(financial_group_rows, "expense"),
            "closing_balance": self._sum_values(financial_group_rows, "closing_balance"),
            "profit": float(role_card_breakdown["profit"] or 0),
            "total_usd_amount": float(role_card_breakdown["total_usd_amount"] or 0),
            "customer_card_rmb_amount": float(role_card_breakdown["customer"]["total_rmb_amount"] or 0),
            "customer_card_usd_amount": float(role_card_breakdown["customer"]["total_usd_amount"] or 0),
            "vendor_card_rmb_amount": float(role_card_breakdown["vendor"]["total_rmb_amount"] or 0),
            "vendor_card_usd_amount": float(role_card_breakdown["vendor"]["total_usd_amount"] or 0),
        }

    def _summarize_history(self, period_rows: list[dict], card_rankings: list[dict], role_card_breakdown: dict) -> dict:
        return {
            "period_count": len(period_rows),
            "total_profit": self._sum_values(period_rows, "profit"),
            "total_usd_amount": float(role_card_breakdown["total_usd_amount"] or 0),
            "card_type_count": len(card_rankings),
            "customer_card_rmb_amount": float(role_card_breakdown["customer"]["total_display_rmb_amount"] or 0),
            "customer_card_usd_amount": float(role_card_breakdown["customer"]["total_usd_amount"] or 0),
            "vendor_card_rmb_amount": float(role_card_breakdown["vendor"]["total_display_rmb_amount"] or 0),
            "vendor_card_usd_amount": float(role_card_breakdown["vendor"]["total_usd_amount"] or 0),
        }

    def _summarize_live_window(self, transactions: list[dict]) -> dict:
        financial_transactions = self._financial_rows(transactions)
        role_card_breakdown = self._build_role_card_breakdown(transactions)
        income = sum(float(row["rmb_value"]) for row in financial_transactions if float(row["rmb_value"]) > 0)
        expense = sum(abs(float(row["rmb_value"])) for row in financial_transactions if float(row["rmb_value"]) < 0)
        return {
            "group_count": len({str(row["group_key"]) for row in financial_transactions}),
            "transaction_count": len(financial_transactions),
            "customer_transaction_count": self._count_transactions_by_role(financial_transactions, "customer"),
            "vendor_transaction_count": self._count_transactions_by_role(financial_transactions, "vendor"),
            "opening_balance": 0.0,
            "income": income,
            "expense": expense,
            "closing_balance": income - expense,
            "profit": float(role_card_breakdown["profit"] or 0),
            "total_usd_amount": float(role_card_breakdown["total_usd_amount"] or 0),
            "customer_card_rmb_amount": float(role_card_breakdown["customer"]["total_display_rmb_amount"] or 0),
            "customer_card_usd_amount": float(role_card_breakdown["customer"]["total_usd_amount"] or 0),
            "vendor_card_rmb_amount": float(role_card_breakdown["vendor"]["total_display_rmb_amount"] or 0),
            "vendor_card_usd_amount": float(role_card_breakdown["vendor"]["total_usd_amount"] or 0),
        }

    def _sort_card_rankings(self, rows: list[dict], *, sort_by: str) -> list[dict]:
        allowed = {"usd_amount", "rmb_amount", "unit_count", "row_count", "period_count"}
        sort_key = sort_by if sort_by in allowed else "rmb_amount"
        return sorted(
            rows,
            key=lambda row: (float(row[sort_key]), str(row["card_type"])),
            reverse=True,
        )

    def _build_role_card_breakdown(self, rows: list[dict], *, card_keyword: str = "") -> dict:
        normalized_keyword = card_keyword.strip().lower()
        group_label_map = self._group_label_map()
        buckets: dict[tuple[str, str], dict] = {}
        for row in self._card_rows(rows):
            role = self._row_business_role(row)
            card_type = self._row_card_type(row)
            if role not in {"customer", "vendor"} or not card_type:
                continue
            if normalized_keyword and normalized_keyword not in card_type.lower():
                continue
            key = (role, card_type)
            bucket = buckets.setdefault(
                key,
                {
                    "business_role": role,
                    "card_type": card_type,
                    "usd_amount": 0.0,
                    "rmb_amount": 0.0,
                    "display_rmb_amount": 0.0,
                    "unit_count": 0.0,
                    "row_count": 0,
                    "_period_ids": set(),
                    "_groups": set(),
                },
            )
            bucket["usd_amount"] += self._row_card_usd_amount(row)
            bucket["rmb_amount"] += self._row_raw_rmb_amount(row)
            bucket["display_rmb_amount"] += self._row_display_rmb_amount(row)
            bucket["unit_count"] += self._row_signed_unit_count(row)
            bucket["row_count"] += 1
            period_id = self._read_optional_value(row, "period_id")
            if period_id is not None:
                bucket["_period_ids"].add(int(period_id))
            bucket["_groups"].add(self._row_group_label(row, group_label_map))

        grouped_rows = {"customer": [], "vendor": []}
        for bucket in buckets.values():
            grouped_rows[str(bucket["business_role"])].append(
                {
                    "business_role": str(bucket["business_role"]),
                    "card_type": str(bucket["card_type"]),
                    "usd_amount": float(bucket["usd_amount"]),
                    "rmb_amount": float(bucket["rmb_amount"]),
                    "display_rmb_amount": float(bucket["display_rmb_amount"]),
                    "unit_count": float(bucket["unit_count"]),
                    "row_count": int(bucket["row_count"]),
                    "period_count": len(bucket["_period_ids"]),
                    "groups": " / ".join(sorted(str(item) for item in bucket["_groups"] if str(item).strip())) or "—",
                }
            )

        customer_rows = self._sort_card_rankings(grouped_rows["customer"], sort_by="rmb_amount")
        vendor_rows = self._sort_card_rankings(grouped_rows["vendor"], sort_by="rmb_amount")
        customer_total_rmb_amount = self._sum_values(customer_rows, "rmb_amount")
        vendor_total_rmb_amount = self._sum_values(vendor_rows, "rmb_amount")
        customer_total_display_rmb_amount = self._sum_values(customer_rows, "display_rmb_amount")
        vendor_total_display_rmb_amount = self._sum_values(vendor_rows, "display_rmb_amount")
        customer_total_usd_amount = self._sum_values(customer_rows, "usd_amount")
        vendor_total_usd_amount = self._sum_values(vendor_rows, "usd_amount")
        return {
            "customer": {
                "total_rmb_amount": customer_total_rmb_amount,
                "total_display_rmb_amount": customer_total_display_rmb_amount,
                "total_usd_amount": customer_total_usd_amount,
                "total_unit_count": self._sum_values(customer_rows, "unit_count"),
                "rows": customer_rows,
            },
            "vendor": {
                "total_rmb_amount": vendor_total_rmb_amount,
                "total_display_rmb_amount": vendor_total_display_rmb_amount,
                "total_usd_amount": vendor_total_usd_amount,
                "total_unit_count": self._sum_values(vendor_rows, "unit_count"),
                "rows": vendor_rows,
            },
            "profit": customer_total_display_rmb_amount - vendor_total_display_rmb_amount,
            "total_usd_amount": customer_total_usd_amount + vendor_total_usd_amount,
        }

    def _build_card_rankings(self, rows: list[dict], *, card_keyword: str, sort_by: str) -> list[dict]:
        normalized_keyword = card_keyword.strip().lower()
        buckets: dict[str, dict] = {}
        for row in self._card_rows(rows):
            card_type = self._row_card_type(row)
            if not card_type:
                continue
            if normalized_keyword and normalized_keyword not in card_type.lower():
                continue
            bucket = buckets.setdefault(
                card_type,
                {
                    "card_type": card_type,
                    "usd_amount": 0.0,
                    "rmb_amount": 0.0,
                    "unit_count": 0.0,
                    "row_count": 0,
                    "_period_ids": set(),
                },
            )
            bucket["usd_amount"] += self._row_card_usd_amount(row)
            bucket["rmb_amount"] += self._row_display_rmb_amount(row)
            bucket["unit_count"] += self._row_signed_unit_count(row)
            bucket["row_count"] += 1
            period_id = self._read_optional_value(row, "period_id")
            if period_id is not None:
                bucket["_period_ids"].add(int(period_id))
        rankings = [
            {
                "card_type": str(bucket["card_type"]),
                "usd_amount": float(bucket["usd_amount"]),
                "rmb_amount": float(bucket["rmb_amount"]),
                "unit_count": float(bucket["unit_count"]),
                "row_count": int(bucket["row_count"]),
                "period_count": len(bucket["_period_ids"]),
            }
            for bucket in buckets.values()
        ]
        return self._sort_card_rankings(rankings, sort_by=sort_by)

    def _apply_workbench_adjustments(self, period_id: int, group_rows: list[dict]) -> list[dict]:
        if not group_rows:
            return group_rows
        allowed_group_keys = {str(row["group_key"]) for row in group_rows}
        adjustments = [
            row
            for row in self.db.get_manual_adjustments(period_id)
            if str(row["group_key"]) in allowed_group_keys
        ]
        if not adjustments:
            return group_rows

        grouped: dict[str, dict[str, float]] = {}
        for item in adjustments:
            bucket = grouped.setdefault(
                str(item["group_key"]),
                {
                    "opening_delta": 0.0,
                    "income_delta": 0.0,
                    "expense_delta": 0.0,
                    "closing_delta": 0.0,
                },
            )
            bucket["opening_delta"] += float(item["opening_delta"] or 0)
            bucket["income_delta"] += float(item["income_delta"] or 0)
            bucket["expense_delta"] += float(item["expense_delta"] or 0)
            bucket["closing_delta"] += float(item["closing_delta"] or 0)

        adjusted_rows: list[dict] = []
        for row in group_rows:
            deltas = grouped.get(str(row["group_key"]))
            if not deltas:
                adjusted_rows.append(row)
                continue
            updated = dict(row)
            updated["opening_balance"] = float(row["opening_balance"]) + deltas["opening_delta"]
            updated["income"] = float(row["income"]) + deltas["income_delta"]
            updated["expense"] = float(row["expense"]) + deltas["expense_delta"]
            updated["closing_balance"] = float(row["closing_balance"]) + deltas["closing_delta"]
            adjusted_rows.append(updated)
        return adjusted_rows

    def _resolve_period_status(self, row, *, periods) -> str:
        if int(row["settled"] or 0):
            return "settled"
        created_at = self._normalize_value(row["created_at"])
        for period in periods:
            if self._period_contains(period, created_at):
                return "settled"
        return "unsettled"

    def _period_contains(self, period, created_at: str | None) -> bool:
        if not created_at:
            return False
        start_at = self._normalize_value(period["start_at"])
        end_at = self._normalize_value(period["end_at"])
        if not start_at or not end_at:
            return False
        return str(start_at) < str(created_at) <= str(end_at)

    def _count_unassigned_groups(self) -> int:
        return sum(
            1
            for row in self.db.get_all_groups()
            if is_unassigned_role(
                resolve_business_role(
                    business_role=row["business_role"],
                    group_num=int(row["group_num"]) if row["group_num"] is not None else None,
                )
            )
        )

    def _resolve_live_window_start_at(self, periods: list[dict]) -> str | None:
        latest_period = periods[0] if periods else None
        return self._normalize_value(latest_period["end_at"]) if latest_period is not None else None

    def _serialize_live_window(self, start_at: str | None, transactions: list[dict]) -> dict:
        if start_at:
            label = f"自 {start_at} 之后的实时交易"
        else:
            label = "尚未结算，显示全部实时交易"
        financial_transactions = self._financial_rows(transactions)
        return {
            "start_at": start_at,
            "label": label,
            "transaction_count": len(transactions),
            "customer_transaction_count": self._count_transactions_by_role(financial_transactions, "customer"),
            "vendor_transaction_count": self._count_transactions_by_role(financial_transactions, "vendor"),
        }

    def _display_usd_amount(self, row) -> float:
        usd_amount = float(row["usd_amount"] or 0)
        if usd_amount:
            return usd_amount
        category = str(row["category"] or "").lower()
        if category == "rmb":
            return 0.0
        return float(row["amount"] or 0)

    def _build_role_rows(self, *, group_rows: list[dict], transactions: list[dict]) -> list[dict]:
        allowed_group_keys = {
            str(row["group_key"])
            for row in group_rows
        } | {
            str(row["group_key"])
            for row in transactions
        }
        role_rows = []
        for row in self.db.get_all_groups():
            if allowed_group_keys and str(row["group_key"]) not in allowed_group_keys:
                continue
            group_num = int(row["group_num"]) if row["group_num"] is not None else None
            business_role = resolve_business_role(
                business_role=row["business_role"],
                group_num=group_num,
            )
            role_rows.append(
                {
                    "group_key": str(row["group_key"]),
                    "chat_name": str(row["chat_name"]),
                    "group_num": group_num,
                    "business_role": business_role,
                    "role_source": resolve_role_source(
                        business_role=row["business_role"],
                        group_num=group_num,
                    ),
                    "current_balance": float(row["tx_balance"] or 0) + self.db.get_manual_adjustment_total(str(row["group_key"])),
                }
            )
        return role_rows

    def _build_live_group_rows(self, transactions: list[dict]) -> list[dict]:
        financial_transactions = self._financial_rows(transactions)
        buckets: dict[str, dict] = {}
        for row in financial_transactions:
            group_key = str(row["group_key"])
            bucket = buckets.setdefault(
                group_key,
                {
                    "id": None,
                    "period_id": None,
                    "group_key": group_key,
                    "platform": str(row["platform"]),
                    "chat_name": str(row["chat_name"]),
                    "group_num": self._int_or_none(self._read_optional_value(row, "group_num")),
                    "business_role": self._row_business_role(row),
                    "opening_balance": 0.0,
                    "income": 0.0,
                    "expense": 0.0,
                    "closing_balance": 0.0,
                    "transaction_count": 0,
                    "total_usd_amount": 0.0,
                    "anomaly_flags_json": "[]",
                },
            )
            rmb_value = float(row["rmb_value"] or 0)
            if rmb_value >= 0:
                bucket["income"] += rmb_value
            else:
                bucket["expense"] += abs(rmb_value)
            bucket["closing_balance"] = float(bucket["income"]) - float(bucket["expense"])
            bucket["transaction_count"] += 1
        for row in self._card_rows(financial_transactions):
            group_key = str(self._read_optional_value(row, "group_key") or "")
            if not group_key or group_key not in buckets:
                continue
            buckets[group_key]["total_usd_amount"] += self._row_card_usd_amount(row)
        return sorted(
            buckets.values(),
            key=lambda item: (str(item["platform"]), str(item["chat_name"])),
        )

    @staticmethod
    def _attach_group_usd_amounts(group_rows: list[dict], card_rows: list[dict]) -> list[dict]:
        if not group_rows:
            return group_rows
        group_totals: dict[str, float] = {}
        for row in card_rows:
            group_key = str(row.get("group_key") or "")
            if not group_key:
                continue
            group_totals[group_key] = float(group_totals.get(group_key, 0.0)) + float(row.get("usd_amount") or 0.0)
        updated_rows: list[dict] = []
        for row in group_rows:
            updated = dict(row)
            updated["total_usd_amount"] = float(group_totals.get(str(row.get("group_key") or ""), 0.0))
            updated_rows.append(updated)
        return updated_rows

    def _build_live_card_stats(self, transactions: list[dict]) -> list[dict]:
        buckets: dict[tuple[str, str], dict] = {}
        for row in self._card_rows(transactions):
            business_role = self._row_business_role(row)
            card_type = self._row_card_type(row)
            if business_role not in {"customer", "vendor"} or card_type is None:
                continue
            key = (business_role, card_type)
            bucket = buckets.setdefault(
                key,
                {
                    "id": None,
                    "period_id": None,
                    "group_key": None,
                    "business_role": business_role,
                    "card_type": card_type,
                    "usd_amount": 0.0,
                    "rate": None,
                    "rmb_amount": 0.0,
                    "display_rmb_amount": 0.0,
                    "unit_face_value": None,
                    "unit_count": 0.0,
                    "sample_raw": None,
                },
            )
            bucket["usd_amount"] += self._row_card_usd_amount(row)
            bucket["rmb_amount"] += self._row_raw_rmb_amount(row)
            bucket["display_rmb_amount"] += self._row_display_rmb_amount(row)
            bucket["unit_count"] += self._row_signed_unit_count(row)
        return sorted(
            buckets.values(),
            key=lambda item: (str(item["business_role"]), -float(item["usd_amount"]), str(item["card_type"])),
        )

    @staticmethod
    def _financial_rows(rows: list[dict]) -> list[dict]:
        return [row for row in rows if is_financial_role(AnalyticsService._row_business_role(row))]

    @staticmethod
    def _vendor_rows(rows: list[dict]) -> list[dict]:
        return [row for row in rows if AnalyticsService._row_business_role(row) == "vendor"]

    @staticmethod
    def _card_rows(rows: list[dict]) -> list[dict]:
        return [
            row
            for row in rows
            if AnalyticsService._row_business_role(row) in {"customer", "vendor"}
            and AnalyticsService._row_card_type(row) is not None
            and AnalyticsService._row_card_type(row).lower() != "rmb"
        ]

    @staticmethod
    def _row_business_role(row) -> str | None:
        business_role = AnalyticsService._read_optional_value(row, "business_role")
        group_num = AnalyticsService._read_optional_value(row, "group_num")
        return resolve_business_role(
            business_role=business_role,
            group_num=int(group_num) if group_num is not None else None,
        )

    @staticmethod
    def _row_card_type(row) -> str | None:
        card_type = AnalyticsService._read_optional_value(row, "card_type")
        if card_type is not None:
            return str(card_type)
        category = AnalyticsService._read_optional_value(row, "category")
        if category is not None:
            return str(category)
        return None

    @staticmethod
    def _normalize_role_card_rmb_amount(raw_rmb_amount: float, business_role: str | None) -> float:
        if business_role in {"customer", "vendor"}:
            return abs(float(raw_rmb_amount or 0))
        return float(raw_rmb_amount or 0)

    @staticmethod
    def _row_display_rmb_amount(row) -> float:
        business_role = AnalyticsService._row_business_role(row)
        normalized = AnalyticsService._normalize_role_card_rmb_amount(
            AnalyticsService._row_raw_rmb_amount(row),
            business_role,
        )
        # Live transaction rows carry input_sign and should net correction pairs (+X then -X).
        if AnalyticsService._read_optional_value(row, "input_sign") in {None, ""}:
            return normalized
        return abs(float(normalized or 0)) * AnalyticsService._input_direction(row)

    @staticmethod
    def _row_raw_rmb_amount(row) -> float:
        raw_rmb_amount = AnalyticsService._read_optional_value(row, "rmb_amount")
        if raw_rmb_amount is None:
            raw_rmb_amount = AnalyticsService._read_optional_value(row, "rmb_value")
        return float(raw_rmb_amount or 0)

    @staticmethod
    def _row_card_usd_amount(row) -> float:
        display_usd_amount = AnalyticsService._read_optional_value(row, "display_usd_amount")
        direction = AnalyticsService._input_direction(row)
        if display_usd_amount is not None:
            return abs(float(display_usd_amount or 0)) * direction
        usd_amount = AnalyticsService._read_optional_value(row, "usd_amount")
        if usd_amount not in {None, ""}:
            raw = float(usd_amount or 0)
            # Pre-aggregated rows (e.g. period_card_stats) do not carry input_sign and should keep stored sign.
            if AnalyticsService._read_optional_value(row, "input_sign") in {None, ""}:
                return raw
            return abs(raw) * direction
        amount = AnalyticsService._read_optional_value(row, "amount")
        return abs(float(amount or 0)) * direction

    @staticmethod
    def _row_signed_unit_count(row) -> float:
        unit_count = AnalyticsService._read_optional_value(row, "unit_count")
        if unit_count in {None, ""}:
            return 0.0
        direction = AnalyticsService._input_direction(row)
        if AnalyticsService._read_optional_value(row, "input_sign") in {None, ""}:
            return float(unit_count or 0)
        return abs(float(unit_count or 0)) * direction

    @staticmethod
    def _input_direction(row) -> float:
        input_sign = AnalyticsService._read_optional_value(row, "input_sign")
        if input_sign is None:
            return 1.0
        try:
            return -1.0 if float(input_sign) < 0 else 1.0
        except (TypeError, ValueError):
            return 1.0

    @staticmethod
    def _sum_values(rows: list[dict], key: str) -> float:
        return sum(float(AnalyticsService._read_value(row, key) or 0) for row in rows)

    @staticmethod
    def _count_transactions_by_role(rows: list[dict], role: str) -> int:
        return sum(1 for row in rows if AnalyticsService._row_business_role(row) == role)

    @staticmethod
    def _sum_role_transaction_count(rows: list[dict], role: str) -> int:
        return sum(
            int(AnalyticsService._read_optional_value(row, "transaction_count") or 0)
            for row in rows
            if AnalyticsService._row_business_role(row) == role
        )

    def _group_label_map(self) -> dict[str, str]:
        return {
            str(row["group_key"]): str(row["chat_name"])
            for row in self.db.get_all_groups()
        }

    @staticmethod
    def _row_group_label(row, group_label_map: dict[str, str]) -> str:
        chat_name = AnalyticsService._read_optional_value(row, "chat_name")
        if chat_name not in {None, ""}:
            return str(chat_name)
        group_key = AnalyticsService._read_optional_value(row, "group_key")
        if group_key is None:
            return "未知群"
        return str(group_label_map.get(str(group_key), str(group_key)))

    @staticmethod
    def _read_value(row, key: str):
        if hasattr(row, "keys"):
            return row[key]
        return row.get(key)

    @staticmethod
    def _read_optional_value(row, key: str):
        if hasattr(row, "keys"):
            return row[key] if key in row.keys() else None
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
