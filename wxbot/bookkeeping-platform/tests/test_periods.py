from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sqlite3

from bookkeeping_core.database import BookkeepingDB
from bookkeeping_core.periods import AccountingPeriodService


class PeriodSchemaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tempdir.name) / "periods.db"
        self.db = BookkeepingDB(self.db_path)

    def tearDown(self) -> None:
        self.db.close()
        self.tempdir.cleanup()

    def _table_names(self) -> set[str]:
        rows = self.db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
        return {str(row["name"]) for row in rows}

    def _columns(self, table_name: str) -> set[str]:
        rows = self.db.conn.execute(f"PRAGMA table_info({table_name})").fetchall()
        return {str(row["name"]) for row in rows}

    def _column_type(self, table_name: str, column_name: str) -> str:
        row = self.db.conn.execute(f"PRAGMA table_info({table_name})").fetchall()
        for item in row:
            if str(item["name"]) == column_name:
                return str(item["type"]).upper()
        self.fail(f"missing column {table_name}.{column_name}")

    def _column_notnull(self, table_name: str, column_name: str) -> bool:
        rows = self.db.conn.execute(f"PRAGMA table_info({table_name})").fetchall()
        for item in rows:
            if str(item["name"]) == column_name:
                return int(item["notnull"]) == 1
        self.fail(f"missing column {table_name}.{column_name}")

    def _has_unique_index(self, table_name: str, columns: tuple[str, ...]) -> bool:
        index_rows = self.db.conn.execute(f"PRAGMA index_list({table_name})").fetchall()
        for index_row in index_rows:
            if int(index_row["unique"]) != 1:
                continue
            index_name = str(index_row["name"])
            info_rows = self.db.conn.execute(f"PRAGMA index_info({index_name})").fetchall()
            indexed_columns = tuple(str(info_row["name"]) for info_row in info_rows)
            if indexed_columns == columns:
                return True
        return False

    def test_bootstraps_phase1_tables_and_columns(self) -> None:
        tables = self._table_names()
        self.assertTrue({"accounting_periods", "period_group_snapshots", "period_card_stats"}.issubset(tables))

        group_columns = self._columns("groups")
        self.assertTrue({"business_role", "role_source", "capture_enabled", "status"}.issubset(group_columns))

        transaction_columns = self._columns("transactions")
        self.assertTrue({"usd_amount", "unit_face_value", "unit_count", "parse_version"}.issubset(transaction_columns))
        self.assertEqual(self._column_type("transactions", "parse_version"), "TEXT")

        self.assertSetEqual(
            self._columns("accounting_periods"),
            {
                "id",
                "start_at",
                "end_at",
                "closed_at",
                "closed_by",
                "note",
                "has_adjustment",
                "snapshot_version",
            },
        )
        self.assertTrue(self._column_notnull("accounting_periods", "start_at"))
        self.assertTrue(self._column_notnull("accounting_periods", "end_at"))
        self.assertTrue(self._column_notnull("accounting_periods", "closed_at"))
        self.assertTrue(self._column_notnull("accounting_periods", "closed_by"))
        self.assertSetEqual(
            self._columns("period_group_snapshots"),
            {
                "id",
                "period_id",
                "group_key",
                "platform",
                "chat_name",
                "group_num",
                "business_role",
                "opening_balance",
                "income",
                "expense",
                "closing_balance",
                "transaction_count",
                "anomaly_flags_json",
            },
        )
        self.assertSetEqual(
            self._columns("period_card_stats"),
            {
                "id",
                "period_id",
                "group_key",
                "business_role",
                "card_type",
                "usd_amount",
                "rate",
                "rmb_amount",
                "unit_face_value",
                "unit_count",
                "sample_raw",
            },
        )
        for column_name in (
            "period_id",
            "group_key",
            "platform",
            "chat_name",
            "opening_balance",
            "income",
            "expense",
            "closing_balance",
            "transaction_count",
            "anomaly_flags_json",
        ):
            self.assertTrue(self._column_notnull("period_group_snapshots", column_name), column_name)
        self.assertTrue(self._has_unique_index("period_group_snapshots", ("period_id", "group_key")))

    def test_reinitializes_legacy_accounting_period_columns(self) -> None:
        self.db.close()

        legacy_db_path = Path(self.tempdir.name) / "legacy-periods.db"
        legacy_conn = sqlite3.connect(legacy_db_path)
        legacy_conn.row_factory = sqlite3.Row
        legacy_conn.executescript(
            """
            CREATE TABLE accounting_periods (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              start_at TEXT NOT NULL
            );
            INSERT INTO accounting_periods (start_at) VALUES ('2026-03-18 08:00:00');
            """
        )
        legacy_conn.commit()
        legacy_conn.close()

        self.db = BookkeepingDB(legacy_db_path)
        self.assertTrue(
            {
                "start_at",
                "end_at",
                "closed_at",
                "closed_by",
                "note",
                "has_adjustment",
                "snapshot_version",
            }.issubset(self._columns("accounting_periods"))
        )
        row = self.db.conn.execute("SELECT * FROM accounting_periods ORDER BY id LIMIT 1").fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(str(row["start_at"]), "2026-03-18 08:00:00")
        self.assertEqual(str(row["end_at"]), "2026-03-18 08:00:00")
        self.assertEqual(str(row["closed_at"]), "2026-03-18 08:00:00")
        self.assertEqual(str(row["closed_by"]), "legacy-migration")
        self.assertEqual(int(row["has_adjustment"]), 0)
        self.assertEqual(int(row["snapshot_version"]), 1)

        self.db.conn.execute(
            """
            UPDATE accounting_periods
            SET end_at = ?, closed_at = ?, closed_by = ?, has_adjustment = ?, snapshot_version = ?
            WHERE id = ?
            """,
            ("2026-03-18 09:00:00", "2026-03-18 09:30:00", "finance-a", 1, 3, int(row["id"])),
        )
        self.db.conn.commit()
        self.db.close()

        self.db = BookkeepingDB(legacy_db_path)
        preserved = self.db.conn.execute("SELECT * FROM accounting_periods ORDER BY id LIMIT 1").fetchone()
        self.assertIsNotNone(preserved)
        self.assertEqual(str(preserved["start_at"]), "2026-03-18 08:00:00")
        self.assertEqual(str(preserved["end_at"]), "2026-03-18 09:00:00")
        self.assertEqual(str(preserved["closed_at"]), "2026-03-18 09:30:00")
        self.assertEqual(str(preserved["closed_by"]), "finance-a")
        self.assertEqual(int(preserved["has_adjustment"]), 1)
        self.assertEqual(int(preserved["snapshot_version"]), 3)


class AccountingPeriodBackfillTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tempdir.name) / "periods.db"
        self.db = BookkeepingDB(self.db_path)

    def tearDown(self) -> None:
        self.db.close()
        self.tempdir.cleanup()

    def test_backfill_legacy_periods_creates_period_and_snapshot(self) -> None:
        group_key = "wechat:g-100"
        self.db.set_group(
            platform="wechat",
            group_key=group_key,
            chat_id="g-100",
            chat_name="客户群-100",
            group_num=5,
        )
        tx_id = self.db.add_transaction(
            platform="wechat",
            group_key=group_key,
            group_num=5,
            chat_id="g-100",
            chat_name="客户群-100",
            sender_id="u-1",
            sender_name="Alice",
            message_id="msg-1",
            input_sign=1,
            amount=380,
            category="rmb",
            rate=None,
            rmb_value=380,
            raw="rmb+380",
            created_at="2026-03-19 09:00:00",
        )
        self.db.settle_transactions(
            "wechat",
            group_key,
            self.db.get_unsettled_transactions(group_key),
            "finance-a",
            settled_at="2026-03-19 10:30:00",
        )
        settlement = self.db.get_settlements(group_key, 1)[0]
        self.assertEqual(int(settlement["id"]), 1)
        self.assertEqual(self.db.conn.execute("SELECT settled FROM transactions WHERE id = ?", (tx_id,)).fetchone()["settled"], 1)

        created = AccountingPeriodService(self.db).backfill_legacy_periods()
        self.assertEqual(created, 1)

        periods = self.db.list_accounting_periods()
        self.assertEqual(len(periods), 1)
        period = periods[0]
        self.assertEqual(str(period["start_at"]), "2026-03-19 09:00:00")
        self.assertEqual(str(period["closed_at"]), "2026-03-19 10:30:00")
        self.assertEqual(str(period["closed_by"]), "finance-a")

        snapshots = self.db.list_period_group_snapshots(int(period["id"]))
        self.assertEqual(len(snapshots), 1)
        snapshot = snapshots[0]
        self.assertEqual(str(snapshot["group_key"]), group_key)
        self.assertEqual(round(float(snapshot["opening_balance"]), 2), 0.00)
        self.assertEqual(round(float(snapshot["closing_balance"]), 2), 380.00)

    def test_backfill_legacy_periods_skips_existing_periods_and_adds_missing_ones(self) -> None:
        group_key = "wechat:g-101"
        self.db.set_group(
            platform="wechat",
            group_key=group_key,
            chat_id="g-101",
            chat_name="客户群-101",
            group_num=5,
        )

        first_tx_id = self.db.add_transaction(
            platform="wechat",
            group_key=group_key,
            group_num=5,
            chat_id="g-101",
            chat_name="客户群-101",
            sender_id="u-1",
            sender_name="Alice",
            message_id="msg-1",
            input_sign=1,
            amount=100,
            category="rmb",
            rate=None,
            rmb_value=100,
            raw="rmb+100",
            created_at="2026-03-19 09:00:00",
        )
        self.db.settle_transactions(
            "wechat",
            group_key,
            self.db.get_unsettled_transactions(group_key),
            "finance-a",
            settled_at="2026-03-19 09:30:00",
        )
        first_run = AccountingPeriodService(self.db).backfill_legacy_periods()
        self.assertEqual(first_run, 1)

        second_tx_id = self.db.add_transaction(
            platform="wechat",
            group_key=group_key,
            group_num=5,
            chat_id="g-101",
            chat_name="客户群-101",
            sender_id="u-1",
            sender_name="Alice",
            message_id="msg-2",
            input_sign=1,
            amount=50,
            category="rmb",
            rate=None,
            rmb_value=50,
            raw="rmb+50",
            created_at="2026-03-19 10:00:00",
        )
        self.db.settle_transactions(
            "wechat",
            group_key,
            self.db.get_unsettled_transactions(group_key),
            "finance-a",
            settled_at="2026-03-19 10:30:00",
        )

        second_run = AccountingPeriodService(self.db).backfill_legacy_periods()
        self.assertEqual(second_run, 1)

        periods = self.db.list_accounting_periods()
        self.assertEqual(len(periods), 2)
        first_period = periods[0]
        second_period = periods[1]
        self.assertEqual(str(first_period["closed_at"]), "2026-03-19 09:30:00")
        self.assertEqual(str(second_period["closed_at"]), "2026-03-19 10:30:00")

        first_snapshot = self.db.list_period_group_snapshots(int(first_period["id"]))[0]
        second_snapshot = self.db.list_period_group_snapshots(int(second_period["id"]))[0]
        self.assertEqual(round(float(first_snapshot["closing_balance"]), 2), 100.00)
        self.assertEqual(round(float(second_snapshot["opening_balance"]), 2), 100.00)
        self.assertEqual(round(float(second_snapshot["closing_balance"]), 2), 150.00)

        self.assertEqual(
            self.db.conn.execute("SELECT COUNT(*) AS cnt FROM transactions WHERE id IN (?, ?)", (first_tx_id, second_tx_id)).fetchone()["cnt"],
            2,
        )

    def test_backfill_legacy_periods_applies_manual_adjustments(self) -> None:
        group_key = "wechat:g-102"
        self.db.set_group(
            platform="wechat",
            group_key=group_key,
            chat_id="g-102",
            chat_name="客户群-102",
            group_num=5,
        )
        self.db.add_transaction(
            platform="wechat",
            group_key=group_key,
            group_num=5,
            chat_id="g-102",
            chat_name="客户群-102",
            sender_id="u-1",
            sender_name="Alice",
            message_id="msg-1",
            input_sign=1,
            amount=380,
            category="rmb",
            rate=None,
            rmb_value=380,
            raw="rmb+380",
            created_at="2026-03-19 09:00:00",
        )
        self.db.settle_transactions(
            "wechat",
            group_key,
            self.db.get_unsettled_transactions(group_key),
            "finance-a",
            settled_at="2026-03-19 10:30:00",
        )
        settlement_id = int(self.db.get_settlements(group_key, 1)[0]["id"])
        self.db.add_manual_adjustment(
            settlement_id=settlement_id,
            group_key=group_key,
            opening_delta=20,
            income_delta=0,
            expense_delta=0,
            closing_delta=20,
            note="补记期初差额",
            created_by="finance-a",
        )

        created = AccountingPeriodService(self.db).backfill_legacy_periods()
        self.assertEqual(created, 1)

        period = self.db.list_accounting_periods()[0]
        self.assertEqual(int(period["has_adjustment"]), 1)
        snapshot = self.db.list_period_group_snapshots(int(period["id"]))[0]
        self.assertEqual(round(float(snapshot["opening_balance"]), 2), 20.00)
        self.assertEqual(round(float(snapshot["closing_balance"]), 2), 400.00)

    def test_backfill_legacy_periods_keeps_chronological_opening_when_later_period_exists(self) -> None:
        group_key = "wechat:g-103"
        self.db.set_group(
            platform="wechat",
            group_key=group_key,
            chat_id="g-103",
            chat_name="客户群-103",
            group_num=5,
        )

        self.db.add_transaction(
            platform="wechat",
            group_key=group_key,
            group_num=5,
            chat_id="g-103",
            chat_name="客户群-103",
            sender_id="u-1",
            sender_name="Alice",
            message_id="msg-1",
            input_sign=1,
            amount=100,
            category="rmb",
            rate=None,
            rmb_value=100,
            raw="rmb+100",
            created_at="2026-03-19 09:00:00",
        )
        self.db.settle_transactions(
            "wechat",
            group_key,
            self.db.get_unsettled_transactions(group_key),
            "finance-a",
            settled_at="2026-03-19 09:30:00",
        )
        self.db.add_transaction(
            platform="wechat",
            group_key=group_key,
            group_num=5,
            chat_id="g-103",
            chat_name="客户群-103",
            sender_id="u-1",
            sender_name="Alice",
            message_id="msg-2",
            input_sign=1,
            amount=50,
            category="rmb",
            rate=None,
            rmb_value=50,
            raw="rmb+50",
            created_at="2026-03-19 10:00:00",
        )
        self.db.settle_transactions(
            "wechat",
            group_key,
            self.db.get_unsettled_transactions(group_key),
            "finance-a",
            settled_at="2026-03-19 10:30:00",
        )

        later_period_id = self.db.insert_accounting_period(
            start_at="2026-03-19 09:00:00",
            end_at="2026-03-19 10:30:00",
            closed_at="2026-03-19 10:30:00",
            closed_by="finance-a",
            note="legacy",
            has_adjustment=0,
            snapshot_version=1,
        )
        self.db.insert_period_group_snapshot(
            period_id=later_period_id,
            group_key=group_key,
            platform="wechat",
            chat_name="客户群-103",
            group_num=5,
            business_role=None,
            opening_balance=100,
            income=50,
            expense=0,
            closing_balance=150,
            transaction_count=1,
        )
        self.db.conn.commit()

        created = AccountingPeriodService(self.db).backfill_legacy_periods()
        self.assertEqual(created, 1)

        periods = self.db.list_accounting_periods()
        self.assertEqual(len(periods), 2)
        earlier_period = next(row for row in periods if str(row["closed_at"]) == "2026-03-19 09:30:00")
        earlier_snapshot = self.db.list_period_group_snapshots(int(earlier_period["id"]))[0]
        self.assertLessEqual(str(earlier_period["start_at"]), str(earlier_period["closed_at"]))
        self.assertEqual(str(earlier_period["closed_at"]), "2026-03-19 09:30:00")
        self.assertEqual(round(float(earlier_snapshot["opening_balance"]), 2), 0.00)
        self.assertEqual(round(float(earlier_snapshot["closing_balance"]), 2), 100.00)

        later_snapshot = self.db.list_period_group_snapshots(int(later_period_id))[0]
        self.assertEqual(round(float(later_snapshot["closing_balance"]), 2), 150.00)

    def test_backfill_legacy_periods_includes_soft_deleted_settled_transactions(self) -> None:
        group_key = "wechat:g-104"
        self.db.set_group(
            platform="wechat",
            group_key=group_key,
            chat_id="g-104",
            chat_name="客户群-104",
            group_num=5,
        )
        tx_id = self.db.add_transaction(
            platform="wechat",
            group_key=group_key,
            group_num=5,
            chat_id="g-104",
            chat_name="客户群-104",
            sender_id="u-1",
            sender_name="Alice",
            message_id="msg-1",
            input_sign=1,
            amount=380,
            category="rmb",
            rate=None,
            rmb_value=380,
            raw="rmb+380",
            created_at="2026-03-19 09:00:00",
        )
        self.db.settle_transactions(
            "wechat",
            group_key,
            self.db.get_unsettled_transactions(group_key),
            "finance-a",
            settled_at="2026-03-19 10:30:00",
        )
        self.db.conn.execute("UPDATE transactions SET deleted = 1 WHERE id = ?", (tx_id,))
        self.db.conn.commit()

        created = AccountingPeriodService(self.db).backfill_legacy_periods()
        self.assertEqual(created, 1)

        period = self.db.list_accounting_periods()[0]
        snapshot = self.db.list_period_group_snapshots(int(period["id"]))[0]
        self.assertEqual(round(float(snapshot["opening_balance"]), 2), 0.00)
        self.assertEqual(round(float(snapshot["closing_balance"]), 2), 380.00)
        self.assertEqual(int(snapshot["transaction_count"]), 1)


class PeriodLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tempdir.name) / "periods.db"
        self.db = BookkeepingDB(self.db_path)

    def tearDown(self) -> None:
        self.db.close()
        self.tempdir.cleanup()

    def test_close_period_uses_half_open_window_and_persists_snapshots_and_card_stats(self) -> None:
        active_group = "wechat:g-201"
        idle_group = "wechat:g-202"
        for group_key, chat_name, group_num in (
            (active_group, "客户群-201", 5),
            (idle_group, "客户群-202", 6),
        ):
            platform, chat_id = group_key.split(":", 1)
            self.db.set_group(
                platform=platform,
                group_key=group_key,
                chat_id=chat_id,
                chat_name=chat_name,
                group_num=group_num,
            )

        self.db.add_transaction(
            platform="wechat",
            group_key=active_group,
            group_num=5,
            chat_id="g-201",
            chat_name="客户群-201",
            sender_id="u-1",
            sender_name="Alice",
            message_id="msg-1",
            input_sign=1,
            amount=100,
            category="rmb",
            rate=None,
            rmb_value=100,
            raw="rmb+100",
            created_at="2026-03-19 09:00:00",
        )
        self.db.add_transaction(
            platform="wechat",
            group_key=active_group,
            group_num=5,
            chat_id="g-201",
            chat_name="客户群-201",
            sender_id="u-1",
            sender_name="Alice",
            message_id="msg-2",
            input_sign=1,
            amount=50,
            category="rmb",
            rate=None,
            rmb_value=50,
            raw="rmb+50",
            created_at="2026-03-19 10:00:00",
        )
        self.db.add_transaction(
            platform="wechat",
            group_key=active_group,
            group_num=5,
            chat_id="g-201",
            chat_name="客户群-201",
            sender_id="u-1",
            sender_name="Alice",
            message_id="msg-3",
            input_sign=1,
            amount=25,
            category="rmb",
            rate=None,
            rmb_value=25,
            raw="rmb+25",
            created_at="2026-03-19 11:00:00",
        )
        self.db.add_transaction(
            platform="wechat",
            group_key=active_group,
            group_num=5,
            chat_id="g-201",
            chat_name="客户群-201",
            sender_id="u-1",
            sender_name="Alice",
            message_id="msg-4",
            input_sign=1,
            amount=4,
            category="rb",
            rate=2.5,
            rmb_value=-10,
            raw="rb+4x2.5",
            created_at="2026-03-19 11:30:00",
        )
        self.db.add_transaction(
            platform="wechat",
            group_key=idle_group,
            group_num=6,
            chat_id="g-202",
            chat_name="客户群-202",
            sender_id="u-2",
            sender_name="Bob",
            message_id="msg-5",
            input_sign=1,
            amount=40,
            category="rmb",
            rate=None,
            rmb_value=40,
            raw="rmb+40",
            created_at="2026-03-19 08:30:00",
        )

        period_id = AccountingPeriodService(self.db).close_period(
            start_at="2026-03-19 10:00:00",
            end_at="2026-03-19 12:00:00",
            closed_by="finance-a",
            note="日终关闭",
        )

        period = self.db.list_accounting_periods()[0]
        self.assertEqual(int(period["id"]), period_id)
        self.assertEqual(str(period["start_at"]), "2026-03-19 10:00:00")
        self.assertEqual(str(period["closed_at"]), "2026-03-19 12:00:00")
        self.assertEqual(str(period["closed_by"]), "finance-a")

        snapshots = self.db.list_period_group_snapshots(period_id)
        self.assertEqual(len(snapshots), 2)
        active_snapshot = next(row for row in snapshots if str(row["group_key"]) == active_group)
        idle_snapshot = next(row for row in snapshots if str(row["group_key"]) == idle_group)
        self.assertEqual(round(float(active_snapshot["opening_balance"]), 2), 100.00)
        self.assertEqual(round(float(active_snapshot["income"]), 2), 25.00)
        self.assertEqual(round(float(active_snapshot["expense"]), 2), 10.00)
        self.assertEqual(round(float(active_snapshot["closing_balance"]), 2), 115.00)
        self.assertEqual(int(active_snapshot["transaction_count"]), 2)
        self.assertEqual(round(float(idle_snapshot["opening_balance"]), 2), 40.00)
        self.assertEqual(round(float(idle_snapshot["closing_balance"]), 2), 40.00)
        self.assertEqual(int(idle_snapshot["transaction_count"]), 0)

        card_stats = self.db.list_period_card_stats(period_id)
        self.assertEqual(len(card_stats), 2)
        rmb_stat = next(row for row in card_stats if str(row["card_type"]) == "rmb")
        rb_stat = next(row for row in card_stats if str(row["card_type"]) == "rb")
        self.assertEqual(round(float(rmb_stat["rmb_amount"]), 2), 25.00)
        self.assertIsNone(rmb_stat["rate"])
        self.assertEqual(round(float(rb_stat["rmb_amount"]), 2), -10.00)
        self.assertEqual(round(float(rb_stat["rate"]), 2), 2.50)

    def test_close_period_includes_soft_deleted_settled_transactions(self) -> None:
        group_key = "wechat:g-203"
        self.db.set_group(
            platform="wechat",
            group_key=group_key,
            chat_id="g-203",
            chat_name="客户群-203",
            group_num=5,
        )
        self.db.add_transaction(
            platform="wechat",
            group_key=group_key,
            group_num=5,
            chat_id="g-203",
            chat_name="客户群-203",
            sender_id="u-1",
            sender_name="Alice",
            message_id="msg-1",
            input_sign=1,
            amount=100,
            category="rmb",
            rate=None,
            rmb_value=100,
            raw="rmb+100",
            created_at="2026-03-19 09:00:00",
        )
        tx_id = self.db.add_transaction(
            platform="wechat",
            group_key=group_key,
            group_num=5,
            chat_id="g-203",
            chat_name="客户群-203",
            sender_id="u-1",
            sender_name="Alice",
            message_id="msg-2",
            input_sign=1,
            amount=80,
            category="rmb",
            rate=None,
            rmb_value=80,
            raw="rmb+80",
            created_at="2026-03-19 11:00:00",
        )
        self.db.settle_transactions(
            "wechat",
            group_key,
            self.db.get_unsettled_transactions(group_key),
            "finance-a",
            settled_at="2026-03-19 11:30:00",
        )
        self.db.conn.execute("UPDATE transactions SET deleted = 1 WHERE id = ?", (tx_id,))
        self.db.conn.commit()

        period_id = AccountingPeriodService(self.db).close_period(
            start_at="2026-03-19 10:00:00",
            end_at="2026-03-19 12:00:00",
            closed_by="finance-a",
        )

        snapshot = self.db.list_period_group_snapshots(period_id)[0]
        self.assertEqual(round(float(snapshot["opening_balance"]), 2), 100.00)
        self.assertEqual(round(float(snapshot["closing_balance"]), 2), 180.00)
        self.assertEqual(int(snapshot["transaction_count"]), 1)

    def test_close_period_excludes_soft_deleted_unsettled_transactions(self) -> None:
        group_key = "wechat:g-204"
        self.db.set_group(
            platform="wechat",
            group_key=group_key,
            chat_id="g-204",
            chat_name="客户群-204",
            group_num=5,
        )
        self.db.add_transaction(
            platform="wechat",
            group_key=group_key,
            group_num=5,
            chat_id="g-204",
            chat_name="客户群-204",
            sender_id="u-1",
            sender_name="Alice",
            message_id="msg-1",
            input_sign=1,
            amount=100,
            category="rmb",
            rate=None,
            rmb_value=100,
            raw="rmb+100",
            created_at="2026-03-19 09:00:00",
        )
        settled_tx_id = self.db.add_transaction(
            platform="wechat",
            group_key=group_key,
            group_num=5,
            chat_id="g-204",
            chat_name="客户群-204",
            sender_id="u-1",
            sender_name="Alice",
            message_id="msg-2",
            input_sign=1,
            amount=80,
            category="rmb",
            rate=None,
            rmb_value=80,
            raw="rmb+80",
            created_at="2026-03-19 11:00:00",
        )
        soft_deleted_tx_id = self.db.add_transaction(
            platform="wechat",
            group_key=group_key,
            group_num=5,
            chat_id="g-204",
            chat_name="客户群-204",
            sender_id="u-1",
            sender_name="Alice",
            message_id="msg-3",
            input_sign=1,
            amount=60,
            category="rmb",
            rate=None,
            rmb_value=60,
            raw="rmb+60",
            created_at="2026-03-19 11:30:00",
        )
        self.db.settle_transactions(
            "wechat",
            group_key,
            [self.db.conn.execute("SELECT * FROM transactions WHERE id = ?", (settled_tx_id,)).fetchone()],
            "finance-a",
            settled_at="2026-03-19 11:45:00",
        )
        self.db.conn.execute("UPDATE transactions SET deleted = 1 WHERE id = ?", (soft_deleted_tx_id,))
        self.db.conn.commit()

        period_id = AccountingPeriodService(self.db).close_period(
            start_at="2026-03-19 10:00:00",
            end_at="2026-03-19 12:00:00",
            closed_by="finance-a",
        )

        snapshot = self.db.list_period_group_snapshots(period_id)[0]
        self.assertEqual(round(float(snapshot["opening_balance"]), 2), 100.00)
        self.assertEqual(round(float(snapshot["closing_balance"]), 2), 180.00)
        self.assertEqual(int(snapshot["transaction_count"]), 1)


if __name__ == "__main__":
    unittest.main()
