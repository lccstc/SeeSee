from __future__ import annotations

import inspect
import json
import logging
import os
from datetime import date, datetime
from pathlib import Path
from urllib.parse import parse_qs

from bookkeeping_core.analytics import AnalyticsService
from bookkeeping_core.contracts import core_action_to_dict
from bookkeeping_core.database import BookkeepingDB, require_postgres_dsn
from bookkeeping_core.periods import AccountingPeriodService
from bookkeeping_core.quotes import (
    list_builtin_quote_dictionary_aliases,
    normalize_quote_card_type,
    normalize_quote_country_or_currency,
    normalize_quote_form_factor,
    normalize_quote_multiplier,
)
from bookkeeping_core.reconciliation import ReconciliationService
from bookkeeping_core.reporting import ReportingService
from bookkeeping_core.runtime import UnifiedBookkeepingRuntime
from bookkeeping_web.pages import (
    render_dashboard_page,
    render_history_page,
    render_quote_dictionary_page,
    render_quotes_page,
    render_reconciliation_page,
    render_role_mapping_page,
    render_workbench_page,
)

logger = logging.getLogger(__name__)


def create_app(
    db_target: str | Path,
    core_token: str | None = None,
    runtime_master_users: list[str] | None = None,
):
    db_file = require_postgres_dsn(db_target, context="Web runtime database")
    _ensure_runtime_database_is_ready(db_file)
    runtime_db = None
    runtime = None
    runtime_export_dir = _runtime_export_dir(db_file)
    master_users = _normalize_runtime_master_users(runtime_master_users)

    def get_runtime():
        nonlocal runtime_db, runtime
        if runtime is None:
            runtime_db = BookkeepingDB(db_file)
            runtime = UnifiedBookkeepingRuntime(
                db=runtime_db,
                master_users=master_users,
                export_dir=runtime_export_dir,
            )
        return runtime

    def close_runtime() -> None:
        nonlocal runtime_db, runtime
        if runtime_db is not None:
            runtime_db.close()
        runtime_db = None
        runtime = None

    def app(environ, start_response):
        method = environ.get("REQUEST_METHOD", "GET").upper()
        path = environ.get("PATH_INFO", "/")
        if path == "/":
            return _respond_html(start_response, render_dashboard_page())
        if path == "/workbench":
            return _respond_html(start_response, render_workbench_page())
        if path == "/quotes":
            return _respond_html(start_response, render_quotes_page())
        if path == "/quote-dictionary":
            return _respond_html(start_response, render_quote_dictionary_page())
        if path == "/role-mapping":
            return _respond_html(start_response, render_role_mapping_page())
        if path == "/history":
            return _respond_html(start_response, render_history_page())
        if path == "/reconciliation":
            return _respond_html(start_response, render_reconciliation_page())
        if path == "/api/dashboard" and method == "GET":
            return _with_db(db_file, start_response, _handle_dashboard, environ)
        if path == "/api/workbench" and method == "GET":
            return _with_db(db_file, start_response, _handle_workbench, environ)
        if path == "/api/role-mapping" and method == "GET":
            return _with_db(db_file, start_response, _handle_role_mapping, environ)
        if path == "/api/role-mapping/group-num" and method == "POST":
            return _with_db(
                db_file, start_response, _handle_role_mapping_group_num, environ
            )
        if path == "/api/history" and method == "GET":
            return _with_db(db_file, start_response, _handle_history, environ)
        if path == "/api/quotes/board" and method == "GET":
            return _with_db(db_file, start_response, _handle_quotes_board, environ)
        if path == "/api/quotes/history" and method == "GET":
            return _with_db(db_file, start_response, _handle_quotes_history, environ)
        if path == "/api/quotes/rankings" and method == "GET":
            return _with_db(db_file, start_response, _handle_quotes_rankings, environ)
        if path == "/api/quotes/matches" and method == "GET":
            return _with_db(db_file, start_response, _handle_quotes_matches, environ)
        if path == "/api/quotes/group-profiles":
            return _with_db(db_file, start_response, _handle_quotes_group_profiles, environ)
        if path == "/api/quotes/dictionary":
            return _with_db(db_file, start_response, _handle_quotes_dictionary, environ)
        if path == "/api/quotes/dictionary/disable" and method == "POST":
            return _with_db(db_file, start_response, _handle_quotes_dictionary_disable, environ)
        if path == "/api/quotes/exceptions" and method == "GET":
            return _with_db(
                db_file, start_response, _handle_quotes_exceptions, environ
            )
        if path == "/api/quotes/exceptions/resolve" and method == "POST":
            return _with_db(
                db_file, start_response, _handle_quotes_exception_resolve, environ
            )
        if path == "/api/quotes/exceptions/suggest-template" and method == "POST":
            return _with_db(
                db_file, start_response, _handle_quotes_suggest_template, environ
            )
        if path == "/api/quotes/exceptions/batch-rules" and method == "POST":
            return _with_db(
                db_file, start_response, _handle_quotes_batch_rules, environ
            )
        if path == "/api/quotes/inquiries":
            return _with_db(db_file, start_response, _handle_quotes_inquiries, environ)
        if path == "/api/quotes/delete" and method == "POST":
            return _with_db(db_file, start_response, _handle_quotes_delete, environ)
        if path == "/api/reconciliation/ledger" and method == "GET":
            return _with_db(
                db_file, start_response, _handle_reconciliation_ledger, environ
            )
        if path == "/api/reconciliation/export" and method == "GET":
            return _with_db(
                db_file, start_response, _handle_reconciliation_export, environ
            )
        if path == "/api/reconciliation/adjustments" and method == "POST":
            return _with_db(
                db_file, start_response, _handle_reconciliation_adjustments, environ
            )
        if path == "/api/reconciliation/difference-trace" and method == "GET":
            return _with_db(
                db_file, start_response, _handle_difference_trace, environ
            )
        if path == "/api/accounting-periods" and method == "GET":
            return _with_db(db_file, start_response, _handle_accounting_periods)
        if path == "/api/accounting-periods/close" and method == "POST":
            return _with_db(
                db_file, start_response, _handle_accounting_period_close, environ
            )
        if path == "/api/accounting-periods/settle-all" and method == "POST":
            return _handle_accounting_period_settle_all(
                get_runtime(), start_response, environ
            )
        if path == "/api/group-broadcasts" and method == "POST":
            return _handle_group_broadcast(get_runtime(), start_response, environ)
        if path == "/api/adjustments" and method == "POST":
            return _with_db(db_file, start_response, _handle_adjustments, environ)
        if path == "/api/transactions/update" and method == "POST":
            return _with_db(
                db_file, start_response, _handle_transaction_update, environ
            )
        if path == "/api/group-combinations":
            return _with_db(
                db_file, start_response, _handle_group_combinations, environ
            )
        if path == "/api/core/messages" and method == "POST":
            if not _is_authorized(environ, core_token):
                return _respond_json(start_response, 401, {"error": "Unauthorized"})
            return _handle_core_messages(get_runtime(), start_response, environ)
        if path == "/api/incoming-messages" and method == "GET":
            if not _is_authorized(environ, core_token):
                return _respond_json(start_response, 401, {"error": "Unauthorized"})
            return _with_db(db_file, start_response, _handle_incoming_messages, environ)
        if path == "/api/incoming-messages/with-transactions" and method == "GET":
            if not _is_authorized(environ, core_token):
                return _respond_json(start_response, 401, {"error": "Unauthorized"})
            return _with_db(
                db_file,
                start_response,
                _handle_incoming_messages_with_transactions,
                environ,
            )
        if path == "/api/core/actions" and method == "POST":
            if not _is_authorized(environ, core_token):
                return _respond_json(start_response, 401, {"error": "Unauthorized"})
            return _handle_core_actions(get_runtime(), start_response)
        if path == "/api/core/actions/ack" and method == "POST":
            if not _is_authorized(environ, core_token):
                return _respond_json(start_response, 401, {"error": "Unauthorized"})
            return _handle_core_actions_ack(get_runtime(), start_response, environ)
        if path == "/api/parse-results" and method == "GET":
            if not _is_authorized(environ, core_token):
                return _respond_json(start_response, 401, {"error": "Unauthorized"})
            return _with_db(db_file, start_response, _handle_parse_results, environ)
        if path == "/api/message-inspector" and method == "GET":
            if not _is_authorized(environ, core_token):
                return _respond_json(start_response, 401, {"error": "Unauthorized"})
            return _with_db(db_file, start_response, _handle_message_inspector, environ)
        if path == "/api/difference-trace" and method == "GET":
            if not _is_authorized(environ, core_token):
                return _respond_json(start_response, 401, {"error": "Unauthorized"})
            return _with_db(db_file, start_response, _handle_difference_trace, environ)
        return _respond_json(start_response, 404, {"error": f"Unknown path: {path}"})

    app.close = close_runtime  # type: ignore[attr-defined]
    return app


