from __future__ import annotations

import sqlite3
import sys
import types
import unittest
import json

from tests.support.bookkeeping_replay import build_runtime_card_scenario, replay_runtime_scenario


class _FakeCursor:
    def __init__(
        self,
        cursor: sqlite3.Cursor | None = None,
        *,
        returned_id: int | None = None,
        rows: list[dict] | None = None,
    ) -> None:
        self._cursor = cursor
        self._returned_id = returned_id
        self._rows = rows
        self._index = 0
        self.rowcount = len(rows) if rows is not None else cursor.rowcount
        self.lastrowid = returned_id

    def fetchone(self):
        if self._rows is not None:
            if self._index >= len(self._rows):
                return None
            row = self._rows[self._index]
            self._index += 1
            return row
        if self._returned_id is not None:
            returned_id = self._returned_id
            self._returned_id = None
            return {"id": returned_id}
        row = self._cursor.fetchone()
        return dict(row) if row is not None else None

    def fetchall(self):
        if self._rows is not None:
            if self._index >= len(self._rows):
                return []
            rows = self._rows[self._index :]
            self._index = len(self._rows)
            return rows
        return [dict(row) for row in self._cursor.fetchall()]


class _FakePsycopgConnection:
    def __init__(self, dsn: str) -> None:
        self.dsn = dsn
        self._conn = sqlite3.connect(":memory:")
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(
            """
            CREATE TABLE transactions (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              platform TEXT NOT NULL,
              group_key TEXT NOT NULL,
              group_num INTEGER,
              chat_id TEXT NOT NULL,
              chat_name TEXT NOT NULL,
              sender_id TEXT NOT NULL,
              sender_name TEXT NOT NULL,
              message_id TEXT,
              input_sign INTEGER NOT NULL,
              amount REAL NOT NULL,
              category TEXT NOT NULL,
              rate REAL,
              rmb_value REAL NOT NULL,
              raw TEXT NOT NULL,
              ngn_rate REAL,
              settlement_id INTEGER,
              settled_at TEXT,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              deleted INTEGER NOT NULL DEFAULT 0,
              settled INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE groups (
              group_key TEXT PRIMARY KEY,
              platform TEXT NOT NULL,
              chat_id TEXT NOT NULL,
              chat_name TEXT NOT NULL,
              group_num INTEGER,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE accounting_periods (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              start_at TEXT NOT NULL,
              end_at TEXT,
              closed_at TEXT,
              closed_by TEXT,
              note TEXT,
              has_adjustment INTEGER,
              snapshot_version INTEGER
            );
            INSERT INTO accounting_periods (
              start_at, end_at, closed_at, closed_by, note, has_adjustment, snapshot_version
            ) VALUES (
              '2026-03-18 08:00:00',
              '2026-03-18 09:00:00',
              '2026-03-18 09:30:00',
              'finance-a',
              'keep',
              1,
              3
            );
            INSERT INTO accounting_periods (start_at) VALUES ('2026-03-19 08:00:00');
            """
        )

    def execute(self, sql: str, params=()):
        translated = sql.replace("%s", "?")
        if translated.lstrip().upper().startswith("ALTER TABLE") and "ADD COLUMN" in translated.upper():
            translated = translated.replace("DEFAULT CURRENT_TIMESTAMP", "DEFAULT ''")
        if translated.lstrip().upper().startswith("ALTER TABLE") and "ALTER COLUMN" in translated.upper() and "SET NOT NULL" in translated.upper():
            return _FakeCursor(rows=[])
        upper_sql = translated.upper()
        if "ACCOUNTING_PERIODS" in upper_sql and (
            "END_AT = ''" in upper_sql
            or "CLOSED_AT = ''" in upper_sql
            or "NULLIF(END_AT, '')" in upper_sql
            or "NULLIF(CLOSED_AT, '')" in upper_sql
        ):
            raise AssertionError("TIMESTAMP columns must not be compared with empty strings")
        if "information_schema.columns" in translated.lower():
            table_name = str(params[0])
            column_name = str(params[1])
            rows = self._conn.execute(f"PRAGMA table_info({table_name})").fetchall()
            exists = any(str(row["name"]) == column_name for row in rows)
            return _FakeCursor(rows=[{"exists": 1}] if exists else [])
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

    def test_postgres_dsn_upgrades_legacy_schema_columns(self) -> None:
        from bookkeeping_core.database import BookkeepingDB

        db = BookkeepingDB("postgresql://bookkeeping:test@localhost:5432/bookkeeping")
        try:
            def _column_map(table_name: str) -> dict[str, str]:
                return {
                    row["name"]: str(row["type"]).upper()
                    for row in db.conn.execute(f"PRAGMA table_info({table_name})").fetchall()
                }

            groups_columns = _column_map("groups")
            self.assertTrue({"business_role", "role_source", "capture_enabled", "status"}.issubset(groups_columns))

            tx_columns = _column_map("transactions")
            self.assertTrue({"usd_amount", "unit_face_value", "unit_count", "parse_version"}.issubset(tx_columns))
            self.assertEqual(tx_columns["parse_version"], "TEXT")

            period_columns = _column_map("accounting_periods")
            self.assertTrue({"end_at", "closed_at", "closed_by"}.issubset(period_columns))
            legacy_rows = db.conn.execute("SELECT * FROM accounting_periods ORDER BY id").fetchall()
            self.assertEqual(len(legacy_rows), 2)
            preserved = legacy_rows[0]
            self.assertEqual(str(preserved["start_at"]), "2026-03-18 08:00:00")
            self.assertEqual(str(preserved["end_at"]), "2026-03-18 09:00:00")
            self.assertEqual(str(preserved["closed_at"]), "2026-03-18 09:30:00")
            self.assertEqual(str(preserved["closed_by"]), "finance-a")
            self.assertEqual(int(preserved["has_adjustment"]), 1)
            self.assertEqual(int(preserved["snapshot_version"]), 3)

            filled = legacy_rows[1]
            self.assertEqual(str(filled["start_at"]), "2026-03-19 08:00:00")
            self.assertEqual(str(filled["end_at"]), "2026-03-19 08:00:00")
            self.assertEqual(str(filled["closed_at"]), "2026-03-19 08:00:00")
            self.assertEqual(str(filled["closed_by"]), "legacy-migration")
            self.assertEqual(int(filled["has_adjustment"]), 0)
            self.assertEqual(int(filled["snapshot_version"]), 1)
        finally:
            db.close()

    def test_postgres_dsn_can_close_period(self) -> None:
        from bookkeeping_core.database import BookkeepingDB
        from bookkeeping_core.periods import AccountingPeriodService

        db = BookkeepingDB("postgresql://bookkeeping:test@localhost:5432/bookkeeping")
        try:
            db.set_group(
                platform="wechat",
                group_key="wechat:g-pg",
                chat_id="g-pg",
                chat_name="PG客户群",
                group_num=9,
            )
            db.add_transaction(
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

            period_id = AccountingPeriodService(db).close_period(
                start_at="2026-03-20 09:00:00",
                end_at="2026-03-20 11:00:00",
                closed_by="finance-pg",
            )

            period = next(row for row in db.list_accounting_periods() if str(row["closed_at"]) == "2026-03-20 11:00:00")
            self.assertEqual(int(period["id"]), period_id)
            snapshot = db.list_period_group_snapshots(period_id)[0]
            self.assertEqual(str(snapshot["group_key"]), "wechat:g-pg")
            self.assertEqual(round(float(snapshot["opening_balance"]), 2), 0.00)
            self.assertEqual(round(float(snapshot["closing_balance"]), 2), 88.00)
        finally:
            db.close()

    def test_postgres_dsn_analytics_payloads_are_json_serializable(self) -> None:
        from bookkeeping_core.analytics import AnalyticsService
        from bookkeeping_core.database import BookkeepingDB
        from bookkeeping_core.periods import AccountingPeriodService

        db = BookkeepingDB("postgresql://bookkeeping:test@localhost:5432/bookkeeping")
        try:
            db.set_group(
                platform="wechat",
                group_key="wechat:g-analytics",
                chat_id="g-analytics",
                chat_name="PG分析群",
                group_num=3,
            )
            db.conn.execute(
                "UPDATE groups SET business_role = ? WHERE group_key = ?",
                ("customer", "wechat:g-analytics"),
            )
            tx_id = db.add_transaction(
                platform="wechat",
                group_key="wechat:g-analytics",
                group_num=3,
                chat_id="g-analytics",
                chat_name="PG分析群",
                sender_id="u-analytics",
                sender_name="Postgres",
                message_id="msg-pg-analytics",
                input_sign=1,
                amount=60,
                category="steam",
                rate=10,
                rmb_value=60,
                raw="steam+60",
                created_at="2026-03-20 10:00:00",
            )
            db.conn.execute(
                "UPDATE transactions SET usd_amount = ?, unit_face_value = ?, unit_count = ? WHERE id = ?",
                (600, 20, 30, tx_id),
            )
            db.conn.commit()

            period_id = AccountingPeriodService(db).close_period(
                start_at="2026-03-20 09:00:00",
                end_at="2026-03-20 11:00:00",
                closed_by="finance-pg",
            )

            service = AnalyticsService(db)
            dashboard = service.build_dashboard_summary(today="2026-03-20")
            workbench = service.build_period_workbench(period_id=period_id)
            history = service.build_history_analysis(
                start_date="2026-03-01",
                end_date="2026-03-31",
                card_keyword="steam",
                sort_by="usd_amount",
            )

            json.dumps(dashboard)
            json.dumps(workbench)
            json.dumps(history)
        finally:
            db.close()

    def test_postgres_dsn_mock_replay_can_fill_workbench_and_history(self) -> None:
        from bookkeeping_core.analytics import AnalyticsService
        from bookkeeping_core.database import BookkeepingDB

        db = BookkeepingDB("postgresql://bookkeeping:test@localhost:5432/bookkeeping")
        try:
            scenario = build_runtime_card_scenario()
            period_id = replay_runtime_scenario(db, scenario)

            service = AnalyticsService(db)
            workbench = service.build_period_workbench(period_id=period_id)
            history = service.build_history_analysis(
                start_date="2026-03-01",
                end_date="2026-03-31",
                card_keyword="steam",
                sort_by="usd_amount",
            )

            self.assertGreater(len(workbench["card_stats"]), 0)
            self.assertGreater(len(history["card_rankings"]), 0)
            steam_rows = [row for row in workbench["card_stats"] if row["card_type"] == "steam"]
            self.assertEqual(len(steam_rows), 1)
            self.assertEqual(workbench["selected_period"]["id"], period_id)
            self.assertEqual(workbench["selected_period"]["closed_by"], "finance-mock")
            self.assertEqual(workbench["selected_period"]["note"], None)
            self.assertEqual(workbench["summary"]["total_usd_amount"], 600.0)
            self.assertEqual(workbench["summary"]["transaction_count"], 2)
            self.assertEqual(steam_rows[0]["usd_amount"], 600.0)
            self.assertEqual(steam_rows[0]["rmb_amount"], 50.0)
            self.assertEqual(steam_rows[0]["unit_face_value"], 20.0)
            self.assertEqual(steam_rows[0]["unit_count"], 30.0)
            self.assertEqual(steam_rows[0]["business_role"], "customer")
            self.assertEqual(history["card_rankings"][0]["card_type"], "steam")
            self.assertEqual(history["card_rankings"][0]["usd_amount"], 600.0)
            self.assertEqual(history["card_rankings"][0]["rmb_amount"], 50.0)
            self.assertEqual(history["summary"]["total_usd_amount"], 600.0)
            self.assertEqual(history["summary"]["card_type_count"], 1)
            json.dumps(workbench)
            json.dumps(history)
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
