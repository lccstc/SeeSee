from __future__ import annotations

from dataclasses import asdict, dataclass, field
import re
from typing import Any

from .quote_candidates import QuoteCandidateMessage


VALIDATOR_VERSION_V1 = "validation-engine-v1"

SCHEMA_MISSING_CARD_TYPE = "schema_missing_card_type"
SCHEMA_MISSING_COUNTRY_OR_CURRENCY = "schema_missing_country_or_currency"
SCHEMA_MISSING_NORMALIZED_SKU_KEY = "schema_missing_normalized_sku_key"
SCHEMA_MISSING_SOURCE_LINE = "schema_missing_source_line"
SCHEMA_INVALID_AMOUNT_RANGE = "schema_invalid_amount_range"
SCHEMA_INVALID_PRICE = "schema_invalid_price"

BUSINESS_QUOTE_STATUS_NOT_ACTIVE = "business_quote_status_not_active"
BUSINESS_LOW_CONFIDENCE_HOLD = "business_low_confidence_hold"
BUSINESS_PARTIAL_NORMALIZATION_HOLD = "business_partial_normalization_hold"
BUSINESS_AMBIGUOUS_RESTRICTION_HOLD = "business_ambiguous_restriction_hold"
BUSINESS_DUPLICATE_SKU_IN_MESSAGE_HOLD = "business_duplicate_sku_in_message_hold"

MESSAGE_NO_CANDIDATE_ROWS = "message_no_candidate_rows"
VALIDATION_MIXED_OUTCOME = "validation_mixed_outcome"

VALIDATOR_AUTO_PUBLISH_CONFIDENCE = 0.8
_NON_AMBIGUOUS_RESTRICTION_PARSE_STATUSES = frozenset({"empty", "parsed", "clear"})

SCHEMA_REASON_CODES = frozenset(
    {
        SCHEMA_MISSING_CARD_TYPE,
        SCHEMA_MISSING_COUNTRY_OR_CURRENCY,
        SCHEMA_MISSING_NORMALIZED_SKU_KEY,
        SCHEMA_MISSING_SOURCE_LINE,
        SCHEMA_INVALID_AMOUNT_RANGE,
        SCHEMA_INVALID_PRICE,
    }
)
BUSINESS_REASON_CODES = frozenset(
    {
        BUSINESS_QUOTE_STATUS_NOT_ACTIVE,
        BUSINESS_LOW_CONFIDENCE_HOLD,
        BUSINESS_PARTIAL_NORMALIZATION_HOLD,
        BUSINESS_AMBIGUOUS_RESTRICTION_HOLD,
        BUSINESS_DUPLICATE_SKU_IN_MESSAGE_HOLD,
    }
)
MESSAGE_REASON_CODES = frozenset({MESSAGE_NO_CANDIDATE_ROWS})
ALL_REASON_CODES = SCHEMA_REASON_CODES | BUSINESS_REASON_CODES | MESSAGE_REASON_CODES

_AMOUNT_RANGE_PATTERN = re.compile(
    r"^\d+(?:\.\d+)?(?:\s*-\s*\d+(?:\.\d+)?)?$"
)


def build_validation_reason(
    code: str,
    *,
    detail: str = "",
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"code": str(code)}
    if detail:
        payload["detail"] = str(detail)
    if context:
        payload["context"] = dict(context)
    return payload


