from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from bookkeeping_core.database import BookkeepingDB
from bookkeeping_core.importers import import_whatsapp_legacy_db
from bookkeeping_core.reporting import ReportingService


def _set_created_at(db: BookkeepingDB, tx_id: int, created_at: str) -> None:
    db.conn.execute(
        "UPDATE transactions SET created_at = ? WHERE id = ?",
        (created_at, tx_id),
    )
    db.conn.commit()


def _make_tx(
    db: BookkeepingDB,
    *,
    platform: str,
    group_key: str,
    chat_id: str,
    chat_name: str,
    sender_id: str,
    sender_name: str,
    input_sign: int,
    amount: float,
    category: str,
    rate: float | None,
    rmb_value: float,
    raw: str,
    created_at: str,
) -> int:
    tx_id = db.add_transaction(
        platform=platform,
        group_key=group_key,
        group_num=db.get_group_num(group_key),
        chat_id=chat_id,
        chat_name=chat_name,
        sender_id=sender_id,
        sender_name=sender_name,
        message_id=f"msg-{created_at}",
        input_sign=input_sign,
        amount=amount,
        category=category,
        rate=rate,
        rmb_value=rmb_value,
        raw=raw,
    )
    _set_created_at(db, tx_id, created_at)
    return tx_id


class ReportingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tempdir.name) / "bookkeeping.db"
        self.db = BookkeepingDB(self.db_path)

    def tearDown(self) -> None:
        self.db.close()
        self.tempdir.cleanup()

    def test_period_summary_uses_actual_settlement_window(self) -> None:
        group_key = "wechat:g-1"
        self.db.set_group(
            platform="wechat",
            group_key=group_key,
            chat_id="g-1",
            chat_name="客户群-A",
            group_num=5,
        )

        _make_tx(
            self.db,
            platform="wechat",
            group_key=group_key,
            chat_id="g-1",
            chat_name="客户群-A",
            sender_id="u-1",
            sender_name="Alice",
            input_sign=1,
            amount=500,
            category="rmb",
            rate=None,
            rmb_value=500,
            raw="rmb+500",
            created_at="2026-03-19 09:00:00",
        )
        _make_tx(
            self.db,
            platform="wechat",
            group_key=group_key,
            chat_id="g-1",
            chat_name="客户群-A",
            sender_id="u-1",
            sender_name="Alice",
            input_sign=-1,
            amount=120,
            category="rmb",
            rate=None,
            rmb_value=-120,
            raw="-120rmb",
            created_at="2026-03-19 10:00:00",
        )
        settled = self.db.get_unsettled_transactions(group_key)
        result = self.db.settle_transactions("wechat", group_key, settled, "finance-a", settled_at="2026-03-19 10:30:00")
        self.assertEqual(round(result["total_rmb"], 2), 380.00)

        _make_tx(
            self.db,
            platform="wechat",
            group_key=group_key,
            chat_id="g-1",
            chat_name="客户群-A",
            sender_id="u-1",
            sender_name="Alice",
            input_sign=1,
            amount=50,
            category="rmb",
            rate=None,
            rmb_value=50,
            raw="rmb+50",
            created_at="2026-03-19 11:00:00",
        )

        settlement_id = self.db.get_settlements(group_key, 1)[0]["id"]
        rows = ReportingService(self.db).get_period_group_rows(settlement_id)

        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["group_key"], group_key)
        self.assertEqual(round(row["opening_balance"], 2), 0.00)
        self.assertEqual(round(row["income"], 2), 500.00)
        self.assertEqual(round(row["expense"], 2), 120.00)
        self.assertEqual(round(row["closing_balance"], 2), 380.00)

    def test_manual_adjustment_changes_period_result_and_keeps_audit(self) -> None:
        group_key = "wechat:g-2"
        self.db.set_group(
            platform="wechat",
            group_key=group_key,
            chat_id="g-2",
            chat_name="客户群-B",
            group_num=6,
        )
        _make_tx(
            self.db,
            platform="wechat",
            group_key=group_key,
            chat_id="g-2",
            chat_name="客户群-B",
            sender_id="u-2",
            sender_name="Bob",
            input_sign=1,
            amount=200,
            category="rmb",
            rate=None,
            rmb_value=200,
            raw="rmb+200",
            created_at="2026-03-19 09:00:00",
        )
        settled = self.db.get_unsettled_transactions(group_key)
        self.db.settle_transactions("wechat", group_key, settled, "finance-b", settled_at="2026-03-19 09:30:00")
        settlement_id = self.db.get_settlements(group_key, 1)[0]["id"]

        adjustment_id = self.db.add_manual_adjustment(
            settlement_id=settlement_id,
            group_key=group_key,
            opening_delta=0,
            income_delta=0,
            expense_delta=30,
            closing_delta=-30,
            note="补记手续费",
            created_by="finance-lead",
        )
        self.assertGreater(adjustment_id, 0)

        rows = ReportingService(self.db).get_period_group_rows(settlement_id)
        row = rows[0]
        self.assertEqual(round(row["expense"], 2), 30.00)
        self.assertEqual(round(row["closing_balance"], 2), 170.00)

        adjustments = self.db.get_manual_adjustments(settlement_id)
        self.assertEqual(len(adjustments), 1)
        self.assertEqual(adjustments[0]["created_by"], "finance-lead")

    def test_group_number_combination_rolls_up_selected_modules(self) -> None:
        specs = [
            ("wechat:g-11", "客户群-1", 5, 120.0),
            ("wechat:g-12", "客户群-2", 7, 80.0),
            ("whatsapp:g-21", "供应商群-1", 2, -60.0),
        ]
        for group_key, chat_name, group_num, balance in specs:
            platform, chat_id = group_key.split(":", 1)
            self.db.set_group(
                platform=platform,
                group_key=group_key,
                chat_id=chat_id,
                chat_name=chat_name,
                group_num=group_num,
            )
            _make_tx(
                self.db,
                platform=platform,
                group_key=group_key,
                chat_id=chat_id,
                chat_name=chat_name,
                sender_id="system",
                sender_name="system",
                input_sign=1 if balance >= 0 else -1,
                amount=abs(balance),
                category="rmb",
                rate=None,
                rmb_value=balance,
                raw=str(balance),
                created_at="2026-03-19 08:00:00",
            )

        service = ReportingService(self.db)
        summary = service.get_combination_summary([5, 7], label="客户汇总")

        self.assertEqual(summary["label"], "客户汇总")
        self.assertEqual(summary["group_numbers"], [5, 7])
        self.assertEqual(summary["group_count"], 2)
        self.assertEqual(round(summary["current_balance"], 2), 200.00)

    def test_whatsapp_legacy_import_brings_groups_transactions_and_settlements(self) -> None:
        legacy_path = Path(self.tempdir.name) / "legacy-whatsapp.db"
        legacy_conn = sqlite3.connect(legacy_path)
        legacy_conn.executescript(
            """
            CREATE TABLE transactions (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              group_id TEXT NOT NULL,
              sender_id TEXT NOT NULL,
              input_sign INTEGER NOT NULL,
              amount REAL NOT NULL,
              category TEXT NOT NULL,
              rate REAL,
              rmb_value REAL NOT NULL,
              raw TEXT NOT NULL,
              created_at TEXT NOT NULL,
              deleted INTEGER NOT NULL DEFAULT 0,
              settled INTEGER NOT NULL DEFAULT 0,
              ngn_rate REAL
            );
            CREATE TABLE settlements (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              group_id TEXT NOT NULL,
              settle_date TEXT NOT NULL,
              total_rmb REAL NOT NULL,
              detail TEXT NOT NULL,
              settled_at TEXT NOT NULL,
              settled_by TEXT NOT NULL
            );
            CREATE TABLE groups (
              group_id TEXT PRIMARY KEY,
              group_num INTEGER,
              created_at TEXT NOT NULL
            );
            """
        )
        legacy_conn.execute(
            "INSERT INTO groups (group_id, group_num, created_at) VALUES (?, ?, ?)",
            ("120363@g.us", 3, "2026-03-01 00:00:00"),
        )
        legacy_conn.execute(
            """
            INSERT INTO transactions (
              group_id, sender_id, input_sign, amount, category, rate, rmb_value, raw,
              created_at, deleted, settled, ngn_rate
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 1, ?)
            """,
            ("120363@g.us", "+85270000000", 1, 100, "rmb", None, 100, "rmb+100", "2026-03-19 08:00:00", None),
        )
        legacy_conn.execute(
            """
            INSERT INTO settlements (
              group_id, settle_date, total_rmb, detail, settled_at, settled_by
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("120363@g.us", "legacy", 100, "RMB: 1 txs +100.00", "2026-03-19 09:00:00", "+85270000000"),
        )
        legacy_conn.commit()
        legacy_conn.close()

        imported = import_whatsapp_legacy_db(legacy_path, self.db)
        self.assertEqual(imported["transactions"], 1)
        self.assertEqual(imported["settlements"], 1)
        self.assertEqual(imported["groups"], 1)

        balance_rows = ReportingService(self.db).get_current_group_rows()
        self.assertEqual(len(balance_rows), 1)
        self.assertEqual(balance_rows[0]["platform"], "whatsapp")
        self.assertEqual(balance_rows[0]["group_num"], 3)


if __name__ == "__main__":
    unittest.main()
