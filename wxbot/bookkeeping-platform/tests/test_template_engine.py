"""Data Engine v1 报价模板引擎测试。"""
import unittest

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tests.support.quote_exception_corpus import load_gold_samples


def _fixture(name: str) -> dict:
    for item in load_gold_samples():
        if item["fixture_name"] == name:
            return item
    raise KeyError(name)


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
        # Only real quote-like unmatched lines should remain in exception pool.
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
        self.assertEqual(exc_lines, ["土耳其0.13"])

    def test_looks_like_quote_line_rejects_balance_like_line(self):
        from bookkeeping_core.template_engine import looks_like_quote_line

        self.assertFalse(looks_like_quote_line("当前账单金额:-26646.17"))
        self.assertFalse(looks_like_quote_line("📊 Balance:+26642.17"))
        self.assertFalse(looks_like_quote_line("✅ +200 RG ×5.75=-1150.00"))
        self.assertTrue(looks_like_quote_line("土耳其0.13"))

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

    def test_parse_message_strict_supports_bracket_virtual_quote_lines(self):
        from bookkeeping_core.template_engine import TemplateConfig, parse_message_with_template

        text = "【Steam】\nUSD-10-200【5.03】\nUK【6.75】  EUR【5.89】"
        config = TemplateConfig(
            version="data-engine-v1",
            rules=[
                {"pattern": "【{card_type}】", "type": "section"},
                {"pattern": "{country} {amount}={price}", "type": "price"},
                {"pattern": "{country}={price}", "type": "price"},
            ],
        )

        doc = parse_message_with_template(text, config, source_group_key="G-bracket")
        self.assertEqual(len(doc.rows), 3)
        self.assertFalse(doc.exceptions)
        self.assertTrue(any(row.country_or_currency == "GBP" and row.price == 6.75 for row in doc.rows))
        self.assertTrue(any(row.country_or_currency == "USD" and row.amount_range == "10-200" for row in doc.rows))


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


class TestScopedNumericCorpusRegressions(unittest.TestCase):
    def test_scoped_numeric_feihong_it_scoped_numeric(self):
        from bookkeeping_core.template_engine import analyze_scoped_quote_lines

        fixture = _fixture("feihong_us_vip_delta_242")
        analyses = analyze_scoped_quote_lines(
            fixture["raw_text"],
            default_card_type="Apple iTunes",
            default_country_or_currency="USD",
            default_form_factor="white_card",
        )
        rows = {
            item["source_line"]: item["candidate"]
            for item in analyses
            if item.get("candidate")
        }
        self.assertIn("50=5.25", rows)
        self.assertIn("100/150=5.41", rows)
        self.assertEqual(rows["50=5.25"]["country_or_currency"], "USD")
        self.assertEqual(rows["50=5.25"]["scope_evidence"]["header_line_index"], 2)

    def test_panda_supermarket_manual_lines_are_not_candidates(self):
        from bookkeeping_core.template_engine import analyze_scoped_quote_lines

        fixture = _fixture("panda_supermarket_delta_222")
        analyses = analyze_scoped_quote_lines(
            fixture["raw_text"],
            default_country_or_currency="USD",
            default_form_factor="card_or_code",
        )
        rows = [item for item in analyses if item.get("candidate")]
        self.assertTrue(any(item["candidate"]["card_type"] == "Sephora" for item in rows))
        manual_lines = [
            item for item in analyses
            if item["source_line"] in {"问价-请勿直发！！", "默认卡图，代码提前问！！"}
        ]
        self.assertTrue(all(item["line_type"] in {"inquiry", "rule"} for item in manual_lines))
        self.assertTrue(all("candidate" not in item for item in manual_lines))

    def test_mile_it_shift_update_keeps_us_scope(self):
        from bookkeeping_core.template_engine import analyze_scoped_quote_lines

        fixture = _fixture("milele_shift_board_169")
        analyses = analyze_scoped_quote_lines(
            fixture["raw_text"],
            default_card_type="Apple iTunes",
            default_country_or_currency="USD",
            default_form_factor="white_card",
        )
        scoped = next(item for item in analyses if item["source_line"] == "100/150=5.4")
        self.assertEqual(scoped["candidate"]["country_or_currency"], "USD")
        self.assertEqual(scoped["candidate"]["scope_evidence"]["header_text"], "US")

    def test_qh_delta_numeric_update_handles_us_and_uk_sections(self):
        from bookkeeping_core.template_engine import analyze_scoped_quote_lines

        fixture = _fixture("qh_delta_us_uk_239")
        analyses = analyze_scoped_quote_lines(
            fixture["raw_text"],
            default_card_type="Apple iTunes",
            default_country_or_currency="USD",
            default_form_factor="white_card",
        )
        us_row = next(item for item in analyses if item["source_line"] == "100/150=5.37")
        uk_row = next(item for item in analyses if item["source_line"].startswith("UK卡图100-250=6.71"))
        self.assertEqual(us_row["candidate"]["country_or_currency"], "USD")
        self.assertEqual(uk_row["candidate"]["country_or_currency"], "GBP")
        self.assertEqual(uk_row["candidate"]["form_factor"], "横白卡")


