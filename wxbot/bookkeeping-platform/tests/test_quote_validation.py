from __future__ import annotations

import unittest

from bookkeeping_core.quote_candidates import QuoteCandidateMessage
from bookkeeping_core.quote_validation import (
    MESSAGE_NO_CANDIDATE_ROWS,
    SCHEMA_INVALID_AMOUNT_RANGE,
    SCHEMA_INVALID_PRICE,
    SCHEMA_MISSING_CARD_TYPE,
    SCHEMA_MISSING_NORMALIZED_SKU_KEY,
    SCHEMA_MISSING_SOURCE_LINE,
    validate_quote_candidate_document,
)


class QuoteValidationTests(unittest.TestCase):
    def test_validate_quote_candidate_document_rejects_schema_failures(self) -> None:
        validation_run = validate_quote_candidate_document(
            quote_document_id=42,
            run_kind="runtime",
            candidate_rows=[
                {
                    "id": 7,
                    "row_ordinal": 1,
                    "card_type": "",
                    "country_or_currency": "USD",
                    "normalized_sku_key": " ",
                    "source_line": "",
                    "amount_range": "bad-range",
                    "price": 0,
                }
            ],
        )

        self.assertEqual(validation_run.message_decision, "no_publish")
        self.assertEqual(validation_run.candidate_row_count, 1)
        self.assertEqual(validation_run.publishable_row_count, 0)
        self.assertEqual(validation_run.rejected_row_count, 1)
        self.assertEqual(len(validation_run.row_results), 1)

        row_result = validation_run.row_results[0]
        self.assertEqual(row_result.schema_status, "failed")
        self.assertEqual(row_result.business_status, "skipped")
        self.assertEqual(row_result.final_decision, "rejected")
        self.assertEqual(row_result.decision_basis, "schema_validation")
        rejection_codes = {reason["code"] for reason in row_result.rejection_reasons}
        self.assertEqual(
            rejection_codes,
            {
                SCHEMA_MISSING_CARD_TYPE,
                SCHEMA_MISSING_NORMALIZED_SKU_KEY,
                SCHEMA_MISSING_SOURCE_LINE,
                SCHEMA_INVALID_AMOUNT_RANGE,
                SCHEMA_INVALID_PRICE,
            },
        )

    def test_validate_quote_candidate_document_marks_schema_passing_rows_publishable(
        self,
    ) -> None:
        validation_run = validate_quote_candidate_document(
            quote_document_id=43,
            run_kind="replay",
            candidate_rows=[
                {
                    "id": 8,
                    "row_ordinal": 1,
                    "card_type": "Apple",
                    "country_or_currency": "USD",
                    "normalized_sku_key": "Apple|USD|100|横白卡",
                    "source_line": "US=5.10",
                    "amount_range": "100",
                    "price": 5.10,
                }
            ],
        )

        self.assertEqual(validation_run.run_kind, "replay")
        self.assertEqual(validation_run.message_decision, "publishable_rows_available")
        self.assertEqual(validation_run.publishable_row_count, 1)
        self.assertEqual(validation_run.rejected_row_count, 0)
        row_result = validation_run.row_results[0]
        self.assertEqual(row_result.schema_status, "passed")
        self.assertEqual(row_result.business_status, "not_evaluated")
        self.assertEqual(row_result.final_decision, "publishable")
        self.assertEqual(row_result.rejection_reasons, [])

    def test_validate_quote_candidate_document_returns_explicit_no_publish_for_zero_rows(
        self,
    ) -> None:
        candidate_document = QuoteCandidateMessage(
            platform="wechat",
            source_group_key="wechat:g-zero",
            chat_id="g-zero",
            chat_name="Zero Rows",
            message_id="msg-zero",
            source_name="报价员",
            sender_id="u-zero",
            sender_display="报价员",
            raw_message="【Apple】",
            message_time="2026-04-14 12:00:00",
            parser_kind="group-parser",
            parser_template="group-parser",
            parser_version="group-parser-v1",
            confidence=0.0,
            parse_status="empty",
            message_fingerprint="fingerprint-zero",
            snapshot_hypothesis="unresolved",
            snapshot_hypothesis_reason="phase1-default",
            rejection_reasons=[{"reason": "missing_group_template"}],
            rows=[],
        )

        validation_run = validate_quote_candidate_document(
            quote_document_id=44,
            run_kind="runtime",
            candidate_rows=[],
            candidate_document=candidate_document,
        )

        self.assertEqual(validation_run.message_decision, "no_publish")
        self.assertEqual(validation_run.validation_status, "completed")
        self.assertEqual(validation_run.candidate_row_count, 0)
        self.assertEqual(validation_run.publishable_row_count, 0)
        self.assertEqual(validation_run.rejected_row_count, 0)
        self.assertEqual(validation_run.held_row_count, 0)
        self.assertEqual(validation_run.row_results, [])
        self.assertEqual(
            validation_run.summary["message_reasons"][0]["code"],
            MESSAGE_NO_CANDIDATE_ROWS,
        )
        self.assertEqual(validation_run.summary["candidate_parse_status"], "empty")
        self.assertEqual(validation_run.summary["message_id"], "msg-zero")


if __name__ == "__main__":
    unittest.main()