def normalize_reason_payloads(
    payloads: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for payload in payloads or []:
        if not payload:
            continue
        code = str(payload.get("code") or "").strip()
        if not code:
            raise ValueError("validation reasons require a non-empty code")
        normalized_payload = {"code": code}
        detail = payload.get("detail")
        if detail not in (None, ""):
            normalized_payload["detail"] = str(detail)
        context = payload.get("context")
        if isinstance(context, dict) and context:
            normalized_payload["context"] = dict(context)
        normalized.extend([normalized_payload])
    return normalized


@dataclass(slots=True)
class QuoteValidationRowResult:
    quote_candidate_row_id: int
    row_ordinal: int
    schema_status: str
    business_status: str
    final_decision: str
    decision_basis: str
    rejection_reasons: list[dict[str, Any]] = field(default_factory=list)
    hold_reasons: list[dict[str, Any]] = field(default_factory=list)

    def to_row_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["rejection_reasons"] = normalize_reason_payloads(
            self.rejection_reasons
        )
        payload["hold_reasons"] = normalize_reason_payloads(self.hold_reasons)
        return payload


@dataclass(slots=True)
class QuoteValidationRun:
    quote_document_id: int
    validator_version: str
    run_kind: str
    message_decision: str
    validation_status: str
    candidate_row_count: int = 0
    publishable_row_count: int = 0
    rejected_row_count: int = 0
    held_row_count: int = 0
    summary: dict[str, Any] = field(default_factory=dict)
    row_results: list[QuoteValidationRowResult] = field(default_factory=list)

    def computed_counts(self) -> dict[str, int]:
        separated = separate_publishable_rows(self.row_results)
        return {
            "candidate_row_count": len(self.row_results),
            "publishable_row_count": len(separated["publishable_rows"]),
            "rejected_row_count": len(separated["rejected_rows"]),
            "held_row_count": len(separated["held_rows"]),
        }

    def to_run_payload(self) -> dict[str, Any]:
        counts = self.computed_counts()
        if self.row_results:
            if self.candidate_row_count not in (0, counts["candidate_row_count"]):
                raise ValueError("candidate_row_count does not match row results")
            if self.publishable_row_count not in (0, counts["publishable_row_count"]):
                raise ValueError("publishable_row_count does not match row results")
            if self.rejected_row_count not in (0, counts["rejected_row_count"]):
                raise ValueError("rejected_row_count does not match row results")
            if self.held_row_count not in (0, counts["held_row_count"]):
                raise ValueError("held_row_count does not match row results")
        else:
            counts["candidate_row_count"] = self.candidate_row_count
            counts["publishable_row_count"] = self.publishable_row_count
            counts["rejected_row_count"] = self.rejected_row_count
            counts["held_row_count"] = self.held_row_count
        return {
            "quote_document_id": self.quote_document_id,
            "validator_version": self.validator_version,
            "run_kind": self.run_kind,
            "message_decision": self.message_decision,
            "validation_status": self.validation_status,
            "candidate_row_count": counts["candidate_row_count"],
            "publishable_row_count": counts["publishable_row_count"],
            "rejected_row_count": counts["rejected_row_count"],
            "held_row_count": counts["held_row_count"],
            "summary": dict(self.summary),
        }


def separate_publishable_rows(
    row_results: list[QuoteValidationRowResult],
) -> dict[str, list[QuoteValidationRowResult]]:
    separated = {
        "publishable_rows": [],
        "rejected_rows": [],
        "held_rows": [],
    }
    for row_result in row_results:
        if row_result.final_decision == "publishable":
            separated["publishable_rows"].append(row_result)
        elif row_result.final_decision == "rejected":
            separated["rejected_rows"].append(row_result)
        elif row_result.final_decision == "held":
            separated["held_rows"].append(row_result)
    return separated


def validate_quote_candidate_document(
    *,
    quote_document_id: int,
    run_kind: str,
    candidate_rows: list[dict[str, Any] | Any],
    candidate_document: QuoteCandidateMessage | dict[str, Any] | None = None,
    validator_version: str = VALIDATOR_VERSION_V1,
) -> QuoteValidationRun:
    row_results: list[QuoteValidationRowResult] = []
    message_reasons: list[dict[str, Any]] = []
    rejection_code_counts: dict[str, int] = {}
    hold_code_counts: dict[str, int] = {}
    duplicate_sku_counts = _duplicate_normalized_sku_counts(candidate_rows)
    parser_advisory_counts = {
        "parser_publishable_true_count": 0,
        "parser_publishable_false_count": 0,
    }

    for row in candidate_rows:
        if _row_publishable_hint(row):
            parser_advisory_counts["parser_publishable_true_count"] += 1
        else:
            parser_advisory_counts["parser_publishable_false_count"] += 1
        schema_rejection_reasons = _schema_rejection_reasons(row)
        for reason in schema_rejection_reasons:
            code = str(reason.get("code") or "")
            rejection_code_counts[code] = rejection_code_counts.get(code, 0) + 1
        rejection_reasons = list(schema_rejection_reasons)
        hold_reasons: list[dict[str, Any]] = []
        business_status = "skipped"
        final_decision = "rejected" if schema_rejection_reasons else "publishable"
        decision_basis = "schema_validation"
        if not schema_rejection_reasons:
            rejection_reasons = _business_rejection_reasons(row)
            hold_reasons = _business_hold_reasons(
                row,
                duplicate_sku_counts=duplicate_sku_counts,
            )
            for reason in rejection_reasons:
                code = str(reason.get("code") or "")
                rejection_code_counts[code] = rejection_code_counts.get(code, 0) + 1
            for reason in hold_reasons:
                code = str(reason.get("code") or "")
                hold_code_counts[code] = hold_code_counts.get(code, 0) + 1
            business_status = "passed"
            final_decision = "publishable"
            decision_basis = "business_validation"
            if rejection_reasons:
                business_status = "failed"
                final_decision = "rejected"
            elif hold_reasons:
                business_status = "held"
                final_decision = "held"
        row_results.append(
            QuoteValidationRowResult(
                quote_candidate_row_id=int(_row_value(row, "id") or 0),
                row_ordinal=int(_row_value(row, "row_ordinal") or 0),
                schema_status="failed" if schema_rejection_reasons else "passed",
                business_status=business_status,
                final_decision=final_decision,
                decision_basis=decision_basis,
                rejection_reasons=rejection_reasons,
                hold_reasons=hold_reasons,
            )
        )

    if not candidate_rows:
        message_reasons.append(
            build_validation_reason(
                MESSAGE_NO_CANDIDATE_ROWS,
                detail="candidate document persisted with zero candidate rows",
                context=_message_reason_context(
                    quote_document_id=quote_document_id,
                    candidate_document=candidate_document,
                ),
            )
        )

    separated_rows = separate_publishable_rows(row_results)
    publishable_rows = len(separated_rows["publishable_rows"])
    rejected_rows = len(separated_rows["rejected_rows"])
    held_rows = len(separated_rows["held_rows"])
    message_decision = "no_publish"
    if publishable_rows > 0 and (rejected_rows > 0 or held_rows > 0):
        message_decision = "mixed_outcome"
        message_reasons.append(
            build_validation_reason(
                VALIDATION_MIXED_OUTCOME,
                detail="publishable rows exist but the same message still contains held/rejected rows",
                context={
                    "publishable_row_count": publishable_rows,
                    "rejected_row_count": rejected_rows,
                    "held_row_count": held_rows,
                },
            )
        )
    elif publishable_rows > 0:
        message_decision = "publishable_rows_available"

    summary: dict[str, Any] = {
        "message_reasons": normalize_reason_payloads(message_reasons),
        "row_decision_counts": {
            "publishable": publishable_rows,
            "rejected": rejected_rows,
            "held": held_rows,
        },
        "row_rejection_code_counts": rejection_code_counts,
        "row_hold_code_counts": hold_code_counts,
        "parser_advisory_counts": dict(parser_advisory_counts),
        "candidate_parse_status": _candidate_document_value(
            candidate_document,
            "parse_status",
        ),
        "candidate_rejection_reasons": _candidate_document_value(
            candidate_document,
            "rejection_reasons",
            default=[],
        ),
    }
    if candidate_document is not None:
        summary["message_id"] = _candidate_document_value(
            candidate_document,
            "message_id",
        )

    return QuoteValidationRun(
        quote_document_id=quote_document_id,
        validator_version=validator_version,
        run_kind=str(run_kind or "runtime"),
        message_decision=message_decision,
        validation_status="completed",
        candidate_row_count=len(candidate_rows),
        publishable_row_count=publishable_rows,
        rejected_row_count=rejected_rows,
        held_row_count=held_rows,
        summary=summary,
        row_results=row_results,
    )


def _schema_rejection_reasons(row: dict[str, Any] | Any) -> list[dict[str, Any]]:
    reasons: list[dict[str, Any]] = []
    if not _normalized_text(_row_value(row, "card_type")):
        reasons.append(
            build_validation_reason(
                SCHEMA_MISSING_CARD_TYPE,
                detail="candidate row requires card_type",
            )
        )
    if not _normalized_text(_row_value(row, "country_or_currency")):
        reasons.append(
            build_validation_reason(
                SCHEMA_MISSING_COUNTRY_OR_CURRENCY,
                detail="candidate row requires country_or_currency",
            )
        )
    if not _normalized_text(_row_value(row, "normalized_sku_key")):
        reasons.append(
            build_validation_reason(
                SCHEMA_MISSING_NORMALIZED_SKU_KEY,
                detail="candidate row requires normalized_sku_key",
            )
        )
    if not _normalized_text(_row_value(row, "source_line")):
        reasons.append(
            build_validation_reason(
                SCHEMA_MISSING_SOURCE_LINE,
                detail="candidate row requires source_line evidence",
            )
        )
    if not _is_valid_amount_range(_row_value(row, "amount_range")):
        reasons.append(
            build_validation_reason(
                SCHEMA_INVALID_AMOUNT_RANGE,
                detail="candidate row amount_range must be normalized",
                context={"amount_range": str(_row_value(row, "amount_range") or "")},
            )
        )
    if not _is_positive_numeric(_row_value(row, "price")):
        reasons.append(
            build_validation_reason(
                SCHEMA_INVALID_PRICE,
                detail="candidate row price must be a positive number",
                context={"price": _row_value(row, "price")},
            )
        )
    return reasons


def _business_rejection_reasons(row: dict[str, Any] | Any) -> list[dict[str, Any]]:
    if _normalized_text(_row_value(row, "quote_status")).lower() == "active":
        return []
    return [
        build_validation_reason(
            BUSINESS_QUOTE_STATUS_NOT_ACTIVE,
            detail="candidate row quote_status must be active for publication",
            context={"quote_status": _normalized_text(_row_value(row, "quote_status"))},
        )
    ]


def _business_hold_reasons(
    row: dict[str, Any] | Any,
    *,
    duplicate_sku_counts: dict[str, int],
) -> list[dict[str, Any]]:
    reasons: list[dict[str, Any]] = []
    line_confidence = _numeric_value(_row_value(row, "line_confidence"))
    if line_confidence < VALIDATOR_AUTO_PUBLISH_CONFIDENCE:
        reasons.append(
            build_validation_reason(
                BUSINESS_LOW_CONFIDENCE_HOLD,
                detail="candidate row confidence is below validator publish threshold",
                context={
                    "line_confidence": line_confidence,
                    "required_confidence": VALIDATOR_AUTO_PUBLISH_CONFIDENCE,
                },
            )
        )
    normalization_status = _normalized_text(_row_value(row, "normalization_status")).lower()
    if normalization_status != "normalized":
        reasons.append(
            build_validation_reason(
                BUSINESS_PARTIAL_NORMALIZATION_HOLD,
                detail="candidate row normalization is not complete enough to publish",
                context={
                    "normalization_status": _normalized_text(
                        _row_value(row, "normalization_status")
                    )
                },
            )
        )
    restriction_parse_status = _normalized_text(
        _row_value(row, "restriction_parse_status")
    ).lower()
    if restriction_parse_status not in _NON_AMBIGUOUS_RESTRICTION_PARSE_STATUSES:
        reasons.append(
            build_validation_reason(
                BUSINESS_AMBIGUOUS_RESTRICTION_HOLD,
                detail="candidate row restriction parsing is ambiguous",
                context={
                    "restriction_parse_status": _normalized_text(
                        _row_value(row, "restriction_parse_status")
                    )
                },
            )
        )
    normalized_sku_key = _normalized_text(_row_value(row, "normalized_sku_key"))
    if normalized_sku_key and duplicate_sku_counts.get(normalized_sku_key, 0) > 1:
        reasons.append(
            build_validation_reason(
                BUSINESS_DUPLICATE_SKU_IN_MESSAGE_HOLD,
                detail="candidate row duplicates another normalized_sku_key in the same message",
                context={"normalized_sku_key": normalized_sku_key},
            )
        )
    return reasons


def _duplicate_normalized_sku_counts(
    candidate_rows: list[dict[str, Any] | Any],
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in candidate_rows:
        normalized_sku_key = _normalized_text(_row_value(row, "normalized_sku_key"))
        if normalized_sku_key:
            counts[normalized_sku_key] = counts.get(normalized_sku_key, 0) + 1
    return counts


def _normalized_text(value: Any) -> str:
    return str(value or "").strip()


def _is_valid_amount_range(value: Any) -> bool:
    normalized = _normalized_text(value)
    if not normalized:
        return False
    if normalized == "不限":
        return True
    return bool(_AMOUNT_RANGE_PATTERN.fullmatch(normalized))


def _is_positive_numeric(value: Any) -> bool:
    try:
        return float(value) > 0.0
    except (TypeError, ValueError):
        return False


def _numeric_value(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _row_publishable_hint(row: dict[str, Any] | Any) -> bool:
    value = _row_value(row, "row_publishable")
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes"}


def _candidate_document_value(
    candidate_document: QuoteCandidateMessage | dict[str, Any] | None,
    key: str,
    *,
    default: Any = "",
) -> Any:
    if candidate_document is None:
        return default
    if isinstance(candidate_document, dict):
        return candidate_document.get(key, default)
    return getattr(candidate_document, key, default)


def _row_value(row: dict[str, Any] | Any, key: str, default: Any = None) -> Any:
    if isinstance(row, dict):
        return row.get(key, default)
    if hasattr(row, "keys") and key in row.keys():
        return row[key]
    return getattr(row, key, default)


def _message_reason_context(
    *,
    quote_document_id: int,
    candidate_document: QuoteCandidateMessage | dict[str, Any] | None,
) -> dict[str, Any]:
    context = {"quote_document_id": int(quote_document_id)}
    parse_status = _candidate_document_value(candidate_document, "parse_status")
    if str(parse_status or "").strip():
        context["parse_status"] = str(parse_status)
    return context