def _with_db(db_target: str | Path, start_response, handler, environ=None, *args):
    db = BookkeepingDB(db_target)
    try:
        return handler(db, start_response, environ, *args)
    finally:
        db.close()


def _ensure_runtime_database_is_ready(db_target: str | Path) -> None:
    db = BookkeepingDB(db_target)
    db.close()


def _handle_dashboard(db: BookkeepingDB, start_response, environ=None):
    payload = ReportingService(db).build_dashboard_payload()
    return _respond_json(start_response, 200, payload)


def _handle_workbench(db: BookkeepingDB, start_response, environ):
    params = _read_query_params(environ)
    raw_period_id = params.get("period_id")
    use_live_period = False
    try:
        if raw_period_id and str(raw_period_id).lower() == "realtime":
            period_id = None
            use_live_period = True
        else:
            period_id = int(raw_period_id) if raw_period_id else None
    except ValueError as exc:
        return _respond_json(start_response, 400, {"error": f"Bad query: {exc}"})
    payload = AnalyticsService(db).build_period_workbench(
        period_id=period_id, use_live_period=use_live_period
    )
    return _respond_json(start_response, 200, payload)


def _handle_role_mapping(db: BookkeepingDB, start_response, environ=None):
    payload = ReportingService(db).build_role_mapping_payload()
    return _respond_json(start_response, 200, payload)


def _handle_role_mapping_group_num(db: BookkeepingDB, start_response, environ):
    try:
        payload = _read_json_body(environ)
        group_key = str(payload["group_key"])
        group_num = int(payload["group_num"])
    except (KeyError, TypeError, ValueError) as exc:
        return _respond_json(start_response, 400, {"error": f"Bad payload: {exc}"})

    group_row = db.get_group_by_key(group_key)
    if group_row is None:
        return _respond_json(
            start_response, 404, {"error": f"group not found: {group_key}"}
        )

    ok = db.set_group(
        platform=str(group_row["platform"] or ""),
        group_key=group_key,
        chat_id=str(group_row["chat_id"] or ""),
        chat_name=str(group_row["chat_name"] or ""),
        group_num=group_num,
    )
    if not ok:
        return _respond_json(
            start_response, 400, {"error": "group_num must be between 0 and 9"}
        )
    return _respond_json(
        start_response, 200, {"group_key": group_key, "group_num": group_num}
    )


def _handle_history(db: BookkeepingDB, start_response, environ):
    params = _read_query_params(environ)
    start_date_value = (
        params.get("start_date") or date.today().replace(day=1).isoformat()
    )
    end_date_value = params.get("end_date") or date.today().isoformat()
    payload = AnalyticsService(db).build_history_analysis(
        start_date=start_date_value,
        end_date=end_date_value,
        card_keyword=params.get("card_keyword", ""),
        sort_by=params.get("sort_by", "profit"),
    )
    return _respond_json(start_response, 200, payload)


def _handle_quotes_board(db: BookkeepingDB, start_response, environ):
    params = _read_query_params(environ)
    payload = _call_optional_db_method(db, "list_quote_board", default={"rows": []})
    normalized = _normalize_quote_payload(payload)
    # 只展示客人组（组号 5/6/7/8）的报价
    rows = normalized.get("rows", [])
    customer_keys = set()
    try:
        for num in (5, 6, 7, 8):
            for g in db.get_groups_by_num(num):
                customer_keys.add(g["group_key"])
    except Exception:
        pass
    if customer_keys:
        rows = [r for r in rows if r.get("source_group_key") in customer_keys]
        normalized["rows"] = rows
        normalized["total"] = len(rows)
    if params:
        normalized["filters"] = {key: value for key, value in params.items() if value}
    return _respond_json(start_response, 200, normalized)


def _handle_quotes_history(db: BookkeepingDB, start_response, environ):
    params = _read_query_params(environ)
    try:
        limit = int(params.get("limit", "50")) if params.get("limit") else 50
        offset = int(params.get("offset", "0")) if params.get("offset") else 0
        if limit < 1 or limit > 500:
            return _respond_json(start_response, 400, {"error": "limit must be 1-500"})
        if offset < 0:
            return _respond_json(start_response, 400, {"error": "offset must be >= 0"})
    except ValueError as exc:
        return _respond_json(start_response, 400, {"error": f"Bad query: {exc}"})
    payload = _call_optional_db_method(
        db,
        "list_quote_history",
        default={"rows": [], "total": 0},
        card_type=params.get("card_type") or None,
        country_or_currency=params.get("country_or_currency") or None,
        source_group_key=params.get("source_group_key") or None,
        limit=limit,
        offset=offset,
    )
    normalized = _normalize_quote_payload(payload)
    normalized.setdefault("limit", limit)
    normalized.setdefault("offset", offset)
    if params.get("card_type"):
        normalized.setdefault("filters", {})["card_type"] = params.get("card_type")
    if params.get("country_or_currency"):
        normalized.setdefault("filters", {})["country_or_currency"] = params.get(
            "country_or_currency"
        )
    if params.get("source_group_key"):
        normalized.setdefault("filters", {})["source_group_key"] = params.get(
            "source_group_key"
        )
    return _respond_json(start_response, 200, normalized)


def _handle_quotes_rankings(db: BookkeepingDB, start_response, environ):
    params = _read_query_params(environ)
    try:
        limit = int(params.get("limit", "50")) if params.get("limit") else 50
        if limit < 1 or limit > 200:
            return _respond_json(start_response, 400, {"error": "limit must be 1-200"})
        required = ("card_type", "country_or_currency", "amount_range", "form_factor")
        missing = [key for key in required if not params.get(key)]
        if missing:
            return _respond_json(
                start_response,
                400,
                {"error": f"missing query params: {', '.join(missing)}"},
            )
    except ValueError as exc:
        return _respond_json(start_response, 400, {"error": f"Bad query: {exc}"})
    payload = _call_optional_db_method(
        db,
        "list_quote_rankings",
        default={"rows": [], "total": 0},
        card_type=params["card_type"],
        country_or_currency=params["country_or_currency"],
        amount_range=params["amount_range"],
        multiplier=params.get("multiplier") or None,
        form_factor=normalize_quote_form_factor(params["form_factor"]),
        limit=limit,
    )
    normalized = _normalize_quote_payload(payload)
    normalized["filters"] = {
        key: value
        for key, value in params.items()
        if key in {"card_type", "country_or_currency", "amount_range", "multiplier", "form_factor"} and value
    }
    return _respond_json(start_response, 200, normalized)


