from __future__ import annotations

import hashlib
import json
from typing import Any

from bookkeeping_core.repair_cases import (
    REPAIR_ATTEMPT_OUTCOME_COMPLETED,
    REPAIR_CASE_STATE_ATTEMPT_FAILED,
    REPAIR_CASE_STATE_ATTEMPT_SUCCEEDED,
    REPAIR_CASE_STATE_BASELINE_READY,
    REPAIR_CASE_STATE_CLOSED_IGNORED,
    REPAIR_CASE_STATE_CLOSED_RESOLVED,
    REPAIR_CASE_STATE_ESCALATED,
    REPAIR_CASE_STATE_PACKAGED,
    REPAIR_CASE_STATE_READY_FOR_ATTEMPT,
    _baseline_attempt_outcome_state,
    _build_repair_attempt_summary,
    _refresh_quote_repair_case_rollup,
    advance_quote_repair_case_state,
    create_baseline_repair_attempt,
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
    _refresh_quote_repair_case_rollup(db=db, repair_case_id=repair_case_id)
    return db.get_quote_repair_case_attempt(attempt_id=int(attempt["id"])) or attempt


def bootstrap_quote_repair_workflow(
    *,
    db,
    repair_case_id: int,
) -> dict[str, Any]:
    repair_case = db.get_quote_repair_case(repair_case_id=repair_case_id)
    if repair_case is None:
        raise ValueError(f"quote repair case requires existing repair_case_id={repair_case_id}")

    lifecycle_state = str(repair_case.get("lifecycle_state") or "").strip()
    if lifecycle_state in {
        REPAIR_CASE_STATE_CLOSED_RESOLVED,
        REPAIR_CASE_STATE_CLOSED_IGNORED,
        REPAIR_CASE_STATE_ESCALATED,
    }:
        return repair_case

    scope_payload = choose_quote_repair_scope(
        **_build_initial_scope_inputs(repair_case=repair_case)
    )

    try:
        baseline_attempt = create_baseline_repair_attempt(
            db=db,
            repair_case_id=repair_case_id,
        )
    except Exception:
        # Runtime exception capture must remain fact-neutral; baseline replay can fail
        # on synthetic/patched inputs and should not break repair-case packaging.
        return db.get_quote_repair_case(repair_case_id=repair_case_id) or repair_case
    baseline_outcome = str(baseline_attempt.get("outcome_state") or "")
    baseline_failure_note = str(baseline_attempt.get("failure_note") or "")
    if baseline_outcome != REPAIR_ATTEMPT_OUTCOME_COMPLETED:
        if not (
            str(scope_payload["scope"]) == REMEDIATION_SCOPE_BOOTSTRAP
            and baseline_failure_note in {"missing_group_profile", "missing_template_config"}
        ):
            return db.get_quote_repair_case(repair_case_id=repair_case_id) or repair_case

    if _list_non_baseline_attempts(db=db, repair_case_id=repair_case_id):
        return db.get_quote_repair_case(repair_case_id=repair_case_id) or repair_case

    begin_quote_repair_remediation_attempt(
        db=db,
        repair_case_id=repair_case_id,
        trigger="auto_bootstrap",
        proposal_scope=str(scope_payload["scope"]),
        proposal_kind=_initial_proposal_kind(str(scope_payload["scope"])),
    )
    return auto_execute_quote_repair_case(db=db, repair_case_id=repair_case_id)


def auto_execute_quote_repair_case(
    *,
    db,
    repair_case_id: int,
) -> dict[str, Any]:
    while True:
        repair_case = db.get_quote_repair_case(repair_case_id=repair_case_id)
        if repair_case is None:
            raise ValueError(f"quote repair case requires existing repair_case_id={repair_case_id}")

        pending_attempt = _latest_pending_remediation_attempt(
            db=db,
            repair_case_id=repair_case_id,
        )
        if pending_attempt is None:
            return repair_case

        _execute_quote_repair_attempt(
            db=db,
            attempt_id=int(pending_attempt["id"]),
        )
        repair_case = db.get_quote_repair_case(repair_case_id=repair_case_id) or repair_case
        lifecycle_state = str(repair_case.get("lifecycle_state") or "").strip()
        if lifecycle_state in {
            REPAIR_CASE_STATE_CLOSED_RESOLVED,
            REPAIR_CASE_STATE_CLOSED_IGNORED,
            REPAIR_CASE_STATE_ESCALATED,
        }:
            return repair_case
        if lifecycle_state != REPAIR_CASE_STATE_ATTEMPT_FAILED:
            continue

        summary = db.get_quote_repair_case_summary(repair_case_id=repair_case_id) or {}
        if int(summary.get("attempt_count") or 0) >= REMEDIATION_MAX_ATTEMPTS:
            return db.get_quote_repair_case(repair_case_id=repair_case_id) or repair_case

        pending_summary = _decode_json_field(
            pending_attempt.get("attempt_summary_json"),
            fallback={},
        )
        next_scope = _next_auto_scope(
            current_scope=str(pending_summary.get("proposal_scope") or "").strip(),
        )
        if not next_scope:
            advance_quote_repair_case_state(
                db=db,
                repair_case_id=repair_case_id,
                next_state=REPAIR_CASE_STATE_ESCALATED,
            )
            return db.get_quote_repair_case(repair_case_id=repair_case_id) or repair_case
        begin_quote_repair_remediation_attempt(
            db=db,
            repair_case_id=repair_case_id,
            trigger="auto_retry",
            proposal_scope=next_scope,
            proposal_kind=_initial_proposal_kind(next_scope),
            history_read=_declared_history_read(
                summary=summary,
            ),
        )


def _execute_quote_repair_attempt(
    *,
    db,
    attempt_id: int,
) -> dict[str, Any]:
    attempt = db.get_quote_repair_case_attempt(attempt_id=attempt_id)
    if attempt is None:
        raise ValueError(f"quote repair case attempt not found: {attempt_id}")
    if str(attempt.get("attempt_kind") or "") != REMEDIATION_ATTEMPT_KIND:
        raise ValueError("quote repair case attempt is not a remediation attempt")
    if str(attempt.get("outcome_state") or "") != REMEDIATION_OUTCOME_PENDING:
        return attempt

    repair_case = db.get_quote_repair_case(repair_case_id=int(attempt["repair_case_id"]))
    if repair_case is None:
        raise ValueError(
            f"quote repair case requires existing repair_case_id={int(attempt['repair_case_id'])}"
        )

    admitted_attempt = admit_quote_repair_proposal(
        db=db,
        attempt_id=attempt_id,
        proposal_files=[],
    )
    attempt_summary = _decode_json_field(
        admitted_attempt.get("attempt_summary_json"),
        fallback={},
    )
    proposal_scope = str(attempt_summary.get("proposal_scope") or "").strip()
    if proposal_scope not in {
        REMEDIATION_SCOPE_GROUP_PROFILE,
        REMEDIATION_SCOPE_GROUP_SECTION,
        REMEDIATION_SCOPE_BOOTSTRAP,
    }:
        replay_result = _build_auto_failure_replay_result(
            repair_case=repair_case,
            reason=f"unsupported_auto_scope:{proposal_scope or 'unknown'}",
        )
        return finalize_quote_repair_attempt(
            db=db,
            attempt_id=attempt_id,
            replay_result=replay_result,
            validator_passed=False,
            regression_passed=False,
            deterministic_artifacts=[],
        )

    return _auto_apply_group_bound_proposal(
        db=db,
        repair_case=repair_case,
        attempt=admitted_attempt,
    )
    return db.get_quote_repair_case(repair_case_id=repair_case_id) or repair_case


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
    if normalized_state == REPAIR_CASE_STATE_CLOSED_RESOLVED:
        return "修复证据已吸收为确定性语法资产，未改动报价墙。"
    if normalized_state == REPAIR_CASE_STATE_CLOSED_IGNORED:
        return "当前异常已忽略，未改动报价墙。"
    if normalized_state == REPAIR_CASE_STATE_ATTEMPT_SUCCEEDED:
        return "修复证据已吸收为确定性语法资产，未改动报价墙。"
    if normalized_state == REPAIR_CASE_STATE_ESCALATED or str(escalation_state or "") == "ready":
        return f"修复尝试已升级（累计 {attempt_count} 次），仍未改动报价墙。"
    if normalized_state == REPAIR_CASE_STATE_ATTEMPT_FAILED:
        return f"修复尝试未通过验证（累计 {attempt_count} 次），未改动报价墙。"
    if normalized_state == REPAIR_CASE_STATE_READY_FOR_ATTEMPT:
        return "修复提案待验证，未改动报价墙。"
    return "当前仅记录修复证据与验证状态，未改动报价墙。"


def _build_initial_scope_inputs(*, repair_case: dict[str, Any]) -> dict[str, Any]:
    current_failure_reason = str(repair_case.get("current_failure_reason") or "").strip()
    group_profile_id = _maybe_int(repair_case.get("group_profile_id"))
    parser_template_snapshot = str(
        repair_case.get("parser_template_snapshot") or ""
    ).strip()
    return {
        "has_group_profile": group_profile_id is not None,
        "section_local_only": False,
        "section_identifier": "",
        "bootstrap_candidate": (
            group_profile_id is None
            or current_failure_reason == "missing_group_template"
            or parser_template_snapshot == "quote-v1"
        ),
        "cross_group_match_count": 0,
        "global_core_required": False,
    }


def _initial_proposal_kind(scope: str) -> str:
    normalized_scope = str(scope or "").strip()
    if normalized_scope == REMEDIATION_SCOPE_BOOTSTRAP:
        return "bootstrap_seed"
    if normalized_scope == REMEDIATION_SCOPE_GROUP_SECTION:
        return "section_patch"
    if normalized_scope == REMEDIATION_SCOPE_SHARED_RULE:
        return "shared_rule_patch"
    if normalized_scope == REMEDIATION_SCOPE_GLOBAL_CORE:
        return "global_core_patch"
    return "group_profile_patch"


def _next_auto_scope(*, current_scope: str) -> str:
    normalized_scope = str(current_scope or "").strip()
    try:
        index = REMEDIATION_SCOPE_ORDER.index(normalized_scope)
    except ValueError:
        return ""
    if index + 1 >= len(REMEDIATION_SCOPE_ORDER):
        return ""
    return str(REMEDIATION_SCOPE_ORDER[index + 1])


def _declared_history_read(*, summary: dict[str, Any]) -> dict[str, Any]:
    failure_log = list(summary.get("failure_log_json") or [])
    return {
        "attempt_count": int(summary.get("attempt_count") or 0),
        "failure_log_count": len(failure_log),
        "history_fingerprint": build_quote_repair_history_fingerprint(
            failure_log=failure_log,
            last_attempt_number=_maybe_int(summary.get("last_attempt_number")),
        ),
        "failure_notes": [str(item.get("failure_note") or "") for item in failure_log],
    }


def _latest_pending_remediation_attempt(
    *,
    db,
    repair_case_id: int,
) -> dict[str, Any] | None:
    attempts = _list_non_baseline_attempts(db=db, repair_case_id=repair_case_id)
    for attempt in reversed(attempts):
        if str(attempt.get("outcome_state") or "") == REMEDIATION_OUTCOME_PENDING:
            return attempt
    return None


def _build_auto_failure_replay_result(
    *,
    repair_case: dict[str, Any],
    reason: str,
    remaining_lines: list[str] | None = None,
) -> dict[str, Any]:
    lines = list(remaining_lines or [])
    if not lines:
        lines = [
            str(line).strip()
            for line in str(repair_case.get("source_line_snapshot") or "").splitlines()
            if str(line).strip()
        ]
    return {
        "replayed": False,
        "rows": 0,
        "exceptions": 0,
        "remaining_lines": lines,
        "reason": str(reason or "").strip() or "auto_remediation_failed",
        "mutated_active_facts": False,
    }


def _auto_apply_group_bound_proposal(
    *,
    db,
    repair_case: dict[str, Any],
    attempt: dict[str, Any],
) -> dict[str, Any]:
    from bookkeeping_core.template_engine import (
        _GROUP_PARSER_MAX_SECTIONS as GROUP_PARSER_MAX_SECTIONS,
        TemplateConfig,
        suggest_result_template_text,
    )
    from bookkeeping_web.app import (
        _build_quote_result_preview_payload,
        _load_bound_quote_group_profile,
        _merge_group_parser_template_config,
        _replay_latest_quote_document_with_current_template,
    )

    attempt_id = int(attempt["id"])
    attempt_summary = _decode_json_field(
        attempt.get("attempt_summary_json"),
        fallback={},
    )
    proposal_scope = str(attempt_summary.get("proposal_scope") or "").strip()
    exception_id = _maybe_int(repair_case.get("origin_exception_id"))
    if exception_id is None:
        replay_result = _build_auto_failure_replay_result(
            repair_case=repair_case,
            reason="repair_case_missing_origin_exception",
        )
        return finalize_quote_repair_attempt(
            db=db,
            attempt_id=attempt_id,
            replay_result=replay_result,
            validator_passed=False,
            regression_passed=False,
            deterministic_artifacts=[],
        )
    exc_row = db.get_quote_exception(exception_id=exception_id)
    if exc_row is None:
        replay_result = _build_auto_failure_replay_result(
            repair_case=repair_case,
            reason=f"missing_exception:{exception_id}",
        )
        return finalize_quote_repair_attempt(
            db=db,
            attempt_id=attempt_id,
            replay_result=replay_result,
            validator_passed=False,
            regression_passed=False,
            deterministic_artifacts=[],
        )
    quote_document = db.get_quote_document(
        quote_document_id=int(exc_row.get("quote_document_id") or 0)
    )
    raw_text = str((quote_document or {}).get("raw_text") or exc_row.get("raw_text") or "")
    chat_name = str((quote_document or {}).get("chat_name") or exc_row.get("chat_name") or "")
    group_profile = _load_bound_quote_group_profile(
        db,
        platform=str(exc_row.get("platform") or ""),
        chat_id=str(exc_row.get("chat_id") or ""),
        chat_name=chat_name,
    )
    default_card_type = str((group_profile or {}).get("default_card_type") or "")
    suggested_result_template_text = suggest_result_template_text(
        raw_text,
        chat_name=chat_name,
        default_card_type=default_card_type,
    )
    preview = _build_quote_result_preview_payload(
        db,
        {
            "exception_id": exception_id,
            "result_template_text": suggested_result_template_text,
        },
    )
    preview_errors = [str(item).strip() for item in list(preview.get("errors") or []) if str(item).strip()]
    if not bool(preview.get("can_save")) or not bool(preview.get("strict_replay_ok")):
        replay_result = _build_auto_failure_replay_result(
            repair_case=repair_case,
            reason="; ".join(preview_errors) or "auto_result_preview_not_saveable",
            remaining_lines=[
                str(line).strip()
                for line in list(preview.get("strict_replay_errors") or [])
                if str(line).strip()
            ],
        )
        return finalize_quote_repair_attempt(
            db=db,
            attempt_id=attempt_id,
            replay_result=replay_result,
            validator_passed=False,
            regression_passed=False,
            deterministic_artifacts=[],
        )

    if proposal_scope == REMEDIATION_SCOPE_GROUP_SECTION and len(list(preview.get("derived_sections") or [])) != 1:
        replay_result = _build_auto_failure_replay_result(
            repair_case=repair_case,
            reason="group_section_scope_requires_single_derived_section",
        )
        return finalize_quote_repair_attempt(
            db=db,
            attempt_id=attempt_id,
            replay_result=replay_result,
            validator_passed=False,
            regression_passed=False,
            deterministic_artifacts=[],
        )

    existing_profile = db.get_quote_group_profile(
        platform=str(exc_row.get("platform") or ""),
        chat_id=str(exc_row.get("chat_id") or ""),
    )
    existing_profile_id = _maybe_int((existing_profile or {}).get("id"))
    existing_template_config = str((existing_profile or {}).get("template_config") or "").strip()
    existing_section_count = 0
    if existing_template_config:
        try:
            existing_template = TemplateConfig.from_json(existing_template_config)
            existing_section_count = len(list(existing_template.sections or []))
        except ValueError:
            existing_section_count = 0
    use_supermarket_mode = str((existing_profile or {}).get("parser_template") or "").strip() == "supermarket-card"
    preview_rows = list(preview.get("preview_rows") or [])
    first_row = preview_rows[0] if preview_rows else {}
    draft_defaults = dict((preview.get("draft_structure") or {}).get("defaults") or {})
    try:
        merged_config = _merge_group_parser_template_config(
            existing_template_config,
            derived_sections=list(preview.get("derived_sections") or []),
            max_sections=None if use_supermarket_mode else GROUP_PARSER_MAX_SECTIONS,
            allow_new_sections=existing_section_count == 0,
        )

        db.upsert_quote_group_profile(
            platform=str(exc_row.get("platform") or ""),
            chat_id=str(exc_row.get("chat_id") or ""),
            chat_name=str(exc_row.get("chat_name") or exc_row.get("chat_id") or ""),
            default_card_type=str(
                (existing_profile or {}).get("default_card_type")
                or first_row.get("card_type")
                or draft_defaults.get("card_type")
                or ""
            ),
            default_country_or_currency=str(
                (existing_profile or {}).get("default_country_or_currency")
                or draft_defaults.get("country_or_currency")
                or first_row.get("country_or_currency")
                or ""
            ),
            default_form_factor=str(
                draft_defaults.get("form_factor")
                or (existing_profile or {}).get("default_form_factor")
                or first_row.get("form_factor")
                or "不限"
            ),
            default_multiplier=str((existing_profile or {}).get("default_multiplier") or ""),
            parser_template="supermarket-card" if use_supermarket_mode else "group-parser",
            stale_after_minutes=int((existing_profile or {}).get("stale_after_minutes") or 30),
            note=str((existing_profile or {}).get("note") or ""),
            template_config=merged_config,
        )

        replay_result = _replay_latest_quote_document_with_current_template(
            db,
            exc_row=exc_row,
            record_exceptions=True,
        )
    except Exception as exc:
        _restore_quote_group_profile_state(
            db=db,
            platform=str(exc_row.get("platform") or ""),
            chat_id=str(exc_row.get("chat_id") or ""),
            chat_name=str(exc_row.get("chat_name") or exc_row.get("chat_id") or ""),
            existing_profile=existing_profile,
            existing_profile_id=existing_profile_id,
        )
        replay_result = _build_auto_failure_replay_result(
            repair_case=repair_case,
            reason=str(exc),
        )
        return finalize_quote_repair_attempt(
            db=db,
            attempt_id=attempt_id,
            replay_result=replay_result,
            validator_passed=False,
            regression_passed=False,
            deterministic_artifacts=[],
        )
    validator_passed = bool(replay_result.get("replayed")) and int(replay_result.get("exceptions") or 0) == 0
    regression_passed = bool(preview.get("strict_replay_ok"))
    artifacts = [
        {
            "kind": f"{proposal_scope}_auto_profile_update",
            "parser_template": "supermarket-card" if use_supermarket_mode else "group-parser",
            "derived_sections": len(list(preview.get("derived_sections") or [])),
            "result_template_text": suggested_result_template_text,
        }
    ]
    finalized = finalize_quote_repair_attempt(
        db=db,
        attempt_id=attempt_id,
        replay_result=replay_result,
        validator_passed=validator_passed,
        regression_passed=regression_passed,
        deterministic_artifacts=artifacts,
    )
    finalized_summary = _decode_json_field(
        finalized.get("attempt_summary_json"),
        fallback={},
    )
    if str(finalized_summary.get("absorption_decision") or "") == "absorbed":
        db.resolve_quote_exception(
            exception_id=exception_id,
            resolution_status="resolved",
            resolution_note=(
                f"auto_remediated scope={proposal_scope} "
                f"sections={len(list(preview.get('derived_sections') or []))} "
                f"rows={len(preview_rows)} strict_replay=true"
            ),
        )
        advance_quote_repair_case_state(
            db=db,
            repair_case_id=int(repair_case["id"]),
            next_state=REPAIR_CASE_STATE_CLOSED_RESOLVED,
            current_failure_reason="",
        )
        return finalized

    _restore_quote_group_profile_state(
        db=db,
        platform=str(exc_row.get("platform") or ""),
        chat_id=str(exc_row.get("chat_id") or ""),
        chat_name=str(exc_row.get("chat_name") or exc_row.get("chat_id") or ""),
        existing_profile=existing_profile,
        existing_profile_id=existing_profile_id,
    )
    db.update_quote_exception(
        exception_id=exception_id,
        resolution_status="open",
        resolution_note=(
            f"auto_remediation_failed scope={proposal_scope} "
            f"reason={str(replay_result.get('reason') or '').strip() or 'validation_failed'}"
        ),
    )
    return finalized


def _restore_quote_group_profile_state(
    *,
    db,
    platform: str,
    chat_id: str,
    chat_name: str,
    existing_profile: dict[str, Any] | None,
    existing_profile_id: int | None,
) -> None:
    if existing_profile is None:
        latest = db.get_quote_group_profile(platform=platform, chat_id=chat_id)
        latest_id = _maybe_int((latest or {}).get("id"))
        if latest_id is not None:
            db.delete_quote_group_profile(profile_id=latest_id)
        return
    db.upsert_quote_group_profile(
        platform=platform,
        chat_id=chat_id,
        chat_name=str(existing_profile.get("chat_name") or chat_name or chat_id),
        default_card_type=str(existing_profile.get("default_card_type") or ""),
        default_country_or_currency=str(
            existing_profile.get("default_country_or_currency") or ""
        ),
        default_form_factor=str(existing_profile.get("default_form_factor") or ""),
        default_multiplier=str(existing_profile.get("default_multiplier") or ""),
        parser_template=str(existing_profile.get("parser_template") or ""),
        stale_after_minutes=int(existing_profile.get("stale_after_minutes") or 30),
        note=str(existing_profile.get("note") or ""),
        template_config=str(existing_profile.get("template_config") or ""),
    )


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
