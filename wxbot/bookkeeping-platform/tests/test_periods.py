from __future__ import annotations

import threading
import unittest
from unittest.mock import patch

from bookkeeping_core.database import BookkeepingDB
from bookkeeping_core.periods import AccountingPeriodService
from tests.support.postgres_test_case import PostgresTestCase


def _make_tx(
    db: BookkeepingDB,
    *,
    group_key: str,
    chat_id: str,
    chat_name: str,
    created_at: str,
    input_sign: int,
    amount: float,
    category: str,
    rate: float | None,
    rmb_value: float,
    raw: str,
) -> int:
    return db.add_transaction(
        platform="wechat",
        group_key=group_key,
        group_num=db.get_group_num(group_key),
        chat_id=chat_id,
        chat_name=chat_name,
        sender_id="u-periods",
        sender_name="Periods",
        message_id=f"msg-{group_key}-{created_at}",
        input_sign=input_sign,
        amount=amount,
        category=category,
        rate=rate,
        rmb_value=rmb_value,
        raw=raw,
        created_at=created_at,
    )


class PeriodSchemaTests(PostgresTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.db = self.make_db("periods-schema")

    def tearDown(self) -> None:
        self.db.close()
        super().tearDown()

    def _columns(self, table_name: str) -> set[str]:
        rows = self.db.conn.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = current_schema()
              AND table_name = ?
            """,
            (table_name,),
        ).fetchall()
        return {str(row["column_name"]) for row in rows}

    def test_bootstraps_current_period_tables_and_columns(self) -> None:
        self.assertTrue({"accounting_periods", "period_group_snapshots", "period_card_stats"}.issubset({
            str(row["table_name"])
            for row in self.db.conn.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = current_schema()
                """
            ).fetchall()
        }))
        self.assertTrue({"business_role", "role_source", "capture_enabled", "status"}.issubset(self._columns("groups")))
        self.assertTrue({"usd_amount", "unit_face_value", "unit_count", "parse_version"}.issubset(self._columns("transactions")))
        self.assertSetEqual(
            self._columns("accounting_periods"),
            {"id", "start_at", "end_at", "closed_at", "closed_by", "note", "has_adjustment", "snapshot_version"},
        )


