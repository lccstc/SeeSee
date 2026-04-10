"""Data Engine v1 报价模板引擎测试。"""
import unittest

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestTemplateConfig(unittest.TestCase):
    def test_schema_data_engine_v1(self):
        from bookkeeping_core.template_engine import TemplateConfig
        raw = '''{
            "version": "data-engine-v1",
            "rules": [
                {"pattern": "【{card_type}】", "type": "section"},
                {"pattern": "{country}={price}({restriction})", "type": "price"}
            ]
        }'''
        config = TemplateConfig.from_json(raw)
        self.assertEqual(config.version, "data-engine-v1")
        self.assertEqual(len(config.rules), 2)
        self.assertEqual(config.rules[0]["type"], "section")
        self.assertEqual(config.rules[1]["type"], "price")

    def test_empty_config_raises(self):
        from bookkeeping_core.template_engine import TemplateConfig
        with self.assertRaises(ValueError):
            TemplateConfig.from_json("")

    def test_roundtrip_json(self):
        from bookkeeping_core.template_engine import TemplateConfig
        config = TemplateConfig(
            version="data-engine-v1",
            rules=[{"pattern": "{a}={b}", "type": "price"}],
            defaults={"card_type": "xb"},
        )
        raw = config.to_json()
        restored = TemplateConfig.from_json(raw)
        self.assertEqual(restored.rules, config.rules)
        self.assertEqual(restored.defaults, config.defaults)


class TestMatchPattern(unittest.TestCase):
    def test_exact_match(self):
        from bookkeeping_core.template_engine import match_pattern
        pattern = "{country}={price}({restriction})"
        res = match_pattern("加拿大=3.4(代码批量问)", pattern)
        self.assertEqual(res, {"country": "加拿大", "price": "3.4", "restriction": "代码批量问"})

    def test_extra_space_fails(self):
        from bookkeeping_core.template_engine import match_pattern
        pattern = "{country}={price}({restriction})"
        res = match_pattern("加拿大 = 3.4(代码批量问)", pattern)
        self.assertIsNone(res)

    def test_section_match(self):
        from bookkeeping_core.template_engine import match_pattern
        res = match_pattern("【XBOX】", "【{card_type}】")
        self.assertEqual(res, {"card_type": "XBOX"})

    def test_amount_price(self):
        from bookkeeping_core.template_engine import match_pattern
        res = match_pattern("10-1000=5.2", "{amount}={price}")
        self.assertEqual(res, {"amount": "10-1000", "price": "5.2"})


class TestParseMessageWithTemplate(unittest.TestCase):
    def test_parse_message_strict(self):
        from bookkeeping_core.template_engine import TemplateConfig, parse_message_with_template
        text = "【XBOX】\n加拿大=3.4(代码批量问)\n10-1000=5.2\n未知格式=1.0"
        config = TemplateConfig(
            version="data-engine-v1",
            rules=[
                {"pattern": "【{card_type}】", "type": "section"},
                {"pattern": "{country}={price}({restriction})", "type": "price"},
                {"pattern": "{amount}={price}", "type": "price"},
            ],
        )
        doc = parse_message_with_template(text, config, source_group_key="G1")
        self.assertEqual(len(doc.rows), 2)
        self.assertEqual(doc.rows[0].country_or_currency, "加拿大")
        self.assertEqual(doc.rows[0].price, 3.4)
        self.assertEqual(doc.rows[0].card_type, "XBOX")
        self.assertEqual(doc.rows[1].amount_range, "10-1000")
        self.assertEqual(doc.rows[1].price, 5.2)
        self.assertEqual(doc.rows[1].card_type, "XBOX")
        self.assertEqual(len(doc.exceptions), 1)
        self.assertEqual(doc.exceptions[0].source_line, "未知格式=1.0")

    def test_message_level_exception(self):
        """Multiple unmatched lines merge into one message-level exception."""
        from bookkeeping_core.template_engine import TemplateConfig, parse_message_with_template
        # Lines without = delimiter and note lines with digits → unmatched → merged exception
        text = "【XBOX】\n加拿大=3.4\n土耳其0.13\n使用时间3-5分钟\n10的倍数只要16位"
        config = TemplateConfig(
            version="data-engine-v1",
            rules=[
                {"pattern": "【{card_type}】", "type": "section"},
                {"pattern": "{country}={price}", "type": "price"},
            ],
        )
        doc = parse_message_with_template(text, config, source_group_key="G1")
        self.assertEqual(len(doc.rows), 1)  # only 加拿大=3.4 matches
        self.assertEqual(len(doc.exceptions), 1)  # ONE merged exception
        exc_lines = doc.exceptions[0].source_line.split("\n")
        self.assertEqual(len(exc_lines), 3)  # 土耳其0.13 + 使用时间3-5分钟 + 10的倍数只要16位

    def test_section_inheritance(self):
        from bookkeeping_core.template_engine import TemplateConfig, parse_message_with_template
        text = "【FT】\n美国=7.0\n【ST】\n英国=6.5"
        config = TemplateConfig(
            version="data-engine-v1",
            rules=[
                {"pattern": "【{card_type}】", "type": "section"},
                {"pattern": "{country}={price}", "type": "price"},
            ],
        )
        doc = parse_message_with_template(text, config)
        self.assertEqual(len(doc.rows), 2)
        self.assertEqual(doc.rows[0].card_type, "FT")
        self.assertEqual(doc.rows[0].country_or_currency, "美国")
        self.assertEqual(doc.rows[1].card_type, "ST")
        self.assertEqual(doc.rows[1].country_or_currency, "英国")


