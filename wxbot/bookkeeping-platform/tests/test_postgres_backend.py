from __future__ import annotations

import unittest

from bookkeeping_core.database import BookkeepingDB
from tests.support.postgres_test_case import PostgresTestCase


class PostgresBackendTests(PostgresTestCase):
    def test_bookkeeping_db_rejects_sqlite_runtime_path(self) -> None:
        with self.assertRaisesRegex(ValueError, "PostgreSQL DSN"):
            BookkeepingDB("/tmp/bookkeeping.db")

    def test_bookkeeping_db_uses_current_schema_for_basic_reads_and_writes(self) -> None:
        db = self.make_db("backend-basic")
        try:
            db.set_group(
                platform="wechat",
                group_key="wechat:g-pg",
                chat_id="g-pg",
                chat_name="PG客户群",
                group_num=9,
            )
            tx_id = db.add_transaction(
                platform="wechat",
                group_key="wechat:g-pg",
                group_num=9,
                chat_id="g-pg",
                chat_name="PG客户群",
                sender_id="u-pg",
                sender_name="Postgres",
                message_id="msg-pg-1",
                input_sign=1,
                amount=88,
                category="rmb",
                rate=None,
                rmb_value=88,
                raw="rmb+88",
                created_at="2026-03-20 10:00:00",
            )
            self.assertGreater(tx_id, 0)
            history = db.get_history("wechat:g-pg", 10)
            self.assertEqual(len(history), 1)
            self.assertEqual(history[0]["chat_name"], "PG客户群")
        finally:
            db.close()

    def test_bookkeeping_db_fails_fast_when_schema_is_missing(self) -> None:
        schema_name = self._schema_name("blank")
        self._create_schema(schema_name)
        blank_dsn = self._dsn_with_search_path(schema_name)

        with self.assertRaisesRegex(RuntimeError, "PostgreSQL schema mismatch"):
            BookkeepingDB(blank_dsn)


if __name__ == "__main__":
    unittest.main()
