from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class QuoteFactPublishResult:
    status: str
    quote_document_id: int
    validation_run_id: int
    source_group_key: str
    publish_mode: str
    attempted_row_count: int
    applied_row_count: int
    reason: str = ""

    @classmethod
    def no_op(
        cls,
        *,
        quote_document_id: int,
        validation_run_id: int,
        source_group_key: str,
        publish_mode: str,
        reason: str,
        attempted_row_count: int,
    ) -> "QuoteFactPublishResult":
        return cls(
            status="no_op",
            quote_document_id=quote_document_id,
            validation_run_id=validation_run_id,
            source_group_key=source_group_key,
            publish_mode=publish_mode,
            attempted_row_count=attempted_row_count,
            applied_row_count=0,
            reason=reason,
        )

    @classmethod
    def applied(
        cls,
        *,
        quote_document_id: int,
        validation_run_id: int,
        source_group_key: str,
        publish_mode: str,
        attempted_row_count: int,
        applied_row_count: int,
    ) -> "QuoteFactPublishResult":
        return cls(
            status="applied",
            quote_document_id=quote_document_id,
            validation_run_id=validation_run_id,
            source_group_key=source_group_key,
            publish_mode=publish_mode,
            attempted_row_count=attempted_row_count,
            applied_row_count=applied_row_count,
            reason="applied",
        )

    @classmethod
    def failed(
        cls,
        *,
        quote_document_id: int,
        validation_run_id: int,
        source_group_key: str,
        publish_mode: str,
        attempted_row_count: int,
        reason: str,
    ) -> "QuoteFactPublishResult":
        return cls(
            status="failed",
            quote_document_id=quote_document_id,
            validation_run_id=validation_run_id,
            source_group_key=source_group_key,
            publish_mode=publish_mode,
            attempted_row_count=attempted_row_count,
            applied_row_count=0,
            reason=reason,
        )


class QuoteFactPublisher:
    VALIDATION_ONLY_MODE = "validation_only"
    REPLACE_GROUP_ACTIVE_ROWS_MODE = "replace_group_active_rows"

    def __init__(self, db) -> None:
        self.db = db

    def publish_quote_document(
        self,
        *,
        quote_document_id: int,
        validation_run_id: int,
        source_group_key: str,
        platform: str,
        chat_id: str,
        chat_name: str,
        message_id: str,
        source_name: str,
        sender_id: str,
        raw_text: str,
        message_time: str,
        parser_template: str,
        parser_version: str,
        publishable_rows: list[dict[str, Any]],
        publish_mode: str,
    ) -> QuoteFactPublishResult:
        attempted_row_count = len(publishable_rows)
        if publish_mode == self.VALIDATION_ONLY_MODE:
            return QuoteFactPublishResult.no_op(
                quote_document_id=quote_document_id,
                validation_run_id=validation_run_id,
                source_group_key=source_group_key,
                publish_mode=publish_mode,
                reason="runtime_validation_only",
                attempted_row_count=attempted_row_count,
            )
        if not publishable_rows:
            return QuoteFactPublishResult.no_op(
                quote_document_id=quote_document_id,
                validation_run_id=validation_run_id,
                source_group_key=source_group_key,
                publish_mode=publish_mode,
                reason="no_publishable_rows",
                attempted_row_count=0,
            )
        if publish_mode != self.REPLACE_GROUP_ACTIVE_ROWS_MODE:
            return QuoteFactPublishResult.failed(
                quote_document_id=quote_document_id,
                validation_run_id=validation_run_id,
                source_group_key=source_group_key,
                publish_mode=publish_mode,
                attempted_row_count=attempted_row_count,
                reason=f"unsupported_publish_mode:{publish_mode}",
            )

        try:
            with self.db.conn.transaction():
                self.db.deactivate_old_quotes_for_group(
                    source_group_key=source_group_key,
                    commit=False,
                )
                for row in publishable_rows:
                    self.db.upsert_quote_price_row_with_history(
                        quote_document_id=quote_document_id,
                        message_id=message_id,
                        platform=platform,
                        source_group_key=source_group_key,
                        chat_id=chat_id,
                        chat_name=chat_name,
                        source_name=source_name,
                        sender_id=sender_id,
                        card_type=str(row.get("card_type") or ""),
                        country_or_currency=str(
                            row.get("country_or_currency") or ""
                        ),
                        amount_range=str(row.get("amount_range") or ""),
                        multiplier=row.get("multiplier"),
                        form_factor=str(row.get("form_factor") or ""),
                        price=float(row.get("price") or 0.0),
                        quote_status=str(row.get("quote_status") or "active"),
                        restriction_text=str(row.get("restriction_text") or ""),
                        source_line=str(row.get("source_line") or ""),
                        raw_text=raw_text,
                        message_time=message_time,
                        effective_at=message_time,
                        expires_at=None,
                        parser_template=parser_template,
                        parser_version=parser_version,
                        confidence=float(row.get("line_confidence") or 0.0),
                        commit=False,
                    )
        except Exception as exc:
            return QuoteFactPublishResult.failed(
                quote_document_id=quote_document_id,
                validation_run_id=validation_run_id,
                source_group_key=source_group_key,
                publish_mode=publish_mode,
                attempted_row_count=attempted_row_count,
                reason=str(exc),
            )

        return QuoteFactPublishResult.applied(
            quote_document_id=quote_document_id,
            validation_run_id=validation_run_id,
            source_group_key=source_group_key,
            publish_mode=publish_mode,
            attempted_row_count=attempted_row_count,
            applied_row_count=attempted_row_count,
        )
