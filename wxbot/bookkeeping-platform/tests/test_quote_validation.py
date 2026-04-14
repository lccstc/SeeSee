from __future__ import annotations

import unittest

from bookkeeping_core.quote_candidates import QuoteCandidateMessage
from bookkeeping_core.quote_validation import (
    BUSINESS_AMBIGUOUS_RESTRICTION_HOLD,
    BUSINESS_DUPLICATE_SKU_IN_MESSAGE_HOLD,
    BUSINESS_LOW_CONFIDENCE_HOLD,
    BUSINESS_PARTIAL_NORMALIZATION_HOLD,
    BUSINESS_QUOTE_STATUS_NOT_ACTIVE,
    MESSAGE_NO_CANDIDATE_ROWS,
    SCHEMA_INVALID_AMOUNT_RANGE,
    SCHEMA_INVALID_PRICE,
    SCHEMA_MISSING_CARD_TYPE,
    SCHEMA_MISSING_NORMALIZED_SKU_KEY,
    SCHEMA_MISSING_SOURCE_LINE,
    separate_publishable_rows,
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
                    "quote_status": "inactive",
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
                    "line_confidence": 0.98,
                    "normalization_status": "normalized",
                    "restriction_parse_status": "parsed",
                    "quote_status": "active",
                    "row_publishable": False,
                }
            ],
        )

        self.assertEqual(validation_run.run_kind, "replay")
        self.assertEqual(validation_run.message_decision, "publishable_rows_available")
        self.assertEqual(validation_run.publishable_row_count, 1)
        self.assertEqual(validation_run.rejected_row_count, 0)
        row_result = validation_run.row_results[0]
        self.assertEqual(row_result.schema_status, "passed")
        self.assertEqual(row_result.business_status, "passed")
        self.assertEqual(row_result.final_decision, "publishable")
        self.assertEqual(row_result.decision_basis, "business_validation")
        self.assertEqual(row_result.rejection_reasons, [])
        self.assertEqual(row_result.hold_reasons, [])

    def test_validate_quote_candidate_document_supports_publishable_rejected_and_held_rows(
        self,
    ) -> None:
        validation_run = validate_quote_candidate_document(
            quote_document_id=45,
            run_kind="runtime",
            candidate_rows=[
                {
                    "id": 101,
                    "row_ordinal": 1,
                    "card_type": "Apple",
                    "country_or_currency": "USD",
                    "normalized_sku_key": "Apple|USD|100|横白卡",
                    "source_line": "US=5.10",
                    "amount_range": "100",
                    "price": 5.10,
                    "line_confidence": 0.98,
                    "normalization_status": "normalized",
                    "restriction_parse_status": "parsed",
                    "quote_status": "active",
                    "row_publishable": False,
                },
                {
                    "id": 102,
                    "row_ordinal": 2,
                    "card_type": "Apple",
                    "country_or_currency": "GBP",
                    "normalized_sku_key": "Apple|GBP|100|横白卡",
                    "source_line": "UK=6.20",
                    "amount_range": "100",
                    "price": 6.20,
                    "line_confidence": 0.61,
                    "normalization_status": "normalized",
                    "restriction_parse_status": "parsed",
                    "quote_status": "active",
                    "row_publishable": True,
                },
                {
                    "id": 103,
                    "row_ordinal": 3,
                    "card_type": "Steam",
                    "country_or_currency": "USD",
                    "normalized_sku_key": "Steam|USD|50|不限",
                    "source_line": "Steam 50=4.10",
                    "amount_range": "50",
                    "price": 4.10,
                    "line_confidence": 0.97,
                    "normalization_status": "partial",
                    "restriction_parse_status": "parsed",
                    "quote_status": "active",
                    "row_publishable": True,
                },
                {
                    "id": 104,
                    "row_ordinal": 4,
                    "card_type": "Razer",
                    "country_or_currency": "USD",
                    "normalized_sku_key": "Razer|USD|100|不限",
                    "source_line": "Razer 100=7.10",
                    "amount_range": "100",
                    "price": 7.10,
                    "line_confidence": 0.99,
                    "normalization_status": "normalized",
                    "restriction_parse_status": "parsed",
                    "quote_status": "inactive",
                    "row_publishable": True,
                },
                {
                    "id": 105,
                    "row_ordinal": 5,
                    "card_type": "Apple",
                    "country_or_currency": "EUR",
                    "normalized_sku_key": "Apple|EUR|100|横白卡",
                    "source_line": "EU=5.55 使用时间待确认",
                    "amount_range": "100",
                    "price": 5.55,
                    "line_confidence": 0.95,
                    "normalization_status": "normalized",
                    "restriction_parse_status": "ambiguous",
                    "quote_status": "active",
                    "row_publishable": True,
                },
            ],
        )

        self.assertEqual(validation_run.message_decision, "mixed_outcome")
        self.assertEqual(validation_run.candidate_row_count, 5)
        self.assertEqual(validation_run.publishable_row_count, 1)
        self.assertEqual(validation_run.rejected_row_count, 1)
        self.assertEqual(validation_run.held_row_count, 3)
        self.assertEqual(
            validation_run.summary["message_reasons"][0]["code"],
            "validation_mixed_outcome",
        )

        separated = separate_publishable_rows(validation_run.row_results)
        self.assertEqual(len(separated["publishable_rows"]), 1)
        self.assertEqual(len(separated["rejected_rows"]), 1)
        self.assertEqual(len(separated["held_rows"]), 3)

        row_results = {
            row_result.row_ordinal: row_result for row_result in validation_run.row_results
        }
        self.assertEqual(row_results[1].final_decision, "publishable")
        self.assertEqual(row_results[1].rejection_reasons, [])
        self.assertEqual(row_results[1].hold_reasons, [])

        self.assertEqual(row_results[2].final_decision, "held")
        self.assertEqual(
            row_results[2].hold_reasons[0]["code"],
            BUSINESS_LOW_CONFIDENCE_HOLD,
        )

        self.assertEqual(row_results[3].final_decision, "held")
        self.assertEqual(
            row_results[3].hold_reasons[0]["code"],
            BUSINESS_PARTIAL_NORMALIZATION_HOLD,
        )

        self.assertEqual(row_results[4].final_decision, "rejected")
        self.assertEqual(
            row_results[4].rejection_reasons[0]["code"],
            BUSINESS_QUOTE_STATUS_NOT_ACTIVE,
        )

        self.assertEqual(row_results[5].final_decision, "held")
        self.assertEqual(
            row_results[5].hold_reasons[0]["code"],
            BUSINESS_AMBIGUOUS_RESTRICTION_HOLD,
        )

        self.assertEqual(
            validation_run.summary["parser_advisory_counts"]["parser_publishable_false_count"],
            1,
        )
        self.assertEqual(
            validation_run.summary["row_decision_counts"],
            {"publishable": 1, "rejected": 1, "held": 3},
        )

    def test_validate_quote_candidate_document_holds_duplicate_normalized_skus(
        self,
    ) -> None:
        validation_run = validate_quote_candidate_document(
            quote_document_id=46,
            run_kind="runtime",
            candidate_rows=[
                {
                    "id": 201,
                    "row_ordinal": 1,
                    "card_type": "Apple",
                    "country_or_currency": "USD",
                    "normalized_sku_key": "Apple|USD|100|横白卡",
                    "source_line": "US=5.10",
                    "amount_range": "100",
                    "price": 5.10,
                    "line_confidence": 0.98,
                    "normalization_status": "normalized",
                    "restriction_parse_status": "parsed",
                    "quote_status": "active",
                    "row_publishable": True,
                },
                {
                    "id": 202,
                    "row_ordinal": 2,
                    "card_type": "Apple",
                    "country_or_currency": "USD",
                    "normalized_sku_key": "Apple|USD|100|横白卡",
                    "source_line": "US=5.20",
                    "amount_range": "100",
                    "price": 5.20,
                    "line_confidence": 0.99,
                    "normalization_status": "normalized",
                    "restriction_parse_status": "clear",
                    "quote_status": "active",
                    "row_publishable": True,
                },
            ],
        )

        self.assertEqual(validation_run.message_decision, "no_publish")
        self.assertEqual(validation_run.publishable_row_count, 0)
        self.assertEqual(validation_run.rejected_row_count, 0)
        self.assertEqual(validation_run.held_row_count, 2)
        self.assertEqual(
            validation_run.summary["row_hold_code_counts"][
                BUSINESS_DUPLICATE_SKU_IN_MESSAGE_HOLD
            ],
            2,
        )
        for row_result in validation_run.row_results:
            self.assertEqual(row_result.final_decision, "held")
            self.assertEqual(
                row_result.hold_reasons[0]["code"],
                BUSINESS_DUPLICATE_SKU_IN_MESSAGE_HOLD,
            )

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
