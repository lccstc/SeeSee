from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any


SNAPSHOT_UNRESOLVED = "unresolved"
SNAPSHOT_DELTA_UPDATE = "delta_update"
SNAPSHOT_FULL_SNAPSHOT = "full_snapshot"

SNAPSHOT_DECISION_SOURCE_SYSTEM = "system"
SNAPSHOT_DECISION_SOURCE_OPERATOR = "operator"

PUBLISH_MODE_VALIDATION_ONLY = "validation_only"
PUBLISH_MODE_DELTA_SAFE_UPSERT_ONLY = "delta_safe_upsert_only"
PUBLISH_MODE_CONFIRMED_FULL_SNAPSHOT = "confirmed_full_snapshot_apply"

_DELTA_MARKERS = (
    "单独更新",
    "局部更新",
    "补几条",
    "补几行",
    "只补",
    "只改",
)
_FULL_BOARD_MARKERS = (
    "价格表",
    "price updates",
    "价格更新",
    "晚班更新",
    "交接班",
    "shift board",
    "full board",
    "全板",
    "整版",
    "广告更新",
)
_SECTION_MARKERS = (
    "【",
    "[",
    "====",
    "---",
    "——",
)
_QUOTE_LINE_RE = re.compile(
    r"(?:(?:^|[\s:：])[A-Z]{2,4}(?:\b|[:：]))|(?:\d+(?:\.\d+)?\s*(?:[-~－—/／=]|[:：]))"
)
_TRAILING_PRICE_RE = re.compile(r"(?:[:：=]|-{2,}|—{2,}|－{2,})\s*\d+(?:\.\d+)?\s*$")


@dataclass(frozen=True, slots=True)
class SnapshotHypothesis:
    hypothesis: str
    reason: str
    evidence: dict[str, Any]


def infer_snapshot_hypothesis(
    *,
    raw_message: str,
    parser_template: str = "",
) -> SnapshotHypothesis:
    lines = [str(line or "").strip() for line in str(raw_message or "").splitlines()]
    lines = [line for line in lines if line]
    lowered = "\n".join(lines).lower()
    quote_like_count = sum(1 for line in lines if _looks_like_quote_line(line))
    section_like_count = sum(1 for line in lines if _looks_like_section_header(line))
    evidence = {
        "quote_like_line_count": quote_like_count,
        "section_like_count": section_like_count,
        "parser_template": str(parser_template or ""),
    }

    delta_marker = _first_marker(lowered, _DELTA_MARKERS)
    if delta_marker:
        evidence["matched_marker"] = delta_marker
        return SnapshotHypothesis(
            hypothesis=SNAPSHOT_DELTA_UPDATE,
            reason=f"explicit_delta_marker:{delta_marker}",
            evidence=evidence,
        )

    full_marker = _first_marker(lowered, _FULL_BOARD_MARKERS)
    if full_marker and quote_like_count >= 2:
        evidence["matched_marker"] = full_marker
        return SnapshotHypothesis(
            hypothesis=SNAPSHOT_FULL_SNAPSHOT,
            reason=f"full_board_marker:{full_marker}",
            evidence=evidence,
        )

    if quote_like_count >= 6 and section_like_count >= 2:
        return SnapshotHypothesis(
            hypothesis=SNAPSHOT_FULL_SNAPSHOT,
            reason="multi_section_quote_board",
            evidence=evidence,
        )

    return SnapshotHypothesis(
        hypothesis=SNAPSHOT_UNRESOLVED,
        reason="insufficient_snapshot_evidence",
        evidence=evidence,
    )


def get_effective_snapshot_decision(snapshot_row: dict[str, Any] | None) -> str:
    if not snapshot_row:
        return SNAPSHOT_UNRESOLVED
    resolved_decision = str(snapshot_row.get("resolved_decision") or "").strip()
    if resolved_decision in {SNAPSHOT_DELTA_UPDATE, SNAPSHOT_FULL_SNAPSHOT}:
        return resolved_decision
    return SNAPSHOT_UNRESOLVED


def get_guarded_publish_mode(snapshot_row: dict[str, Any] | None) -> str:
    if not snapshot_row:
        return PUBLISH_MODE_DELTA_SAFE_UPSERT_ONLY
    resolved_decision = get_effective_snapshot_decision(snapshot_row)
    decision_source = str(snapshot_row.get("decision_source") or "").strip()
    if (
        resolved_decision == SNAPSHOT_FULL_SNAPSHOT
        and decision_source == SNAPSHOT_DECISION_SOURCE_OPERATOR
    ):
        return PUBLISH_MODE_CONFIRMED_FULL_SNAPSHOT
    return PUBLISH_MODE_DELTA_SAFE_UPSERT_ONLY


def snapshot_decision_label(decision: str) -> str:
    normalized = str(decision or "").strip()
    if normalized == SNAPSHOT_FULL_SNAPSHOT:
        return "整版快照"
    if normalized == SNAPSHOT_DELTA_UPDATE:
        return "局部更新"
    return "未决"


def _first_marker(text: str, markers: tuple[str, ...]) -> str | None:
    for marker in markers:
        if marker.lower() in text:
            return marker
    return None


def _looks_like_quote_line(line: str) -> bool:
    normalized = str(line or "").strip()
    if not normalized:
        return False
    if not any(char.isdigit() for char in normalized):
        return False
    return bool(_QUOTE_LINE_RE.search(normalized) or _TRAILING_PRICE_RE.search(normalized))


def _looks_like_section_header(line: str) -> bool:
    normalized = str(line or "").strip()
    if not normalized:
        return False
    if normalized.startswith("#") and len(normalized) <= 32:
        return True
    return any(marker in normalized for marker in _SECTION_MARKERS)
