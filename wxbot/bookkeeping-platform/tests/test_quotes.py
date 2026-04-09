from __future__ import annotations

import unittest

from bookkeeping_core.contracts import NormalizedMessageEnvelope
from bookkeeping_core.database import BookkeepingDB
from bookkeeping_core.runtime import UnifiedBookkeepingRuntime
from tests.support.postgres_test_case import PostgresTestCase


class QuoteBackendTests(PostgresTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.db = BookkeepingDB(self.make_dsn("quotes"))
        self.runtime = UnifiedBookkeepingRuntime(
            db=self.db,
            master_users=["master-user"],
            export_dir=self.temp_path / "exports",
        )

    def tearDown(self) -> None:
        self.db.close()
        super().tearDown()

    def _send(self, *, chat_id: str, message_id: str, text: str, received_at: str) -> None:
        envelope = NormalizedMessageEnvelope.from_dict(
            {
                "platform": "wechat",
                "message_id": message_id,
                "chat_id": chat_id,
                "chat_name": f"报价群-{chat_id}",
                "is_group": True,
                "sender_id": f"user-{chat_id}",
                "sender_name": f"来源{chat_id}",
                "sender_kind": "user",
                "content_type": "text",
                "text": text,
                "received_at": received_at,
            }
        )
        self.runtime.process_envelope(envelope)

    def test_section_quote_document_publishes_price_rows(self) -> None:
        text = """【Xbox】#非5倍数问 #批量先问！
US：10~250/5倍数图密=5.0
UK卡图/纸质=6.2 （电子/代码6.15）
═════════════
【Razer Gold 雷蛇】
美国=5.83
新加坡=4.30
加拿大=4.15
澳大利亚：4.00
新西兰：3.23
"""
        self._send(
            chat_id="g-quote-1",
            message_id="quote-1",
            text=text,
            received_at="2026-04-08 09:00:00",
        )

        docs = self.db.conn.execute("SELECT * FROM quote_documents").fetchall()
        self.assertEqual(len(docs), 1)
        rows, total = self.db.list_quote_history(card_type="Xbox")
        self.assertGreaterEqual(total, 2)
        self.assertTrue(any(row["country_or_currency"] == "USD" for row in rows))
        board = self.db.list_quote_board()
        self.assertTrue(any(row["card_type"] == "Xbox" and float(row["price"]) == 5.0 for row in board))
        self.assertTrue(any(row["card_type"] == "Razer" and row["country_or_currency"] == "USD" for row in board))

    def test_same_source_sku_overwrites_previous_active_row(self) -> None:
        first = """【Steam 蒸汽】
USD美元=5.10
EUR欧元=5.88
"""
        second = """【Steam 蒸汽】
USD美元=5.30
EUR欧元=6.09
"""
        self._send(
            chat_id="g-steam",
            message_id="steam-1",
            text=first,
            received_at="2026-04-08 10:00:00",
        )
        self._send(
            chat_id="g-steam",
            message_id="steam-2",
            text=second,
            received_at="2026-04-08 10:30:00",
        )

        history, total = self.db.list_quote_history(
            card_type="Steam",
            country_or_currency="USD",
            amount_range="不限",
            form_factor="不限",
        )
        self.assertEqual(total, 2)
        self.assertEqual(history[0]["price"], 5.30)
        self.assertEqual(history[1]["price"], 5.10)
        self.assertEqual(history[1]["expires_at"], "2026-04-08 10:30:00")

        board = self.db.list_quote_board()
        steam_usd = next(
            row
            for row in board
            if row["card_type"] == "Steam" and row["country_or_currency"] == "USD"
        )
        self.assertEqual(float(steam_usd["price"]), 5.30)
        self.assertEqual(steam_usd["message_id"], "steam-2")
        self.assertEqual(steam_usd["change_status"], "up")
        self.assertEqual(steam_usd["previous_price"], 5.10)
        self.assertEqual(steam_usd["price_change"], 0.20)

    def test_short_quote_without_context_becomes_exception(self) -> None:
        self._send(
            chat_id="g-short",
            message_id="short-1",
            text="uk 10\n6.25",
            received_at="2026-04-08 11:00:00",
        )

        docs = self.db.conn.execute("SELECT * FROM quote_documents").fetchall()
        self.assertEqual(len(docs), 1)
        rows = self.db.conn.execute("SELECT * FROM quote_price_rows").fetchall()
        self.assertEqual(len(rows), 0)
        exceptions, total = self.db.list_quote_exceptions()
        self.assertGreaterEqual(total, 1)
        self.assertTrue(any(row["reason"] == "missing_context" for row in exceptions))

    def test_open_inquiry_context_captures_short_price_reply(self) -> None:
        inquiry_id = self.db.create_quote_inquiry_context(
            platform="wechat",
            source_group_key="wechat:g-inquiry",
            chat_id="g-inquiry",
            chat_name="询价群",
            card_type="Apple",
            country_or_currency="GBP",
            amount_range="10",
            form_factor="不限",
            expires_at="2026-04-08 11:30:00",
        )

        self._send(
            chat_id="g-inquiry",
            message_id="inquiry-reply-1",
            text="6.25",
            received_at="2026-04-08 11:00:00",
        )

        rows, total = self.db.list_quote_history(
            card_type="Apple",
            country_or_currency="GBP",
            amount_range="10",
            form_factor="不限",
        )
        self.assertEqual(total, 1)
        self.assertEqual(rows[0]["price"], 6.25)
        context = self.db.conn.execute(
            "SELECT status, resolved_message_id FROM quote_inquiry_contexts WHERE id = ?",
            (inquiry_id,),
        ).fetchone()
        self.assertEqual(context["status"], "resolved")
        self.assertEqual(context["resolved_message_id"], "inquiry-reply-1")

    def test_apple_50x_quote_matches_supplier_amount_query(self) -> None:
        self.db.upsert_quote_group_profile(
            platform="wechat",
            chat_id="g-apple",
            chat_name="Apple测试群",
            default_card_type="Apple",
            parser_template="apple_modifier_sheet",
            stale_after_minutes=30,
        )
        self._send(
            chat_id="g-apple",
            message_id="apple-1",
            text="""US横白卡：100-150=5.45（50倍数）
#代码-0.3
""",
            received_at="2026-04-08 12:00:00",
        )

        matches, total = self.db.list_quote_matches(
            card_type="Apple",
            country_or_currency="USD",
            amount=250,
            form_factor="代码",
        )
        self.assertEqual(total, 1)
        self.assertEqual(matches[0]["price"], 5.15)
        self.assertEqual(matches[0]["amount_display"], "100-150 / 50X")

    def test_group_fixed_sheet_parses_amount_equals_price_lines(self) -> None:
        self.db.upsert_quote_group_profile(
            platform="wechat",
            chat_id="g-apple-fixed",
            chat_name="Apple固定模板群",
            default_card_type="Apple",
            default_country_or_currency="USD",
            default_form_factor="横白卡",
            parser_template="group_fixed_sheet",
            stale_after_minutes=30,
        )
        self._send(
            chat_id="g-apple-fixed",
            message_id="apple-fixed-1",
            text="""【US快速网单】1-10分钟
横白卡图：50=5.3
横白卡图：100 150 5.42 连卡问
横白卡图：200-450 5.42
横白卡图：300-500 5.45 250不要 连卡问
#注：40分钟赎回/被扫扣账单，尾刀勿动，请勿盗刷！
""",
            received_at="2026-04-08 12:30:00",
        )

        history, total = self.db.list_quote_history(
            card_type="Apple",
            country_or_currency="USD",
            form_factor="横白卡",
        )
        self.assertEqual(total, 4)
        self.assertTrue(any(row["amount_range"] == "50" and row["price"] == 5.3 for row in history))
        self.assertTrue(any(row["amount_range"] == "100-150" and row["price"] == 5.42 for row in history))
        self.assertTrue(any(row["amount_range"] == "200-450" and row["price"] == 5.42 for row in history))
        self.assertTrue(any(row["amount_range"] == "300-500" and row["price"] == 5.45 for row in history))
        self.assertTrue(any("40分钟赎回" in row["restriction_text"] for row in history))

    def test_sectioned_group_sheet_parses_itunes_multi_section_sample(self) -> None:
        self.db.upsert_quote_group_profile(
            platform="wechat",
            chat_id="g-itunes-sectioned",
            chat_name="iTunes固定模板群",
            default_card_type="Apple",
            default_country_or_currency="USD",
            default_form_factor="横白",
            parser_template="sectioned_group_sheet",
            stale_after_minutes=30,
        )
        self._send(
            chat_id="g-itunes-sectioned",
            message_id="itunes-sectioned-1",
            text="""=======[ iTunes USD 快速网单 ]=======
白卡图：100/150=5.42
白卡图：200-450=5.43 （250不要）
白卡图：500=5.46  压40分钟
白卡图：50=5.3
#注：使用时间1-5分钟，堆卡10分钟
==========[ iTunes 外卡 ]==========
瑞士50-250=6.55 50倍（连卡问）
香港200-2000= 0.835 卡图
英国卡图 50=6.4  100-500=6.7 50倍
----------------------------------------------
iTS Regular类型卡片都不要
""",
            received_at="2026-04-08 12:32:00",
        )

        history, total = self.db.list_quote_history(card_type="Apple")
        scoped = [
            row for row in history
            if row["source_group_key"] == "wechat:g-itunes-sectioned"
        ]
        self.assertEqual(len(scoped), 8)
        actual = {
            (
                row["country_or_currency"],
                row["amount_range"],
                row["multiplier"] or "",
                row["form_factor"],
            ): float(row["price"])
            for row in scoped
        }
        self.assertEqual(actual[("USD", "100-150", "", "横白卡")], 5.42)
        self.assertEqual(actual[("USD", "200-450", "", "横白卡")], 5.43)
        self.assertEqual(actual[("USD", "500", "", "横白卡")], 5.46)
        self.assertEqual(actual[("USD", "50", "", "横白卡")], 5.3)
        self.assertEqual(actual[("CHF", "50-250", "50X", "横白卡")], 6.55)
        self.assertEqual(actual[("HKD", "200-2000", "", "横白卡")], 0.835)
        self.assertEqual(actual[("GBP", "50", "", "横白卡")], 6.4)
        self.assertEqual(actual[("GBP", "100-500", "50X", "横白卡")], 6.7)
        self.assertTrue(any("250不要" in row["restriction_text"] for row in scoped))
        self.assertTrue(any("压40分钟" in row["restriction_text"] for row in scoped))
        exceptions, _ = self.db.list_quote_exceptions()
        self.assertTrue(
            any(
                row["source_group_key"] == "wechat:g-itunes-sectioned"
                and row["source_line"] == "iTS Regular类型卡片都不要"
                for row in exceptions
            )
        )

    def test_sectioned_group_sheet_parses_country_combinations(self) -> None:
        self.db.upsert_quote_group_profile(
            platform="wechat",
            chat_id="g-country-combo",
            chat_name="组合国家群",
            default_card_type="Apple",
            default_form_factor="横白",
            parser_template="sectioned_group_sheet",
            stale_after_minutes=30,
        )
        self._send(
            chat_id="g-country-combo",
            message_id="country-combo-1",
            text="""==========[ iTunes 外卡 ]==========
希腊/葡萄牙：15~49=5.2    50~500=5.6
""",
            received_at="2026-04-08 12:33:00",
        )
        history, _ = self.db.list_quote_history(card_type="Apple", country_or_currency="EUR")
        scoped = [
            row for row in history
            if row["source_group_key"] == "wechat:g-country-combo"
        ]
        self.assertEqual(len(scoped), 2)
        self.assertTrue(any(row["amount_range"] == "15-49" and row["price"] == 5.2 for row in scoped))
        self.assertTrue(any(row["amount_range"] == "50-500" and row["price"] == 5.6 for row in scoped))

    def test_sectioned_group_sheet_uses_country_combo_header_for_following_rows(self) -> None:
        self.db.upsert_quote_group_profile(
            platform="wechat",
            chat_id="g-country-combo-header",
            chat_name="组合国家标题群",
            default_card_type="Apple",
            default_form_factor="横白",
            parser_template="sectioned_group_sheet",
            stale_after_minutes=30,
        )
        self._send(
            chat_id="g-country-combo-header",
            message_id="country-combo-header-1",
            text="""==========[ iTunes 外卡 ]==========
斯洛伐克-斯洛文尼亚
15~49=5.2    50~500=5.6
德国/希腊/葡萄牙
100=5.7
""",
            received_at="2026-04-08 12:34:00",
        )
        history, _ = self.db.list_quote_history(card_type="Apple", country_or_currency="EUR")
        scoped = [
            row for row in history
            if row["source_group_key"] == "wechat:g-country-combo-header"
        ]
        self.assertEqual(len(scoped), 3)
        self.assertTrue(any(row["amount_range"] == "15-49" and row["price"] == 5.2 for row in scoped))
        self.assertTrue(any(row["amount_range"] == "50-500" and row["price"] == 5.6 for row in scoped))
        self.assertTrue(any(row["amount_range"] == "100" and row["price"] == 5.7 for row in scoped))

    def test_group_dictionary_alias_overrides_global_and_builtin_alias(self) -> None:
        self.db.upsert_quote_dictionary_alias(
            category="country_currency",
            alias="香港",
            canonical_value="ZZZ",
        )
        self.db.upsert_quote_dictionary_alias(
            category="country_currency",
            alias="香港",
            canonical_value="YYY",
            scope_platform="wechat",
            scope_chat_id="g-dict-override",
        )
        self.db.upsert_quote_group_profile(
            platform="wechat",
            chat_id="g-dict-override",
            chat_name="字典覆盖群",
            default_card_type="Apple",
            default_form_factor="横白",
            parser_template="sectioned_group_sheet",
            stale_after_minutes=30,
        )
        self._send(
            chat_id="g-dict-override",
            message_id="dict-override-1",
            text="""==========[ iTunes 外卡 ]==========
香港100=1.23
""",
            received_at="2026-04-08 12:34:00",
        )
        rows, total = self.db.list_quote_history(
            card_type="Apple",
            source_group_key="wechat:g-dict-override",
        )
        self.assertEqual(total, 1)
        self.assertEqual(rows[0]["country_or_currency"], "YYY")
        self.assertEqual(rows[0]["amount_range"], "100")
        self.assertEqual(rows[0]["price"], 1.23)

    def test_custom_template_name_uses_fixed_sheet_when_group_defaults_exist(self) -> None:
        self.db.upsert_quote_group_profile(
            platform="wechat",
            chat_id="g-apple-custom-name",
            chat_name="Apple自定义模板名群",
            default_card_type="Apple",
            default_country_or_currency="USD",
            default_form_factor="横白卡",
            parser_template="test1",
            stale_after_minutes=30,
        )
        self._send(
            chat_id="g-apple-custom-name",
            message_id="apple-custom-1",
            text="""【US快速网单】1-10分钟
横白卡图：50=5.3
横白卡图：100 150 5.42 连卡问
""",
            received_at="2026-04-08 12:35:00",
        )
        board = self.db.list_quote_board()
        apple_rows = [
            row
            for row in board
            if row["source_group_key"] == "wechat:g-apple-custom-name"
        ]
        self.assertGreaterEqual(len(apple_rows), 2)
        self.assertTrue(any(row["amount_range"] == "50" and float(row["price"]) == 5.3 for row in apple_rows))
        self.assertTrue(any(row["amount_range"] == "100-150" and float(row["price"]) == 5.42 for row in apple_rows))

    def test_board_hides_dominated_lower_price_ranges(self) -> None:
        self._send(
            chat_id="g-prune-a",
            message_id="prune-a-1",
            text="""【Apple】
USD 100-500=5.50
""",
            received_at="2026-04-08 12:40:00",
        )
        self._send(
            chat_id="g-prune-b",
            message_id="prune-b-1",
            text="""【Apple】
USD 100-150=5.20
USD 200-300=5.30
USD 350-450=5.40
""",
            received_at="2026-04-08 12:41:00",
        )
        board = self.db.list_quote_board()
        apple_rows = [
            row
            for row in board
            if row["card_type"] == "Apple"
            and row["country_or_currency"] == "USD"
            and row["source_group_key"] in {"wechat:g-prune-a", "wechat:g-prune-b"}
        ]
        self.assertEqual(len(apple_rows), 1)
        self.assertEqual(apple_rows[0]["source_group_key"], "wechat:g-prune-a")
        self.assertEqual(apple_rows[0]["amount_range"], "100-500")
        self.assertEqual(float(apple_rows[0]["price"]), 5.5)

    def test_board_normalizes_multi_token_amount_ranges_for_pruning(self) -> None:
        self._send(
            chat_id="g-prune-irregular-a",
            message_id="prune-irregular-a-1",
            text="""【Apple】
USD 150-250-350-450=5.43
""",
            received_at="2026-04-08 12:42:00",
        )
        self._send(
            chat_id="g-prune-irregular-b",
            message_id="prune-irregular-b-1",
            text="""【Apple】
USD 200-450=5.42
""",
            received_at="2026-04-08 12:43:00",
        )
        board = self.db.list_quote_board()
        apple_rows = [
            row
            for row in board
            if row["card_type"] == "Apple"
            and row["country_or_currency"] == "USD"
            and row["source_group_key"] in {"wechat:g-prune-irregular-a", "wechat:g-prune-irregular-b"}
        ]
        self.assertEqual(len(apple_rows), 1)
        self.assertEqual(apple_rows[0]["source_group_key"], "wechat:g-prune-irregular-a")
        self.assertEqual(apple_rows[0]["amount_range"], "150-450")
        self.assertEqual(float(apple_rows[0]["price"]), 5.43)

    def test_board_hides_lower_multiplier_row_when_generic_condition_exists(self) -> None:
        generic_document_id = self.db.record_quote_document(
            platform="wechat",
            source_group_key="wechat:g-prune-generic",
            chat_id="g-prune-generic",
            chat_name="通用条件群",
            message_id="prune-generic-1",
            source_name="通用来源",
            sender_id="sender-generic",
            raw_text="generic",
            message_time="2026-04-08 12:44:00",
            parser_template="quote-v1",
            parser_version="quote-v1",
            confidence=0.9,
            parse_status="parsed",
        )
        self.db.upsert_quote_price_row_with_history(
            quote_document_id=generic_document_id,
            message_id="prune-generic-1",
            platform="wechat",
            source_group_key="wechat:g-prune-generic",
            chat_id="g-prune-generic",
            chat_name="通用条件群",
            source_name="通用来源",
            sender_id="sender-generic",
            card_type="Apple",
            country_or_currency="USD",
            amount_range="50",
            multiplier=None,
            form_factor="横白卡",
            price=5.30,
            quote_status="active",
            restriction_text="",
            source_line="USD 50=5.30",
            raw_text="generic",
            message_time="2026-04-08 12:44:00",
            effective_at="2026-04-08 12:44:00",
            expires_at=None,
            parser_template="quote-v1",
            parser_version="quote-v1",
            confidence=0.9,
        )
        specific_document_id = self.db.record_quote_document(
            platform="wechat",
            source_group_key="wechat:g-prune-specific",
            chat_id="g-prune-specific",
            chat_name="倍数条件群",
            message_id="prune-specific-1",
            source_name="倍数来源",
            sender_id="sender-specific",
            raw_text="specific",
            message_time="2026-04-08 12:45:00",
            parser_template="quote-v1",
            parser_version="quote-v1",
            confidence=0.9,
            parse_status="parsed",
        )
        self.db.upsert_quote_price_row_with_history(
            quote_document_id=specific_document_id,
            message_id="prune-specific-1",
            platform="wechat",
            source_group_key="wechat:g-prune-specific",
            chat_id="g-prune-specific",
            chat_name="倍数条件群",
            source_name="倍数来源",
            sender_id="sender-specific",
            card_type="Apple",
            country_or_currency="USD",
            amount_range="50",
            multiplier="100X",
            form_factor="横白卡",
            price=5.20,
            quote_status="active",
            restriction_text="",
            source_line="USD 50=5.20（100倍数）",
            raw_text="specific",
            message_time="2026-04-08 12:45:00",
            effective_at="2026-04-08 12:45:00",
            expires_at=None,
            parser_template="quote-v1",
            parser_version="quote-v1",
            confidence=0.9,
        )
        board = self.db.list_quote_board()
        apple_rows = [
            row
            for row in board
            if row["card_type"] == "Apple"
            and row["country_or_currency"] == "USD"
            and row["source_group_key"] in {"wechat:g-prune-generic", "wechat:g-prune-specific"}
        ]
        self.assertEqual(len(apple_rows), 1)
        self.assertEqual(apple_rows[0]["source_group_key"], "wechat:g-prune-generic")
        self.assertEqual(apple_rows[0]["amount_display"], "50")
        self.assertEqual(float(apple_rows[0]["price"]), 5.3)

    def test_board_merges_card_image_and_horizontal_white_form_factor(self) -> None:
        self._send(
            chat_id="g-form-a",
            message_id="form-a-1",
            text="""【Apple】
USD 100-150 卡图=5.40
""",
            received_at="2026-04-08 12:45:00",
        )
        self._send(
            chat_id="g-form-b",
            message_id="form-b-1",
            text="""【Apple】
USD 100-150 横白卡=5.42
""",
            received_at="2026-04-08 12:46:00",
        )
        board = self.db.list_quote_board()
        apple_rows = [
            row
            for row in board
            if row["card_type"] == "Apple"
            and row["country_or_currency"] == "USD"
            and row["source_group_key"] in {"wechat:g-form-a", "wechat:g-form-b"}
        ]
        self.assertEqual(len(apple_rows), 1)
        self.assertEqual(apple_rows[0]["form_factor"], "横白卡")
        self.assertEqual(float(apple_rows[0]["price"]), 5.42)

    def test_rankings_match_normalized_amount_range_for_legacy_rows(self) -> None:
        quote_document_id = self.db.record_quote_document(
            platform="wechat",
            source_group_key="wechat:g-legacy-range",
            chat_id="g-legacy-range",
            chat_name="旧区间群",
            message_id="legacy-range-1",
            source_name="旧区间来源",
            sender_id="legacy-sender",
            raw_text="legacy",
            message_time="2026-04-08 12:46:00",
            parser_template="quote-v1",
            parser_version="quote-v1",
            confidence=0.9,
            parse_status="parsed",
        )
        self.db.upsert_quote_price_row_with_history(
            quote_document_id=quote_document_id,
            message_id="legacy-range-1",
            platform="wechat",
            source_group_key="wechat:g-legacy-range",
            chat_id="g-legacy-range",
            chat_name="旧区间群",
            source_name="旧区间来源",
            sender_id="legacy-sender",
            card_type="Apple",
            country_or_currency="USD",
            amount_range="150-250-350-450",
            multiplier=None,
            form_factor="横白卡",
            price=5.43,
            quote_status="active",
            restriction_text="",
            source_line="USD 150-250-350-450=5.43",
            raw_text="legacy",
            message_time="2026-04-08 12:46:00",
            effective_at="2026-04-08 12:46:00",
            expires_at=None,
            parser_template="quote-v1",
            parser_version="quote-v1",
            confidence=0.9,
        )
        rankings, total = self.db.list_quote_rankings(
            card_type="Apple",
            country_or_currency="USD",
            amount_range="150-450",
            multiplier=None,
            form_factor="横白卡",
        )
        self.assertEqual(total, 1)
        self.assertEqual(len(rankings), 1)
        self.assertEqual(rankings[0]["source_group_key"], "wechat:g-legacy-range")

    def test_fixed_sheet_parses_multiplier_line_price_from_tail_token(self) -> None:
        self.db.upsert_quote_group_profile(
            platform="wechat",
            chat_id="g-mult-tail",
            chat_name="倍数尾价群",
            default_card_type="Apple",
            default_country_or_currency="USD",
            default_form_factor="横白卡",
            parser_template="group_fixed_sheet",
            stale_after_minutes=30,
        )
        self._send(
            chat_id="g-mult-tail",
            message_id="mult-tail-1",
            text="""【US快速网单】1-10分钟
100 - 500     100倍数    5.47
""",
            received_at="2026-04-08 12:42:00",
        )
        rows, total = self.db.list_quote_history(
            card_type="Apple",
            country_or_currency="USD",
            amount_range="100-500",
            form_factor="横白卡",
            multiplier="100X",
        )
        self.assertEqual(total, 1)
        self.assertEqual(rows[0]["price"], 5.47)

    def test_blocked_exception_can_attach_to_matching_card_restrictions(self) -> None:
        self._send(
            chat_id="g-restrictions",
            message_id="restriction-1",
            text="""【Razer Gold 雷蛇】
美国=5.74
雷蛇待定卡不加账！！
【Steam 蒸汽】
USD=5.1
""",
            received_at="2026-04-08 12:10:00",
        )

        exceptions, total = self.db.list_quote_exceptions()
        self.assertGreaterEqual(total, 1)
        exception = next(
            row
            for row in exceptions
            if row["source_line"] == "雷蛇待定卡不加账！！"
        )
        result = self.db.attach_quote_exception_to_restrictions(
            exception_id=exception["id"],
        )
        self.assertEqual(result["status"], "attached")
        self.assertGreaterEqual(result["attached"], 1)

        history, _ = self.db.list_quote_history(card_type="Razer")
        self.assertTrue(
            any("雷蛇待定卡不加账！！" in row["restriction_text"] for row in history)
        )
        steam_history, _ = self.db.list_quote_history(card_type="Steam")
        self.assertFalse(
            any("雷蛇待定卡不加账！！" in row["restriction_text"] for row in steam_history)
        )

    def test_board_prefers_highest_price_across_sources(self) -> None:
        self._send(
            chat_id="g-source-a",
            message_id="source-a-1",
            text="""【Steam】
USD=5.10
""",
            received_at="2026-04-08 12:00:00",
        )
        self._send(
            chat_id="g-source-b",
            message_id="source-b-1",
            text="""【Steam】
USD=5.30
""",
            received_at="2026-04-08 12:05:00",
        )

        board = self.db.list_quote_board()
        steam_usd = next(
            row
            for row in board
            if row["card_type"] == "Steam" and row["country_or_currency"] == "USD"
        )
        self.assertEqual(float(steam_usd["price"]), 5.30)
        self.assertEqual(steam_usd["source_group_key"], "wechat:g-source-b")


if __name__ == "__main__":
    unittest.main()
