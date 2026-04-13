from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


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
        counts = {
            "candidate_row_count": len(self.row_results),
            "publishable_row_count": 0,
            "rejected_row_count": 0,
            "held_row_count": 0,
        }
        for row in self.row_results:
            if row.final_decision == "publishable":
                counts["publishable_row_count"] += 1
            elif row.final_decision == "rejected":
                counts["rejected_row_count"] += 1
            elif row.final_decision == "held":
                counts["held_row_count"] += 1
        return counts

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
