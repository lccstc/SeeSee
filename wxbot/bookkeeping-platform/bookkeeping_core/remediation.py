from __future__ import annotations

import hashlib
import json
from typing import Any

from bookkeeping_core.repair_cases import (
    REPAIR_CASE_STATE_ATTEMPT_FAILED,
    REPAIR_CASE_STATE_ATTEMPT_SUCCEEDED,
    REPAIR_CASE_STATE_BASELINE_READY,
    REPAIR_CASE_STATE_ESCALATED,
    REPAIR_CASE_STATE_PACKAGED,
    REPAIR_CASE_STATE_READY_FOR_ATTEMPT,
    _baseline_attempt_outcome_state,
    _build_repair_attempt_summary,
    _refresh_quote_repair_case_rollup,
    advance_quote_repair_case_state,
)


REMEDIATION_ATTEMPT_KIND = "remediation"
REMEDIATION_OUTCOME_PENDING = "pending"
REMEDIATION_MAX_ATTEMPTS = 3
REMEDIATION_SCOPE_GROUP_PROFILE = "group_profile"
REMEDIATION_SCOPE_GROUP_SECTION = "group_section"
REMEDIATION_SCOPE_BOOTSTRAP = "bootstrap"
REMEDIATION_SCOPE_SHARED_RULE = "shared_rule"
REMEDIATION_SCOPE_GLOBAL_CORE = "global_core"

ALLOWED_REMEDIATION_SCOPES = {
    REMEDIATION_SCOPE_GROUP_PROFILE,
    REMEDIATION_SCOPE_GROUP_SECTION,
    REMEDIATION_SCOPE_BOOTSTRAP,
    REMEDIATION_SCOPE_SHARED_RULE,
    REMEDIATION_SCOPE_GLOBAL_CORE,
}

REMEDIATION_SCOPE_ORDER = (
    REMEDIATION_SCOPE_GROUP_PROFILE,
    REMEDIATION_SCOPE_GROUP_SECTION,
    REMEDIATION_SCOPE_BOOTSTRAP,
    REMEDIATION_SCOPE_SHARED_RULE,
    REMEDIATION_SCOPE_GLOBAL_CORE,
)

_SAFE_WRITE_ENVELOPES = {
    REMEDIATION_SCOPE_GROUP_PROFILE: {
        "allowed_prefixes": ("wxbot/bookkeeping-platform/tests/",),
        "forbidden_prefixes": (
            "wxbot/bookkeeping-platform/bookkeeping_web/",
            "wxbot/bookkeeping-platform/bookkeeping_core/database.py",
            "wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py",
            "wxbot/bookkeeping-platform/bookkeeping_core/quotes.py",
            "wxbot/bookkeeping-platform/sql/",
        ),
        "logical_targets": ("quote_group_profiles.defaults", "quote_group_profiles.template_config"),
    },
    REMEDIATION_SCOPE_GROUP_SECTION: {
        "allowed_prefixes": ("wxbot/bookkeeping-platform/tests/",),
        "forbidden_prefixes": (
            "wxbot/bookkeeping-platform/bookkeeping_web/",
            "wxbot/bookkeeping-platform/bookkeeping_core/database.py",
            "wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py",
            "wxbot/bookkeeping-platform/bookkeeping_core/quotes.py",
            "wxbot/bookkeeping-platform/sql/",
        ),
        "logical_targets": ("quote_group_profiles.template_config.sections",),
    },
    REMEDIATION_SCOPE_BOOTSTRAP: {
        "allowed_prefixes": (
            "wxbot/bookkeeping-platform/scripts/bootstrap_quote_group_profiles.py",
            "wxbot/bookkeeping-platform/tests/",
        ),
        "forbidden_prefixes": (
            "wxbot/bookkeeping-platform/bookkeeping_web/",
            "wxbot/bookkeeping-platform/bookkeeping_core/database.py",
            "wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py",
            "wxbot/bookkeeping-platform/bookkeeping_core/quotes.py",
            "wxbot/bookkeeping-platform/sql/",
        ),
        "logical_targets": ("bootstrap.quote_group_profiles",),
    },
    REMEDIATION_SCOPE_SHARED_RULE: {
        "allowed_prefixes": (
            "wxbot/bookkeeping-platform/bookkeeping_core/template_engine.py",
            "wxbot/bookkeeping-platform/tests/",
        ),
        "forbidden_prefixes": (
            "wxbot/bookkeeping-platform/bookkeeping_web/",
            "wxbot/bookkeeping-platform/bookkeeping_core/database.py",
            "wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py",
            "wxbot/bookkeeping-platform/bookkeeping_core/quotes.py",
            "wxbot/bookkeeping-platform/sql/",
        ),
        "logical_targets": ("template_engine.shared_rules",),
    },
    REMEDIATION_SCOPE_GLOBAL_CORE: {
        "allowed_prefixes": (
            "wxbot/bookkeeping-platform/bookkeeping_core/template_engine.py",
            "wxbot/bookkeeping-platform/bookkeeping_core/quotes.py",
            "wxbot/bookkeeping-platform/bookkeeping_core/remediation.py",
            "wxbot/bookkeeping-platform/tests/",
        ),
        "forbidden_prefixes": (
            "wxbot/bookkeeping-platform/bookkeeping_web/",
            "wxbot/bookkeeping-platform/bookkeeping_core/database.py",
            "wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py",
            "wxbot/bookkeeping-platform/sql/",
        ),
        "logical_targets": ("quote_parser.global_core",),
    },
}


