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

REPAIR_ATTEMPT_KIND_BASELINE = "baseline"
REPAIR_ATTEMPT_KIND_REPAIR = "repair"
REPAIR_ATTEMPT_OUTCOME_COMPLETED = "completed"
REPAIR_ATTEMPT_OUTCOME_BLOCKED = "blocked"

_REPAIR_CASE_ALLOWED_TRANSITIONS = {
    REPAIR_CASE_STATE_DETECTED: {
        REPAIR_CASE_STATE_PACKAGED,
        REPAIR_CASE_STATE_CLOSED_IGNORED,
    },
    REPAIR_CASE_STATE_PACKAGED: {
        REPAIR_CASE_STATE_BASELINE_READY,
        REPAIR_CASE_STATE_READY_FOR_ATTEMPT,
        REPAIR_CASE_STATE_CLOSED_RESOLVED,
        REPAIR_CASE_STATE_CLOSED_IGNORED,
    },
    REPAIR_CASE_STATE_BASELINE_READY: {
        REPAIR_CASE_STATE_READY_FOR_ATTEMPT,
        REPAIR_CASE_STATE_ESCALATED,
        REPAIR_CASE_STATE_CLOSED_RESOLVED,
        REPAIR_CASE_STATE_CLOSED_IGNORED,
    },
    REPAIR_CASE_STATE_READY_FOR_ATTEMPT: {
        REPAIR_CASE_STATE_ATTEMPT_FAILED,
        REPAIR_CASE_STATE_ATTEMPT_SUCCEEDED,
        REPAIR_CASE_STATE_ESCALATED,
        REPAIR_CASE_STATE_CLOSED_IGNORED,
        REPAIR_CASE_STATE_CLOSED_RESOLVED,
    },
    REPAIR_CASE_STATE_ATTEMPT_FAILED: {
        REPAIR_CASE_STATE_READY_FOR_ATTEMPT,
        REPAIR_CASE_STATE_ESCALATED,
        REPAIR_CASE_STATE_CLOSED_IGNORED,
        REPAIR_CASE_STATE_CLOSED_RESOLVED,
    },
    REPAIR_CASE_STATE_ATTEMPT_SUCCEEDED: {
        REPAIR_CASE_STATE_CLOSED_RESOLVED,
    },
    REPAIR_CASE_STATE_ESCALATED: {
        REPAIR_CASE_STATE_READY_FOR_ATTEMPT,
        REPAIR_CASE_STATE_CLOSED_RESOLVED,
        REPAIR_CASE_STATE_CLOSED_IGNORED,
    },
    REPAIR_CASE_STATE_CLOSED_RESOLVED: {
        REPAIR_CASE_STATE_READY_FOR_ATTEMPT,
    },
    REPAIR_CASE_STATE_CLOSED_IGNORED: {
        REPAIR_CASE_STATE_READY_FOR_ATTEMPT,
    },
}


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