def _handle_quotes_matches(db: BookkeepingDB, start_response, environ):
    params = _read_query_params(environ)
    try:
        limit = int(params.get("limit", "50")) if params.get("limit") else 50
        amount = float(params["amount"])
        if limit < 1 or limit > 200:
            return _respond_json(start_response, 400, {"error": "limit must be 1-200"})
        card_type = normalize_quote_card_type(params["card_type"])
        country_or_currency = normalize_quote_country_or_currency(
            params["country_or_currency"]
        )
        form_factor = (
            normalize_quote_form_factor(params.get("form_factor") or "")
            if params.get("form_factor")
            else None
        )
        if not card_type or not country_or_currency:
            raise ValueError("card_type and country_or_currency are required")
    except (KeyError, ValueError) as exc:
        return _respond_json(start_response, 400, {"error": f"Bad query: {exc}"})
    payload = _call_optional_db_method(
        db,
        "list_quote_matches",
        default={"rows": [], "total": 0},
        card_type=card_type,
        country_or_currency=country_or_currency,
        amount=amount,
        form_factor=form_factor,
        limit=limit,
    )
    normalized = _normalize_quote_payload(payload)
    normalized["filters"] = {
        "card_type": card_type,
        "country_or_currency": country_or_currency,
        "amount": amount,
    }
    return _respond_json(start_response, 200, normalized)


def _handle_quotes_group_profiles(db: BookkeepingDB, start_response, environ):
    method = environ.get("REQUEST_METHOD", "GET").upper()
    if method == "GET":
        rows = _call_optional_db_method(
            db,
            "list_quote_group_profiles",
            default=[],
        )
        return _respond_json(start_response, 200, {"rows": rows, "total": len(rows)})
    if method != "POST":
        return _respond_json(start_response, 405, {"error": "Method not allowed"})
    try:
        payload = _read_json_body(environ)
        profile_id = db.upsert_quote_group_profile(
            platform=str(payload.get("platform") or "whatsapp").strip(),
            chat_id=str(payload["chat_id"]).strip(),
            chat_name=str(payload.get("chat_name") or payload["chat_id"]).strip(),
            default_card_type=normalize_quote_card_type(
                str(payload.get("default_card_type") or "")
            ),
            default_country_or_currency=normalize_quote_country_or_currency(
                str(payload.get("default_country_or_currency") or "")
            ),
            default_form_factor=normalize_quote_form_factor(
                str(payload.get("default_form_factor") or "不限").strip() or "不限"
            ),
            default_multiplier=normalize_quote_multiplier(
                str(payload.get("default_multiplier") or "").strip()
            ),
            parser_template=str(payload.get("parser_template") or "").strip(),
            stale_after_minutes=int(payload.get("stale_after_minutes") or 120),
            note=str(payload.get("note") or ""),
            template_config=str(payload.get("template_config") or ""),
        )
    except (KeyError, TypeError, ValueError) as exc:
        return _respond_json(start_response, 400, {"error": f"Bad payload: {exc}"})
    return _respond_json(start_response, 200, {"profile_id": profile_id})


def _handle_quotes_dictionary(db: BookkeepingDB, start_response, environ):
    method = environ.get("REQUEST_METHOD", "GET").upper()
    if method == "GET":
        params = _read_query_params(environ)
        category = params.get("category") or None
        include_disabled = str(params.get("include_disabled") or "1") != "0"
        include_builtin = str(params.get("include_builtin") or "1") != "0"
        db_rows = db.list_quote_dictionary_aliases(
            category=category,
            include_disabled=include_disabled,
        )
        rows: list[dict] = []
        existing_global_keys: set[str] = set()
        for row in db_rows:
            row = dict(row)
            row["canonical_input"] = str(
                row.get("canonical_input") or row.get("canonical_value") or ""
            )
            row["source"] = "custom"
            row["editable"] = True
            rows.append(row)
            if not str(row.get("scope_chat_id") or "").strip():
                existing_global_keys.add(
                    f'{row.get("category")}:{str(row.get("alias") or "").strip().lower()}'
                )
        builtin_total = 0
        if include_builtin:
            for row in list_builtin_quote_dictionary_aliases(category=category):
                global_key = (
                    f'{row.get("category")}:{str(row.get("alias") or "").strip().lower()}'
                )
                if global_key in existing_global_keys:
                    continue
                rows.append(row)
                builtin_total += 1
        return _respond_json(
            start_response,
            200,
            {
                "rows": rows,
                "total": len(rows),
                "custom_total": len(db_rows),
                "builtin_total": builtin_total,
            },
        )
    if method != "POST":
        return _respond_json(start_response, 405, {"error": "Method not allowed"})
    try:
        payload = _read_json_body(environ)
        _require_quote_admin_password(payload)
        category = _normalize_dictionary_category(str(payload["category"]).strip())
        alias = str(payload["alias"]).strip()
        canonical_value = _normalize_dictionary_canonical(
            category,
            str(payload["canonical_value"]).strip(),
        )
        if not alias or not canonical_value:
            raise ValueError("alias and canonical_value are required")
        alias_id = db.upsert_quote_dictionary_alias(
            category=category,
            alias=alias,
            canonical_value=canonical_value,
            canonical_input=str(payload.get("canonical_input") or payload["canonical_value"]).strip(),
            scope_platform=str(payload.get("scope_platform") or "").strip(),
            scope_chat_id=str(payload.get("scope_chat_id") or "").strip(),
            note=str(payload.get("note") or ""),
            enabled=bool(payload.get("enabled", True)),
        )
    except (KeyError, TypeError, ValueError) as exc:
        return _respond_json(start_response, 400, {"error": f"Bad payload: {exc}"})
    return _respond_json(start_response, 200, {"alias_id": alias_id})


def _handle_quotes_dictionary_disable(db: BookkeepingDB, start_response, environ):
    try:
        payload = _read_json_body(environ)
        _require_quote_admin_password(payload)
        updated = db.set_quote_dictionary_alias_enabled(
            alias_id=int(payload["id"]),
            enabled=False,
        )
    except (KeyError, TypeError, ValueError) as exc:
        return _respond_json(start_response, 400, {"error": f"Bad payload: {exc}"})
    return _respond_json(start_response, 200, {"updated": updated})


def _normalize_dictionary_category(category: str) -> str:
    allowed = {"country_currency", "card_type", "form_factor"}
    if category not in allowed:
        raise ValueError("category must be country_currency, card_type, or form_factor")
    return category


def _normalize_dictionary_canonical(category: str, value: str) -> str:
    if category == "card_type":
        return normalize_quote_card_type(value)
    if category == "form_factor":
        return normalize_quote_form_factor(value)
    return normalize_quote_country_or_currency(value)


def _require_quote_admin_password(payload: dict) -> None:
    expected = os.environ.get("QUOTE_ADMIN_PASSWORD", "")
    if not expected:
        raise ValueError("QUOTE_ADMIN_PASSWORD is not configured")
    provided = str(payload.get("admin_password") or "")
    if provided != expected:
        raise ValueError("admin password is invalid")


def _handle_quotes_exceptions(db: BookkeepingDB, start_response, environ):
    params = _read_query_params(environ)
    try:
        limit = int(params.get("limit", "50")) if params.get("limit") else 50
        offset = int(params.get("offset", "0")) if params.get("offset") else 0
        if limit < 1 or limit > 500:
            return _respond_json(start_response, 400, {"error": "limit must be 1-500"})
        if offset < 0:
            return _respond_json(start_response, 400, {"error": "offset must be >= 0"})
    except ValueError as exc:
        return _respond_json(start_response, 400, {"error": f"Bad query: {exc}"})
    payload = _call_optional_db_method(
        db,
        "list_quote_exceptions",
        default={"rows": [], "total": 0},
        limit=limit,
        offset=offset,
    )
    normalized = _normalize_quote_payload(payload)
    normalized.setdefault("limit", limit)
    normalized.setdefault("offset", offset)
    return _respond_json(start_response, 200, normalized)