class TestQuoteRemediationScopeRouter(unittest.TestCase):
    def test_choose_quote_repair_scope_defaults_to_group_profile_first(self):
        from bookkeeping_core.remediation import choose_quote_repair_scope

        decision = choose_quote_repair_scope(
            has_group_profile=True,
            section_local_only=False,
        )
        self.assertEqual(decision["scope"], "group_profile")
        self.assertEqual(decision["reason"], "default_group_profile_first")

    def test_choose_quote_repair_scope_falls_to_group_section_only_with_local_evidence(self):
        from bookkeeping_core.remediation import choose_quote_repair_scope

        decision = choose_quote_repair_scope(
            has_group_profile=True,
            section_local_only=True,
            section_identifier="apple-us",
        )
        self.assertEqual(decision["scope"], "group_section")
        self.assertEqual(decision["reason"], "section_local_only")

    def test_choose_quote_repair_scope_uses_bootstrap_when_group_profile_missing(self):
        from bookkeeping_core.remediation import choose_quote_repair_scope

        decision = choose_quote_repair_scope(
            has_group_profile=False,
            section_local_only=False,
            bootstrap_candidate=True,
        )
        self.assertEqual(decision["scope"], "bootstrap")
        self.assertEqual(decision["reason"], "no_group_profile_bootstrap_candidate")

    def test_choose_quote_repair_scope_promotes_shared_rule_only_after_repeated_cross_group_evidence(self):
        from bookkeeping_core.remediation import choose_quote_repair_scope

        decision = choose_quote_repair_scope(
            has_group_profile=True,
            section_local_only=False,
            cross_group_match_count=2,
        )
        self.assertEqual(decision["scope"], "shared_rule")
        self.assertEqual(decision["reason"], "repeated_cross_group_shared_rule")

    def test_validate_quote_repair_write_scope_blocks_web_and_database_surfaces(self):
        from bookkeeping_core.remediation import validate_quote_repair_write_scope

        with self.assertRaisesRegex(ValueError, "forbidden remediation surfaces"):
            validate_quote_repair_write_scope(
                proposal_scope="shared_rule",
                touched_files=[
                    "wxbot/bookkeeping-platform/bookkeeping_web/app.py",
                    "wxbot/bookkeeping-platform/tests/test_template_engine.py",
                ],
            )

    def test_validate_quote_repair_write_scope_accepts_shared_rule_template_and_tests(self):
        from bookkeeping_core.remediation import validate_quote_repair_write_scope

        envelope = validate_quote_repair_write_scope(
            proposal_scope="shared_rule",
            touched_files=[
                "wxbot/bookkeeping-platform/bookkeeping_core/template_engine.py",
                "wxbot/bookkeeping-platform/tests/test_template_engine.py",
            ],
        )
        self.assertEqual(envelope["scope"], "shared_rule")
        self.assertIn(
            "wxbot/bookkeeping-platform/bookkeeping_core/template_engine.py",
            envelope["touched_files"],
        )

    def test_wannuo_xb_shorthand_scoped_numeric(self):
        from bookkeeping_core.template_engine import analyze_scoped_quote_lines

        fixture = _fixture("wannuo_xbox_shorthand_174")
        analyses = analyze_scoped_quote_lines(
            fixture["raw_text"],
            default_country_or_currency="USD",
            default_form_factor="card_or_code",
        )
        rows = [item["candidate"] for item in analyses if item.get("candidate")]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["card_type"], "Xbox")
        self.assertEqual(rows[0]["amount_range"], "100")

    def test_qingsong_noise_token_is_suppressed(self):
        from bookkeeping_core.template_engine import analyze_scoped_quote_lines

        fixture = _fixture("qingsong_noise_token_177")
        analyses = analyze_scoped_quote_lines(fixture["raw_text"])
        self.assertTrue(all(item["line_type"] == "noise" for item in analyses))
        self.assertTrue(all("candidate" not in item for item in analyses))


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

    def test_build_annotations_amount_uses_flexible_matcher(self):
        from bookkeeping_core.template_engine import build_annotations_from_fields

        line = "200- 450=5.44(50倍数)"
        fields = {"amount": "200-450", "price": "5.44"}
        anns = build_annotations_from_fields(line, fields)

        self.assertEqual(len(anns), 2)
        self.assertEqual(anns[0], {"type": "amount", "value": "200- 450", "start": 0, "end": 8})
        self.assertEqual(anns[1], {"type": "price", "value": "5.44", "start": 9, "end": 13})

    def test_build_annotations_amount_does_not_mix_slash_and_dash(self):
        from bookkeeping_core.template_engine import build_annotations_from_fields

        line = "100/150=5.43"
        fields = {"amount": "100-150", "price": "5.43"}
        anns = build_annotations_from_fields(line, fields)

        self.assertEqual(len(anns), 1)
        self.assertEqual(anns[0], {"type": "price", "value": "5.43", "start": 8, "end": 12})

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

    def test_inner_decoration_normalized(self):
        from bookkeeping_core.template_engine import normalize_quote_text
        result = normalize_quote_text("【===黄金雷蛇US===】")
        # triple equals collapsed to single by == normalization
        self.assertEqual(result, "【=黄金雷蛇US=】")

    def test_no_change_for_clean_line(self):
        from bookkeeping_core.template_engine import normalize_quote_text
        self.assertEqual(normalize_quote_text("加拿大=4.15"), "加拿大=4.15")

    def test_double_equals_normalized(self):
        from bookkeeping_core.template_engine import normalize_quote_text
        result = normalize_quote_text("50-500==6.53")
        self.assertEqual(result, "50-500=6.53")

    def test_triple_equals_normalized(self):
        from bookkeeping_core.template_engine import normalize_quote_text
        result = normalize_quote_text("50-500===6.53")
        self.assertEqual(result, "50-500=6.53")


class TestStrictSectionAmountLabels(unittest.TestCase):
    def test_normalize_strict_section_amount_label_preserves_separator_kind(self):
        from bookkeeping_core.template_engine import normalize_strict_section_amount_label

        self.assertEqual(normalize_strict_section_amount_label("100 / 150"), "100/150")
        self.assertEqual(normalize_strict_section_amount_label("200- 450"), "200-450")


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

    def test_bracket_multi_quote_lines_virtualize(self):
        from bookkeeping_core.template_engine import _normalized_virtual_lines

        lines = _normalized_virtual_lines("UK【6.75】  EUR【5.89】\nNZD【2.92】CHF【6.37】", split_multi_quotes=True)
        self.assertEqual(
            [(item["line"], item["source_line"]) for item in lines],
            [
                ("GBP=6.75", "UK【6.75】"),
                ("EUR=5.89", "EUR【5.89】"),
                ("NZD=2.92", "NZD【2.92】"),
                ("CHF=6.37", "CHF【6.37】"),
            ],
        )

    def test_prefixed_amount_lines_virtualize(self):
        from bookkeeping_core.template_engine import _normalized_virtual_lines

        lines = _normalized_virtual_lines(
            "葡萄牙 PT 50-500=5.5  15-49=5.0\n希腊 50-500=5.5  15-49=5.0",
            split_multi_quotes=True,
        )
        self.assertEqual(
            [(item["line"], item["source_line"]) for item in lines],
            [
                ("葡萄牙 PT 50-500=5.5", "葡萄牙 PT 50-500=5.5"),
                ("葡萄牙 PT 15-49=5.0", "葡萄牙 PT 15-49=5.0"),
                ("希腊 50-500=5.5", "希腊 50-500=5.5"),
                ("希腊 15-49=5.0", "希腊 15-49=5.0"),
            ],
        )


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

    def test_country_amount_price_restriction_without_space_before_tail(self):
        from bookkeeping_core.template_engine import auto_detect_line_type

        result = auto_detect_line_type("US:1-499=5.68批量问")
        self.assertEqual(result["type"], "price")
        self.assertEqual(result["pattern"], "{country}:{amount}={price}{restriction}")

    def test_country_price_without_equals(self):
        from bookkeeping_core.template_engine import auto_detect_line_type

        result = auto_detect_line_type("土耳其0.13")
        self.assertEqual(result["type"], "price")
        self.assertEqual(result["pattern"], "{country}{price}")

    def test_country_space_price_without_equals(self):
        from bookkeeping_core.template_engine import auto_detect_line_type

        result = auto_detect_line_type("us 3.35")
        self.assertEqual(result["type"], "price")
        self.assertEqual(result["pattern"], "{country} {price}")

    def test_country_price_space_restriction(self):
        from bookkeeping_core.template_engine import auto_detect_line_type

        result = auto_detect_line_type("欧盟=5.35 图 代码问(批量问)")
        self.assertEqual(result["type"], "price")
        self.assertEqual(result["pattern"], "{country}={price} {restriction}")

    def test_double_equals_normalized_in_autodetect(self):
        """Lines with == should normalize to = and match as price."""
        from bookkeeping_core.template_engine import suggest_template_rules
        detections = suggest_template_rules("欧盟 EUR 50-500==6.55")
        prices = [d for d in detections if d["type"] == "price"]
        self.assertEqual(len(prices), 1)
        self.assertEqual(prices[0]["pattern"], "{country} {currency} {amount}={price}")

    def test_country_currency_colon_price(self):
        """e.g. 美金USD:5.20, 欧元EUR:6.00"""
        from bookkeeping_core.template_engine import auto_detect_line_type
        result = auto_detect_line_type("美金USD:5.20")
        self.assertEqual(result["type"], "price")
        self.assertEqual(result["pattern"], "{country}{currency}:{price}")
        self.assertEqual(result["fields"]["country"], "美金")
        self.assertEqual(result["fields"]["currency"], "USD")
        self.assertEqual(result["fields"]["price"], "5.20")

    def test_country_space_currency_colon_price(self):
        """e.g. 美 USD:5.78"""
        from bookkeeping_core.template_engine import auto_detect_line_type
        result = auto_detect_line_type("美 USD:5.78")
        self.assertEqual(result["type"], "price")
        self.assertEqual(result["pattern"], "{country} {currency}:{price}")

    def test_spaced_country_colon_price(self):
        """e.g. 新 加 坡:4.32"""
        from bookkeeping_core.template_engine import auto_detect_line_type
        result = auto_detect_line_type("新 加 坡:4.32")
        self.assertEqual(result["type"], "price")
        self.assertEqual(result["pattern"], "{country}:{price}")

    def test_note_line_skip(self):
        from bookkeeping_core.template_engine import auto_detect_line_type
        result = auto_detect_line_type("使用时间3-5分钟,只能使用")
        self.assertEqual(result["type"], "skip")

    def test_looks_like_quote_line_skips_timing_note(self):
        from bookkeeping_core.template_engine import looks_like_quote_line

        self.assertFalse(looks_like_quote_line("使用时间:5-20分钟左右反馈 时间未到勿催"))

    def test_bracket_country_price(self):
        from bookkeeping_core.template_engine import auto_detect_line_type

        result = auto_detect_line_type("UK【6.75】")
        self.assertEqual(result["type"], "price")
        self.assertEqual(result["pattern"], "{country}={price}")
        self.assertEqual(result["fields"]["country"], "GBP")

    def test_bracket_country_amount_form_factor_price(self):
        from bookkeeping_core.template_engine import auto_detect_line_type

        result = auto_detect_line_type("US-300-500 白卡 【5.38】")
        self.assertEqual(result["type"], "price")
        self.assertEqual(result["pattern"], "{country} {amount} {form_factor}={price}")
        self.assertEqual(result["fields"]["country"], "USD")
        self.assertEqual(result["fields"]["amount"], "300-500")
        self.assertEqual(result["fields"]["form_factor"], "横白卡")

    def test_suggest_template_rules(self):
        from bookkeeping_core.template_engine import suggest_template_rules, deduplicate_rules
        text = "【XBOX】\n加拿大=4.15\n巴西=1.03 新加坡=4.25\n10-1000=5.2\n使用时间3分钟"
        detections = suggest_template_rules(text)
        rules = deduplicate_rules(detections)
        patterns = {r["pattern"] for r in rules}
        self.assertIn("【{card_type}】", patterns)
        self.assertIn("{country}={price}", patterns)
        self.assertIn("{amount}={price}", patterns)

    def test_suggest_template_rules_supports_bracket_lines(self):
        from bookkeeping_core.template_engine import suggest_template_rules

        detections = suggest_template_rules(
            "【Steam】\nUSD-10-200【5.03】\nUK【6.75】  EUR【5.89】\nUS-300-500 白卡 【5.38】"
        )
        prices = [item for item in detections if item["type"] == "price"]
        self.assertEqual(len(prices), 4)
        patterns = {item["pattern"] for item in prices}
        self.assertIn("{country} {amount}={price}", patterns)
        self.assertIn("{country}={price}", patterns)
        self.assertIn("{country} {amount} {form_factor}={price}", patterns)