def create_baseline_repair_attempt(
    *,
    db,
    repair_case_id: int,
    replay_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    repair_case = db.get_quote_repair_case(repair_case_id=repair_case_id)
    if repair_case is None:
        raise ValueError(f"quote repair case requires existing repair_case_id={repair_case_id}")

    existing_baseline_attempt_id = repair_case.get("baseline_attempt_id")
    if existing_baseline_attempt_id is not None:
        existing_attempt = db.get_quote_repair_case_attempt(
            attempt_id=int(existing_baseline_attempt_id)
        )
        if existing_attempt is not None:
            return existing_attempt

    existing_attempt = db.get_quote_repair_case_attempt_by_number(
        repair_case_id=repair_case_id,
        attempt_number=0,
    )
    if existing_attempt is not None:
        if repair_case.get("baseline_attempt_id") is None:
            db.link_quote_repair_case_baseline_attempt(
                repair_case_id=repair_case_id,
                baseline_attempt_id=int(existing_attempt["id"]),
                lifecycle_state=REPAIR_CASE_STATE_BASELINE_READY,
            )
        return existing_attempt

    actual_replay_result = replay_result
    if actual_replay_result is None:
        actual_replay_result = _run_repair_case_baseline_replay(
            db=db,
            repair_case=repair_case,
        )
    attempt_summary = _build_baseline_attempt_summary(
        db=db,
        repair_case=repair_case,
        replay_result=actual_replay_result,
    )
    attempt = db.create_quote_repair_case_attempt(
        repair_case_id=repair_case_id,
        attempt_kind=REPAIR_ATTEMPT_KIND_BASELINE,
        attempt_number=0,
        trigger="baseline_replay",
        quote_document_id=_maybe_int(actual_replay_result.get("quote_document_id")),
        validation_run_id=_maybe_int(actual_replay_result.get("validation_run_id")),
        replayed_from_quote_document_id=_maybe_int(
            repair_case.get("origin_quote_document_id")
        ),
        group_profile_id=_maybe_int(repair_case.get("group_profile_id")),
        profile_snapshot=_decode_json_field(
            repair_case.get("profile_snapshot_json"),
            fallback={},
        ),
        remaining_lines=_coerce_string_list(actual_replay_result.get("remaining_lines")),
        attempt_summary=attempt_summary,
        outcome_state=_baseline_attempt_outcome_state(replay_result=actual_replay_result),
        failure_note=str(actual_replay_result.get("reason") or ""),
    )
    db.link_quote_repair_case_baseline_attempt(
        repair_case_id=repair_case_id,
        baseline_attempt_id=int(attempt["id"]),
        lifecycle_state=REPAIR_CASE_STATE_BASELINE_READY,
    )
    _refresh_quote_repair_case_rollup(db=db, repair_case_id=repair_case_id)
    return db.get_quote_repair_case_attempt(attempt_id=int(attempt["id"])) or attempt


def advance_quote_repair_case_state(
    *,
    db,
    repair_case_id: int,
    next_state: str,
    current_failure_reason: str | None = None,
) -> dict[str, Any]:
    repair_case = db.get_quote_repair_case(repair_case_id=repair_case_id)
    if repair_case is None:
        raise ValueError(f"quote repair case requires existing repair_case_id={repair_case_id}")

    normalized_next_state = str(next_state or "").strip()
    if normalized_next_state not in _REPAIR_CASE_ALLOWED_TRANSITIONS:
        raise ValueError(f"unsupported repair case state: {normalized_next_state}")

    current_state = str(repair_case.get("lifecycle_state") or REPAIR_CASE_STATE_PACKAGED)
    allowed_next_states = _REPAIR_CASE_ALLOWED_TRANSITIONS.get(current_state, set())
    if (
        normalized_next_state != current_state
        and normalized_next_state not in allowed_next_states
    ):
        raise ValueError(
            f"illegal repair case transition: {current_state} -> {normalized_next_state}"
        )

    updated_case = db.update_quote_repair_case(
        repair_case_id=repair_case_id,
        lifecycle_state=normalized_next_state,
        current_failure_reason=current_failure_reason,
    )
    return _refresh_quote_repair_case_rollup(
        db=db,
        repair_case_id=int(updated_case["id"]),
    )


def record_quote_repair_attempt(
    *,
    db,
    repair_case_id: int,
    trigger: str,
    replay_result: dict[str, Any],
) -> dict[str, Any]:
    repair_case = db.get_quote_repair_case(repair_case_id=repair_case_id)
    if repair_case is None:
        raise ValueError(f"quote repair case requires existing repair_case_id={repair_case_id}")

    current_state = str(repair_case.get("lifecycle_state") or REPAIR_CASE_STATE_PACKAGED)
    if current_state in {
        REPAIR_CASE_STATE_PACKAGED,
        REPAIR_CASE_STATE_BASELINE_READY,
        REPAIR_CASE_STATE_ATTEMPT_FAILED,
        REPAIR_CASE_STATE_ESCALATED,
    }:
        repair_case = advance_quote_repair_case_state(
            db=db,
            repair_case_id=repair_case_id,
            next_state=REPAIR_CASE_STATE_READY_FOR_ATTEMPT,
        )
    elif current_state in {
        REPAIR_CASE_STATE_CLOSED_RESOLVED,
        REPAIR_CASE_STATE_CLOSED_IGNORED,
    }:
        raise ValueError(f"repair case is closed and cannot record attempts: {current_state}")

    attempts = db.list_quote_repair_case_attempts(repair_case_id=repair_case_id)
    next_attempt_number = (
        max(int(item.get("attempt_number") or 0) for item in attempts) + 1
        if attempts
        else 1
    )
    attempt_summary = _build_repair_attempt_summary(
        db=db,
        repair_case=repair_case,
        replay_result=replay_result,
    )
    attempt = db.create_quote_repair_case_attempt(
        repair_case_id=repair_case_id,
        attempt_kind=REPAIR_ATTEMPT_KIND_REPAIR,
        attempt_number=next_attempt_number,
        trigger=str(trigger or "").strip() or "repair_attempt",
        quote_document_id=_existing_quote_document_id(
            db=db,
            value=replay_result.get("quote_document_id"),
        ),
        validation_run_id=_existing_validation_run_id(
            db=db,
            value=replay_result.get("validation_run_id"),
        ),
        replayed_from_quote_document_id=_maybe_int(
            repair_case.get("origin_quote_document_id")
        ),
        group_profile_id=_maybe_int(repair_case.get("group_profile_id")),
        profile_snapshot=_decode_json_field(
            repair_case.get("profile_snapshot_json"),
            fallback={},
        ),
        remaining_lines=_coerce_string_list(replay_result.get("remaining_lines")),
        attempt_summary=attempt_summary,
        outcome_state=_baseline_attempt_outcome_state(replay_result=replay_result),
        failure_note=str(replay_result.get("reason") or ""),
    )
    refreshed_case = _refresh_quote_repair_case_rollup(
        db=db,
        repair_case_id=repair_case_id,
    )
    refreshed_summary = _decode_json_field(
        refreshed_case.get("case_summary_json"),
        fallback={},
    )
    failure_log = list(refreshed_summary.get("failure_log_json") or [])
    classification = str(
        ((attempt_summary.get("comparison") or {}).get("classification")) or ""
    ).strip()
    next_state = REPAIR_CASE_STATE_ATTEMPT_SUCCEEDED
    if classification != "better":
        next_state = (
            REPAIR_CASE_STATE_ESCALATED
            if len(failure_log) >= 3
            else REPAIR_CASE_STATE_ATTEMPT_FAILED
        )
    advance_quote_repair_case_state(
        db=db,
        repair_case_id=repair_case_id,
        next_state=next_state,
        current_failure_reason=str(replay_result.get("reason") or ""),
    )
    return db.get_quote_repair_case_attempt(attempt_id=int(attempt["id"])) or attempt


def ensure_quote_repair_case(
    *,
    db,
    exception_id: int,
) -> dict[str, Any]:
    existing = db.get_quote_repair_case_by_origin_exception(
        origin_exception_id=exception_id
    )
    if existing is not None:
        return existing
    return package_quote_repair_case(db=db, exception_id=exception_id)


def sync_quote_exception_repair_case(
    *,
    db,
    exception_id: int,
    resolution_status: str | None = None,
    replay_result: dict[str, Any] | None = None,
    trigger: str,
) -> dict[str, Any]:
    try:
        repair_case = ensure_quote_repair_case(db=db, exception_id=exception_id)
    except ValueError:
        return {}
    normalized_resolution_status = str(resolution_status or "").strip().lower()

    if replay_result is not None and bool(replay_result.get("replayed")):
        record_quote_repair_attempt(
            db=db,
            repair_case_id=int(repair_case["id"]),
            trigger=trigger,
            replay_result=replay_result,
        )
        repair_case = db.get_quote_repair_case(repair_case_id=int(repair_case["id"])) or repair_case

    if normalized_resolution_status in {"ignored"}:
        return advance_quote_repair_case_state(
            db=db,
            repair_case_id=int(repair_case["id"]),
            next_state=REPAIR_CASE_STATE_CLOSED_IGNORED,
        )
    if normalized_resolution_status in {"resolved", "attached"}:
        return advance_quote_repair_case_state(
            db=db,
            repair_case_id=int(repair_case["id"]),
            next_state=REPAIR_CASE_STATE_CLOSED_RESOLVED,
            current_failure_reason="",
        )
    if normalized_resolution_status in {"open", "annotate"} and not (
        replay_result and bool(replay_result.get("replayed"))
    ):
        return advance_quote_repair_case_state(
            db=db,
            repair_case_id=int(repair_case["id"]),
            next_state=REPAIR_CASE_STATE_READY_FOR_ATTEMPT,
        )
    return _refresh_quote_repair_case_rollup(
        db=db,
        repair_case_id=int(repair_case["id"]),
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


def _build_baseline_attempt_summary(
    *,
    db,
    repair_case: dict[str, Any],
    replay_result: dict[str, Any],
) -> dict[str, Any]:
    origin_metrics = _build_origin_metrics(db=db, repair_case=repair_case)
    attempt_metrics = _build_attempt_metrics(db=db, replay_result=replay_result)
    comparison = {
        "classification": _classify_attempt_comparison(
            replayed=bool(replay_result.get("replayed")),
            origin_metrics=origin_metrics,
            attempt_metrics=attempt_metrics,
            explicit_classification=(replay_result.get("comparison") or {}).get(
                "classification"
            ),
        ),
        "origin": origin_metrics,
        "attempt": attempt_metrics,
    }
    blocked_reason = ""
    if comparison["classification"] == "blocked":
        blocked_reason = str(replay_result.get("reason") or "")
    return {
        "replayed": bool(replay_result.get("replayed")),
        "rows": int(replay_result.get("rows") or 0),
        "exceptions": int(replay_result.get("exceptions") or 0),
        "quote_document_id": _maybe_int(replay_result.get("quote_document_id")),
        "validation_run_id": _maybe_int(replay_result.get("validation_run_id")),
        "remaining_lines": _coerce_string_list(replay_result.get("remaining_lines")),
        "mutated_active_facts": bool(replay_result.get("mutated_active_facts")),
        "origin_quote_document_id": _maybe_int(repair_case.get("origin_quote_document_id")),
        "origin_validation_run_id": _maybe_int(repair_case.get("origin_validation_run_id")),
        "blocked_reason": blocked_reason,
        "comparison": comparison,
    }


def _build_repair_attempt_summary(
    *,
    db,
    repair_case: dict[str, Any],
    replay_result: dict[str, Any],
) -> dict[str, Any]:
    reference_metrics, reference_kind = _build_reference_metrics(
        db=db,
        repair_case=repair_case,
    )
    attempt_metrics = _build_attempt_metrics(db=db, replay_result=replay_result)
    comparison = {
        "classification": _classify_attempt_comparison(
            replayed=bool(replay_result.get("replayed")),
            origin_metrics=reference_metrics,
            attempt_metrics=attempt_metrics,
            explicit_classification=(replay_result.get("comparison") or {}).get(
                "classification"
            ),
        ),
        "reference_kind": reference_kind,
        "reference": reference_metrics,
        "attempt": attempt_metrics,
    }
    blocked_reason = ""
    if comparison["classification"] == "blocked":
        blocked_reason = str(replay_result.get("reason") or "")
    return {
        "replayed": bool(replay_result.get("replayed")),
        "rows": int(replay_result.get("rows") or 0),
        "exceptions": int(replay_result.get("exceptions") or 0),
        "quote_document_id": _maybe_int(replay_result.get("quote_document_id")),
        "validation_run_id": _maybe_int(replay_result.get("validation_run_id")),
        "remaining_lines": _coerce_string_list(replay_result.get("remaining_lines")),
        "mutated_active_facts": bool(replay_result.get("mutated_active_facts")),
        "reference_kind": reference_kind,
        "baseline_attempt_id": _maybe_int(repair_case.get("baseline_attempt_id")),
        "origin_quote_document_id": _maybe_int(repair_case.get("origin_quote_document_id")),
        "origin_validation_run_id": _maybe_int(repair_case.get("origin_validation_run_id")),
        "blocked_reason": blocked_reason,
        "comparison": comparison,
    }


def _baseline_attempt_outcome_state(*, replay_result: dict[str, Any]) -> str:
    if bool(replay_result.get("replayed")):
        return REPAIR_ATTEMPT_OUTCOME_COMPLETED
    return REPAIR_ATTEMPT_OUTCOME_BLOCKED


def _run_repair_case_baseline_replay(*, db, repair_case: dict[str, Any]) -> dict[str, Any]:
    from bookkeeping_web.app import _replay_latest_quote_document_with_current_template

    exception_id = _maybe_int(repair_case.get("origin_exception_id"))
    if exception_id is None:
        raise ValueError("quote repair case missing origin_exception_id")
    exc_row = db.get_quote_exception(exception_id=exception_id)
    if exc_row is None:
        raise ValueError(
            f"quote repair case requires existing exception_id={exception_id}"
        )
    return _replay_latest_quote_document_with_current_template(
        db,
        exc_row=exc_row,
        record_exceptions=False,
    )


def _build_origin_metrics(*, db, repair_case: dict[str, Any]) -> dict[str, Any]:
    origin_quote_document_id = _maybe_int(repair_case.get("origin_quote_document_id"))
    origin_validation_run_id = _maybe_int(repair_case.get("origin_validation_run_id"))
    origin_row_count = 0
    if origin_quote_document_id is not None:
        origin_row_count = len(
            db.list_quote_candidate_rows(quote_document_id=origin_quote_document_id)
        )
    validation_run = None
    if origin_quote_document_id is not None:
        validation_run = db.get_latest_quote_validation_run(
            quote_document_id=origin_quote_document_id
        )
    source_line_snapshot = str(repair_case.get("source_line_snapshot") or "").strip()
    remaining_lines = (
        [line for line in source_line_snapshot.splitlines() if line.strip()]
        if source_line_snapshot
        else []
    )
    return {
        "row_count": origin_row_count,
        "message_decision": str((validation_run or {}).get("message_decision") or ""),
        "exception_count": _count_quote_document_exceptions(
            db=db,
            quote_document_id=origin_quote_document_id,
        ),
        "remaining_lines": remaining_lines,
        "publishable_row_count": int(
            (validation_run or {}).get("publishable_row_count") or 0
        ),
        "held_row_count": int((validation_run or {}).get("held_row_count") or 0),
        "rejected_row_count": int(
            (validation_run or {}).get("rejected_row_count") or 0
        ),
        "validation_run_id": origin_validation_run_id,
    }


def _build_attempt_metrics(*, db, replay_result: dict[str, Any]) -> dict[str, Any]:
    quote_document_id = _maybe_int(replay_result.get("quote_document_id"))
    validation_run = None
    row_count = int(replay_result.get("rows") or 0)
    if quote_document_id is not None:
        row_count = len(db.list_quote_candidate_rows(quote_document_id=quote_document_id))
        validation_run = db.get_latest_quote_validation_run(
            quote_document_id=quote_document_id
        )
    detected_exception_count = replay_result.get("detected_exceptions")
    if detected_exception_count is None:
        detected_exception_count = replay_result.get("exceptions") or 0
    return {
        "row_count": row_count,
        "message_decision": str(
            replay_result.get("message_decision")
            or (validation_run or {}).get("message_decision")
            or ""
        ),
        "exception_count": int(detected_exception_count or 0),
        "remaining_lines": _coerce_string_list(replay_result.get("remaining_lines")),
        "publishable_row_count": int(
            replay_result.get("publishable_row_count")
            or (validation_run or {}).get("publishable_row_count")
            or 0
        ),
        "held_row_count": int(
            replay_result.get("held_row_count")
            or (validation_run or {}).get("held_row_count")
            or 0
        ),
        "rejected_row_count": int(
            replay_result.get("rejected_row_count")
            or (validation_run or {}).get("rejected_row_count")
            or 0
        ),
        "validation_run_id": _maybe_int(
            replay_result.get("validation_run_id")
            or (validation_run or {}).get("id")
        ),
    }


def _build_reference_metrics(
    *,
    db,
    repair_case: dict[str, Any],
) -> tuple[dict[str, Any], str]:
    baseline_attempt_id = _maybe_int(repair_case.get("baseline_attempt_id"))
    if baseline_attempt_id is not None:
        baseline_attempt = db.get_quote_repair_case_attempt(attempt_id=baseline_attempt_id)
        if baseline_attempt is not None:
            baseline_summary = _decode_json_field(
                baseline_attempt.get("attempt_summary_json"),
                fallback={},
            )
            comparison = baseline_summary.get("comparison") or {}
            attempt_metrics = comparison.get("attempt")
            if isinstance(attempt_metrics, dict) and attempt_metrics:
                return dict(attempt_metrics), "baseline"
    return _build_origin_metrics(db=db, repair_case=repair_case), "origin"


def _classify_attempt_comparison(
    *,
    replayed: bool,
    origin_metrics: dict[str, Any],
    attempt_metrics: dict[str, Any],
    explicit_classification: Any,
) -> str:
    explicit = str(explicit_classification or "").strip()
    if explicit:
        return explicit
    if not replayed:
        return "blocked"

    origin_rank = _message_decision_rank(str(origin_metrics.get("message_decision") or ""))
    attempt_rank = _message_decision_rank(
        str(attempt_metrics.get("message_decision") or "")
    )
    origin_exceptions = int(origin_metrics.get("exception_count") or 0)
    attempt_exceptions = int(attempt_metrics.get("exception_count") or 0)
    origin_remaining = len(origin_metrics.get("remaining_lines") or [])
    attempt_remaining = len(attempt_metrics.get("remaining_lines") or [])
    origin_rows = int(origin_metrics.get("row_count") or 0)
    attempt_rows = int(attempt_metrics.get("row_count") or 0)
    origin_publishable = int(origin_metrics.get("publishable_row_count") or 0)
    attempt_publishable = int(attempt_metrics.get("publishable_row_count") or 0)

    improved = (
        attempt_rank > origin_rank
        or attempt_exceptions < origin_exceptions
        or attempt_remaining < origin_remaining
        or attempt_rows > origin_rows
        or attempt_publishable > origin_publishable
    )
    regressed = (
        attempt_rank < origin_rank
        or attempt_exceptions > origin_exceptions
        or attempt_remaining > origin_remaining
        or attempt_publishable < origin_publishable
    )
    if improved and not regressed:
        return "better"
    if not improved and not regressed:
        return "same"
    if regressed and not improved:
        return "worse"
    return "same"


def _count_quote_document_exceptions(*, db, quote_document_id: int | None) -> int:
    if quote_document_id is None:
        return 0
    row = db.conn.execute(
        """
        SELECT COUNT(*) AS cnt
        FROM quote_parse_exceptions
        WHERE quote_document_id = ?
        """,
        (quote_document_id,),
    ).fetchone()
    if row is None:
        return 0
    return int(row["cnt"] or 0)


def _message_decision_rank(value: str) -> int:
    normalized = str(value or "").strip().lower()
    if normalized in {"publish", "publishable", "partial_publish"}:
        return 3
    if normalized in {"mixed", "held_only"}:
        return 2
    if normalized in {"no_publish"}:
        return 1
    return 0


def _coerce_string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if value in (None, ""):
        return []
    return [str(value)]


def _maybe_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    return int(value)


def _decode_json_field(value: Any, *, fallback: Any) -> Any:
    if value in (None, ""):
        return fallback
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return fallback


def _existing_quote_document_id(*, db, value: Any) -> int | None:
    quote_document_id = _maybe_int(value)
    if quote_document_id is None:
        return None
    if db.get_quote_document(quote_document_id=quote_document_id) is None:
        return None
    return quote_document_id


def _existing_validation_run_id(*, db, value: Any) -> int | None:
    validation_run_id = _maybe_int(value)
    if validation_run_id is None:
        return None
    row = db.conn.execute(
        """
        SELECT id
        FROM quote_validation_runs
        WHERE id = ?
        LIMIT 1
        """,
        (validation_run_id,),
    ).fetchone()
    if row is None:
        return None
    return int(row["id"])


def _refresh_quote_repair_case_rollup(*, db, repair_case_id: int) -> dict[str, Any]:
    summary = db.get_quote_repair_case_summary(repair_case_id=repair_case_id)
    if summary is None:
        raise ValueError(f"quote repair case requires existing repair_case_id={repair_case_id}")
    return db.update_quote_repair_case(
        repair_case_id=repair_case_id,
        case_summary=summary,
    )