def _handle_quotes_exception_resolve(db: BookkeepingDB, start_response, environ):
    import json
    from bookkeeping_core.template_engine import generate_strict_pattern_from_annotations
    try:
        payload = _read_json_body(environ)
        exception_id = int(payload["exception_id"])
        
        # New resolution mode: "annotate"
        resolution_status = str(payload.get("resolution_status") or "ignored").strip()
        if resolution_status == "annotate":
            fields = payload.get("fields", {})
            if not fields:
                return _respond_json(start_response, 400, {"error": "fields is required for annotate"})
            exc_row = db.get_quote_exception(exception_id=exception_id)
            if not exc_row:
                return _respond_json(start_response, 404, {"error": "exception not found"})

            # 支持对消息级异常中的单行进行标注
            annotate_line = str(payload.get("annotate_line", "")).strip()
            source_line = annotate_line if annotate_line else str(exc_row["source_line"])
            platform = str(exc_row["platform"])
            chat_id = str(exc_row["chat_id"])

            # 构建 annotations
            from bookkeeping_core.template_engine import build_annotations_from_fields
            annotations = build_annotations_from_fields(source_line, fields)

            # 尾部 (...) 自动追加 restriction
            import re as _re
            restriction_match = _re.search(r'\([^)]*\)\s*$', source_line)
            if restriction_match and "restriction" not in fields:
                ann_start = restriction_match.start()
                annotations.append({
                    "type": "restriction",
                    "value": source_line[ann_start:],
                    "start": ann_start,
                    "end": len(source_line),
                })
                annotations.sort(key=lambda a: a["start"])

            pattern = generate_strict_pattern_from_annotations(source_line, annotations)
            new_rule = {"pattern": pattern, "type": "price"}

            # Append rule to DB
            db.append_rule_to_group_profile(platform=platform, chat_id=chat_id, new_rule=new_rule)

            # 消息级异常：标注单行后保持 open，追加 note 记录已生成的规则
            existing_note = str(exc_row.get("resolution_note") or "")
            new_note = f"{existing_note}\n生成规则: {pattern}".strip()
            updated = db.resolve_quote_exception(
                exception_id=exception_id,
                resolution_status="open",
                resolution_note=new_note,
            )
            return _respond_json(start_response, 200, {"updated": updated, "new_pattern": pattern})
            
        if resolution_status == "attached":
            result = db.attach_quote_exception_to_restrictions(
                exception_id=exception_id,
            )
            return _respond_json(start_response, 200, result)
        if resolution_status not in {"ignored", "resolved", "attached", "annotate", "open"}:
            raise ValueError("resolution_status must be ignored, resolved, attached, annotate, or open")
        updated = db.resolve_quote_exception(
            exception_id=exception_id,
            resolution_status=resolution_status,
            resolution_note=str(payload.get("resolution_note") or ""),
        )
    except (KeyError, TypeError, ValueError) as exc:
        return _respond_json(start_response, 400, {"error": f"Bad payload: {exc}"})
    return _respond_json(start_response, 200, {"updated": updated})


def _handle_quotes_suggest_template(db: BookkeepingDB, start_response, environ):
    """Auto-detect template rules from an exception's source text."""
    from bookkeeping_core.template_engine import suggest_template_rules, deduplicate_rules
    try:
        payload = _read_json_body(environ)
        exception_id = int(payload["exception_id"])
        exc_row = db.get_quote_exception(exception_id=exception_id)
        if not exc_row:
            return _respond_json(start_response, 404, {"error": "exception not found"})
        source_text = str(exc_row.get("source_line") or "")
        detections = suggest_template_rules(source_text)
        rules = deduplicate_rules(detections)
        return _respond_json(start_response, 200, {
            "detections": detections,
            "suggested_rules": rules,
            "source_group_key": str(exc_row.get("source_group_key") or ""),
        })
    except (KeyError, TypeError, ValueError) as exc:
        return _respond_json(start_response, 400, {"error": f"Bad payload: {exc}"})


def _handle_quotes_batch_rules(db: BookkeepingDB, start_response, environ):
    """Save multiple template rules to a group's config at once."""
    try:
        payload = _read_json_body(environ)
        exception_id = int(payload["exception_id"])
        rules = payload.get("rules", [])
        if not rules:
            return _respond_json(start_response, 400, {"error": "rules is required"})
        exc_row = db.get_quote_exception(exception_id=exception_id)
        if not exc_row:
            return _respond_json(start_response, 404, {"error": "exception not found"})
        platform = str(exc_row["platform"])
        chat_id = str(exc_row["chat_id"])
        added = 0
        for rule in rules:
            pattern = str(rule.get("pattern", "")).strip()
            rule_type = str(rule.get("type", "price")).strip()
            if not pattern:
                continue
            db.append_rule_to_group_profile(
                platform=platform, chat_id=chat_id,
                new_rule={"pattern": pattern, "type": rule_type},
            )
            added += 1
        db.resolve_quote_exception(
            exception_id=exception_id,
            resolution_status="resolved",
            resolution_note=f"batch: {added} rules generated",
        )
        return _respond_json(start_response, 200, {"added": added})
    except (KeyError, TypeError, ValueError) as exc:
        return _respond_json(start_response, 400, {"error": f"Bad payload: {exc}"})


def _handle_quotes_inquiries(db: BookkeepingDB, start_response, environ):
    method = environ.get("REQUEST_METHOD", "GET").upper()
    if method == "GET":
        try:
            params = _read_query_params(environ)
            limit = int(params.get("limit", "100")) if params.get("limit") else 100
            if limit < 1 or limit > 500:
                return _respond_json(start_response, 400, {"error": "limit must be 1-500"})
        except ValueError as exc:
            return _respond_json(start_response, 400, {"error": f"Bad query: {exc}"})
        rows = _call_optional_db_method(
            db,
            "list_quote_inquiry_contexts",
            default=[],
            limit=limit,
        )
        return _respond_json(start_response, 200, {"rows": rows, "total": len(rows)})
    if method != "POST":
        return _respond_json(start_response, 405, {"error": "Method not allowed"})
    try:
        payload = _read_json_body(environ)
        platform = str(payload.get("platform") or "wechat").strip()
        chat_id = str(payload["chat_id"]).strip()
        chat_name = str(payload.get("chat_name") or chat_id).strip()
        source_group_key = str(payload.get("source_group_key") or f"{platform}:{chat_id}")
        inquiry_id = db.create_quote_inquiry_context(
            platform=platform,
            source_group_key=source_group_key,
            chat_id=chat_id,
            chat_name=chat_name,
            card_type=normalize_quote_card_type(str(payload["card_type"]).strip()),
            country_or_currency=normalize_quote_country_or_currency(
                str(payload["country_or_currency"]).strip()
            ),
            amount_range=str(payload["amount_range"]).strip(),
            multiplier=str(payload.get("multiplier") or "").strip() or None,
            form_factor=normalize_quote_form_factor(
                str(payload.get("form_factor") or "不限").strip() or "不限"
            ),
            requested_by=str(payload.get("requested_by") or "web"),
            prompt_text=str(payload.get("prompt_text") or ""),
            expires_at=str(payload.get("expires_at") or "").strip() or None,
        )
    except (KeyError, TypeError, ValueError) as exc:
        return _respond_json(start_response, 400, {"error": f"Bad payload: {exc}"})
    return _respond_json(start_response, 200, {"inquiry_id": inquiry_id})


def _handle_quotes_delete(db: BookkeepingDB, start_response, environ):
    try:
        payload = _read_json_body(environ)
        quote_id = int(payload["id"])
    except (KeyError, TypeError, ValueError) as exc:
        return _respond_json(start_response, 400, {"error": f"需要报价 id: {exc}"})
    conn = getattr(db, "conn", None)
    if conn is None:
        return _respond_json(start_response, 500, {"error": "数据库连接不可用"})
    try:
        conn.execute("DELETE FROM quote_price_rows WHERE id = ?", (quote_id,))
        if hasattr(conn, "commit"):
            conn.commit()
    except Exception:
        try:
            conn.execute("DELETE FROM quote_price_rows WHERE id = %s", (quote_id,))
            if hasattr(conn, "commit"):
                conn.commit()
        except Exception as exc:
            return _respond_json(start_response, 500, {"error": str(exc)})
    return _respond_json(start_response, 200, {"deleted": True, "id": quote_id})