class TestQuoteDictionaryCountryAliases(unittest.TestCase):
    def test_eurozone_country_names_do_not_collapse_to_eur(self):
        from bookkeeping_core.quotes import _infer_country_or_currency

        self.assertEqual(_infer_country_or_currency("德国6.55收100-250卡图"), "德国")
        self.assertEqual(_infer_country_or_currency("法国5.4收50-250卡图"), "法国")
        self.assertEqual(_infer_country_or_currency("荷兰5.4收50-250卡图"), "荷兰")
        self.assertEqual(_infer_country_or_currency("奥地利5.45收100-250卡图"), "奥地利")

    def test_longer_country_alias_wins_over_single_character_alias(self):
        from bookkeeping_core.quotes import _infer_country_or_currency

        self.assertEqual(_infer_country_or_currency("墨西哥=0.265(500+)"), "MXN")
        self.assertEqual(_infer_country_or_currency("墨西哥 500=0.265"), "MXN")

    def test_missing_external_card_countries_map_to_expected_canonicals(self):
        from bookkeeping_core.quotes import _infer_country_or_currency

        self.assertEqual(_infer_country_or_currency("欧盟=5.1"), "EUR")
        self.assertEqual(_infer_country_or_currency("印度=0.055"), "INR")
        self.assertEqual(_infer_country_or_currency("泰国=0.16"), "THB")
        self.assertEqual(_infer_country_or_currency("印度尼西亚=0.0003"), "IDR")
        self.assertEqual(_infer_country_or_currency("土耳其0.13"), "TRY")
        self.assertEqual(_infer_country_or_currency("智利=0.005"), "CLP")
        self.assertEqual(_infer_country_or_currency("巴基斯坦0.015"), "PKR")
        self.assertEqual(_infer_country_or_currency("台湾=0.1"), "TWD")
        self.assertEqual(_infer_country_or_currency("日本=0.03"), "JPY")
        self.assertEqual(_infer_country_or_currency("沙特阿拉伯=1.4"), "SAR")
        self.assertEqual(_infer_country_or_currency("匈牙利 HUF 5000-50000=0.01"), "HUF")
        self.assertEqual(_infer_country_or_currency("南非=0.21"), "ZAR")
        self.assertEqual(_infer_country_or_currency("以色列=1.2"), "ILS")
        self.assertEqual(_infer_country_or_currency("乌拉圭 UYU 1500-50000=0.008"), "UYU")
        self.assertEqual(_infer_country_or_currency("保加利亚 BGN 25-1000==3.0"), "BGN")
        self.assertEqual(_infer_country_or_currency("罗马尼亚 RON 100-1000==1.0"), "RON")
        self.assertEqual(_infer_country_or_currency("葡萄牙 PT 50-500==5.5"), "葡萄牙")


class TestQuoteDictionaryCardAndFormFactorAliases(unittest.TestCase):
    def test_missing_card_type_aliases_map_to_expected_canonicals(self):
        from bookkeeping_core.quotes import _infer_card_type

        self.assertEqual(_infer_card_type("【===黄金雷蛇US===】"), "Razer")
        self.assertEqual(_infer_card_type("【====外卡雷蛇====】"), "Razer")
        self.assertEqual(_infer_card_type("【====绿蛇====】"), "Razer")
        self.assertEqual(_infer_card_type("美国雷蛇降价5.68"), "Razer")
        self.assertEqual(_infer_card_type("【====外卡XBOX====】"), "Xbox")
        self.assertEqual(_infer_card_type("美国xb降价5.11"), "Xbox")
        self.assertEqual(_infer_card_type("【Paysafecard 安全支付图密同价】"), "Paysafe")

    def test_missing_form_factor_aliases_map_to_expected_canonicals(self):
        from bookkeeping_core.quotes import normalize_quote_form_factor

        self.assertEqual(normalize_quote_form_factor("纯数字"), "代码")
        self.assertEqual(normalize_quote_form_factor("图密"), "代码")
        self.assertEqual(normalize_quote_form_factor("图密同价"), "代码")
        self.assertEqual(normalize_quote_form_factor("电子"), "代码")
        self.assertEqual(normalize_quote_form_factor("电子代码"), "代码")
        self.assertEqual(normalize_quote_form_factor("电子卡图"), "代码")
        self.assertEqual(normalize_quote_form_factor("code"), "代码")


