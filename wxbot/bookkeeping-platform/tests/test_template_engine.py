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


if __name__ == "__main__":
    unittest.main()
