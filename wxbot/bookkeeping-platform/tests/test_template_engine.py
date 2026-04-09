from __future__ import annotations

import json
import unittest

from bookkeeping_core.template_engine import (
    TemplateConfig,
    auto_generate_template,
    match_pattern,
    parse_message_with_template,
)


class MatchPatternTests(unittest.TestCase):
    """T1.2: 单行 pattern 匹配 + 变量提取"""

    def test_exact_match_extracts_amount_and_price(self) -> None:
        result = match_pattern("卡图：100=5.35", "卡图：{amount}={price}")
        self.assertIsNotNone(result)
        self.assertEqual(result["amount"], "100")
        self.assertEqual(result["price"], "5.35")

    def test_amount_with_slash_range(self) -> None:
        result = match_pattern("卡图：100/150=5.35", "卡图：{amount}={price}")
        self.assertIsNotNone(result)
        self.assertEqual(result["amount"], "100/150")
        self.assertEqual(result["price"], "5.35")

    def test_amount_with_dash_range(self) -> None:
        result = match_pattern("卡图：200-450=5.38", "卡图：{amount}={price}")
        self.assertIsNotNone(result)
        self.assertEqual(result["amount"], "200-450")
        self.assertEqual(result["price"], "5.38")

    def test_no_match_returns_none(self) -> None:
        result = match_pattern("随便写的文字", "卡图：{amount}={price}")
        self.assertIsNone(result)

    def test_no_match_partial_overlap(self) -> None:
        result = match_pattern("横白卡图：100=5.35", "卡图：{amount}={price}")
        self.assertIsNone(result)

    def test_trailing_text_after_price(self) -> None:
        result = match_pattern(
            "横白卡图：100=5.37 连卡问",
            "横白卡图：{amount}={price}",
        )
        self.assertIsNotNone(result)
        self.assertEqual(result["amount"], "100")
        self.assertEqual(result["price"], "5.37")

    def test_bare_amount_equals_price(self) -> None:
        result = match_pattern("500=5.45", "{amount}={price}")
        self.assertIsNotNone(result)
        self.assertEqual(result["amount"], "500")
        self.assertEqual(result["price"], "5.45")

    def test_amount_dash_amount_equals_price(self) -> None:
        result = match_pattern("10-195=5.25", "{amount}-{amount2}={price}")
        self.assertIsNotNone(result)
        self.assertEqual(result["amount"], "10")
        self.assertEqual(result["amount2"], "195")
        self.assertEqual(result["price"], "5.25")


class ParseMessageTests(unittest.TestCase):
    """T3: 完整消息模板解析"""

    def _make_apple_template(self) -> TemplateConfig:
        return TemplateConfig(
            defaults={"card_type": "Apple", "country": "USD", "form_factor": "横白卡"},
            price_lines=[
                {"pattern": "卡图：{amount}={price}", "form_factor": "横白卡"},
                {"pattern": "横白卡图：{amount}={price}", "form_factor": "横白卡"},
                {"pattern": "{amount}={price}", "form_factor": None},
            ],
            restriction_lines=["^#"],
            section_lines=["^———"],
            skip_lines=["^\\s*$"],
        )

    def test_simple_price_line(self) -> None:
        tpl = self._make_apple_template()
        doc = parse_message_with_template("卡图：100=5.35", tpl)
        self.assertEqual(len(doc.rows), 1)
        row = doc.rows[0]
        self.assertEqual(row.card_type, "Apple")
        self.assertEqual(row.country_or_currency, "USD")
        self.assertEqual(row.amount_range, "100")
        self.assertEqual(row.price, 5.35)
        self.assertEqual(row.form_factor, "横白卡")
        self.assertEqual(len(doc.exceptions), 0)

    def test_multiline_with_restrictions(self) -> None:
        tpl = self._make_apple_template()
        text = "卡图：100/150=5.35\n卡图：200-450=5.38\n#250面值不拿\n#尾刀勿动"
        doc = parse_message_with_template(text, tpl)
        self.assertEqual(len(doc.rows), 2)
        self.assertEqual(len(doc.exceptions), 0)
        # 限制文字消息级共享
        self.assertIn("250面值不拿", doc.rows[0].restriction_text)
        self.assertIn("尾刀勿动", doc.rows[0].restriction_text)
        self.assertIn("250面值不拿", doc.rows[1].restriction_text)

    def test_unmatched_lines_are_silent(self) -> None:
        tpl = self._make_apple_template()
        text = "随便说句话\n卡图：100=5.35\n[左哼哼]"
        doc = parse_message_with_template(text, tpl)
        self.assertEqual(len(doc.rows), 1)
        self.assertEqual(len(doc.exceptions), 0)

    def test_empty_text(self) -> None:
        tpl = self._make_apple_template()
        doc = parse_message_with_template("", tpl)
        self.assertEqual(len(doc.rows), 0)
        self.assertEqual(len(doc.exceptions), 0)

    def test_amount_range_normalized(self) -> None:
        tpl = self._make_apple_template()
        doc = parse_message_with_template("卡图：100/150=5.35", tpl)
        # normalize_quote_amount_range 会把 / 转成 -
        self.assertEqual(doc.rows[0].amount_range, "100-150")

    def test_parse_status(self) -> None:
        tpl = self._make_apple_template()
        doc = parse_message_with_template("卡图：100=5.35", tpl)
        self.assertEqual(doc.parse_status, "parsed")
        doc_empty = parse_message_with_template("没有价格", tpl)
        self.assertEqual(doc_empty.parse_status, "empty")