def _handle_reconciliation_ledger(db: BookkeepingDB, start_response, environ):
    try:
        params = _read_query_params(environ)
        period_id = _parse_optional_int(params.get("period_id"))
        combination_id = _parse_optional_int(params.get("combination_id"))
        group_num = _parse_optional_int(params.get("group_num"))
        payload = ReconciliationService(db).build_ledger_payload(
            scope=params.get("scope", "realtime"),
            period_id=period_id,
            start_date=params.get("start_date"),
            end_date=params.get("end_date"),
            combination_id=combination_id,
            group_num=group_num,
            business_role=params.get("business_role", ""),
            group_key=params.get("group_key", ""),
            card_type=params.get("card_type", ""),
            edited=params.get("edited", "all"),
            issue_type=params.get("issue_type", ""),
        )
    except ValueError as exc:
        return _respond_json(start_response, 400, {"error": f"Bad query: {exc}"})
    return _respond_json(start_response, 200, payload)


def _handle_reconciliation_export(db: BookkeepingDB, start_response, environ):
    try:
        params = _read_query_params(environ)
        period_id = _parse_optional_int(params.get("period_id"))
        combination_id = _parse_optional_int(params.get("combination_id"))
        group_num = _parse_optional_int(params.get("group_num"))
        scope = params.get("scope", "realtime")
        export_mode = params.get("export_mode", "detail")
        csv_text = ReconciliationService(db).export_ledger_csv(
            scope=scope,
            period_id=period_id,
            start_date=params.get("start_date"),
            end_date=params.get("end_date"),
            combination_id=combination_id,
            group_num=group_num,
            business_role=params.get("business_role", ""),
            group_key=params.get("group_key", ""),
            card_type=params.get("card_type", ""),
            edited=params.get("edited", "all"),
            issue_type=params.get("issue_type", ""),
            export_mode=export_mode,
        )
    except ValueError as exc:
        return _respond_json(start_response, 400, {"error": f"Bad query: {exc}"})
    filename = f"reconciliation-{export_mode}-{scope}-{date.today().isoformat()}.csv"
    return _respond_csv(start_response, csv_text, filename=filename)


def _handle_accounting_periods(db: BookkeepingDB, start_response, environ=None):
    rows = [
        _row_to_dict(row)
        for row in sorted(
            db.list_accounting_periods(),
            key=lambda row: (str(row["closed_at"]), int(row["id"])),
            reverse=True,
        )
    ][:20]
    return _respond_json(start_response, 200, {"items": rows})


def _handle_accounting_period_close(db: BookkeepingDB, start_response, environ):
    try:
        payload = _read_json_body(environ)
        period_id = AccountingPeriodService(db).close_period(
            start_at=str(payload["start_at"]),
            end_at=str(payload["end_at"]),
            closed_by=str(payload["closed_by"]),
            note=str(payload["note"]) if payload.get("note") is not None else None,
        )
    except (KeyError, TypeError, ValueError) as exc:
        return _respond_json(start_response, 400, {"error": f"Bad payload: {exc}"})
    return _respond_json(start_response, 200, {"period_id": period_id})


def _handle_accounting_period_settle_all(
    runtime: UnifiedBookkeepingRuntime, start_response, environ
):
    try:
        _reset_runtime_db_session(runtime)
        payload = _read_json_body(environ)
        closed_by = str(payload["closed_by"]).strip()
        if not closed_by:
            raise ValueError("closed_by cannot be empty")
        _resolve_runtime_manager_id(runtime)
        result = AccountingPeriodService(runtime.service.db).settle_all_with_receipts(
            closed_by=closed_by,
            note="web:/alljs",
        )
        if result is None:
            return _respond_json(
                start_response,
                200,
                {
                    "closed": False,
                    "message": "当前没有可结账的实时交易",
                },
            )
        queued_action_count = runtime.service.db.enqueue_outbound_actions(
            result.get("receipt_actions", [])
        )
    except (KeyError, TypeError, ValueError) as exc:
        return _respond_json(start_response, 400, {"error": f"Bad payload: {exc}"})
    return _respond_json(
        start_response,
        200,
        {
            "closed": True,
            "period_id": int(result["period_id"]),
            "summary": result["summary"],
            "queued_action_count": queued_action_count,
        },
    )


def _handle_group_broadcast(
    runtime: UnifiedBookkeepingRuntime, start_response, environ
):
    try:
        _reset_runtime_db_session(runtime)
        payload = _read_json_body(environ)
        created_by = str(payload["created_by"]).strip()
        if not created_by:
            raise ValueError("created_by cannot be empty")
        message = str(payload["message"]).strip()
        if not message:
            raise ValueError("message cannot be empty")
        group_num = int(payload["group_num"])
        if group_num < 0 or group_num > 9:
            raise ValueError("group_num must be between 0 and 9")

        _resolve_runtime_manager_id(runtime)
        groups = runtime.service.db.get_groups_by_num(group_num)
        if not groups:
            return _respond_json(
                start_response, 400, {"error": f"Group {group_num} has no groups"}
            )

        actions = [
            {
                "action_type": "send_text",
                "chat_id": str(group["chat_id"]),
                "text": message,
            }
            for group in groups
            if str(group["chat_id"] or "").strip()
        ]
        if not actions:
            return _respond_json(
                start_response,
                400,
                {"error": f"Group {group_num} has no deliverable chats"},
            )

        queued_action_count = runtime.service.db.enqueue_outbound_actions(actions)
    except (KeyError, TypeError, ValueError) as exc:
        return _respond_json(start_response, 400, {"error": f"Bad payload: {exc}"})
    return _respond_json(
        start_response,
        200,
        {
            "group_num": group_num,
            "target_count": len(actions),
            "queued_action_count": queued_action_count,
        },
    )