def begin_quote_repair_remediation_attempt(
    *,
    db,
    repair_case_id: int,
    trigger: str,
    proposal_scope: str,
    proposal_kind: str,
    history_read: dict[str, Any] | None = None,
) -> dict[str, Any]:
    repair_case = db.get_quote_repair_case(repair_case_id=repair_case_id)
    if repair_case is None:
        raise ValueError(f"quote repair case requires existing repair_case_id={repair_case_id}")

    normalized_scope = str(proposal_scope or "").strip()
    if normalized_scope not in ALLOWED_REMEDIATION_SCOPES:
        raise ValueError(f"unsupported remediation scope: {proposal_scope}")
    normalized_kind = str(proposal_kind or "").strip()
    if not normalized_kind:
        raise ValueError("proposal_kind is required")

    current_state = str(repair_case.get("lifecycle_state") or "")
    if current_state in {"closed_resolved", "closed_ignored"}:
        raise ValueError(f"repair case is closed and cannot remediate: {current_state}")
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

    prior_attempts = _list_non_baseline_attempts(db=db, repair_case_id=repair_case_id)
    if prior_attempts:
        latest_attempt = prior_attempts[-1]
        latest_outcome = str(latest_attempt.get("outcome_state") or "").strip()
        if latest_outcome == REMEDIATION_OUTCOME_PENDING:
            raise ValueError("previous remediation attempt is still pending")
    next_attempt_number = len(prior_attempts) + 1
    if next_attempt_number > REMEDIATION_MAX_ATTEMPTS:
        advance_quote_repair_case_state(
            db=db,
            repair_case_id=repair_case_id,
            next_state=REPAIR_CASE_STATE_ESCALATED,
        )
        raise ValueError("maximum remediation attempts exceeded for repair case")

    history_payload = _build_history_read_payload(
        db=db,
        repair_case_id=repair_case_id,
        next_attempt_number=next_attempt_number,
        declared_history=history_read,
    )
    profile_snapshot = _decode_json_field(
        repair_case.get("profile_snapshot_json"),
        fallback={},
    )
    attempt_summary = {
        "protocol": "quote_remediation_v1",
        "protocol_stage": "proposal_opened",
        "proposal_scope": normalized_scope,
        "proposal_kind": normalized_kind,
        "history_read": history_payload,
        "verification_gates": {},
        "absorption_decision": "",
        "mutated_active_facts": False,
        "replayed": False,
        "rows": 0,
        "exceptions": 0,
        "remaining_lines": [],
        "comparison": {"classification": "pending"},
    }
    attempt = db.create_quote_repair_case_attempt(
        repair_case_id=repair_case_id,
        attempt_kind=REMEDIATION_ATTEMPT_KIND,
        attempt_number=next_attempt_number,
        trigger=str(trigger or "").strip() or "remediation_attempt",
        quote_document_id=None,
        validation_run_id=None,
        replayed_from_quote_document_id=_maybe_int(
            repair_case.get("origin_quote_document_id")
        ),
        group_profile_id=_maybe_int(repair_case.get("group_profile_id")),
        profile_snapshot=profile_snapshot,
        remaining_lines=[],
        attempt_summary=attempt_summary,
        outcome_state=REMEDIATION_OUTCOME_PENDING,
        failure_note="",
    )
    return db.get_quote_repair_case_attempt(attempt_id=int(attempt["id"])) or attempt