class PeriodLifecycleTests(PostgresTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.db = self.make_db("periods-lifecycle")
        self.db.set_group(
            platform="wechat",
            group_key="wechat:g-periods",
            chat_id="g-periods",
            chat_name="账期群",
            group_num=5,
        )

    def tearDown(self) -> None:
        self.db.close()
        super().tearDown()

    def test_close_period_closes_current_window_and_persists_snapshot(self) -> None:
        _make_tx(
            self.db,
            group_key="wechat:g-periods",
            chat_id="g-periods",
            chat_name="账期群",
            created_at="2026-03-20 09:00:00",
            input_sign=1,
            amount=300,
            category="rmb",
            rate=None,
            rmb_value=300,
            raw="+300rmb",
        )

        period_id = AccountingPeriodService(self.db).close_period(
            start_at="2026-03-20 08:00:00",
            end_at="2026-03-20 10:00:00",
            closed_by="finance-periods",
        )

        period = self.db.list_accounting_periods()[0]
        snapshot = self.db.list_period_group_snapshots(period_id)[0]
        self.assertEqual(int(period["id"]), period_id)
        self.assertEqual(str(period["closed_by"]), "finance-periods")
        self.assertEqual(int(snapshot["transaction_count"]), 1)
        self.assertEqual(round(float(snapshot["closing_balance"]), 2), 300.00)
        self.assertEqual(self.db.get_unsettled_transactions("wechat:g-periods"), [])

    def test_close_period_builds_period_card_stats_without_precomputed_usd_amount(self) -> None:
        tx_id = _make_tx(
            self.db,
            group_key="wechat:g-periods",
            chat_id="g-periods",
            chat_name="账期群",
            created_at="2026-03-20 09:10:00",
            input_sign=1,
            amount=60,
            category="steam",
            rate=10,
            rmb_value=60,
            raw="steam+60",
        )
        self.db.conn.execute(
            "UPDATE transactions SET unit_face_value = ?, unit_count = ? WHERE id = ?",
            (20, 3, tx_id),
        )
        self.db.conn.commit()

        period_id = AccountingPeriodService(self.db).close_period(
            start_at="2026-03-20 09:00:00",
            end_at="2026-03-20 10:00:00",
            closed_by="finance-periods",
        )

        card_row = self.db.list_period_card_stats(period_id)[0]
        self.assertEqual(str(card_row["card_type"]), "steam")
        self.assertEqual(round(float(card_row["usd_amount"]), 2), 60.00)
        self.assertEqual(round(float(card_row["unit_face_value"]), 2), 20.00)
        self.assertEqual(round(float(card_row["unit_count"]), 2), 3.00)

    def test_close_period_nets_card_usd_and_unit_count_for_correction_pairs(self) -> None:
        tx_plus = _make_tx(
            self.db,
            group_key="wechat:g-periods",
            chat_id="g-periods",
            chat_name="账期群",
            created_at="2026-03-20 09:10:00",
            input_sign=1,
            amount=300,
            category="it",
            rate=5.57,
            rmb_value=-1671,
            raw="+300it5.57",
        )
        tx_minus = _make_tx(
            self.db,
            group_key="wechat:g-periods",
            chat_id="g-periods",
            chat_name="账期群",
            created_at="2026-03-20 09:11:00",
            input_sign=-1,
            amount=300,
            category="it",
            rate=5.57,
            rmb_value=1671,
            raw="-300it5.57",
        )
        tx_new = _make_tx(
            self.db,
            group_key="wechat:g-periods",
            chat_id="g-periods",
            chat_name="账期群",
            created_at="2026-03-20 09:12:00",
            input_sign=1,
            amount=300,
            category="it",
            rate=5.63,
            rmb_value=-1689,
            raw="+300it5.63",
        )
        self.db.conn.execute(
            "UPDATE transactions SET unit_count = ?, usd_amount = ? WHERE id IN (?, ?, ?)",
            (300, 300, tx_plus, tx_minus, tx_new),
        )
        self.db.conn.commit()

        period_id = AccountingPeriodService(self.db).close_period(
            start_at="2026-03-20 09:00:00",
            end_at="2026-03-20 10:00:00",
            closed_by="finance-periods",
        )

        card_rows = sorted(
            self.db.list_period_card_stats(period_id),
            key=lambda row: float(row["rate"]) if row["rate"] is not None else 0.0,
        )
        self.assertEqual(len(card_rows), 2)
        self.assertEqual(round(float(card_rows[0]["rate"]), 2), 5.57)
        self.assertEqual(round(float(card_rows[0]["usd_amount"]), 2), 0.00)
        self.assertEqual(round(float(card_rows[0]["unit_count"]), 2), 0.00)
        self.assertEqual(round(float(card_rows[1]["rate"]), 2), 5.63)
        self.assertEqual(round(float(card_rows[1]["usd_amount"]), 2), 300.00)
        self.assertEqual(round(float(card_rows[1]["unit_count"]), 2), 300.00)

    def test_settle_all_with_receipts_serializes_concurrent_requests(self) -> None:
        _make_tx(
            self.db,
            group_key="wechat:g-periods",
            chat_id="g-periods",
            chat_name="账期群",
            created_at="2026-03-20 09:30:00",
            input_sign=1,
            amount=300,
            category="rmb",
            rate=None,
            rmb_value=300,
            raw="+300rmb",
        )
        other_db = BookkeepingDB(self.make_dsn("periods-lifecycle"))
        self.addCleanup(other_db.close)
        first_entered = threading.Event()
        release_first = threading.Event()
        results: list[dict | None] = []
        errors: list[Exception] = []
        original_close_period = AccountingPeriodService._close_period_locked

        def delayed_close_period(self, *, start_at: str, end_at: str, closed_by: str, note: str | None = None) -> int:
            if not first_entered.is_set():
                first_entered.set()
                release_first.wait(timeout=2)
            return original_close_period(
                self,
                start_at=start_at,
                end_at=end_at,
                closed_by=closed_by,
                note=note,
            )

        def worker(db: BookkeepingDB, closed_by: str) -> None:
            try:
                result = AccountingPeriodService(db).settle_all_with_receipts(
                    closed_by=closed_by,
                    note=closed_by,
                )
                results.append(result)
            except Exception as exc:  # pragma: no cover - assertion below surfaces payload
                errors.append(exc)

        with patch.object(
            AccountingPeriodService,
            "_backup_postgres_after_period_close",
            return_value=None,
        ):
            with patch.object(
                AccountingPeriodService,
                "_close_period_locked",
                delayed_close_period,
            ):
                first = threading.Thread(
                    target=worker,
                    args=(self.db, "finance-periods-a"),
                )
                second = threading.Thread(
                    target=worker,
                    args=(other_db, "finance-periods-b"),
                )
                first.start()
                self.assertTrue(first_entered.wait(timeout=2))
                second.start()
                release_first.set()
                first.join(timeout=5)
                second.join(timeout=5)

        self.assertEqual(errors, [])
        settled_results = [item for item in results if item is not None]
        empty_results = [item for item in results if item is None]
        self.assertEqual(len(settled_results), 1)
        self.assertEqual(len(empty_results), 1)
        self.assertEqual(len(self.db.list_accounting_periods()), 1)
        self.assertEqual(self.db.get_unsettled_transactions("wechat:g-periods"), [])


if __name__ == "__main__":
    unittest.main()
