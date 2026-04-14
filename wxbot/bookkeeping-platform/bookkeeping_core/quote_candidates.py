from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


def resolve_candidate_sender_display(*, source_name: str, sender_display: str) -> str:
    """Phase 1 stores explicit sender-display evidence via the existing source-name path."""
    # Brownfield adapters only provide one display-name source today, so sender_display
    # must be carried explicitly but still comes from source_name until the adapters emit
    # a distinct sender label. EVID-01 should never depend on an implied mapping.
    return str(sender_display or source_name or "")


@dataclass(slots=True)
class QuoteCandidateRow:
    row_ordinal: int
    source_line: str
    source_line_index: int | None
    line_confidence: float
    normalized_sku_key: str
    normalization_status: str
    row_publishable: bool
    publishability_basis: str
    restriction_parse_status: str
    card_type: str | None
    country_or_currency: str | None
    amount_range: str | None
    multiplier: str | None
    form_factor: str | None
    price: float | None
    quote_status: str
    restriction_text: str
    field_sources: dict[str, Any] = field(default_factory=dict)
    rejection_reasons: list[dict[str, Any]] = field(default_factory=list)
    parser_template: str = ""
    parser_version: str = ""

    def to_row_payload(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class QuoteCandidateMessage:
    platform: str
    source_group_key: str
    chat_id: str
    chat_name: str
    message_id: str
    source_name: str
    sender_id: str
    sender_display: str
    raw_message: str
    message_time: str
    parser_kind: str
    parser_template: str
    parser_version: str
    confidence: float
    parse_status: str
    message_fingerprint: str
    snapshot_hypothesis: str
    snapshot_hypothesis_reason: str
    snapshot_hypothesis_evidence: dict[str, Any] = field(default_factory=dict)
    rejection_reasons: list[dict[str, Any]] = field(default_factory=list)
    run_kind: str = "runtime"
    replay_of_quote_document_id: int | None = None
    rows: list[QuoteCandidateRow] = field(default_factory=list)

    def to_document_payload(self) -> dict[str, Any]:
        return {
            "platform": self.platform,
            "source_group_key": self.source_group_key,
            "chat_id": self.chat_id,
            "chat_name": self.chat_name,
            "message_id": self.message_id,
            "source_name": self.source_name,
            "sender_id": self.sender_id,
            "sender_display": resolve_candidate_sender_display(
                source_name=self.source_name,
                sender_display=self.sender_display,
            ),
            "raw_message": self.raw_message,
            "message_time": self.message_time,
            "parser_kind": self.parser_kind,
            "parser_template": self.parser_template,
            "parser_version": self.parser_version,
            "confidence": self.confidence,
            "parse_status": self.parse_status,
            "message_fingerprint": self.message_fingerprint,
            "snapshot_hypothesis": self.snapshot_hypothesis,
            "snapshot_hypothesis_reason": self.snapshot_hypothesis_reason,
            "snapshot_hypothesis_evidence": dict(
                self.snapshot_hypothesis_evidence
            ),
            "rejection_reasons": list(self.rejection_reasons),
            "run_kind": self.run_kind,
            "replay_of_quote_document_id": self.replay_of_quote_document_id,
        }

    def to_row_payloads(self) -> list[dict[str, Any]]:
        return [row.to_row_payload() for row in self.rows]