class TestStrictSectionHarvest(unittest.TestCase):
    def test_derive_strict_section_preview(self):
        from bookkeeping_core.template_engine import derive_strict_section_preview

        preview = derive_strict_section_preview(
            raw_text="Apple USA\n10-50=5.20\n使用时间3分钟\n100-200=5.40",
            section_start_line=0,
            section_end_line=3,
            defaults={
                "section_label": "Apple USA",
                "priority": 10,
                "card_type": "Apple",
                "country_or_currency": "USD",
                "form_factor": "横白",
            },
            rows=[
                {"source_line_index": 1, "amount": "10-50", "price": "5.20"},
                {"source_line_index": 3, "amount": "100-200", "price": "5.40"},
            ],
            ignored_line_indexes=[],
        )

        self.assertTrue(preview["can_save"])
        self.assertEqual(len(preview["preview_rows"]), 2)
        self.assertEqual(preview["derived_section"]["lines"][0]["kind"], "literal")
        self.assertEqual(preview["derived_section"]["lines"][1]["pattern"], "{amount}={price}")
        self.assertEqual(preview["preview_rows"][0]["country_or_currency"], "USD")

    def test_unhandled_price_like_line_blocks_save(self):
        from bookkeeping_core.template_engine import derive_strict_section_preview

        preview = derive_strict_section_preview(
            raw_text="Apple USA\n10-50=5.20\n100-200=5.40",
            section_start_line=0,
            section_end_line=2,
            defaults={
                "section_label": "Apple USA",
                "priority": 10,
                "card_type": "Apple",
                "country_or_currency": "USD",
                "form_factor": "横白",
            },
            rows=[
                {"source_line_index": 1, "amount": "10-50", "price": "5.20"},
            ],
            ignored_line_indexes=[],
        )

        self.assertFalse(preview["can_save"])
        self.assertEqual(len(preview["unhandled_lines"]), 1)
        self.assertEqual(preview["unhandled_lines"][0]["source_line_index"], 2)

    def test_derive_strict_section_preview_collects_restriction_candidates(self):
        from bookkeeping_core.template_engine import derive_strict_section_preview

        preview = derive_strict_section_preview(
            raw_text=(
                "Apple USA\n"
                "#连卡先问\n"
                "10-50=5.20\n"
                "35分钟内赎回会撤账\n"
                "100-200=5.40"
            ),
            section_start_line=0,
            section_end_line=4,
            defaults={
                "section_label": "Apple USA",
                "priority": 10,
                "card_type": "Apple",
                "country_or_currency": "USD",
                "form_factor": "横白",
            },
            rows=[
                {"source_line_index": 2, "amount": "10-50", "price": "5.20"},
                {"source_line_index": 4, "amount": "100-200", "price": "5.40"},
            ],
            ignored_line_indexes=[],
        )

        self.assertTrue(preview["can_save"])
        self.assertEqual(
            [item["line"] for item in preview["restriction_candidates"]],
            ["#连卡先问", "35分钟内赎回会撤账"],
        )
        self.assertEqual(
            [line["kind"] for line in preview["derived_section"]["lines"]],
            ["literal", "restriction", "quote", "restriction", "quote"],
        )
        self.assertEqual(
            preview["preview_rows"][0]["restriction_text"],
            "#连卡先问 | 35分钟内赎回会撤账",
        )

    def test_derive_strict_section_preview_ignored_line_is_not_written_as_literal(self):
        from bookkeeping_core.template_engine import derive_strict_section_preview

        preview = derive_strict_section_preview(
            raw_text="Apple USA\n10-50=5.20\nuo123solhie",
            section_start_line=0,
            section_end_line=2,
            defaults={
                "section_label": "Apple USA",
                "priority": 10,
                "card_type": "Apple",
                "country_or_currency": "USD",
                "form_factor": "横白",
            },
            rows=[
                {"source_line_index": 1, "amount": "10-50", "price": "5.20"},
            ],
            ignored_line_indexes=[2],
        )

        self.assertTrue(preview["can_save"])
        self.assertEqual(
            [line["kind"] for line in preview["derived_section"]["lines"]],
            ["literal", "quote"],
        )
        self.assertEqual(preview["ignored_lines"][0]["line"], "uo123solhie")

    def test_derive_strict_section_preview_accepts_space_normalized_amount_labels(self):
        from bookkeeping_core.template_engine import derive_strict_section_preview

        preview = derive_strict_section_preview(
            raw_text=(
                "Apple USA\n"
                "100/150=5.43\n"
                "200- 450=5.44(50倍数)\n"
                "散卡25- 95=5.1(5倍数)"
            ),
            section_start_line=0,
            section_end_line=3,
            defaults={
                "section_label": "Apple USA",
                "priority": 10,
                "card_type": "Apple",
                "country_or_currency": "USD",
                "form_factor": "横白",
            },
            rows=[
                {"source_line_index": 1, "amount": "100/150", "price": "5.43"},
                {"source_line_index": 2, "amount": "200-450", "price": "5.44"},
                {"source_line_index": 3, "amount": "25-95", "price": "5.1"},
            ],
            ignored_line_indexes=[],
        )

        self.assertTrue(preview["can_save"])
        self.assertFalse(preview["unhandled_lines"])
        self.assertEqual(
            [item["amount"] for item in preview["preview_rows"]],
            ["100/150", "200-450", "25-95"],
        )

    def test_derive_strict_section_preview_rejects_slash_as_dash_amount(self):
        from bookkeeping_core.template_engine import derive_strict_section_preview

        preview = derive_strict_section_preview(
            raw_text="Apple USA\n100/150=5.43",
            section_start_line=0,
            section_end_line=1,
            defaults={
                "section_label": "Apple USA",
                "priority": 10,
                "card_type": "Apple",
                "country_or_currency": "USD",
                "form_factor": "横白",
            },
            rows=[
                {"source_line_index": 1, "amount": "100-150", "price": "5.43"},
            ],
            ignored_line_indexes=[],
        )

        self.assertFalse(preview["can_save"])
        self.assertEqual(preview["unhandled_lines"][0]["reason"], "amount_not_found")

    def test_derive_strict_section_preview_allows_fixed_amount_when_raw_line_has_no_amount(self):
        from bookkeeping_core.template_engine import TemplateConfig, derive_strict_section_preview, parse_message_with_template

        preview = derive_strict_section_preview(
            raw_text="📋 今日价目表:\ncvs:5.80元 (CVS/CVS Pharmacy)",
            section_start_line=0,
            section_end_line=1,
            defaults={
                "section_label": "阿栋",
                "priority": 10,
                "card_type": "CVS",
                "country_or_currency": "USD",
                "form_factor": "卡图",
            },
            rows=[
                {"source_line_index": 1, "amount": "10-500", "price": "5.8"},
            ],
            ignored_line_indexes=[],
        )

        self.assertTrue(preview["can_save"])
        self.assertFalse(preview["unhandled_lines"])
        self.assertEqual(preview["preview_rows"][0]["amount"], "10-500")
        quote_line = next(
            line for line in preview["derived_section"]["lines"] if line["kind"] == "quote"
        )
        self.assertEqual(quote_line["outputs"]["amount_range"], "10-500")

        config = TemplateConfig(
            version="strict-section-v1",
            sections=[
                {
                    **preview["derived_section"],
                    "id": "section-1",
                    "enabled": True,
                }
            ],
        )
        doc = parse_message_with_template(
            "📋 今日价目表:\ncvs:5.80元 (CVS/CVS Pharmacy)",
            config,
            source_group_key="strict:fixed-amount",
        )
        self.assertEqual(len(doc.rows), 1)
        self.assertEqual(doc.rows[0].amount_range, "10-500")

    def test_parse_message_with_strict_sections(self):
        from bookkeeping_core.template_engine import TemplateConfig, parse_message_with_template

        config = TemplateConfig(
            version="strict-section-v1",
            sections=[
                {
                    "id": "section-1",
                    "enabled": True,
                    "priority": 10,
                    "label": "Apple USA",
                    "defaults": {
                        "card_type": "Apple",
                        "country_or_currency": "USD",
                        "form_factor": "横白",
                    },
                    "lines": [
                        {"kind": "literal", "pattern": "Apple USA"},
                        {
                            "kind": "quote",
                            "pattern": "{amount}={price}",
                            "outputs": {
                                "card_type": "Apple",
                                "country_or_currency": "USD",
                                "form_factor": "横白",
                            },
                        },
                        {"kind": "literal", "pattern": "使用时间3分钟"},
                        {
                            "kind": "quote",
                            "pattern": "{amount}={price}",
                            "outputs": {
                                "card_type": "Apple",
                                "country_or_currency": "USD",
                                "form_factor": "横白",
                            },
                        },
                    ],
                }
            ],
        )

        doc = parse_message_with_template(
            "Apple USA\n10-50=5.20\n使用时间3分钟\n100-200=5.40",
            config,
            source_group_key="strict:G1",
        )
        self.assertEqual(len(doc.rows), 2)
        self.assertEqual(len(doc.exceptions), 0)
        self.assertEqual(doc.rows[0].card_type, "Apple")
        self.assertEqual(doc.rows[0].country_or_currency, "USD")
        self.assertEqual(doc.rows[1].amount_range, "100-200")
        self.assertEqual(doc.parser_version, "strict-section-v1")

    def test_parse_message_with_strict_sections_preserves_discrete_amount_label(self):
        from bookkeeping_core.template_engine import TemplateConfig, parse_message_with_template

        config = TemplateConfig(
            version="strict-section-v1",
            sections=[
                {
                    "id": "section-1",
                    "enabled": True,
                    "priority": 10,
                    "label": "Apple USA",
                    "defaults": {
                        "card_type": "Apple",
                        "country_or_currency": "USD",
                        "form_factor": "横白",
                    },
                    "lines": [
                        {
                            "kind": "quote",
                            "pattern": "{amount}={price}",
                            "outputs": {
                                "card_type": "Apple",
                                "country_or_currency": "USD",
                                "form_factor": "横白",
                            },
                        },
                    ],
                }
            ],
        )

        doc = parse_message_with_template(
            "100/150=5.43",
            config,
            source_group_key="strict:G2",
        )
        self.assertEqual(len(doc.rows), 1)
        self.assertEqual(doc.rows[0].amount_range, "100/150")

    def test_parse_message_with_strict_sections_skips_changed_noise_tail(self):
        from bookkeeping_core.template_engine import TemplateConfig, parse_message_with_template

        config = TemplateConfig(
            version="strict-section-v1",
            sections=[
                {
                    "id": "section-1",
                    "enabled": True,
                    "priority": 10,
                    "label": "Apple USA",
                    "defaults": {
                        "card_type": "Apple",
                        "country_or_currency": "USD",
                        "form_factor": "横白",
                    },
                    "lines": [
                        {"kind": "literal", "pattern": "Apple USA"},
                        {
                            "kind": "quote",
                            "pattern": "{amount}={price}",
                            "outputs": {
                                "card_type": "Apple",
                                "country_or_currency": "USD",
                                "form_factor": "横白",
                            },
                        },
                    ],
                }
            ],
        )

        doc = parse_message_with_template(
            "Apple USA\n10-50=5.20\nuo999abc",
            config,
            source_group_key="strict:G3",
        )
        self.assertEqual(len(doc.rows), 1)
        self.assertFalse(doc.exceptions)

    def test_parse_message_with_strict_sections_attaches_restriction_lines(self):
        from bookkeeping_core.template_engine import TemplateConfig, parse_message_with_template

        config = TemplateConfig(
            version="strict-section-v1",
            sections=[
                {
                    "id": "section-1",
                    "enabled": True,
                    "priority": 10,
                    "label": "Apple USA",
                    "defaults": {
                        "card_type": "Apple",
                        "country_or_currency": "USD",
                        "form_factor": "横白",
                    },
                    "lines": [
                        {"kind": "literal", "pattern": "Apple USA"},
                        {"kind": "restriction", "pattern": "#连卡先问"},
                        {
                            "kind": "quote",
                            "pattern": "{amount}={price}",
                            "outputs": {
                                "card_type": "Apple",
                                "country_or_currency": "USD",
                                "form_factor": "横白",
                            },
                        },
                        {"kind": "restriction", "pattern": "35分钟内赎回会撤账"},
                    ],
                }
            ],
        )

        doc = parse_message_with_template(
            "Apple USA\n#连卡先问\n10-50=5.20\n35分钟内赎回会撤账",
            config,
            source_group_key="strict:G3",
        )
        self.assertEqual(len(doc.rows), 1)
        self.assertEqual(len(doc.exceptions), 0)
        self.assertEqual(doc.rows[0].restriction_text, "#连卡先问 | 35分钟内赎回会撤账")


