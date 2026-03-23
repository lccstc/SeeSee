from __future__ import annotations

import json
import logging
from datetime import date, datetime
from pathlib import Path
from urllib.parse import parse_qs

from bookkeeping_core.analytics import AnalyticsService
from bookkeeping_core.contracts import core_action_to_dict
from bookkeeping_core.database import BookkeepingDB, require_postgres_dsn
from bookkeeping_core.periods import AccountingPeriodService
from bookkeeping_core.reporting import ReportingService
from bookkeeping_core.runtime import UnifiedBookkeepingRuntime
from bookkeeping_web.pages import (
    render_dashboard_page,
    render_history_page,
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

    def app(environ, start_response):
        method = environ.get("REQUEST_METHOD", "GET").upper()
        path = environ.get("PATH_INFO", "/")
        if path == "/":
            return _respond_html(start_response, render_dashboard_page())
        if path == "/workbench":
            return _respond_html(start_response, render_workbench_page())
        if path == "/role-mapping":
            return _respond_html(start_response, render_role_mapping_page())
        if path == "/history":
            return _respond_html(start_response, render_history_page())
        if path == "/api/dashboard" and method == "GET":
            return _with_db(db_file, start_response, _handle_dashboard, environ)
        if path == "/api/workbench" and method == "GET":
            return _with_db(db_file, start_response, _handle_workbench, environ)
        if path == "/api/role-mapping" and method == "GET":
            return _with_db(db_file, start_response, _handle_role_mapping, environ)
        if path == "/api/role-mapping/group-num" and method == "POST":
            return _with_db(db_file, start_response, _handle_role_mapping_group_num, environ)
        if path == "/api/history" and method == "GET":
            return _with_db(db_file, start_response, _handle_history, environ)
        if path == "/api/accounting-periods" and method == "GET":
            return _with_db(db_file, start_response, _handle_accounting_periods)
        if path == "/api/accounting-periods/close" and method == "POST":
            return _with_db(db_file, start_response, _handle_accounting_period_close, environ)
        if path == "/api/accounting-periods/settle-all" and method == "POST":
            return _handle_accounting_period_settle_all(get_runtime(), start_response, environ)
        if path == "/api/group-broadcasts" and method == "POST":
            return _handle_group_broadcast(get_runtime(), start_response, environ)
        if path == "/api/adjustments" and method == "POST":
            return _with_db(db_file, start_response, _handle_adjustments, environ)
        if path == "/api/transactions/update" and method == "POST":
            return _with_db(db_file, start_response, _handle_transaction_update, environ)
        if path == "/api/group-combinations":
            return _with_db(db_file, start_response, _handle_group_combinations, environ)
        if path == "/api/core/messages" and method == "POST":
            if not _is_authorized(environ, core_token):
                return _respond_json(start_response, 401, {"error": "Unauthorized"})
            return _handle_core_messages(get_runtime(), start_response, environ)
        if path == "/api/core/actions" and method == "POST":
            if not _is_authorized(environ, core_token):
                return _respond_json(start_response, 401, {"error": "Unauthorized"})
            return _handle_core_actions(get_runtime(), start_response)
        if path == "/api/core/actions/ack" and method == "POST":
            if not _is_authorized(environ, core_token):
                return _respond_json(start_response, 401, {"error": "Unauthorized"})
            return _handle_core_actions_ack(get_runtime(), start_response, environ)
        return _respond_json(start_response, 404, {"error": f"Unknown path: {path}"})

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
    payload = AnalyticsService(db).build_period_workbench(period_id=period_id, use_live_period=use_live_period)
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
        return _respond_json(start_response, 404, {"error": f"group not found: {group_key}"})

    ok = db.set_group(
        platform=str(group_row["platform"] or ""),
        group_key=group_key,
        chat_id=str(group_row["chat_id"] or ""),
        chat_name=str(group_row["chat_name"] or ""),
        group_num=group_num,
    )
    if not ok:
        return _respond_json(start_response, 400, {"error": "group_num must be between 0 and 9"})
    return _respond_json(start_response, 200, {"group_key": group_key, "group_num": group_num})


def _handle_history(db: BookkeepingDB, start_response, environ):
    params = _read_query_params(environ)
    start_date_value = params.get("start_date") or date.today().replace(day=1).isoformat()
    end_date_value = params.get("end_date") or date.today().isoformat()
    payload = AnalyticsService(db).build_history_analysis(
        start_date=start_date_value,
        end_date=end_date_value,
        card_keyword=params.get("card_keyword", ""),
        sort_by=params.get("sort_by", "profit"),
    )
    return _respond_json(start_response, 200, payload)


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


def _handle_accounting_period_settle_all(runtime: UnifiedBookkeepingRuntime, start_response, environ):
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
        queued_action_count = runtime.service.db.enqueue_outbound_actions(result.get("receipt_actions", []))
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


def _handle_group_broadcast(runtime: UnifiedBookkeepingRuntime, start_response, environ):
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
            return _respond_json(start_response, 400, {"error": f"Group {group_num} has no groups"})

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
            return _respond_json(start_response, 400, {"error": f"Group {group_num} has no deliverable chats"})

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
        period_exists = any(int(row["id"]) == period_id for row in db.list_accounting_periods())
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
                before_json=json.dumps(before_payload, ensure_ascii=False, sort_keys=True),
                after_json=json.dumps(after_payload, ensure_ascii=False, sort_keys=True),
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
        actions = [core_action_to_dict(action) for action in runtime.process_envelope(payload)]
    except (TypeError, ValueError, KeyError) as exc:
        logger.warning(
            "Rejected core runtime payload: %s | payload=%s",
            exc,
            _summarize_runtime_payload(payload),
        )
        return _respond_json(start_response, 400, {"error": f"Bad payload: {exc}"})
    return _respond_json(start_response, 200, {"actions": actions})


def _handle_core_actions(runtime: UnifiedBookkeepingRuntime, start_response):
    _reset_runtime_db_session(runtime)
    db_actions = [_serialize_outbound_action_row(action) for action in runtime.service.db.claim_outbound_actions()]
    runtime_actions = [core_action_to_dict(action) for action in runtime.drain_outbound_actions()]
    actions = db_actions + runtime_actions
    return _respond_json(
        start_response,
        200,
        {"actions": actions},
        extra_headers=[("X-Outbound-Action-Count", str(len(actions)))],
    )


def _handle_core_actions_ack(runtime: UnifiedBookkeepingRuntime, start_response, environ):
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
    bootstrap_ids = sorted(str(user).strip() for user in commands.bootstrap_masters if str(user).strip())
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
        for key, values in parse_qs(str(environ.get("QUERY_STRING") or ""), keep_blank_values=True).items()
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
