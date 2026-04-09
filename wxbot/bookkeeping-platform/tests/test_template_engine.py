from __future__ import annotations

import json
import unittest

from bookkeeping_core.template_engine import (
    TemplateConfig,
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


if __name__ == "__main__":
    unittest.main()