def build_quote_repair_history_fingerprint(
    *,
    failure_log: list[dict[str, Any]],
    last_attempt_number: int | None,
) -> str:
    canonical_payload = {
        "failure_log": [
            {
                "attempt_number": int(item.get("attempt_number") or 0),
                "outcome_state": str(item.get("outcome_state") or ""),
                "classification": str(item.get("classification") or ""),
                "failure_note": str(item.get("failure_note") or ""),
            }
            for item in failure_log
        ],
        "last_attempt_number": int(last_attempt_number or 0),
    }
    encoded = json.dumps(canonical_payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def choose_quote_repair_scope(
    *,
    has_group_profile: bool,
    section_local_only: bool,
    section_identifier: str = "",
    bootstrap_candidate: bool = False,
    cross_group_match_count: int = 0,
    global_core_required: bool = False,
) -> dict[str, Any]:
    if global_core_required:
        if int(cross_group_match_count or 0) < 3:
            raise ValueError("global_core remediation requires repeated cross-group evidence")
        return {
            "scope": REMEDIATION_SCOPE_GLOBAL_CORE,
            "reason": "repeated_cross_group_global_core",
            "scope_order": list(REMEDIATION_SCOPE_ORDER),
        }
    if int(cross_group_match_count or 0) >= 2:
        return {
            "scope": REMEDIATION_SCOPE_SHARED_RULE,
            "reason": "repeated_cross_group_shared_rule",
            "scope_order": list(REMEDIATION_SCOPE_ORDER),
        }
    if has_group_profile:
        if section_local_only and str(section_identifier or "").strip():
            return {
                "scope": REMEDIATION_SCOPE_GROUP_SECTION,
                "reason": "section_local_only",
                "scope_order": list(REMEDIATION_SCOPE_ORDER),
            }
        return {
            "scope": REMEDIATION_SCOPE_GROUP_PROFILE,
            "reason": "default_group_profile_first",
            "scope_order": list(REMEDIATION_SCOPE_ORDER),
        }
    if bootstrap_candidate:
        return {
            "scope": REMEDIATION_SCOPE_BOOTSTRAP,
            "reason": "no_group_profile_bootstrap_candidate",
            "scope_order": list(REMEDIATION_SCOPE_ORDER),
        }
    return {
        "scope": REMEDIATION_SCOPE_GROUP_PROFILE,
        "reason": "fallback_group_profile_first",
        "scope_order": list(REMEDIATION_SCOPE_ORDER),
    }


def validate_quote_repair_write_scope(
    *,
    proposal_scope: str,
    touched_files: list[str] | tuple[str, ...],
) -> dict[str, Any]:
    normalized_scope = str(proposal_scope or "").strip()
    if normalized_scope not in _SAFE_WRITE_ENVELOPES:
        raise ValueError(f"unsupported remediation scope: {proposal_scope}")
    envelope = _SAFE_WRITE_ENVELOPES[normalized_scope]
    normalized_files = [str(path).strip() for path in touched_files if str(path).strip()]
    forbidden_hits = [
        path
        for path in normalized_files
        if any(path.startswith(prefix) for prefix in envelope["forbidden_prefixes"])
    ]
    if forbidden_hits:
        raise ValueError(
            f"proposal targets forbidden remediation surfaces: {', '.join(sorted(forbidden_hits))}"
        )
    disallowed_hits = [
        path
        for path in normalized_files
        if not any(path.startswith(prefix) for prefix in envelope["allowed_prefixes"])
    ]
    if disallowed_hits:
        raise ValueError(
            f"proposal falls outside allowed write scope for {normalized_scope}: {', '.join(sorted(disallowed_hits))}"
        )
    return {
        "scope": normalized_scope,
        "allowed_prefixes": list(envelope["allowed_prefixes"]),
        "forbidden_prefixes": list(envelope["forbidden_prefixes"]),
        "logical_targets": list(envelope["logical_targets"]),
        "touched_files": normalized_files,
    }


def admit_quote_repair_proposal(
    *,
    db,
    attempt_id: int,
    proposal_files: list[str] | tuple[str, ...],
) -> dict[str, Any]:
    attempt = db.get_quote_repair_case_attempt(attempt_id=attempt_id)
    if attempt is None:
        raise ValueError(f"quote repair case attempt not found: {attempt_id}")
    attempt_summary = _decode_json_field(attempt.get("attempt_summary_json"), fallback={})
    proposal_scope = str(attempt_summary.get("proposal_scope") or "").strip()
    envelope = validate_quote_repair_write_scope(
        proposal_scope=proposal_scope,
        touched_files=list(proposal_files),
    )
    attempt_summary["write_envelope"] = envelope
    attempt_summary["protocol_stage"] = "proposal_admitted"
    updated = db.update_quote_repair_case_attempt(
        attempt_id=attempt_id,
        attempt_summary=attempt_summary,
    )
    return db.get_quote_repair_case_attempt(attempt_id=int(updated["id"])) or updated


def finalize_quote_repair_attempt(
    *,
    db,
    attempt_id: int,
    replay_result: dict[str, Any],
    validator_passed: bool,
    regression_passed: bool,
    deterministic_artifacts: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    attempt = db.get_quote_repair_case_attempt(attempt_id=attempt_id)
    if attempt is None:
        raise ValueError(f"quote repair case attempt not found: {attempt_id}")
    if str(attempt.get("attempt_kind") or "") != REMEDIATION_ATTEMPT_KIND:
        raise ValueError("quote repair case attempt is not a remediation attempt")
    if str(attempt.get("outcome_state") or "") != REMEDIATION_OUTCOME_PENDING:
        raise ValueError("quote repair case remediation attempt is not pending")

    repair_case_id = int(attempt["repair_case_id"])
    repair_case = db.get_quote_repair_case(repair_case_id=repair_case_id)
    if repair_case is None:
        raise ValueError(f"quote repair case requires existing repair_case_id={repair_case_id}")

    attempt_summary = _decode_json_field(attempt.get("attempt_summary_json"), fallback={})
    computed_summary = _build_repair_attempt_summary(
        db=db,
        repair_case=repair_case,
        replay_result=replay_result,
    )
    replay_passed = bool(replay_result.get("replayed")) and not bool(
        replay_result.get("mutated_active_facts")
    )
    artifact_list = [dict(item) for item in (deterministic_artifacts or [])]
    absorption_decision = "absorbed"
    if not (replay_passed and validator_passed and regression_passed and artifact_list):
        absorption_decision = "rejected"

    attempt_summary.update(computed_summary)
    attempt_summary["verification_gates"] = {
        "replay_passed": replay_passed,
        "validator_passed": bool(validator_passed),
        "regression_passed": bool(regression_passed),
        "artifacts_present": bool(artifact_list),
    }
    attempt_summary["deterministic_artifacts"] = artifact_list
    attempt_summary["absorption_decision"] = absorption_decision
    attempt_summary["protocol_stage"] = "finalized"
    attempt_summary["proof_status_text"] = build_quote_repair_status_text(
        lifecycle_state=(
            REPAIR_CASE_STATE_ATTEMPT_SUCCEEDED
            if absorption_decision == "absorbed"
            else REPAIR_CASE_STATE_ESCALATED
            if int(attempt.get("attempt_number") or 0) >= REMEDIATION_MAX_ATTEMPTS
            else REPAIR_CASE_STATE_ATTEMPT_FAILED
        ),
        attempt_count=int(attempt.get("attempt_number") or 0),
        escalation_state=(
            "ready"
            if int(attempt.get("attempt_number") or 0) >= REMEDIATION_MAX_ATTEMPTS
            and absorption_decision != "absorbed"
            else "retryable"
            if absorption_decision != "absorbed"
            else "not_ready"
        ),
    )
    failure_note = str(replay_result.get("reason") or "")
    updated_attempt = db.update_quote_repair_case_attempt(
        attempt_id=attempt_id,
        quote_document_id=_maybe_int(replay_result.get("quote_document_id")),
        validation_run_id=_maybe_int(replay_result.get("validation_run_id")),
        remaining_lines=_coerce_string_list(replay_result.get("remaining_lines")),
        attempt_summary=attempt_summary,
        outcome_state=_baseline_attempt_outcome_state(replay_result=replay_result),
        failure_note=failure_note,
    )
    refreshed_case = _refresh_quote_repair_case_rollup(db=db, repair_case_id=repair_case_id)
    refreshed_summary = _decode_json_field(refreshed_case.get("case_summary_json"), fallback={})
    next_state = REPAIR_CASE_STATE_ATTEMPT_SUCCEEDED
    if absorption_decision != "absorbed":
        next_state = (
            REPAIR_CASE_STATE_ESCALATED
            if int(refreshed_summary.get("attempt_count") or 0) >= REMEDIATION_MAX_ATTEMPTS
            else REPAIR_CASE_STATE_ATTEMPT_FAILED
        )
    advance_quote_repair_case_state(
        db=db,
        repair_case_id=repair_case_id,
        next_state=next_state,
        current_failure_reason=failure_note,
    )
    return db.get_quote_repair_case_attempt(attempt_id=int(updated_attempt["id"])) or updated_attempt


def build_quote_repair_status_text(
    *,
    lifecycle_state: str,
    attempt_count: int,
    escalation_state: str,
) -> str:
    normalized_state = str(lifecycle_state or "").strip()
    if normalized_state == REPAIR_CASE_STATE_ATTEMPT_SUCCEEDED:
        return "修复证据已吸收为确定性语法资产，未改动报价墙。"
    if normalized_state == REPAIR_CASE_STATE_ESCALATED or str(escalation_state or "") == "ready":
        return f"修复尝试已升级（累计 {attempt_count} 次），仍未改动报价墙。"
    if normalized_state == REPAIR_CASE_STATE_ATTEMPT_FAILED:
        return f"修复尝试未通过验证（累计 {attempt_count} 次），未改动报价墙。"
    if normalized_state == REPAIR_CASE_STATE_READY_FOR_ATTEMPT:
        return "修复提案待验证，未改动报价墙。"
    return "当前仅记录修复证据与验证状态，未改动报价墙。"


def _build_history_read_payload(
    *,
    db,
    repair_case_id: int,
    next_attempt_number: int,
    declared_history: dict[str, Any] | None,
) -> dict[str, Any]:
    summary = db.get_quote_repair_case_summary(repair_case_id=repair_case_id) or {}
    failure_log = list(summary.get("failure_log_json") or [])
    last_attempt_number = summary.get("last_attempt_number")
    fingerprint = build_quote_repair_history_fingerprint(
        failure_log=failure_log,
        last_attempt_number=_maybe_int(last_attempt_number),
    )
    expected = {
        "attempt_count": int(summary.get("attempt_count") or 0),
        "failure_log_count": len(failure_log),
        "history_fingerprint": fingerprint,
        "failure_notes": [str(item.get("failure_note") or "") for item in failure_log],
    }
    if next_attempt_number == 1:
        return {
            **expected,
            "required": False,
            "consumed": True,
            "mode": "initial_attempt",
        }

    declared = dict(declared_history or {})
    if int(declared.get("attempt_count") or -1) != expected["attempt_count"]:
        raise ValueError("retry attempt requires prior history attempt_count")
    if int(declared.get("failure_log_count") or -1) != expected["failure_log_count"]:
        raise ValueError("retry attempt requires prior history failure_log_count")
    if str(declared.get("history_fingerprint") or "") != expected["history_fingerprint"]:
        raise ValueError("retry attempt requires matching prior history fingerprint")
    declared_notes = [str(item) for item in (declared.get("failure_notes") or [])]
    if declared_notes != expected["failure_notes"]:
        raise ValueError("retry attempt requires consumed failure-note history")
    return {
        **expected,
        "required": True,
        "consumed": True,
        "mode": "retry_attempt",
    }


def _list_non_baseline_attempts(*, db, repair_case_id: int) -> list[dict[str, Any]]:
    attempts = db.list_quote_repair_case_attempts(repair_case_id=repair_case_id)
    return [item for item in attempts if int(item.get("attempt_number") or 0) > 0]


def _decode_json_field(value: Any, *, fallback: Any) -> Any:
    if value in (None, ""):
        return fallback
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return fallback


def _maybe_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    return int(value)


def _coerce_string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if value in (None, ""):
        return []
    return [str(value)]
