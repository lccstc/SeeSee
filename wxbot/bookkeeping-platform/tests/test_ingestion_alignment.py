from __future__ import annotations

import unittest

from bookkeeping_core.database import BookkeepingDB
from tests.support.postgres_test_case import PostgresTestCase


class StructuredTransactionContractTests(PostgresTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.db = BookkeepingDB(self.make_dsn("ingestion-alignment"))

    def tearDown(self) -> None:
        self.db.close()
        super().tearDown()

    def test_structured_record_persists_parse_and_card_fields(self) -> None:
        from bookkeeping_core.ingestion import StructuredTransactionRecord, persist_transaction_record
        from tests.support.bookkeeping_replay import ensure_group, close_period_for_test

        ensure_group(
            self.db,
            platform="wechat",
            group_key="wechat:g-align",
            chat_id="g-align",
            chat_name="对齐测试群",
            group_num=5,
        )

        record = StructuredTransactionRecord(
            platform="wechat",
            group_key="wechat:g-align",
            group_num=5,
            chat_id="g-align",
            chat_name="对齐测试群",
            sender_id="user-1",
            sender_name="User One",
            message_id="msg-align-1",
            created_at="2026-03-22 09:10:00",
            input_sign=1,
            amount=60,
            category="steam",
            rate=10,
            rmb_value=60,
            raw="steam+60",
            parse_version="mock-card-v1",
            usd_amount=600,
            unit_face_value=20,
            unit_count=30,
        )

        persist_transaction_record(self.db, record)
        period_id = close_period_for_test(self.db, start_at="2026-03-22 09:00:00", end_at="2026-03-22 10:00:00")

        tx_row = self.db.get_history("wechat:g-align", 1)[0]
        card_row = self.db.list_period_card_stats(period_id)[0]

        self.assertEqual(str(tx_row["parse_version"]), "mock-card-v1")
        self.assertEqual(float(tx_row["usd_amount"]), 600.0)
        self.assertEqual(float(card_row["usd_amount"]), 600.0)
        self.assertEqual(float(card_row["unit_face_value"]), 20.0)
        self.assertEqual(float(card_row["unit_count"]), 30.0)


class RecordBuilderTests(unittest.TestCase):
    def test_runtime_and_sync_builders_share_one_structured_shape(self) -> None:
        from bookkeeping_core.ingestion import build_runtime_record, build_sync_created_record
        from bookkeeping_core.models import ParsedTransaction

        parsed = ParsedTransaction(
            input_sign=1,
            amount=100,
            category="rmb",
            rate=None,
            rmb_value=100,
            raw="+100rmb",
        )

        runtime_record = build_runtime_record(
            platform="wechat",
            group_key="wechat:g-1",
            group_num=5,
            chat_id="g-1",
            chat_name="运行时群",
            sender_id="u-runtime",
            sender_name="Runtime",
            message_id="msg-runtime-1",
            created_at="2026-03-22 09:15:00",
            parsed=parsed,
        )
        sync_record = build_sync_created_record(
            platform="whatsapp",
            group_key="whatsapp:12036340001@g.us",
            group_num=5,
            chat_id="12036340001@g.us",
            chat_name="兼容群",
            sender_id="u-sync",
            sender_name="Sync",
            message_id="whatsapp-local-tx-501",
            created_at="2026-03-22 09:15:00",
            input_sign=1,
            amount=100,
            category="rmb",
            rate=None,
            rmb_value=100,
            raw="+100rmb",
        )

        self.assertEqual(runtime_record.parse_version, "1")
        self.assertEqual(sync_record.parse_version, "1")
        self.assertEqual(runtime_record.amount, 100)
        self.assertEqual(sync_record.amount, 100)


class ReplayScenarioContractTests(PostgresTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.db = BookkeepingDB(self.make_dsn("ingestion-alignment-replay"))

    def tearDown(self) -> None:
        self.db.close()
        super().tearDown()

    def test_runtime_replay_helper_centralizes_card_field_population_for_period_stats(self) -> None:
        from tests.support.bookkeeping_replay import build_runtime_card_scenario, replay_runtime_scenario

        period_id = replay_runtime_scenario(
            self.db,
            build_runtime_card_scenario(
                message_prefix="ingestion-alignment",
                chat_id="g-align-runtime",
                chat_name="对齐回放群",
                group_num=5,
                business_role="customer",
                start_at="2026-03-22 09:00:00",
                end_at="2026-03-22 10:00:00",
                opening_created_at="2026-03-22 08:30:00",
                card_created_at="2026-03-22 09:10:00",
                expense_created_at="2026-03-22 09:20:00",
            ),
        )

        tx_row = self.db.conn.execute(
            "SELECT * FROM transactions WHERE message_id = ?",
            ("ingestion-alignment-card",),
        ).fetchone()
        card_row = self.db.list_period_card_stats(period_id)[0]

        self.assertEqual(str(tx_row["category"]), "steam")
        self.assertEqual(float(tx_row["usd_amount"]), 600.0)
        self.assertEqual(float(card_row["usd_amount"]), 600.0)
        self.assertEqual(float(card_row["unit_face_value"]), 20.0)
        self.assertEqual(float(card_row["unit_count"]), 30.0)
