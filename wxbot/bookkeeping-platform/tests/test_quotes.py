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