class TestResultTemplateFlow(unittest.TestCase):
    SAMPLE_RAW = (
        "【 影子steam价格表】\n"
        "美金USD :5.20\n"
        "欧元EUR :6.00\n"
        "英镑GBP :6.85\n"
        "加元CAD :3.75\n"
        "澳元AUD :3.65\n"
        "新西兰NZD ：3.05\n"
        "瑞士CHF ：6.40\n"
        "波兰PLN  :1.39\n"
        "*\n"
        "报其他国家按到账美金*5.20\n"
        "【影子】\n"
        "=== 雷蛇/Razer ===\n"
        "美  USD ：5.78\n"
        "新 加 坡 ：4.32\n"
        "加 拿 大 ：4.20\n"
        "澳大利亚：4.07\n"
        "新西兰   ：3.25\n"
        "马来西亚：1.48\n"
        "推荐客户有🧧（200-2000)\n"
        "上不封顶"
    )

    SAMPLE_RESULT_TEXT = (
        "[默认]\n"
        "形态=card\n"
        "\n"
        "[Steam]\n"
        "USD=5.20\n"
        "EUR=6.00\n"
        "GBP=6.85\n"
        "CAD=3.75\n"
        "AUD=3.65\n"
        "NZD=3.05\n"
        "CHF=6.40\n"
        "PLN=1.39\n"
        "\n"
        "[Razer]\n"
        "USD=5.78\n"
        "SGD=4.32\n"
        "CAD=4.20\n"
        "AUD=4.07\n"
        "NZD=3.25\n"
        "MYR=1.48\n"
    )

    GROUP_FALLBACK_RAW = (
        "#晚班更新\n"
        "US\n"
        "10-195=5.25（5倍数）\n"
        "----------------------------\n"
        "50=5.3\n"
        "100/150=5.43\n"
        "200- 450=5.44（50倍数）\n"
        "300/400/500=5.45\n"
        "【2- 8分钟反馈】\n"
        "【有扫卡记录的提醒我下。】\n"
        "------------------------------\n"
        "\n"
        "wovxteqeox"
    )

    GROUP_FALLBACK_RESULT_TEXT = (
        "[默认]\n"
        "国家 / 币种=USD\n"
        "形态=横白卡\n"
        "\n"
        "[Steam]\n"
        "10-195=5.25\n"
        "50=5.3\n"
        "100/150=5.43\n"
        "200-450=5.44\n"
        "300/400/500=5.45\n"
    )
    BRACKET_RAW = (
        "【Steam蒸汽】\n"
        "USD-10-200【5.03】\n"
        "UK【6.75】  EUR【5.89】\n"
        "CAD【3.62】 AUD【3.54】\n"
        "NZD【2.92】CHF【6.37】\n"
        "其余国家按到账美金*5.02\n"
        "====================\n"
        "【苹果-快加/快刷】\n"
        "US-300-500   白卡   【5.38】 \n"
        "US-200-450   白卡   【5.38】 \n"
        "US-100/150   白卡   【5.38】   \n"
        "US-20-90       白卡   【5.2】 5倍数 \n"
        "US-25-145    卡密    【5.11】 5倍数\n"
    )
    BRACKET_RESULT_TEXT = (
        "[默认]\n"
        "国家 / 币种=USD\n"
        "形态=不限\n"
        "\n"
        "[Steam]\n"
        "10-200=5.03\n"
        "GBP=6.75\n"
        "EUR=5.89\n"
        "CAD=3.62\n"
        "AUD=3.54\n"
        "NZD=2.92\n"
        "CHF=6.37\n"
        "\n"
        "[默认]\n"
        "国家 / 币种=USD\n"
        "形态=横白卡\n"
        "\n"
        "[Apple]\n"
        "300-500=5.38\n"
        "200-450=5.38\n"
        "100/150=5.38\n"
        "20-90=5.2\n"
        "\n"
        "[默认]\n"
        "国家 / 币种=USD\n"
        "形态=代码\n"
        "\n"
        "[Apple]\n"
        "25-145=5.11\n"
        "\n"
        "[说明]\n"
        "其余国家按到账美金*5.02\n"
    )
    MULTI_SECTION_SAME_CARD_RAW = (
        "=【#iTunes 快刷】==\n"
        "白25-175=5.2【5倍】快加审图\n"
        "100-150=5.42【50倍】只要稳卡\n"
        "200-450=5.42【50倍】只要稳卡\n"
        "300-400=5.42【100倍】 只要稳卡\n"
        "500=5.42【100倍】 只要稳卡\n"
        "纯代码15-90=5.0【5倍】只要稳卡\n"
        "#快速网单1-5分钟\n"
    )
    MULTI_SECTION_SAME_CARD_RESULT_TEXT = (
        "[默认]\n"
        "国家 / 币种=USD\n"
        "形态=横白卡\n"
        "\n"
        "[Apple]\n"
        "25-175=5.2\n"
        "100-150=5.42\n"
        "200-450=5.42\n"
        "300-400=5.42\n"
        "500=5.42\n"
        "\n"
        "[默认]\n"
        "国家 / 币种=USD\n"
        "形态=代码\n"
        "\n"
        "[Apple]\n"
        "15-90=5.0\n"
    )

    def test_suggest_result_template_text_prefills_card_blocks(self):
        from bookkeeping_core.template_engine import suggest_result_template_text

        suggested = suggest_result_template_text(self.SAMPLE_RAW)

        self.assertIn("[默认]", suggested)
        self.assertIn("[Steam]", suggested)
        self.assertIn("[Razer]", suggested)
        self.assertIn("USD=5.20", suggested)
        self.assertIn("SGD=4.32", suggested)
        self.assertNotIn("[说明]", suggested)

    def test_derive_result_template_preview_handles_two_card_types(self):
        from bookkeeping_core.template_engine import derive_result_template_preview

        preview = derive_result_template_preview(
            raw_text=self.SAMPLE_RAW,
            result_template_text=self.SAMPLE_RESULT_TEXT,
        )

        self.assertTrue(preview["can_save"])
        self.assertEqual(len(preview["derived_sections"]), 2)
        self.assertEqual(len(preview["preview_rows"]), 14)
        steam_rows = [row for row in preview["preview_rows"] if row["card_type"] == "Steam"]
        razer_rows = [row for row in preview["preview_rows"] if row["card_type"] == "Razer"]
        self.assertEqual(len(steam_rows), 8)
        self.assertEqual(len(razer_rows), 6)
        self.assertTrue(preview["strict_replay_ok"])
        self.assertTrue(any(note == "报其他国家按到账美金*5.20" for note in preview["notes"]))
        self.assertTrue(any(note == "推荐客户有🧧(200-2000)" for note in preview["notes"]))
        self.assertTrue(any(note == "上不封顶" for note in preview["notes"]))

    def test_derive_result_template_preview_falls_back_to_chat_name_card_type(self):
        from bookkeeping_core.template_engine import derive_result_template_preview, suggest_result_template_text

        suggested = suggest_result_template_text(self.GROUP_FALLBACK_RAW, chat_name="Steam 夜班群")
        self.assertIn("[Steam]", suggested)
        self.assertNotIn("[unknown]", suggested)

        preview = derive_result_template_preview(
            raw_text=self.GROUP_FALLBACK_RAW,
            result_template_text=self.GROUP_FALLBACK_RESULT_TEXT,
            chat_name="Steam 夜班群",
        )

        self.assertTrue(preview["can_save"])
        self.assertFalse(preview["errors"])
        self.assertTrue(any("已按群名“Steam 夜班群”回退" in item for item in preview["warnings"]))
        self.assertTrue(preview["strict_replay_ok"])
        self.assertEqual(len(preview["derived_sections"]), 1)
        self.assertEqual(len(preview["preview_rows"]), 5)
        self.assertTrue(
            any(
                row["amount"] == "100-150"
                and row["price"] == "5.43"
                and row["country_or_currency"] == "USD"
                for row in preview["preview_rows"]
            )
        )

    def test_derive_result_template_preview_prefers_group_default_card_type(self):
        from bookkeeping_core.template_engine import derive_result_template_preview, suggest_result_template_text

        raw_text = (
            "#US秒刷更新\n"
            "10-195=5.15（5倍数）\n"
            "50=5.3\n"
            "100/150=5.4\n"
            "200-450=5.42（50倍）\n"
        )
        result_text = (
            "[默认]\n"
            "国家 / 币种=USD\n"
            "形态=不限\n\n"
            "[unknown]\n"
            "10-195=5.15\n"
            "50=5.3\n"
            "100/150=5.4\n"
            "200-450=5.42\n"
        )

        suggested = suggest_result_template_text(
            raw_text,
            chat_name="C-523【QH-IT-设备组-禁赎回",
            default_card_type="Apple",
        )
        self.assertIn("[Apple]", suggested)
        self.assertNotIn("[unknown]", suggested)

        preview = derive_result_template_preview(
            raw_text=raw_text,
            result_template_text=result_text,
            chat_name="C-523【QH-IT-设备组-禁赎回",
            default_card_type="Apple",
        )

        self.assertTrue(preview["can_save"])
        self.assertFalse(preview["errors"])
        self.assertTrue(all(row["card_type"] == "Apple" for row in preview["preview_rows"]))
        self.assertTrue(
            any(
                row["amount"] == "200-450"
                and row["price"] == "5.42"
                and row["country_or_currency"] == "USD"
                for row in preview["preview_rows"]
            )
        )

    def test_derive_result_template_preview_preserves_stable_prefix_in_quote_pattern(self):
        from bookkeeping_core.template_engine import derive_result_template_preview

        preview = derive_result_template_preview(
            raw_text=(
                "卡图：100/150=5.4\n"
                "卡图：200/350/450=5.4\n"
                "卡图：300/400/500=5.4"
            ),
            result_template_text=(
                "[默认]\n"
                "国家 / 币种=USD\n"
                "形态=横白卡\n"
                "\n"
                "[Steam]\n"
                "100/150=5.4\n"
                "200/350/450=5.4\n"
                "300/400/500=5.4\n"
            ),
            chat_name="Steam 卡图群",
        )

        self.assertTrue(preview["can_save"])
        self.assertTrue(preview["strict_replay_ok"])
        patterns = [
            line["pattern"]
            for section in preview["derived_sections"]
            for line in section["lines"]
        ]
        self.assertIn("卡图:{amount}={price}", patterns)

    def test_derive_result_template_preview_supports_same_card_with_second_defaults_block(self):
        from bookkeeping_core.template_engine import derive_result_template_preview

        preview = derive_result_template_preview(
            raw_text=self.MULTI_SECTION_SAME_CARD_RAW,
            result_template_text=self.MULTI_SECTION_SAME_CARD_RESULT_TEXT,
            chat_name="C-502CH-143-夕希&臻韵IT收卡群",
        )

        self.assertTrue(preview["can_save"])
        self.assertFalse(preview["errors"])
        self.assertTrue(preview["strict_replay_ok"])
        self.assertEqual(len(preview["derived_sections"]), 2)
        self.assertEqual(preview["derived_sections"][0]["defaults"]["form_factor"], "横白卡")
        self.assertEqual(preview["derived_sections"][1]["defaults"]["form_factor"], "代码")
        code_row = next(
            row for row in preview["preview_rows"] if row["amount"] == "15-90"
        )
        self.assertEqual(code_row["form_factor"], "代码")
        self.assertTrue(
            any("第一条报价行开始编译骨架" in item for item in preview["warnings"])
        )

    def test_derive_result_template_preview_aligns_repeated_same_card_type_sections(self):
        from bookkeeping_core.template_engine import derive_result_template_preview

        raw_text = (
            "【===黄金雷蛇US===】\n"
            "US:1-499=5.68批量问\n"
            "【====外卡雷蛇====】\n"
            "欧盟=5.1 英国=5.1\n"
            "土耳其0.13 智利=0.005\n"
        )
        result_template_text = (
            "[默认]\n"
            "国家 / 币种=USD\n"
            "形态=不限\n"
            "\n"
            "[Razer]\n"
            "1-499=5.68\n"
            "\n"
            "[默认]\n"
            "形态=不限\n"
            "\n"
            "[Razer]\n"
            "EUR=5.1\n"
            "GBP=5.1\n"
            "TRY=0.13\n"
            "CLP=0.005\n"
        )

        preview = derive_result_template_preview(
            raw_text=raw_text,
            result_template_text=result_template_text,
        )

        self.assertTrue(preview["can_save"], preview["errors"])
        self.assertTrue(preview["strict_replay_ok"], preview["strict_replay_errors"])
        self.assertEqual(len(preview["preview_rows"]), 5)

    def test_suggest_result_template_text_supports_bracket_quote_cards(self):
        from bookkeeping_core.template_engine import suggest_result_template_text

        suggested = suggest_result_template_text(self.BRACKET_RAW, chat_name="Steam蒸汽")

        self.assertIn("[Steam]", suggested)
        self.assertIn("[Apple]", suggested)
        self.assertIn("10-200=5.03", suggested)
        self.assertIn("GBP=6.75", suggested)
        self.assertIn("100/150=5.38", suggested)
        self.assertIn("形态=代码", suggested)

    def test_suggest_result_template_text_avoids_polluting_country_defaults_with_form_factor_tokens(self):
        from bookkeeping_core.template_engine import suggest_result_template_text

        raw_text = (
            "iTunes US 快刷\n"
            "横白卡图：300/400/500=5.41（单张清晰）\n"
            "横白卡图：100/150=5.38（单张清晰）\n"
            "整卡卡密：100-500=5.2（50倍数）\n"
        )

        suggested = suggest_result_template_text(
            raw_text,
            chat_name="C-537-【tm】-itunes",
            default_card_type="Apple",
        )

        self.assertIn("[Apple]", suggested)
        self.assertIn("国家 / 币种=USD", suggested)
        self.assertIn("形态=横白卡", suggested)
        self.assertIn("形态=代码", suggested)
        self.assertNotIn("国家 / 币种=横白卡图", suggested)
        self.assertNotIn("国家 / 币种=整卡卡密", suggested)

    def test_derive_result_template_preview_supports_bracket_quote_cards(self):
        from bookkeeping_core.template_engine import derive_result_template_preview

        preview = derive_result_template_preview(
            raw_text=self.BRACKET_RAW,
            result_template_text=self.BRACKET_RESULT_TEXT,
            chat_name="Steam蒸汽",
        )

        self.assertTrue(preview["can_save"])
        self.assertFalse(preview["errors"])
        self.assertTrue(preview["strict_replay_ok"])
        self.assertEqual(len(preview["preview_rows"]), 12)
        self.assertEqual(len(preview["derived_sections"]), 3)
        self.assertTrue(any(note == "其余国家按到账美金*5.02" for note in preview["notes"]))
        self.assertTrue(
            any(
                row["card_type"] == "Steam"
                and row["country_or_currency"] == "GBP"
                and row["price"] == "6.75"
                for row in preview["preview_rows"]
            )
        )
        self.assertTrue(
            any(
                row["card_type"] == "Apple"
                and row["amount"] == "100-150"
                and row["price"] == "5.38"
                for row in preview["preview_rows"]
            )
        )

    def test_suggest_result_template_and_preview_support_large_mixed_quote_sheet(self):
        from bookkeeping_core.template_engine import (
            derive_result_template_preview,
            suggest_result_template_text,
        )

        raw_text = (
            "【===黄金雷蛇US===】\n"
            "US:  1-499=5.68批量问\n"
            "\n"
            "【====外卡雷蛇====】\n"
            "欧盟=5.1    英国=5.1\n"
            "巴西=1.03          新加坡 =4.25\n"
            "澳大利亚=4.03   加拿大=4.15\n"
            "墨西哥=0.326    菲律宾= 0.095\n"
            "马来西亚=1.42    印度=0.055\n"
            "泰国=0.16         印度尼西亚=0.0003\n"
            "香港 =0.65         新西兰 =3.15\n"
            "土耳其0.13         智利=0.005\n"
            "巴基斯坦0.015    哥伦比亚=0.001\n"
            "\n"
            "【====绿蛇====】\n"
            "10-1000=5.2\n"
            "使用时间3-5分钟，只能使用\n"
            "10的倍数，只要新版绿蛇，16位英文字母\n"
            "\n"
            "【===XBOX===】\n"
            "美国 10-250=5.11（5的倍数）\n"
            "\n"
            "【====外卡XBOX====】\n"
            "欧盟  =5.35  图 代码问（批量问）\n"
            "加拿大=3.4（代码批量问）英国=6.15卡图\n"
            "挪威=0.43          瑞士=5.0卡图\n"
            "丹麦=0.55          澳大利亚=3.55\n"
            "新西兰=2.8        新加坡=3.55\n"
            "瑞典=0.43          香港=0.7\n"
            "台湾=0.1            哥伦比亚=0.0011\n"
            "墨西哥=0.275       日本=0.03\n"
            "沙特阿拉伯=1.4   智利=0.005\n"
            "波兰=1.05           印度=0.06\n"
            "捷克=0.12           匈牙利=0.008\n"
            "南非=0.21           巴西=0.81\n"
            "以色列=1.2          韩国=0.0035\n"
            "注:   代码问价 连卡问！！！xb\n"
            "注:   电子卡图  纸质算代码\n"
            "\n"
            "【Paysafecard 安全支付图密同价】\n"
            "---------------------------------------\n"
            "欧盟 EUR          50-500==6.56\n"
            "美国 USD        20-500==暂停\n"
            "英国 GBP          50-500==7.0\n"
            "波兰 PLN          50-500==1.3\n"
            "丹麦 DKK          100-5000=0.75\n"
            "捷克 CZK          300-3000=0.2\n"
            "瑞典 SEK           200-5000=0.5\n"
            "挪威 NOK         200-5000=0.47\n"
            "加拿大 CAD      25-500=3.5\n"
            "新西兰 NZD      50-500=3.0\n"
            "墨西哥 MXN     200-5000=0.23\n"
            "乌拉圭 UYU      1500-50000=0.008\n"
            "匈牙利 HUF      5000-50000=0.01\n"
            "保加利亚 BGN  25-1000==3.0\n"
            "澳大利亚 AUD  25-500==3.2\n"
            "罗马尼亚 RON 100-1000==1.0\n"
            "葡萄牙 PT 50-500==5.5  15-49=5.0\n"
            "希腊       50-500=5.5  15-49=5.0\n"
            "注：希腊 葡萄牙加卡可能出现死户 死户不赔\n"
            "\n"
            "欧盟/意大利/  支付卡不收\n"
            "--------------------------------------------\n"
            "注；发卡请注明国家、面值\n"
            "EUR-15-49【6.1】\n"
            "UK- 50 以下【6.8】\n"
            "注：使用时间5-15分钟\n"
            "消费期间勿查卡/会导致锁卡\n"
            "二人同时使用/会导致锁卡\n"
            "国家不一致/会导致锁卡\n"
            "请务必发送准确的国家，国家错误100%锁\n"
            "\n"
            "======【Roblox】======\n"
            "us 3.35\n"
            "所有国家都按到账美金*3.35\n"
            "【RI  RB  RE/纯数字】\n"
        )

        suggested = suggest_result_template_text(raw_text, chat_name="综合报价群")
        self.assertIn("1-499=5.68", suggested)
        self.assertIn("TRY=0.13", suggested)
        self.assertIn("PKR=0.015", suggested)
        self.assertIn("USD=3.35", suggested)
        self.assertIn("15-49=5.0", suggested)

        preview = derive_result_template_preview(
            raw_text=raw_text,
            result_template_text=suggested,
            chat_name="综合报价群",
        )

        self.assertTrue(preview["can_save"], preview["errors"])
        self.assertTrue(preview["strict_replay_ok"], preview["strict_replay_errors"])
        self.assertFalse(preview["errors"])
        self.assertGreaterEqual(len(preview["preview_rows"]), 60)

    def test_parse_message_with_group_parser_ignores_non_price_text(self):
        from bookkeeping_core.template_engine import TemplateConfig, parse_message_with_template

        config = TemplateConfig(
            version="group-parser-v1",
            sections=[
                {
                    "id": "section-1",
                    "enabled": True,
                    "priority": 10,
                    "label": "Steam",
                    "defaults": {
                        "card_type": "Steam",
                        "country_or_currency": "USD",
                        "form_factor": "横白卡",
                    },
                    "lines": [
                        {
                            "kind": "quote",
                            "pattern": "{amount}={price}(5倍数)",
                            "outputs": {
                                "card_type": "Steam",
                                "country_or_currency": "USD",
                                "form_factor": "横白卡",
                                "amount_range": "10-195",
                            },
                        },
                        {
                            "kind": "quote",
                            "pattern": "{amount}={price}",
                            "outputs": {
                                "card_type": "Steam",
                                "country_or_currency": "USD",
                                "form_factor": "横白卡",
                                "amount_range": "50",
                            },
                        },
                        {
                            "kind": "quote",
                            "pattern": "{amount}={price}",
                            "outputs": {
                                "card_type": "Steam",
                                "country_or_currency": "USD",
                                "form_factor": "横白卡",
                                "amount_range": "100-150",
                            },
                        },
                        {
                            "kind": "quote",
                            "pattern": "{amount}={price}(50倍数)",
                            "outputs": {
                                "card_type": "Steam",
                                "country_or_currency": "USD",
                                "form_factor": "横白卡",
                                "amount_range": "200-450",
                            },
                        },
                        {
                            "kind": "quote",
                            "pattern": "{amount}={price}",
                            "outputs": {
                                "card_type": "Steam",
                                "country_or_currency": "USD",
                                "form_factor": "横白卡",
                                "amount_range": "300-500",
                            },
                        },
                    ],
                }
            ],
        )

        doc = parse_message_with_template(
            self.GROUP_FALLBACK_RAW,
            config,
            source_group_key="group-parser:G1",
        )

        self.assertEqual(len(doc.rows), 5)
        self.assertFalse(doc.exceptions)
        self.assertEqual(doc.parser_version, "group-parser-v1")
        self.assertTrue(any(row.amount_range == "200-450" and row.price == 5.44 for row in doc.rows))

    def test_parse_message_with_strict_sections_supports_price_only_pattern(self):
        from bookkeeping_core.template_engine import TemplateConfig, parse_message_with_template

        config = TemplateConfig(
            version="strict-section-v1",
            sections=[
                {
                    "id": "section-1",
                    "enabled": True,
                    "priority": 10,
                    "label": "Steam",
                    "defaults": {"card_type": "Steam", "form_factor": "card"},
                    "lines": [
                        {"kind": "literal", "pattern": "【 影子steam价格表】"},
                        {
                            "kind": "quote",
                            "pattern": "美金USD:{price}",
                            "outputs": {
                                "card_type": "Steam",
                                "country_or_currency": "USD",
                                "form_factor": "card",
                                "amount_range": "不限",
                            },
                        },
                    ],
                }
            ],
        )

        doc = parse_message_with_template(
            "【 影子steam价格表】\n美金USD :5.20",
            config,
            source_group_key="strict:G2",
        )

        self.assertEqual(len(doc.rows), 1)
        self.assertEqual(doc.rows[0].card_type, "Steam")
        self.assertEqual(doc.rows[0].country_or_currency, "USD")
        self.assertEqual(doc.rows[0].amount_range, "不限")
        self.assertEqual(doc.rows[0].price, 5.2)

    def test_parse_message_with_strict_sections_allows_spaces_inside_amount_variable(self):
        from bookkeeping_core.template_engine import TemplateConfig, parse_message_with_template

        config = TemplateConfig(
            version="strict-section-v1",
            sections=[
                {
                    "id": "section-1",
                    "enabled": True,
                    "priority": 10,
                    "label": "Apple",
                    "defaults": {
                        "card_type": "Apple",
                        "country_or_currency": "USD",
                        "form_factor": "横白卡",
                    },
                    "lines": [
                        {"kind": "literal", "pattern": "#晚班更新"},
                        {"kind": "literal", "pattern": "US"},
                        {
                            "kind": "quote",
                            "pattern": "{amount}={price}(50倍数)",
                            "outputs": {
                                "card_type": "Apple",
                                "country_or_currency": "USD",
                                "form_factor": "横白卡",
                                "amount_range": "200-450",
                            },
                        },
                    ],
                }
            ],
        )

        doc = parse_message_with_template(
            "#晚班更新\nUS\n200- 450=5.44（50倍数）",
            config,
            source_group_key="strict:G3",
        )

        self.assertEqual(len(doc.rows), 1)
        self.assertFalse(doc.exceptions)
        self.assertEqual(doc.rows[0].amount_range, "200-450")
        self.assertEqual(doc.rows[0].price, 5.44)


if __name__ == "__main__":
    unittest.main()
