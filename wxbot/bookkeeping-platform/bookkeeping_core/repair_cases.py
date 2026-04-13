from __future__ import annotations

import hashlib
import json
from typing import Any


REPAIR_CASE_STATE_DETECTED = "detected"
REPAIR_CASE_STATE_PACKAGED = "packaged"
REPAIR_CASE_STATE_BASELINE_READY = "baseline_ready"
REPAIR_CASE_STATE_READY_FOR_ATTEMPT = "ready_for_attempt"
REPAIR_CASE_STATE_ATTEMPT_FAILED = "attempt_failed"
REPAIR_CASE_STATE_ATTEMPT_SUCCEEDED = "attempt_succeeded"
REPAIR_CASE_STATE_ESCALATED = "escalated"
REPAIR_CASE_STATE_CLOSED_RESOLVED = "closed_resolved"
REPAIR_CASE_STATE_CLOSED_IGNORED = "closed_ignored"


def package_quote_repair_case(*, db, exception_id: int) -> dict[str, Any]:
    existing = db.get_quote_repair_case_by_origin_exception(
        origin_exception_id=exception_id
    )
    if existing is not None:
        return existing

    exception = db.get_quote_exception(exception_id=exception_id)
    if exception is None:
        raise ValueError(f"quote repair case requires existing exception_id={exception_id}")

    quote_document_id = int(exception["quote_document_id"])
    quote_document = db.get_quote_document(quote_document_id=quote_document_id)
    if quote_document is None:
        raise ValueError(
            f"quote repair case requires existing quote_document_id={quote_document_id}"
        )

    validation_run = db.get_latest_quote_validation_run(quote_document_id=quote_document_id)
    group_profile = db.get_quote_group_profile(
        platform=str(exception["platform"]),
        chat_id=str(exception["chat_id"]),
    )
    profile_snapshot = _build_group_profile_snapshot(group_profile)
    validation_summary = _decode_json_field(
        validation_run.get("summary_json") if validation_run else None,
        fallback={},
    )
    case_summary = {
        "quote_document_parse_status": str(quote_document.get("parse_status") or ""),
        "quote_document_run_kind": str(quote_document.get("run_kind") or ""),
        "quote_document_message_id": str(quote_document.get("message_id") or ""),
        "validator_message_decision": str(
            (validation_run or {}).get("message_decision") or ""
        ),
        "validator_run_kind": str((validation_run or {}).get("run_kind") or ""),
    }

    return db.create_or_get_quote_repair_case(
        origin_exception_id=exception_id,
        origin_quote_document_id=quote_document_id,
        origin_validation_run_id=int(validation_run["id"]) if validation_run else None,
        platform=str(exception["platform"]),
        source_group_key=str(exception["source_group_key"]),
        chat_id=str(exception["chat_id"]),
        chat_name=str(exception["chat_name"]),
        group_profile_id=int(group_profile["id"]) if group_profile else None,
        lifecycle_state=REPAIR_CASE_STATE_PACKAGED,
        current_failure_reason=str(exception["reason"]),
        parser_template_snapshot=str(exception.get("parser_template") or ""),
        parser_version_snapshot=str(exception.get("parser_version") or ""),
        message_time_snapshot=str(exception.get("message_time") or ""),
        raw_message_snapshot=str(exception.get("raw_text") or ""),
        source_line_snapshot=str(exception.get("source_line") or ""),
        profile_snapshot=profile_snapshot,
        validation_summary=validation_summary,
        case_summary=case_summary,
        case_fingerprint=build_quote_repair_case_fingerprint(
            source_group_key=str(exception["source_group_key"]),
            current_failure_reason=str(exception["reason"]),
            raw_message_snapshot=str(exception.get("raw_text") or ""),
            source_line_snapshot=str(exception.get("source_line") or ""),
        ),
    )


def build_quote_repair_case_fingerprint(
    *,
    source_group_key: str,
    current_failure_reason: str,
    raw_message_snapshot: str,
    source_line_snapshot: str,
) -> str:
    payload = "\x1f".join(
        [
            str(source_group_key or "").strip(),
            str(current_failure_reason or "").strip(),
            str(source_line_snapshot or "").strip(),
            str(raw_message_snapshot or "").strip(),
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _build_group_profile_snapshot(group_profile: dict[str, Any] | None) -> dict[str, Any]:
    if not group_profile:
        return {}
    return {
        "id": int(group_profile["id"]),
        "platform": str(group_profile.get("platform") or ""),
        "chat_id": str(group_profile.get("chat_id") or ""),
        "chat_name": str(group_profile.get("chat_name") or ""),
        "default_card_type": str(group_profile.get("default_card_type") or ""),
        "default_country_or_currency": str(
            group_profile.get("default_country_or_currency") or ""
        ),
        "default_form_factor": str(group_profile.get("default_form_factor") or ""),
        "default_multiplier": str(group_profile.get("default_multiplier") or ""),
        "parser_template": str(group_profile.get("parser_template") or ""),
        "stale_after_minutes": int(group_profile.get("stale_after_minutes") or 0),
        "note": str(group_profile.get("note") or ""),
        "template_config": _decode_json_field(
            group_profile.get("template_config"),
            fallback={"raw": str(group_profile.get("template_config") or "")},
        ),
        "updated_at": str(group_profile.get("updated_at") or ""),
    }


def _decode_json_field(value: Any, *, fallback: Any) -> Any:
    if value in (None, ""):
        return fallback
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return fallback