class TestGenerateStrictPattern(unittest.TestCase):
    def test_generate_from_annotations(self):
        from bookkeeping_core.template_engine import generate_strict_pattern_from_annotations
        line = "加拿大=3.4(代码批量问)"
        annotations = [
            {"type": "country", "value": "加拿大", "start": 0, "end": 3},
            {"type": "price", "value": "3.4", "start": 4, "end": 7},
            {"type": "restriction", "value": "代码批量问", "start": 8, "end": 13},
        ]
        pattern = generate_strict_pattern_from_annotations(line, annotations)
        self.assertEqual(pattern, "{country}={price}({restriction})")

    def test_pattern_roundtrip(self):
        """标注生成的 pattern 应该能反过来匹配原始文本。"""
        from bookkeeping_core.template_engine import (
            generate_strict_pattern_from_annotations,
            match_pattern,
        )
        line = "加拿大=3.4(代码批量问)"
        annotations = [
            {"type": "country", "value": "加拿大", "start": 0, "end": 3},
            {"type": "price", "value": "3.4", "start": 4, "end": 7},
            {"type": "restriction", "value": "代码批量问", "start": 8, "end": 13},
        ]
        pattern = generate_strict_pattern_from_annotations(line, annotations)
        result = match_pattern(line, pattern)
        self.assertIsNotNone(result)
        self.assertEqual(result["country"], "加拿大")
        self.assertEqual(result["price"], "3.4")


class TestBuildAnnotations(unittest.TestCase):
    def test_build_annotations_basic(self):
        from bookkeeping_core.template_engine import build_annotations_from_fields
        line = "加拿大=3.4(代码批量问)"
        fields = {"country": "加拿大", "price": "3.4"}
        anns = build_annotations_from_fields(line, fields)
        self.assertEqual(len(anns), 2)
        self.assertEqual(anns[0], {"type": "country", "value": "加拿大", "start": 0, "end": 3})
        self.assertEqual(anns[1], {"type": "price", "value": "3.4", "start": 4, "end": 7})

    def test_build_annotations_skips_empty(self):
        from bookkeeping_core.template_engine import build_annotations_from_fields
        line = "加拿大=3.4"
        fields = {"country": "加拿大", "price": ""}
        anns = build_annotations_from_fields(line, fields)
        self.assertEqual(len(anns), 1)
        self.assertEqual(anns[0]["type"], "country")

    def test_build_annotations_skips_not_found(self):
        from bookkeeping_core.template_engine import build_annotations_from_fields
        line = "加拿大=3.4"
        fields = {"country": "加拿大", "price": "99.9"}
        anns = build_annotations_from_fields(line, fields)
        self.assertEqual(len(anns), 1)

    def test_annotate_end_to_end(self):
        """模拟完整标注流程：fields → annotations → pattern → 能匹配原始行"""
        from bookkeeping_core.template_engine import (
            build_annotations_from_fields,
            generate_strict_pattern_from_annotations,
            match_pattern,
        )
        line = "加拿大=3.4(代码批量问)"
        fields = {"country": "加拿大", "price": "3.4"}

        annotations = build_annotations_from_fields(line, fields)
        pattern = generate_strict_pattern_from_annotations(line, annotations)

        # 尾部 restriction 自动追加
        import re as _re
        restriction_match = _re.search(r'\([^)]*\)\s*$', line)
        if restriction_match and "restriction" not in fields:
            ann_start = restriction_match.start()
            annotations.append({
                "type": "restriction",
                "value": line[ann_start:],
                "start": ann_start,
                "end": len(line),
            })
            annotations.sort(key=lambda a: a["start"])
            pattern = generate_strict_pattern_from_annotations(line, annotations)

        self.assertIn("{restriction}", pattern)
        result = match_pattern(line, pattern)
        self.assertIsNotNone(result)
        self.assertEqual(result["country"], "加拿大")
        self.assertEqual(result["price"], "3.4")


