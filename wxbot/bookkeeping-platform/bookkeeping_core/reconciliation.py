from __future__ import annotations

import csv
import io
from datetime import date, datetime

from .database import BookkeepingDB
from .parser import NEGATIVE_CATEGORIES
from .role_mapping import is_financial_role, resolve_business_role


RMB_TOLERANCE = 0.01
RATE_TOLERANCE = 0.0001
ISSUE_PENDING_RECONCILIATION = "pending_reconciliation"
ISSUE_RATE_FORMULA_ERROR = "rate_formula_error"
ISSUE_MISSING_RATE = "missing_rate"
ISSUE_EDITED_UNREVIEWED = "edited_unreviewed"


class ReconciliationService:
    def __init__(self, db: BookkeepingDB) -> None:
        self.db = db

    def build_ledger_payload(
        self,
        *,
        scope: str = "realtime",
        period_id: int | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        combination_id: int | None = None,
        group_num: int | None = None,
        business_role: str = "",
        group_key: str = "",
        card_type: str = "",
        edited: str = "all",
        issue_type: str = "",
    ) -> dict:
        normalized_scope = self._normalize_scope(scope)
        normalized_edited = self._normalize_edited_filter(edited)
        normalized_issue_type = self._normalize_issue_type(issue_type)
        normalized_group_num = self._normalize_group_num(group_num)
        combinations = self._list_combinations()
        selected_combination = self._resolve_selected_combination(combinations, combination_id)
        if selected_combination is not None and normalized_group_num is not None:
            raise ValueError("combination_id and group_num cannot be used together")
        normalized_start_date, normalized_end_date = self._normalize_date_range(
            scope=normalized_scope,
            start_date=start_date,
            end_date=end_date,
        )
        periods = self._list_periods()
        scope_rows = self._build_scope_rows(
            scope=normalized_scope,
            period_id=period_id,
            start_date=normalized_start_date,
            end_date=normalized_end_date,
            periods=periods,
        )
        scoped_rows = self._filter_primary_scope_rows(
            scope_rows,
            selected_combination=selected_combination,
            group_num=normalized_group_num,
        )
        available_group_rows = self._filter_rows(
            scoped_rows,
            business_role=business_role,
            group_key="",
            card_type="",
            edited="all",
            issue_type="",
        )
        available_card_rows = self._filter_rows(
            scoped_rows,
            business_role=business_role,
            group_key=group_key,
            card_type="",
            edited="all",
            issue_type="",
        )
        summary_rows = self._filter_rows(
            scoped_rows,
            business_role=business_role,
            group_key=group_key,
            card_type=card_type,
            edited=normalized_edited,
            issue_type="",
        )
        rows = self._filter_rows(
            summary_rows,
            business_role="",
            group_key="",
            card_type="",
            edited="all",
            issue_type=normalized_issue_type,
        )
        return {
            "scope": normalized_scope,
            "periods": periods,
            "selected_period_id": period_id,
            "range": {
                "start_date": normalized_start_date,
                "end_date": normalized_end_date,
            },
            "filters": {
                "combination_id": int(selected_combination["id"]) if selected_combination is not None else None,
                "group_num": normalized_group_num,
                "business_role": business_role,
                "group_key": group_key,
                "card_type": card_type,
                "edited": normalized_edited,
                "issue_type": normalized_issue_type,
            },
            "summary": self._build_summary(summary_rows),
            "rows": rows,
            "available_combinations": combinations,
            "available_group_nums": self._build_group_num_options(scope_rows),
            "available_groups": self._build_group_options(available_group_rows),
            "available_card_types": self._build_card_type_options(available_card_rows),
            "selected_combination": selected_combination,
        }

    def export_ledger_csv(
        self,
        *,
        scope: str = "realtime",
        period_id: int | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        combination_id: int | None = None,
        group_num: int | None = None,
        business_role: str = "",
        group_key: str = "",
        card_type: str = "",
        edited: str = "all",
        issue_type: str = "",
        export_mode: str = "detail",
    ) -> str:
        normalized_export_mode = self._normalize_export_mode(export_mode)
        payload = self.build_ledger_payload(
            scope=scope,
            period_id=period_id,
            start_date=start_date,
            end_date=end_date,
            combination_id=combination_id,
            group_num=group_num,
            business_role=business_role,
            group_key=group_key,
            card_type=card_type,
            edited=edited,
            issue_type=issue_type,
        )
        if normalized_export_mode == "summary":
            return self._export_summary_csv(payload)
        return self._export_detail_csv(payload)

    def _export_detail_csv(self, payload: dict) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "row_type",
                "row_id",
                "period_id",
                "period_status",
                "group_key",
                "chat_name",
                "group_num",
                "business_role",
                "sender_name",
                "message_id",
                "raw",
                "card_type",
                "amount",
                "rate",
                "expected_rmb_value",
                "rmb_value",
                "usd_amount",
                "created_at",
                "edited_by",
                "edited_at",
                "issue_flags",
                "source_table",
                "edit_note",
                "entry_note",
                "match_status",
                "variance_rmb",
                "variance_rate",
                "linked_transaction_id",
            ]
        )
        for row in payload["rows"]:
            writer.writerow(
                [
                    row["row_type"],
                    row["row_id"],
                    row["period_id"] or "",
                    row["period_status"],
                    row["group_key"],
                    row["chat_name"],
                    row["group_num"] if row["group_num"] is not None else "",
                    row["business_role"] or "",
                    row["sender_name"] or "",
                    row["message_id"] or "",
                    row["raw"] or "",
                    row["card_type"],
                    self._csv_number(row["amount"]),
                    self._csv_number(row["rate"]),
                    self._csv_number(row["expected_rmb_value"]),
                    self._csv_number(row["rmb_value"]),
                    self._csv_number(row["usd_amount"]),
                    row["created_at"] or "",
                    row["edited_by"] or "",
                    row["edited_at"] or "",
                    "|".join(row["issue_flags"]),
                    row["source_table"],
                    row["edit_note"] or "",
                    row["note"] or "",
                    row["match_status"],
                    self._csv_number(row["variance_rmb"]),
                    self._csv_number(row["variance_rate"]),
                    row["linked_transaction_id"] or "",
                ]
            )
        return output.getvalue()

    def _export_summary_csv(self, payload: dict) -> str:
        filters = payload.get("filters", {})
        selected_combination = payload.get("selected_combination")
        combination_name = str(selected_combination.get("name") or "") if isinstance(selected_combination, dict) else ""
        combination_groups = (
            "+".join(str(item) for item in selected_combination.get("group_numbers", []))
            if isinstance(selected_combination, dict)
            else ""
        )
        group_num = filters.get("group_num")
        group_key = str(filters.get("group_key") or "")
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "scope",
                "combination_name",
                "combination_group_nums",
                "group_num",
                "group_key",
                "business_role",
                "card_type",
                "row_count",
                "usd_amount",
                "rmb_value",
            ]
        )
        for row in self._build_summary_export_rows(payload.get("rows", [])):
            writer.writerow(
                [
                    payload.get("scope") or "",
                    combination_name,
                    combination_groups,
                    group_num if group_num is not None else "",
                    group_key,
                    row["business_role"],
                    row["card_type"],
                    row["row_count"],
                    self._csv_number(row["usd_amount"]),
                    self._csv_number(row["rmb_value"]),
                ]
            )
        return output.getvalue()

    def _build_scope_rows(
        self,
        *,
        scope: str,
        period_id: int | None,
        start_date: str | None,
        end_date: str | None,
        periods: list[dict],
    ) -> list[dict]:
        if scope == "period":
            if period_id is None:
                raise ValueError("period_id is required when scope=period")
            transactions = self.db.list_period_transactions(int(period_id))
            finance_entries = self.db.list_finance_adjustment_entries(period_id=int(period_id))
        elif scope == "range":
            if not start_date or not end_date:
                raise ValueError("start_date and end_date are required when scope=range")
            start_at = f"{start_date} 00:00:00"
            end_at = f"{end_date} 23:59:59.999999"
            transactions = self.db.list_transactions_in_date_range(start_at, end_at)
            finance_entries = self.db.list_finance_adjustment_entries(start_at=start_at, end_at=end_at)
            linked_transaction_ids = [int(row["id"]) for row in transactions if row.get("id") is not None]
            linked_entries = self.db.list_finance_adjustment_entries_by_transaction_ids(linked_transaction_ids)
            existing_entry_ids = {int(row["id"]) for row in finance_entries if row.get("id") is not None}
            finance_entries.extend(
                row
                for row in linked_entries
                if int(row["id"]) not in existing_entry_ids
            )
        else:
            live_window_start_at = self._resolve_live_window_start_at(periods)
            transactions = self.db.list_current_window_transactions(live_window_start_at)
            finance_entries = self.db.list_finance_adjustment_entries(
                start_at=live_window_start_at,
                include_unscoped_only=True,
            )

        rows = [
            self._serialize_transaction_row(
                row,
                scope=scope,
                selected_period_id=period_id,
                periods=periods,
            )
            for row in transactions
        ]
        rows.extend(
            self._serialize_finance_adjustment_row(
                row,
                scope=scope,
                selected_period_id=period_id,
            )
            for row in finance_entries
        )
        return sorted(
            rows,
            key=lambda item: (str(item["created_at"] or ""), int(item["row_id"] or 0)),
            reverse=True,
        )

    def _serialize_transaction_row(
        self,
        row,
        *,
        scope: str,
        selected_period_id: int | None,
        periods: list[dict],
    ) -> dict:
        transaction_group_num = self._int_or_none(row.get("group_num"))
        mapped_group_num = self._int_or_none(row.get("mapped_group_num"))
        group_num = mapped_group_num if mapped_group_num is not None else transaction_group_num
        business_role = resolve_business_role(
            business_role=row.get("business_role"),
            group_num=group_num,
        )
        category = str(row.get("category") or "rmb").lower()
        amount = float(row.get("amount") or 0)
        rate = float(row["rate"]) if row.get("rate") is not None else None
        rmb_value = float(row.get("rmb_value") or 0)
        usd_amount = float(row["usd_amount"]) if row.get("usd_amount") is not None else (0.0 if category == "rmb" else amount)
        expected_rmb_value = self._expected_transaction_rmb(
            input_sign=int(row.get("input_sign") or 0),
            amount=amount,
            category=category,
            rate=rate,
        )
        period_match = self._resolve_transaction_period(
            created_at=str(row.get("created_at") or ""),
            periods=periods,
        )
        if scope == "period" and selected_period_id is not None:
            period_id = int(selected_period_id)
            period_status = "settled"
        else:
            period_id = period_match["id"] if period_match is not None else None
            period_status = "settled" if period_id is not None or int(row.get("settled") or 0) else "unsettled"
        actual_rate = None
        variance_rate = None
        if category != "rmb" and amount:
            actual_rate = abs(rmb_value) / abs(amount)
            if rate is not None:
                variance_rate = actual_rate - rate
        issue_flags = self._build_transaction_issue_flags(
            business_role=business_role,
            category=category,
            rate=rate,
            expected_rmb_value=expected_rmb_value,
            rmb_value=rmb_value,
            is_edited=row.get("edited_at") is not None,
        )
        return {
            "row_type": "transaction",
            "row_id": int(row["id"]),
            "period_id": period_id,
            "period_status": period_status,
            "group_key": str(row.get("group_key") or ""),
            "chat_name": str(row.get("chat_name") or ""),
            "group_num": group_num,
            "business_role": business_role,
            "sender_name": str(row.get("sender_name") or ""),
            "message_id": str(row.get("message_id") or ""),
            "raw": str(row.get("raw") or ""),
            "card_type": category,
            "amount": amount,
            "rate": rate,
            "expected_rmb_value": expected_rmb_value,
            "rmb_value": rmb_value,
            "usd_amount": usd_amount,
            "created_at": self._normalize_timestamp(row.get("created_at")),
            "edited_by": self._normalize_text(row.get("edited_by")),
            "edited_at": self._normalize_timestamp(row.get("edited_at")),
            "edit_note": self._normalize_text(row.get("edit_note")),
            "is_edited": row.get("edited_at") is not None,
            "issue_flags": issue_flags,
            "source_table": "transactions",
            "match_status": "pending" if is_financial_role(business_role) else "not_applicable",
            "variance_rmb": (rmb_value - expected_rmb_value) if expected_rmb_value is not None else None,
            "variance_rate": variance_rate,
            "linked_transaction_id": int(row["id"]),
            "note": "",
        }

    def _serialize_finance_adjustment_row(
        self,
        row,
        *,
        scope: str,
        selected_period_id: int | None,
    ) -> dict:
        group_num = self._int_or_none(row.get("group_num"))
        business_role = resolve_business_role(
            business_role=row.get("business_role") or row.get("mapped_business_role"),
            group_num=group_num,
        )
        period_id = self._int_or_none(row.get("period_id"))
        if scope == "period" and selected_period_id is not None:
            period_id = int(selected_period_id)
        return {
            "row_type": "finance_adjustment",
            "row_id": int(row["id"]),
            "period_id": period_id,
            "period_status": "settled" if period_id is not None else "unsettled",
            "group_key": str(row.get("group_key") or ""),
            "chat_name": str(row.get("chat_name") or ""),
            "group_num": group_num,
            "business_role": business_role,
            "sender_name": str(row.get("created_by") or ""),
            "message_id": "",
            "raw": str(row.get("note") or ""),
            "card_type": str(row.get("card_type") or "").lower(),
            "amount": float(row.get("usd_amount") or 0),
            "rate": float(row["rate"]) if row.get("rate") is not None else None,
            "expected_rmb_value": None,
            "rmb_value": float(row.get("rmb_amount") or 0),
            "usd_amount": float(row.get("usd_amount") or 0),
            "created_at": self._normalize_timestamp(row.get("created_at")),
            "edited_by": None,
            "edited_at": None,
            "edit_note": None,
            "is_edited": False,
            "issue_flags": [ISSUE_PENDING_RECONCILIATION] if is_financial_role(business_role) else [],
            "source_table": "finance_adjustment_entries",
            "match_status": "pending" if is_financial_role(business_role) else "not_applicable",
            "variance_rmb": None,
            "variance_rate": None,
            "linked_transaction_id": self._int_or_none(row.get("linked_transaction_id")),
            "note": str(row.get("note") or ""),
        }

    def _build_transaction_issue_flags(
        self,
        *,
        business_role: str | None,
        category: str,
        rate: float | None,
        expected_rmb_value: float | None,
        rmb_value: float,
        is_edited: bool,
    ) -> list[str]:
        flags: list[str] = []
        if is_financial_role(business_role):
            flags.append(ISSUE_PENDING_RECONCILIATION)
        if category != "rmb" and rate is None:
            flags.append(ISSUE_MISSING_RATE)
        if (
            category != "rmb"
            and rate is not None
            and expected_rmb_value is not None
            and abs(expected_rmb_value - rmb_value) > RMB_TOLERANCE
        ):
            flags.append(ISSUE_RATE_FORMULA_ERROR)
        if is_edited:
            flags.append(ISSUE_EDITED_UNREVIEWED)
        return flags

    def _filter_primary_scope_rows(
        self,
        rows: list[dict],
        *,
        selected_combination: dict | None,
        group_num: int | None,
    ) -> list[dict]:
        if selected_combination is not None:
            allowed_group_nums = {int(item) for item in selected_combination.get("group_numbers", [])}
            return [
                row for row in rows
                if row.get("group_num") is not None and int(row["group_num"]) in allowed_group_nums
            ]
        if group_num is not None:
            return [
                row for row in rows
                if row.get("group_num") is not None and int(row["group_num"]) == group_num
            ]
        return rows

    def _filter_rows(
        self,
        rows: list[dict],
        *,
        business_role: str,
        group_key: str,
        card_type: str,
        edited: str,
        issue_type: str,
    ) -> list[dict]:
        normalized_role = str(business_role or "").strip().lower()
        normalized_group_key = str(group_key or "").strip()
        normalized_card_type = str(card_type or "").strip().lower()
        filtered: list[dict] = []
        for row in rows:
            row_role = str(row.get("business_role") or "").lower()
            if normalized_role:
                if normalized_role == "unassigned":
                    if row_role not in {"", "unassigned"}:
                        continue
                elif row_role != normalized_role:
                    continue
            if normalized_group_key and str(row.get("group_key") or "") != normalized_group_key:
                continue
            if normalized_card_type and str(row.get("card_type") or "").lower() != normalized_card_type:
                continue
            if edited == "yes" and not row.get("is_edited"):
                continue
            if edited == "no" and row.get("is_edited"):
                continue
            if issue_type and issue_type not in row.get("issue_flags", []):
                continue
            filtered.append(row)
        return filtered

    def _build_summary(self, rows: list[dict]) -> dict:
        return {
            "row_count": len(rows),
            "financial_row_count": sum(1 for row in rows if is_financial_role(row.get("business_role"))),
            "unreconciled_count": sum(1 for row in rows if ISSUE_PENDING_RECONCILIATION in row.get("issue_flags", [])),
            "rate_formula_error_count": sum(1 for row in rows if ISSUE_RATE_FORMULA_ERROR in row.get("issue_flags", [])),
            "missing_rate_count": sum(1 for row in rows if ISSUE_MISSING_RATE in row.get("issue_flags", [])),
            "edited_unreviewed_count": sum(1 for row in rows if ISSUE_EDITED_UNREVIEWED in row.get("issue_flags", [])),
        }

    def _build_group_options(self, rows: list[dict]) -> list[dict]:
        grouped: dict[str, dict] = {}
        for row in rows:
            group_key = str(row.get("group_key") or "").strip()
            if not group_key:
                continue
            grouped[group_key] = {
                "group_key": group_key,
                "chat_name": str(row.get("chat_name") or ""),
                "group_num": row.get("group_num"),
                "business_role": row.get("business_role"),
            }
        return sorted(
            grouped.values(),
            key=lambda item: (
                self._sort_group_num(item.get("group_num")),
                str(item.get("chat_name") or item.get("group_key") or ""),
            ),
        )

    def _build_group_num_options(self, rows: list[dict]) -> list[int]:
        values = {
            int(row["group_num"])
            for row in rows
            if row.get("group_num") is not None
        }
        return sorted(values)

    def _build_card_type_options(self, rows: list[dict]) -> list[str]:
        values = {
            str(row.get("card_type") or "").lower()
            for row in rows
            if str(row.get("card_type") or "").strip()
        }
        return sorted(values)

    def _list_combinations(self) -> list[dict]:
        rows = sorted(
            self.db.list_group_combinations(),
            key=lambda row: (str(row.get("name") or ""), int(row["id"])),
        )
        combinations: list[dict] = []
        for row in rows:
            group_numbers = [
                int(item)
                for item in str(row.get("group_numbers") or "").split(",")
                if str(item).strip()
            ]
            combinations.append(
                {
                    "id": int(row["id"]),
                    "name": str(row.get("name") or ""),
                    "group_numbers": group_numbers,
                }
            )
        return combinations

    def _resolve_selected_combination(self, combinations: list[dict], combination_id: int | None) -> dict | None:
        if combination_id is None:
            return None
        for row in combinations:
            if int(row["id"]) == int(combination_id):
                return row
        raise ValueError(f"unknown combination_id: {combination_id}")

    def _build_summary_export_rows(self, rows: list[dict]) -> list[dict]:
        buckets: dict[tuple[str, str], dict] = {}
        for row in rows:
            role = str(row.get("business_role") or "unassigned").strip().lower() or "unassigned"
            card_type = str(row.get("card_type") or "").strip().lower()
            if not card_type:
                continue
            bucket = buckets.setdefault(
                (role, card_type),
                {
                    "business_role": role,
                    "card_type": card_type,
                    "row_count": 0,
                    "usd_amount": 0.0,
                    "rmb_value": 0.0,
                },
            )
            bucket["row_count"] += 1
            bucket["usd_amount"] += float(row.get("usd_amount") or 0)
            bucket["rmb_value"] += float(row.get("rmb_value") or 0)
        return sorted(
            buckets.values(),
            key=lambda item: (str(item["business_role"]), str(item["card_type"])),
        )

    def _list_periods(self) -> list[dict]:
        periods = sorted(
            self.db.list_accounting_periods(),
            key=lambda row: (self._normalize_timestamp(row["closed_at"]) or "", int(row["id"])),
            reverse=True,
        )[:20]
        return [
            {
                "id": int(row["id"]),
                "start_at": self._normalize_timestamp(row["start_at"]),
                "end_at": self._normalize_timestamp(row["end_at"]),
                "closed_at": self._normalize_timestamp(row["closed_at"]),
                "closed_by": self._normalize_text(row.get("closed_by")),
            }
            for row in periods
        ]

    def _resolve_live_window_start_at(self, periods: list[dict]) -> str | None:
        if not periods:
            return None
        return periods[0]["end_at"]

    def _resolve_transaction_period(self, *, created_at: str, periods: list[dict]) -> dict | None:
        if not created_at:
            return None
        for period in periods:
            start_at = str(period.get("start_at") or "")
            end_at = str(period.get("end_at") or "")
            if start_at and end_at and start_at < created_at <= end_at:
                return period
        return None

    def _normalize_scope(self, value: str) -> str:
        normalized = str(value or "realtime").strip().lower()
        if normalized not in {"realtime", "period", "range"}:
            raise ValueError(f"unsupported scope: {value}")
        return normalized

    def _normalize_edited_filter(self, value: str) -> str:
        normalized = str(value or "all").strip().lower()
        if normalized not in {"all", "yes", "no"}:
            raise ValueError(f"unsupported edited filter: {value}")
        return normalized

    def _normalize_issue_type(self, value: str) -> str:
        normalized = str(value or "").strip().lower()
        if not normalized:
            return ""
        allowed = {
            ISSUE_PENDING_RECONCILIATION,
            ISSUE_RATE_FORMULA_ERROR,
            ISSUE_MISSING_RATE,
            ISSUE_EDITED_UNREVIEWED,
        }
        if normalized not in allowed:
            raise ValueError(f"unsupported issue_type: {value}")
        return normalized

    def _normalize_export_mode(self, value: str) -> str:
        normalized = str(value or "detail").strip().lower()
        if normalized not in {"detail", "summary"}:
            raise ValueError(f"unsupported export_mode: {value}")
        return normalized

    def _normalize_date_range(
        self,
        *,
        scope: str,
        start_date: str | None,
        end_date: str | None,
    ) -> tuple[str | None, str | None]:
        if scope != "range":
            return None, None
        today = date.today().isoformat()
        start_text = str(start_date or today).strip()
        end_text = str(end_date or today).strip()
        date.fromisoformat(start_text)
        date.fromisoformat(end_text)
        if start_text > end_text:
            raise ValueError("start_date cannot be after end_date")
        return start_text, end_text

    @staticmethod
    def _normalize_group_num(value: int | None) -> int | None:
        if value is None:
            return None
        if int(value) < 0 or int(value) > 9:
            raise ValueError(f"unsupported group_num: {value}")
        return int(value)

    @staticmethod
    def _expected_transaction_rmb(
        *,
        input_sign: int,
        amount: float,
        category: str,
        rate: float | None,
    ) -> float | None:
        if category == "rmb":
            return input_sign * amount
        if rate is None:
            return None
        effective_sign = -input_sign if category in NEGATIVE_CATEGORIES else input_sign
        return effective_sign * amount * rate

    @staticmethod
    def _normalize_timestamp(value) -> str | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.isoformat(sep=" ")
        text = str(value).strip()
        return text or None

    @staticmethod
    def _normalize_text(value) -> str | None:
        text = str(value or "").strip()
        return text or None

    @staticmethod
    def _sort_group_num(value) -> tuple[int, int]:
        if value is None:
            return (1, 999)
        return (0, int(value))

    @staticmethod
    def _int_or_none(value) -> int | None:
        if value in {None, ""}:
            return None
        return int(value)

    @staticmethod
    def _csv_number(value) -> str:
        if value is None:
            return ""
        return f"{float(value):.6f}".rstrip("0").rstrip(".")