class TemplateConfigTests(unittest.TestCase):
    """T2: 模板数据类 JSON 序列化"""

    def test_from_json_roundtrip(self) -> None:
        raw = json.dumps({
            "version": "tpl-v1",
            "defaults": {
                "card_type": "Apple",
                "country": "USD",
                "form_factor": "横白卡",
            },
            "price_lines": [
                {"pattern": "卡图：{amount}={price}", "form_factor": "横白卡"},
            ],
            "restriction_lines": ["^#"],
            "skip_lines": ["^\\s*$"],
        })
        tpl = TemplateConfig.from_json(raw)
        self.assertEqual(tpl.version, "tpl-v1")
        self.assertEqual(tpl.defaults["card_type"], "Apple")
        self.assertEqual(len(tpl.price_lines), 1)
        self.assertEqual(tpl.price_lines[0]["pattern"], "卡图：{amount}={price}")
        # roundtrip
        restored = TemplateConfig.from_json(tpl.to_json())
        self.assertEqual(restored.defaults, tpl.defaults)
        self.assertEqual(restored.price_lines, tpl.price_lines)

    def test_from_json_empty_string(self) -> None:
        with self.assertRaises(ValueError):
            TemplateConfig.from_json("")

    def test_from_json_invalid(self) -> None:
        with self.assertRaises(ValueError):
            TemplateConfig.from_json("{bad json")


class AutoGenerateTests(unittest.TestCase):
    """T7: 从真实消息自动生成模板"""

    def test_generates_from_simple_message(self) -> None:
        text = "卡图：100/150=5.35\n卡图：200-450=5.38\n#250面值不拿"
        tpl = auto_generate_template(text, defaults={"card_type": "Apple", "country": "USD"})
        # 两行格式相同，去重后只保留 1 个 pattern
        self.assertTrue(len(tpl.price_lines) >= 1)
        self.assertTrue(len(tpl.restriction_lines) >= 1)
        # 生成的模板应该能解析同一条消息的两行
        doc = parse_message_with_template(text, tpl)
        self.assertEqual(len(doc.rows), 2)

    def test_generates_with_restrictions_and_skips(self) -> None:
        text = "【US快速网单】\n横白卡图：50=5.3\n横白卡图：100=5.4\n#尾刀勿动\n[左哼哼]"
        tpl = auto_generate_template(text, defaults={"card_type": "Apple", "country": "USD"})
        doc = parse_message_with_template(text, tpl)
        self.assertEqual(len(doc.rows), 2)
        self.assertIn("尾刀勿动", doc.rows[0].restriction_text)

    def test_empty_text_raises(self) -> None:
        with self.assertRaises(ValueError):
            auto_generate_template("")


if __name__ == "__main__":
    unittest.main()