class TestNormalizeQuoteText(unittest.TestCase):
    def test_fullwidth_to_halfwidth(self):
        from bookkeeping_core.template_engine import normalize_quote_text
        self.assertEqual(normalize_quote_text("加拿大=3.4（代码批量问）"), "加拿大=3.4(代码批量问)")

    def test_whitespace_around_equals(self):
        from bookkeeping_core.template_engine import normalize_quote_text
        self.assertEqual(normalize_quote_text("新加坡 =4.25"), "新加坡=4.25")
        self.assertEqual(normalize_quote_text("菲律宾= 0.098"), "菲律宾=0.098")
        self.assertEqual(normalize_quote_text("加拿大 = 4.15"), "加拿大=4.15")

    def test_whitespace_around_colon(self):
        from bookkeeping_core.template_engine import normalize_quote_text
        self.assertEqual(normalize_quote_text("US:  1-499=5.73"), "US:1-499=5.73")

    def test_collapse_multiple_spaces(self):
        from bookkeeping_core.template_engine import normalize_quote_text
        self.assertEqual(normalize_quote_text("欧盟  EUR  50-500=6.53"), "欧盟 EUR 50-500=6.53")

    def test_strip_outer_decoration(self):
        from bookkeeping_core.template_engine import normalize_quote_text
        self.assertEqual(normalize_quote_text("======【Roblox】======"), "【Roblox】")
        self.assertEqual(normalize_quote_text("  === 【XBOX】===  "), "【XBOX】")

    def test_inner_decoration_preserved(self):
        from bookkeeping_core.template_engine import normalize_quote_text
        result = normalize_quote_text("【===黄金雷蛇US===】")
        self.assertEqual(result, "【===黄金雷蛇US===】")

    def test_no_change_for_clean_line(self):
        from bookkeeping_core.template_engine import normalize_quote_text
        self.assertEqual(normalize_quote_text("加拿大=4.15"), "加拿大=4.15")

    def test_double_equals_preserved(self):
        from bookkeeping_core.template_engine import normalize_quote_text
        result = normalize_quote_text("50-500==6.53")
        self.assertIn("==", result)


class TestCleanCardType(unittest.TestCase):
    def test_strip_decoration(self):
        from bookkeeping_core.template_engine import _clean_card_type
        self.assertEqual(_clean_card_type("===黄金雷蛇US==="), "黄金雷蛇US")
        self.assertEqual(_clean_card_type("====外卡雷蛇===="), "外卡雷蛇")
        self.assertEqual(_clean_card_type("====绿蛇===="), "绿蛇")

    def test_no_decoration(self):
        from bookkeeping_core.template_engine import _clean_card_type
        self.assertEqual(_clean_card_type("XBOX"), "XBOX")
        self.assertEqual(_clean_card_type("Paysafecard 安全支付图密同价"), "Paysafecard 安全支付图密同价")


