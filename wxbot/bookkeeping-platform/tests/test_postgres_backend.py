from __future__ import annotations

import sqlite3
import sys
import types
import unittest


class _FakeCursor:
    def __init__(self, cursor: sqlite3.Cursor, *, returned_id: int | None = None) -> None:
        self._cursor = cursor
        self._returned_id = returned_id
        self.rowcount = cursor.rowcount
        self.lastrowid = returned_id

    def fetchone(self):
        if self._returned_id is not None:
            returned_id = self._returned_id
            self._returned_id = None
            return {"id": returned_id}
        row = self._cursor.fetchone()
        return dict(row) if row is not None else None

    def fetchall(self):
        return [dict(row) for row in self._cursor.fetchall()]


class _FakePsycopgConnection:
    def __init__(self, dsn: str) -> None:
        self.dsn = dsn
        self._conn = sqlite3.connect(":memory:")
        self._conn.row_factory = sqlite3.Row

    def execute(self, sql: str, params=()):
        translated = sql.replace("%s", "?")
        returning_id = None
        if " RETURNING id" in translated:
            translated = translated.replace(" RETURNING id", "")
            cursor = self._conn.execute(translated, params)
            returning_id = int(cursor.lastrowid)
            return _FakeCursor(cursor, returned_id=returning_id)
        cursor = self._conn.execute(translated, params)
        return _FakeCursor(cursor)

    def commit(self) -> None:
        self._conn.commit()

    def rollback(self) -> None:
        self._conn.rollback()

    def close(self) -> None:
        self._conn.close()


class PostgresBackendTests(unittest.TestCase):
    def setUp(self) -> None:
        self._original_psycopg = sys.modules.get("psycopg")
        fake_module = types.ModuleType("psycopg")
        fake_module.connect_calls: list[str] = []

        def _connect(dsn: str):
            fake_module.connect_calls.append(dsn)
            return _FakePsycopgConnection(dsn)

        fake_module.connect = _connect
        self.fake_module = fake_module
        sys.modules["psycopg"] = fake_module

    def tearDown(self) -> None:
        if self._original_psycopg is None:
            sys.modules.pop("psycopg", None)
        else:
            sys.modules["psycopg"] = self._original_psycopg

    def test_postgres_dsn_uses_postgres_backend_for_basic_reads_and_writes(self) -> None:
        from bookkeeping_core.database import BookkeepingDB

        db = BookkeepingDB("postgresql://bookkeeping:test@localhost:5432/bookkeeping")
        try:
            self.assertEqual(
                self.fake_module.connect_calls,
                ["postgresql://bookkeeping:test@localhost:5432/bookkeeping"],
            )
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
            self.assertEqual(float(history[0]["rmb_value"]), 88.0)
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