def _handle_adjustments(db: BookkeepingDB, start_response, environ):
    try:
        payload = _read_json_body(environ)
        period_id = int(payload["period_id"])
        if period_id <= 0:
            raise ValueError("period_id must be a positive settlement period id")
        period_exists = any(
            int(row["id"]) == period_id for row in db.list_accounting_periods()
        )
        if not period_exists:
            raise ValueError(f"period_id not found: {period_id}")
        group_key = str(payload["group_key"])
        if db.get_group_by_key(group_key) is None:
            raise ValueError(f"group_key not found: {group_key}")
        adjustment_id = db.add_manual_adjustment(
            period_id=period_id,
            group_key=group_key,
            opening_delta=float(payload.get("opening_delta", 0)),
            income_delta=float(payload.get("income_delta", 0)),
            expense_delta=float(payload.get("expense_delta", 0)),
            closing_delta=float(payload.get("closing_delta", 0)),
            note=str(payload["note"]),
            created_by=str(payload["created_by"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        return _respond_json(start_response, 400, {"error": f"Bad payload: {exc}"})
    return _respond_json(start_response, 200, {"adjustment_id": adjustment_id})


def _handle_reconciliation_adjustments(db: BookkeepingDB, start_response, environ):
    try:
        payload = _read_json_body(environ)
        group_key = str(payload["group_key"]).strip()
        if not group_key:
            raise ValueError("group_key cannot be empty")
        group_row = db.get_group_by_key(group_key)
        if group_row is None:
            raise ValueError(f"group_key not found: {group_key}")
        created_by = str(payload["created_by"]).strip()
        note = str(payload["note"]).strip()
        card_type = str(payload["card_type"]).strip().lower()
        if not created_by:
            raise ValueError("created_by cannot be empty")
        if not note:
            raise ValueError("note cannot be empty")
        if not card_type:
            raise ValueError("card_type cannot be empty")

        period_id = _parse_optional_int(payload.get("period_id"))
        if period_id is not None:
            period_exists = any(
                int(row["id"]) == period_id for row in db.list_accounting_periods()
            )
            if not period_exists:
                raise ValueError(f"period_id not found: {period_id}")

        linked_transaction_id = _parse_optional_int(
            payload.get("linked_transaction_id")
        )
        if linked_transaction_id is not None:
            transaction = db.get_transaction_by_id(linked_transaction_id)
            if transaction is None:
                raise ValueError(
                    f"linked_transaction_id not found: {linked_transaction_id}"
                )

        adjustment_id = db.add_finance_adjustment_entry(
            period_id=period_id,
            linked_transaction_id=linked_transaction_id,
            group_key=group_key,
            business_role=str(
                payload.get("business_role") or group_row.get("business_role") or ""
            ).strip()
            or None,
            card_type=card_type,
            usd_amount=float(payload.get("usd_amount", 0) or 0),
            rate=None if payload.get("rate") in {None, ""} else float(payload["rate"]),
            rmb_amount=float(payload["rmb_amount"]),
            note=note,
            created_by=created_by,
        )
    except (KeyError, TypeError, ValueError) as exc:
        return _respond_json(start_response, 400, {"error": f"Bad payload: {exc}"})
    return _respond_json(start_response, 200, {"adjustment_id": adjustment_id})


def _handle_transaction_update(db: BookkeepingDB, start_response, environ):
    try:
        payload = _read_json_body(environ)
        transaction_id = int(payload["transaction_id"])
        transaction = db.get_transaction_by_id(transaction_id)
        if transaction is None:
            raise ValueError(f"transaction not found: {transaction_id}")
        if int(transaction["deleted"] or 0) != 0:
            raise ValueError("cannot edit a deleted transaction")
        if int(transaction["settled"] or 0) != 0:
            raise ValueError("cannot edit a settled transaction")

        sender_name = str(payload["sender_name"]).strip()
        category = str(payload["category"]).strip()
        edited_by = str(payload["edited_by"]).strip()
        if not sender_name:
            raise ValueError("sender_name cannot be empty")
        if not category:
            raise ValueError("category cannot be empty")
        if not edited_by:
            raise ValueError("edited_by cannot be empty")

        amount = float(payload["amount"])
        rmb_value = float(payload["rmb_value"])
        rate_value = payload.get("rate")
        usd_amount_value = payload.get("usd_amount")
        rate = None if rate_value in {None, ""} else float(rate_value)
        usd_amount = None if usd_amount_value in {None, ""} else float(usd_amount_value)

        before_payload = {
            "sender_name": _normalize_json_value(transaction["sender_name"]),
            "amount": _normalize_json_value(transaction["amount"]),
            "category": _normalize_json_value(transaction["category"]),
            "rate": _normalize_json_value(transaction["rate"]),
            "rmb_value": _normalize_json_value(transaction["rmb_value"]),
            "usd_amount": _normalize_json_value(transaction["usd_amount"]),
        }
        after_payload = {
            "sender_name": sender_name,
            "amount": amount,
            "category": category,
            "rate": rate,
            "rmb_value": rmb_value,
            "usd_amount": usd_amount,
        }

        db.conn.execute("BEGIN")
        try:
            updated = db.update_transaction_fields(
                transaction_id=transaction_id,
                sender_name=sender_name,
                amount=amount,
                category=category,
                rate=rate,
                rmb_value=rmb_value,
                usd_amount=usd_amount,
                commit=False,
            )
            if updated != 1:
                raise RuntimeError("transaction update affected unexpected rows")
            db.add_transaction_edit_log(
                transaction_id=transaction_id,
                edited_by=edited_by,
                note=str(payload.get("note") or ""),
                before_json=json.dumps(
                    before_payload, ensure_ascii=False, sort_keys=True
                ),
                after_json=json.dumps(
                    after_payload, ensure_ascii=False, sort_keys=True
                ),
                commit=False,
            )
            db.conn.commit()
        except Exception:
            db.conn.rollback()
            raise
    except (KeyError, TypeError, ValueError, RuntimeError) as exc:
        return _respond_json(start_response, 400, {"error": f"Bad payload: {exc}"})
    return _respond_json(start_response, 200, {"transaction_id": transaction_id})


def _handle_group_combinations(db: BookkeepingDB, start_response, environ):
    method = environ.get("REQUEST_METHOD", "GET").upper()
    if method == "GET":
        payload = ReportingService(db).list_combination_summaries()
        return _respond_json(start_response, 200, payload)

    try:
        payload = _read_json_body(environ)
        raw_numbers = payload.get("group_numbers", [])
        if isinstance(raw_numbers, str):
            numbers = [int(item) for item in raw_numbers.split(",") if item.strip()]
        else:
            numbers = [int(item) for item in raw_numbers]
        combination_id = db.save_group_combination(
            name=str(payload["name"]),
            group_numbers=numbers,
            note=str(payload.get("note", "")),
            created_by=str(payload.get("created_by", "web")),
        )
    except (KeyError, TypeError, ValueError) as exc:
        return _respond_json(start_response, 400, {"error": f"Bad payload: {exc}"})
    return _respond_json(start_response, 200, {"combination_id": combination_id})


def _handle_core_messages(runtime: UnifiedBookkeepingRuntime, start_response, environ):
    payload = None
    try:
        _reset_runtime_db_session(runtime)
        payload = _read_json_body(environ)
        if not isinstance(payload, dict):
            raise ValueError("payload must be a JSON object")
        _validate_runtime_message_payload(payload)
        actions = [
            core_action_to_dict(action) for action in runtime.process_envelope(payload)
        ]
    except (TypeError, ValueError, KeyError) as exc:
        logger.warning(
            "Rejected core runtime payload: %s | payload=%s",
            exc,
            _summarize_runtime_payload(payload),
        )
        return _respond_json(start_response, 400, {"error": f"Bad payload: {exc}"})
    return _respond_json(start_response, 200, {"actions": actions})


def _handle_incoming_messages(db: BookkeepingDB, start_response, environ):
    params = _read_query_params(environ)
    try:
        limit = int(params.get("limit", "50")) if params.get("limit") else 50
        offset = int(params.get("offset", "0")) if params.get("offset") else 0
        platform = params.get("platform") or None
        chat_id = params.get("chat_id") or None
        message_id = params.get("message_id") or None
        if limit < 1 or limit > 500:
            return _respond_json(start_response, 400, {"error": "limit must be 1-500"})
        if offset < 0:
            return _respond_json(start_response, 400, {"error": "offset must be >= 0"})
    except ValueError as exc:
        return _respond_json(start_response, 400, {"error": f"Bad query: {exc}"})
    rows, total = db.query_incoming_messages(
        platform=platform,
        chat_id=chat_id,
        message_id=message_id,
        limit=limit,
        offset=offset,
    )
    messages = [_serialize_incoming_message_row(row) for row in rows]
    return _respond_json(
        start_response,
        200,
        {
            "messages": messages,
            "total": total,
            "limit": limit,
            "offset": offset,
        },
    )


def _serialize_incoming_message_row(row) -> dict[str, object]:
    return {
        "id": int(row["id"]),
        "platform": str(row["platform"] or ""),
        "chat_id": str(row["chat_id"] or ""),
        "chat_name": str(row["chat_name"] or ""),
        "message_id": str(row["message_id"] or ""),
        "sender_id": str(row["sender_id"] or ""),
        "sender_name": str(row["sender_name"] or ""),
        "sender_kind": str(row["sender_kind"] or ""),
        "content_type": str(row["content_type"] or ""),
        "text": str(row["text"] or ""),
        "from_self": bool(row["from_self"]),
        "received_at": str(row["received_at"] or ""),
        "raw_json": str(row["raw_json"] or ""),
        "created_at": str(row["created_at"] or ""),
    }


def _handle_incoming_messages_with_transactions(
    db: BookkeepingDB, start_response, environ
):
    params = _read_query_params(environ)
    try:
        limit = int(params.get("limit", "50")) if params.get("limit") else 50
        offset = int(params.get("offset", "0")) if params.get("offset") else 0
        platform = params.get("platform") or None
        chat_id = params.get("chat_id") or None
        if limit < 1 or limit > 500:
            return _respond_json(start_response, 400, {"error": "limit must be 1-500"})
        if offset < 0:
            return _respond_json(start_response, 400, {"error": "offset must be >= 0"})
    except ValueError as exc:
        return _respond_json(start_response, 400, {"error": f"Bad query: {exc}"})
    messages, total = db.get_incoming_messages_with_transactions(
        platform=platform,
        chat_id=chat_id,
        limit=limit,
        offset=offset,
    )
    return _respond_json(
        start_response,
        200,
        {
            "messages": messages,
            "total": total,
            "limit": limit,
            "offset": offset,
        },
    )


def _handle_core_actions(runtime: UnifiedBookkeepingRuntime, start_response):
    _reset_runtime_db_session(runtime)
    db_actions = [
        _serialize_outbound_action_row(action)
        for action in runtime.service.db.claim_outbound_actions()
    ]
    runtime_actions = [
        core_action_to_dict(action) for action in runtime.drain_outbound_actions()
    ]
    actions = db_actions + runtime_actions
    return _respond_json(
        start_response,
        200,
        {"actions": actions},
        extra_headers=[("X-Outbound-Action-Count", str(len(actions)))],
    )


def _handle_core_actions_ack(
    runtime: UnifiedBookkeepingRuntime, start_response, environ
):
    try:
        _reset_runtime_db_session(runtime)
        payload = _read_json_body(environ)
        items = payload.get("items", [])
        if not isinstance(items, list):
            raise ValueError("items must be a list")
        updated = runtime.service.db.acknowledge_outbound_actions(items)
    except (TypeError, ValueError, KeyError) as exc:
        return _respond_json(start_response, 400, {"error": f"Bad payload: {exc}"})
    return _respond_json(start_response, 200, {"updated": updated})


def _handle_parse_results(db: BookkeepingDB, start_response, environ):
    params = _read_query_params(environ)
    try:
        limit = int(params.get("limit", "50")) if params.get("limit") else 50
        offset = int(params.get("offset", "0")) if params.get("offset") else 0
        platform = params.get("platform") or None
        chat_id = params.get("chat_id") or None
        classification = params.get("classification") or None
        parse_status = params.get("parse_status") or None
        if limit < 1 or limit > 500:
            return _respond_json(start_response, 400, {"error": "limit must be 1-500"})
        if offset < 0:
            return _respond_json(start_response, 400, {"error": "offset must be >= 0"})
    except ValueError as exc:
        return _respond_json(start_response, 400, {"error": f"Bad query: {exc}"})
    rows, total = db.query_parse_results(
        platform=platform,
        chat_id=chat_id,
        classification=classification,
        parse_status=parse_status,
        limit=limit,
        offset=offset,
    )
    results = [
        {
            "id": int(row["id"]),
            "platform": str(row["platform"] or ""),
            "chat_id": str(row["chat_id"] or ""),
            "message_id": str(row["message_id"] or ""),
            "classification": str(row["classification"] or ""),
            "parse_status": str(row["parse_status"] or ""),
            "raw_text": str(row["raw_text"] or "") if row["raw_text"] else None,
            "created_at": str(row["created_at"] or ""),
        }
        for row in rows
    ]
    return _respond_json(
        start_response,
        200,
        {
            "results": results,
            "total": total,
            "limit": limit,
            "offset": offset,
        },
    )


def _handle_message_inspector(db: BookkeepingDB, start_response, environ):
    params = _read_query_params(environ)
    platform = params.get("platform")
    chat_id = params.get("chat_id")
    message_id = params.get("message_id")
    if not platform or not chat_id or not message_id:
        return _respond_json(
            start_response,
            400,
            {"error": "platform, chat_id, message_id are required"},
        )
    result = db.get_message_triple(
        platform=platform, chat_id=chat_id, message_id=message_id
    )
    if result is None:
        return _respond_json(start_response, 404, {"error": "message not found"})
    return _respond_json(start_response, 200, result)


def _call_optional_db_method(db: BookkeepingDB, method_name: str, default, **kwargs):
    method = getattr(db, method_name, None)
    if not callable(method):
        return default
    call_kwargs = _filter_callable_kwargs(method, kwargs)
    return method(**call_kwargs)


def _filter_callable_kwargs(method, kwargs: dict[str, object]) -> dict[str, object]:
    try:
        signature = inspect.signature(method)
    except (TypeError, ValueError):
        return kwargs
    params = signature.parameters
    if any(param.kind == inspect.Parameter.VAR_KEYWORD for param in params.values()):
        return kwargs
    allowed = {
        name
        for name, param in params.items()
        if param.kind in {inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY}
    }
    return {key: value for key, value in kwargs.items() if key in allowed}


def _normalize_quote_payload(payload) -> dict:
    if isinstance(payload, dict):
        normalized = dict(payload)
        rows = normalized.get("rows")
        if rows is None and "items" in normalized:
            normalized["rows"] = normalized.get("items") or []
        if "total" not in normalized:
            row_count = normalized.get("rows")
            if isinstance(row_count, list):
                normalized["total"] = len(row_count)
            else:
                normalized["total"] = 0
        if not isinstance(normalized.get("rows"), list):
            normalized["rows"] = []
        return normalized
    if isinstance(payload, tuple) and payload:
        rows = payload[0]
        total = payload[1] if len(payload) > 1 else None
        if not isinstance(rows, list):
            rows = list(rows or [])
        return {
            "rows": rows,
            "total": int(total) if total is not None else len(rows),
        }
    if isinstance(payload, list):
        return {"rows": payload, "total": len(payload)}
    return {"rows": [], "total": 0}


def _handle_difference_trace(db: BookkeepingDB, start_response, environ):
    from bookkeeping_core.reconciliation import (
        ISSUE_EDITED_UNREVIEWED,
        ISSUE_MISSING_RATE,
        ISSUE_PENDING_RECONCILIATION,
        ISSUE_RATE_FORMULA_ERROR,
        ReconciliationService,
    )

    params = _read_query_params(environ)
    transaction_id = params.get("transaction_id")
    if not transaction_id:
        return _respond_json(
            start_response, 400, {"error": "transaction_id is required"}
        )
    try:
        transaction_id = int(transaction_id)
    except ValueError:
        return _respond_json(
            start_response, 400, {"error": "transaction_id must be an integer"}
        )

    transaction = db.get_transaction_by_id(transaction_id)
    if transaction is None:
        return _respond_json(start_response, 404, {"error": "transaction not found"})

    result = {
        "transaction": _serialize_transaction_row(transaction),
        "message": None,
        "parse_result": None,
        "issue_flags": [],
        "latest_edit": None,
        "trace_status": {
            "captured": bool(transaction.get("message_id")),
            "parsed": False,
            "posted": False,
            "edited": False,
            "flagged": False,
        },
    }

    if transaction.get("message_id"):
        message_row = db.get_incoming_message(
            platform=transaction["platform"],
            chat_id=transaction["chat_id"],
            message_id=transaction["message_id"],
        )
        if message_row:
            result["message"] = {
                "id": int(message_row["id"]),
                "platform": str(message_row["platform"] or ""),
                "chat_id": str(message_row["chat_id"] or ""),
                "chat_name": str(message_row["chat_name"] or ""),
                "message_id": str(message_row["message_id"] or ""),
                "sender_id": str(message_row["sender_id"] or ""),
                "sender_name": str(message_row["sender_name"] or ""),
                "sender_kind": str(message_row["sender_kind"] or ""),
                "content_type": str(message_row["content_type"] or ""),
                "text": str(message_row["text"] or ""),
                "from_self": bool(message_row["from_self"]),
                "received_at": str(message_row["received_at"] or ""),
                "created_at": str(message_row["created_at"] or ""),
            }
            parse_row = db.conn.execute(
                """
                SELECT classification, parse_status, raw_text
                FROM message_parse_results
                WHERE platform = ? AND chat_id = ? AND message_id = ?
                """,
                (
                    transaction["platform"],
                    transaction["chat_id"],
                    transaction["message_id"],
                ),
            ).fetchone()
            if parse_row and parse_row["classification"]:
                result["parse_result"] = {
                    "classification": str(parse_row["classification"]),
                    "parse_status": str(parse_row["parse_status"]),
                    "raw_text": str(parse_row["raw_text"] or "")
                    if parse_row["raw_text"]
                    else None,
                }
                result["trace_status"]["parsed"] = True

    service = ReconciliationService(db)
    category = str(transaction.get("category") or "")
    rate = transaction.get("rate")
    rmb_value = float(transaction["rmb_value"]) if transaction.get("rmb_value") else 0
    business_role = transaction.get("business_role")
    is_edited = False
    latest_edit_log = db.get_latest_edit_log(transaction_id)
    if latest_edit_log:
        is_edited = True
        result["latest_edit"] = {
            "edited_by": str(latest_edit_log["edited_by"]),
            "edited_at": str(latest_edit_log["edited_at"]),
            "note": str(latest_edit_log["note"] or ""),
        }
        result["trace_status"]["edited"] = True

    issue_flags = service._build_transaction_issue_flags(
        business_role=business_role,
        category=category,
        rate=rate,
        expected_rmb_value=None,
        rmb_value=rmb_value,
        is_edited=is_edited,
    )
    result["issue_flags"] = issue_flags
    if issue_flags:
        result["trace_status"]["flagged"] = True

    result["trace_status"]["posted"] = True

    return _respond_json(start_response, 200, result)


def _serialize_transaction_row(row) -> dict:
    return {
        "id": int(row["id"]),
        "platform": str(row["platform"] or ""),
        "group_key": str(row["group_key"] or ""),
        "chat_id": str(row["chat_id"] or ""),
        "chat_name": str(row["chat_name"] or ""),
        "sender_id": str(row["sender_id"] or ""),
        "sender_name": str(row["sender_name"] or ""),
        "message_id": str(row["message_id"] or "") if row["message_id"] else None,
        "input_sign": int(row["input_sign"]),
        "amount": str(row["amount"] or ""),
        "category": str(row["category"] or ""),
        "rate": float(row["rate"]) if row["rate"] is not None else None,
        "rmb_value": float(row["rmb_value"]) if row["rmb_value"] else 0,
        "usd_amount": float(row["usd_amount"])
        if row["usd_amount"] is not None
        else None,
        "raw": str(row["raw"] or ""),
        "parse_version": str(row["parse_version"] or ""),
        "deleted": bool(row["deleted"]),
        "settled": bool(row["settled"]),
        "settled_at": str(row["settled_at"] or "") if row["settled_at"] else None,
        "created_at": str(row["created_at"] or ""),
        "business_role": str(row["business_role"] or "")
        if row.get("business_role")
        else None,
        "group_num": int(row["mapped_group_num"])
        if row.get("mapped_group_num") is not None
        else None,
    }


def _read_json_body(environ) -> dict:
    length = int(environ.get("CONTENT_LENGTH") or "0")
    raw = environ["wsgi.input"].read(length) if length > 0 else b"{}"
    if not raw:
        return {}
    return json.loads(raw.decode("utf-8"))


def _reset_runtime_db_session(runtime: UnifiedBookkeepingRuntime) -> None:
    runtime.service.db.conn.rollback()


def _resolve_runtime_manager_id(runtime: UnifiedBookkeepingRuntime) -> str:
    commands = runtime.service.commands
    bootstrap_ids = sorted(
        str(user).strip() for user in commands.bootstrap_masters if str(user).strip()
    )
    if bootstrap_ids:
        return bootstrap_ids[0]
    for row in runtime.service.db.get_admins():
        user_key = str(row.get("user_key") or "").strip()
        if user_key:
            return user_key
    raise ValueError("core runtime has no configured admin user")


def _serialize_outbound_action_row(row) -> dict[str, object]:
    action_type = str(row.get("action_type") or "").strip()
    payload: dict[str, object] = {
        "id": int(row["id"]),
        "action_type": action_type,
        "chat_id": str(row.get("chat_id") or ""),
    }
    if action_type == "send_text":
        payload["text"] = str(row.get("text") or "")
        return payload
    if action_type == "send_file":
        payload["file_path"] = str(row.get("file_path") or "")
        caption = row.get("caption")
        if caption:
            payload["caption"] = str(caption)
        return payload
    raise ValueError(f"Unsupported outbound action type: {action_type}")


def _read_query_params(environ) -> dict[str, str]:
    return {
        key: values[-1]
        for key, values in parse_qs(
            str(environ.get("QUERY_STRING") or ""), keep_blank_values=True
        ).items()
    }


def _respond_json(
    start_response,
    status_code: int,
    payload: dict | list,
    extra_headers: list[tuple[str, str]] | None = None,
):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = [
        ("Content-Type", "application/json; charset=utf-8"),
        ("Content-Length", str(len(body))),
    ]
    if extra_headers:
        headers.extend(extra_headers)
    start_response(f"{status_code} {'OK' if status_code < 400 else 'ERROR'}", headers)
    return [body]


def _respond_html(start_response, html: str):
    body = html.encode("utf-8")
    start_response(
        "200 OK",
        [
            ("Content-Type", "text/html; charset=utf-8"),
            ("Content-Length", str(len(body))),
        ],
    )
    return [body]


def _respond_csv(start_response, text: str, *, filename: str):
    body = text.encode("utf-8-sig")
    start_response(
        "200 OK",
        [
            ("Content-Type", "text/csv; charset=utf-8"),
            ("Content-Disposition", f'attachment; filename="{filename}"'),
            ("Content-Length", str(len(body))),
        ],
    )
    return [body]


def _is_authorized(environ, core_token: str | None) -> bool:
    if not core_token:
        return False
    header = str(environ.get("HTTP_AUTHORIZATION") or "").strip()
    return header == f"Bearer {core_token}"


def _validate_runtime_message_payload(payload: dict) -> None:
    if "is_group" not in payload or not isinstance(payload["is_group"], bool):
        raise ValueError("is_group must be a boolean")
    if "from_self" in payload and not isinstance(payload["from_self"], bool):
        raise ValueError("from_self must be a boolean")


def _runtime_export_dir(db_target: str | Path) -> Path:
    if isinstance(db_target, Path):
        return db_target.parent / "exports"
    if "://" in str(db_target):
        return Path("exports")
    return Path(str(db_target)).expanduser().resolve().parent / "exports"


def _normalize_runtime_master_users(values: list[str] | None) -> list[str]:
    if not values:
        return []
    result: list[str] = []
    for value in values:
        text = str(value).strip()
        if text and text not in result:
            result.append(text)
    return result


def _summarize_runtime_payload(payload) -> dict | str | None:
    if not isinstance(payload, dict):
        return payload
    keys = (
        "platform",
        "message_id",
        "chat_id",
        "chat_name",
        "is_group",
        "sender_id",
        "sender_name",
        "sender_kind",
        "content_type",
        "text",
        "from_self",
        "received_at",
    )
    return {key: payload.get(key) for key in keys if key in payload}


def _row_to_dict(row) -> dict:
    if hasattr(row, "keys"):
        return {key: _normalize_json_value(row[key]) for key in row.keys()}
    return {key: _normalize_json_value(value) for key, value in dict(row).items()}


def _parse_optional_int(value) -> int | None:
    if value in {None, ""}:
        return None
    return int(value)


def _normalize_json_value(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (datetime, date)):
        return value.isoformat(sep=" ")
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if hasattr(value, "__float__"):
        try:
            return float(value)
        except (TypeError, ValueError):
            pass
    return str(value)