class TestC531RealData(unittest.TestCase):
    """Real C-531 group message parsing verification."""

    @classmethod
    def setUpClass(cls):
        from bookkeeping_core.template_engine import TemplateConfig
        cls.TEMPLATE_CONFIG = TemplateConfig(
            version="data-engine-v1",
            rules=[
                {"pattern": "【{card_type}】", "type": "section"},
                {"pattern": "{country} {currency} {amount}={price}", "type": "price"},
                {"pattern": "{country} {amount}={price}({restriction})", "type": "price"},
                {"pattern": "{country} {amount}={price}", "type": "price"},
                {"pattern": "{country}:{amount}={price} {restriction}", "type": "price"},
                {"pattern": "{country}:{amount}={price}", "type": "price"},
                {"pattern": "{country}={price}({restriction})", "type": "price"},
                {"pattern": "{amount}={price}", "type": "price"},
                {"pattern": "{country}={price}", "type": "price"},
            ],
        )
        # Curated subset of real C-531 message
        cls.C531_MESSAGE = (
            "【===黄金雷蛇US===】\n"
            "   US:  1-499=5.73 批量问\n"
            "\n"
            "【====外卡雷蛇====】\n"
            "巴西=1.03          新加坡 =4.25\n"  # two quotes one line → exception
            "澳大利亚=4.02   加拿大=4.15\n"  # two quotes one line → exception
            "香港 =0.65         新西兰 =3.15\n"  # two quotes one line → exception
            "土耳其0.13         智利=0.005\n"  # 土耳其0.13 no separator → exception
            "\n"
            "  【====绿蛇====】 \n"
            " 10-1000=5.2\n"
            "\n"
            "      【===XBOX===】 \n"
            "美国 10-250=5.1（5的倍数）\n"
            "\n"
            "【====外卡XBOX====】\n"
            "加拿大=3.4（代码批量问）英国=6.15卡图 \n"  # two quotes one line → exception
            "挪威=0.41          瑞士=5.0卡图\n"  # two quotes one line → exception
            "台湾=0.1            哥伦比亚=0.0011\n"  # two quotes one line → exception
            "沙特阿拉伯=1.4   智利=0.005\n"  # two quotes one line → exception
            "\n"
            "【Paysafecard 安全支付图密同价】\n"
            "---------------------------------------\n"
            "欧盟 EUR          50-500==6.53\n"  # double == → exception
            "英国 GBP          50-500==7.0\n"  # double == → exception
            "加拿大 CAD      25-500=3.5\n"
            "\n"
            "======【Roblox】======\n"
            "          us 3.45\n"  # no separator → exception
        )

    def test_section_headers_set_card_type(self):
        from bookkeeping_core.template_engine import parse_message_with_template
        doc = parse_message_with_template(self.C531_MESSAGE, self.TEMPLATE_CONFIG, source_group_key="C-531")
        card_types = set(row.card_type for row in doc.rows)
        self.assertIn("黄金雷蛇US", card_types)
        self.assertIn("绿蛇", card_types)
        self.assertIn("XBOX", card_types)
        # 外卡雷蛇 section only has multi-quote lines → all go to exceptions, no rows

    def test_simple_country_price(self):
        from bookkeeping_core.template_engine import parse_message_with_template
        doc = parse_message_with_template(self.C531_MESSAGE, self.TEMPLATE_CONFIG, source_group_key="C-531")
        # After normalization "新加坡 =4.25" → "新加坡=4.25" but it's on a multi-quote line
        # Single-quote lines that should work:
        amount_rows = [r for r in doc.rows if r.amount_range == "10-1000"]
        self.assertEqual(len(amount_rows), 1)
        self.assertEqual(amount_rows[0].price, 5.2)
        self.assertEqual(amount_rows[0].card_type, "绿蛇")

    def test_fullwidth_brackets_normalize(self):
        from bookkeeping_core.template_engine import parse_message_with_template
        doc = parse_message_with_template(self.C531_MESSAGE, self.TEMPLATE_CONFIG, source_group_key="C-531")
        # "美国 10-250=5.1（5的倍数）" after normalization → "美国 10-250=5.1(5的倍数)"
        xbox_rows = [r for r in doc.rows if r.card_type == "XBOX"]
        self.assertEqual(len(xbox_rows), 1)
        self.assertEqual(xbox_rows[0].country_or_currency, "美国")
        self.assertEqual(xbox_rows[0].price, 5.1)
        self.assertEqual(xbox_rows[0].restriction_text, "5的倍数")

    def test_colon_pattern_with_restriction(self):
        from bookkeeping_core.template_engine import parse_message_with_template
        doc = parse_message_with_template(self.C531_MESSAGE, self.TEMPLATE_CONFIG, source_group_key="C-531")
        # "US:  1-499=5.73 批量问" after normalization → "US:1-499=5.73 批量问"
        us_rows = [r for r in doc.rows if r.country_or_currency == "US" and r.card_type == "黄金雷蛇US"]
        self.assertEqual(len(us_rows), 1)
        self.assertEqual(us_rows[0].price, 5.73)
        self.assertEqual(us_rows[0].restriction_text, "批量问")

    def test_paysafecard_triple_pattern(self):
        from bookkeeping_core.template_engine import parse_message_with_template
        doc = parse_message_with_template(self.C531_MESSAGE, self.TEMPLATE_CONFIG, source_group_key="C-531")
        # "加拿大 CAD 25-500=3.5" → country currency amount=price
        paysafe_rows = [r for r in doc.rows if "Paysafecard" in r.card_type]
        self.assertTrue(len(paysafe_rows) >= 1)
        cad_row = [r for r in paysafe_rows if r.country_or_currency == "加拿大"]
        self.assertEqual(len(cad_row), 1)
        self.assertEqual(cad_row[0].price, 3.5)

    def test_multi_quote_lines_go_to_exceptions(self):
        from bookkeeping_core.template_engine import parse_message_with_template
        doc = parse_message_with_template(self.C531_MESSAGE, self.TEMPLATE_CONFIG, source_group_key="C-531")
        exception_lines = [e.source_line for e in doc.exceptions]
        # Lines with two quotes should fail (e.g. "澳大利亚=4.02 加拿大=4.15")
        self.assertTrue(len(doc.exceptions) > 0)

    def test_has_both_rows_and_exceptions(self):
        from bookkeeping_core.template_engine import parse_message_with_template
        doc = parse_message_with_template(self.C531_MESSAGE, self.TEMPLATE_CONFIG, source_group_key="C-531")
        self.assertTrue(len(doc.rows) > 0, "Should have some successfully parsed rows")
        self.assertTrue(len(doc.exceptions) > 0, "Should have some exceptions for multi-quote lines")


