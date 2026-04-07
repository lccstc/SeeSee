from __future__ import annotations

import unittest

from bookkeeping_core.quotes import parse_quote_document


def _parse(text: str):
    return _parse_with_chat_name(text, chat_name="报价群")


def _parse_with_chat_name(text: str, *, chat_name: str):
    return parse_quote_document(
        platform="wechat",
        chat_id="g-parser",
        chat_name=chat_name,
        message_id="quote-parser-1",
        source_name="客人",
        sender_id="u-parser",
        source_group_key="wechat:g-parser",
        raw_text=text,
        message_time="2026-04-08 10:00:00",
    )


class QuoteParserTests(unittest.TestCase):
    def test_contextless_short_quote_stays_exception_only(self) -> None:
        document = _parse("uk 10\n6.25")

        self.assertEqual(document.rows, [])
        self.assertEqual(document.parse_status, "exception")
        self.assertGreaterEqual(len(document.exceptions), 1)
        self.assertTrue(
            all(item.reason == "missing_context" for item in document.exceptions)
        )

    def test_complete_single_quote_parses_card_country_amount_and_price(self) -> None:
        document = _parse("Mexico apple card 200 0.265")

        self.assertEqual(len(document.rows), 1)
        row = document.rows[0]
        self.assertEqual(row.card_type, "Apple")
        self.assertEqual(row.country_or_currency, "MXN")
        self.assertEqual(row.amount_range, "200")
        self.assertEqual(row.price, 0.265)

    def test_section_quote_parses_condition_rows(self) -> None:
        document = _parse(
            """【Xbox】#非5倍数问 #批量先问！
US：10~250/5倍数图密=5.0
UK卡图/纸质=6.2 （电子/代码6.15）
"""
        )

        rows = {
            (row.card_type, row.country_or_currency, row.form_factor): row
            for row in document.rows
        }
        self.assertEqual(rows[("Xbox", "USD", "图密")].amount_range, "10-250")
        self.assertEqual(rows[("Xbox", "USD", "图密")].price, 5.0)
        self.assertEqual(rows[("Xbox", "GBP", "卡图/纸质")].price, 6.2)
        self.assertEqual(rows[("Xbox", "GBP", "电子/代码")].price, 6.15)

    def test_same_line_country_price_pairs_are_split(self) -> None:
        document = _parse(
            """【Steam 蒸汽】
USD美元=5.1        EUR欧元=5.88
AUD澳元=3.48      CAD加元=3.62
"""
        )

        prices = {
            (row.card_type, row.country_or_currency): row.price
            for row in document.rows
        }
        self.assertEqual(prices[("Steam", "USD")], 5.1)
        self.assertEqual(prices[("Steam", "EUR")], 5.88)
        self.assertEqual(prices[("Steam", "AUD")], 3.48)
        self.assertEqual(prices[("Steam", "CAD")], 3.62)

    def test_chat_name_can_provide_group_default_card_type(self) -> None:
        document = _parse_with_chat_name(
            "US横白卡：100-150=5.45（50倍数）",
            chat_name="客人1 Apple报价群",
        )

        self.assertEqual(len(document.rows), 1)
        row = document.rows[0]
        self.assertEqual(row.card_type, "Apple")
        self.assertEqual(row.country_or_currency, "USD")
        self.assertEqual(row.amount_range, "100-150")
        self.assertEqual(row.multiplier, "50X")
        self.assertEqual(row.form_factor, "横白卡")
        self.assertEqual(row.price, 5.45)
        self.assertEqual(document.parser_template, "apple_modifier_sheet")

    def test_modifier_lines_create_derived_form_factor_prices(self) -> None:
        document = _parse_with_chat_name(
            """US横白卡：50=5.4
US横白卡：100-150=5.45（50倍数）
#竖卡-0.1
#电子-0.15
#代码-0.3
""",
            chat_name="客人1 Apple报价群",
        )

        rows = {
            (row.amount_range, row.form_factor): row
            for row in document.rows
        }
        self.assertEqual(rows[("50", "横白卡")].price, 5.4)
        self.assertEqual(rows[("50", "竖卡")].price, 5.3)
        self.assertEqual(rows[("50", "电子")].price, 5.25)
        self.assertEqual(rows[("50", "代码")].price, 5.1)
        self.assertEqual(rows[("100-150", "横白卡")].price, 5.45)
        self.assertEqual(rows[("100-150", "竖卡")].price, 5.35)
        self.assertEqual(rows[("100-150", "电子")].price, 5.3)
        self.assertEqual(rows[("100-150", "代码")].price, 5.15)


if __name__ == "__main__":
    unittest.main()
