from __future__ import annotations

import unittest

from bookkeeping_core.quotes import ParsedQuoteRow, _parsed_quote_row_to_candidate_row
from bookkeeping_core.template_engine import analyze_scoped_quote_lines
from tests.support.quote_exception_corpus import load_gold_samples


def _fixture(name: str) -> dict:
    for item in load_gold_samples():
        if item["fixture_name"] == name:
            return item
    raise KeyError(name)


class TestQuoteParserScopeEvidence(unittest.TestCase):
    def test_scope_evidence_is_persisted_for_scoped_numeric_rows(self):
        fixture = _fixture("feihong_us_vip_delta_242")
        analyses = analyze_scoped_quote_lines(
            fixture["raw_text"],
            default_card_type="Apple iTunes",
            default_country_or_currency="USD",
            default_form_factor="white_card",
        )
        scoped = next(item for item in analyses if item["source_line"] == "50=5.25")
        candidate = scoped["candidate"]

        parsed_row = ParsedQuoteRow(
            source_group_key="wechat:test",
            platform="wechat",
            chat_id=fixture["chat_id"],
            chat_name=fixture["chat_name"],
            message_id="fixture-242",
            source_name="fixture",
            sender_id="fixture",
            card_type=candidate["card_type"],
            country_or_currency=candidate["country_or_currency"],
            amount_range=candidate["amount_range"],
            multiplier=None,
            form_factor=candidate["form_factor"],
            price=candidate["price"],
            quote_status="active",
            restriction_text="",
            source_line=scoped["source_line"],
            raw_text=fixture["raw_text"],
            message_time="2026-04-14 00:00:00",
            effective_at="2026-04-14 00:00:00",
            expires_at=None,
            parser_template="group-parser",
            parser_version="quote-v1",
            confidence=0.9,
            scope_header_text=candidate["scope_evidence"]["header_text"],
            scope_header_line_index=candidate["scope_evidence"]["header_line_index"],
            inherited_fields=tuple(candidate["scope_evidence"]["inherited_fields"]),
        )
        row = _parsed_quote_row_to_candidate_row(parsed_row, row_ordinal=1)
        self.assertIn("scope_evidence", row.field_sources)
        self.assertEqual(row.field_sources["scope_evidence"]["header_text"], "#US凑卡网单 【5- 15分钟】")
        self.assertEqual(
            row.field_sources["scope_evidence"]["inherited_fields"],
            ["card_type", "country_or_currency", "form_factor"],
        )

    def test_shorthand_xbox_line_produces_candidate_row(self):
        fixture = _fixture("wannuo_xbox_shorthand_174")
        analyses = analyze_scoped_quote_lines(
            fixture["raw_text"],
            default_country_or_currency="USD",
            default_form_factor="card_or_code",
        )
        shorthand = next(item for item in analyses if item["line_type"] == "quote")
        candidate = shorthand["candidate"]
        self.assertEqual(candidate["card_type"], "Xbox")
        self.assertEqual(candidate["amount_range"], "100")
        self.assertEqual(candidate["price"], 5.13)

    def test_token_noise_does_not_create_candidates(self):
        fixture = _fixture("qingsong_noise_token_177")
        analyses = analyze_scoped_quote_lines(fixture["raw_text"])
        self.assertTrue(all(item["line_type"] == "noise" for item in analyses))
        self.assertTrue(all("candidate" not in item for item in analyses))