class TestAnnotationFlywheel(unittest.TestCase):
    """End-to-end: exception → annotate → new rule → re-parse succeeds."""

    def test_flywheel_cycle(self):
        from bookkeeping_core.template_engine import (
            TemplateConfig,
            parse_message_with_template,
            build_annotations_from_fields,
            generate_strict_pattern_from_annotations,
        )
        # Step 1: Parse with limited rules — missing the colon pattern
        limited_config = TemplateConfig(
            version="data-engine-v1",
            rules=[
                {"pattern": "【{card_type}】", "type": "section"},
                {"pattern": "{country}={price}", "type": "price"},
            ],
        )
        text = "【Roblox】\nUS:1-499=5.73 批量问"
        doc = parse_message_with_template(text, limited_config, source_group_key="test")
        self.assertEqual(len(doc.exceptions), 1)
        failed_line = doc.exceptions[0].source_line

        # Step 2: Simulate annotation
        fields = {"country": "US", "amount": "1-499", "price": "5.73", "restriction": "批量问"}
        annotations = build_annotations_from_fields(failed_line, fields)
        pattern = generate_strict_pattern_from_annotations(failed_line, annotations)
        self.assertEqual(pattern, "{country}:{amount}={price} {restriction}")

        # Step 3: Append new rule and re-parse
        limited_config.rules.append({"pattern": pattern, "type": "price"})
        doc2 = parse_message_with_template(text, limited_config, source_group_key="test")
        self.assertEqual(len(doc2.rows), 1)
        self.assertEqual(len(doc2.exceptions), 0)
        self.assertEqual(doc2.rows[0].country_or_currency, "US")
        self.assertEqual(doc2.rows[0].price, 5.73)
        self.assertEqual(doc2.rows[0].restriction_text, "批量问")


class TestSplitMultiQuoteLine(unittest.TestCase):
    def test_split_two_quotes(self):
        from bookkeeping_core.template_engine import split_multi_quote_line
        result = split_multi_quote_line("巴西=1.03 新加坡=4.25")
        self.assertEqual(result, ["巴西=1.03", "新加坡=4.25"])

    def test_split_no_space(self):
        from bookkeeping_core.template_engine import split_multi_quote_line
        result = split_multi_quote_line("加拿大=3.4(代码批量问)英国=6.15卡图")
        self.assertEqual(result, ["加拿大=3.4(代码批量问)", "英国=6.15卡图"])

    def test_no_split_single(self):
        from bookkeeping_core.template_engine import split_multi_quote_line
        result = split_multi_quote_line("加拿大=4.15")
        self.assertEqual(result, ["加拿大=4.15"])

    def test_multi_quote_lines_now_parse(self):
        """Multi-quote lines are auto-split and parsed as individual quotes."""
        from bookkeeping_core.template_engine import TemplateConfig, parse_message_with_template
        text = "【XBOX】\n巴西=1.03 新加坡=4.25\n香港=0.65 新西兰=3.15"
        config = TemplateConfig(
            version="data-engine-v1",
            rules=[
                {"pattern": "【{card_type}】", "type": "section"},
                {"pattern": "{country}={price}", "type": "price"},
            ],
        )
        doc = parse_message_with_template(text, config, source_group_key="G1")
        self.assertEqual(len(doc.rows), 4)
        countries = {r.country_or_currency for r in doc.rows}
        self.assertEqual(countries, {"巴西", "新加坡", "香港", "新西兰"})
        self.assertEqual(len(doc.exceptions), 0)


class TestAutoDetect(unittest.TestCase):
    def test_section_header(self):
        from bookkeeping_core.template_engine import auto_detect_line_type
        result = auto_detect_line_type("【XBOX】")
        self.assertEqual(result["type"], "section")
        self.assertEqual(result["pattern"], "【{card_type}】")

    def test_country_price(self):
        from bookkeeping_core.template_engine import auto_detect_line_type
        result = auto_detect_line_type("加拿大=4.15")
        self.assertEqual(result["type"], "price")
        self.assertEqual(result["pattern"], "{country}={price}")

    def test_country_price_restriction(self):
        from bookkeeping_core.template_engine import auto_detect_line_type
        result = auto_detect_line_type("加拿大=3.4(代码批量问)")
        self.assertEqual(result["type"], "price")
        self.assertEqual(result["pattern"], "{country}={price}({restriction})")

    def test_amount_price(self):
        from bookkeeping_core.template_engine import auto_detect_line_type
        result = auto_detect_line_type("10-1000=5.2")
        self.assertEqual(result["type"], "price")
        self.assertEqual(result["pattern"], "{amount}={price}")

    def test_country_amount_price(self):
        from bookkeeping_core.template_engine import auto_detect_line_type
        result = auto_detect_line_type("美国 10-250=5.1")
        self.assertEqual(result["type"], "price")
        self.assertEqual(result["pattern"], "{country} {amount}={price}")

    def test_note_line_skip(self):
        from bookkeeping_core.template_engine import auto_detect_line_type
        result = auto_detect_line_type("使用时间3-5分钟,只能使用")
        self.assertEqual(result["type"], "skip")

    def test_suggest_template_rules(self):
        from bookkeeping_core.template_engine import suggest_template_rules, deduplicate_rules
        text = "【XBOX】\n加拿大=4.15\n巴西=1.03 新加坡=4.25\n10-1000=5.2\n使用时间3分钟"
        detections = suggest_template_rules(text)
        rules = deduplicate_rules(detections)
        patterns = {r["pattern"] for r in rules}
        self.assertIn("【{card_type}】", patterns)
        self.assertIn("{country}={price}", patterns)
        self.assertIn("{amount}={price}", patterns)


if __name__ == "__main__":
    unittest.main()
