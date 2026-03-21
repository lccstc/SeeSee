from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from bookkeeping_core.database import BookkeepingDB
from bookkeeping_core.periods import AccountingPeriodService
from bookkeeping_core.analytics import AnalyticsService


def _set_transaction_fields(
    db: BookkeepingDB,
    tx_id: int,
    *,
    created_at: str,
    usd_amount: float | None = None,
    unit_face_value: float | None = None,
    unit_count: float | None = None,
) -> None:
    db.conn.execute(
        """
        UPDATE transactions
        SET created_at = ?,
            usd_amount = ?,
            unit_face_value = ?,
            unit_count = ?
        WHERE id = ?
        """,
        (created_at, usd_amount, unit_face_value, unit_count, tx_id),
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
    usd_amount: float | None = None,
    unit_face_value: float | None = None,
    unit_count: float | None = None,
) -> int:
    tx_id = db.add_transaction(
        platform=platform,
        group_key=group_key,
        group_num=db.get_group_num(group_key),
        chat_id=chat_id,
        chat_name=chat_name,
        sender_id=sender_id,
        sender_name=sender_name,
        message_id=f"msg-{group_key}-{created_at}",
        input_sign=input_sign,
        amount=amount,
        category=category,
        rate=rate,
        rmb_value=rmb_value,
        raw=raw,
    )
    _set_transaction_fields(
        db,
        tx_id,
        created_at=created_at,
        usd_amount=usd_amount,
        unit_face_value=unit_face_value,
        unit_count=unit_count,
    )
    return tx_id


class DashboardAnalyticsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tempdir.name) / "analytics-dashboard.db"
        self.db = BookkeepingDB(self.db_path)

        self.db.set_group(
            platform="wechat",
            group_key="wechat:g-dashboard-a",
            chat_id="g-dashboard-a",
            chat_name="客户群-A",
            group_num=5,
        )
        self.db.conn.execute(
            "UPDATE groups SET business_role = ? WHERE group_key = ?",
            ("customer", "wechat:g-dashboard-a"),
        )
        self.db.set_group(
            platform="wechat",
            group_key="wechat:g-dashboard-b",
            chat_id="g-dashboard-b",
            chat_name="供应商群-B",
            group_num=7,
        )
        self.db.conn.execute(
            "UPDATE groups SET business_role = ? WHERE group_key = ?",
            ("vendor", "wechat:g-dashboard-b"),
        )
        self.db.set_group(
            platform="wechat",
            group_key="wechat:g-dashboard-c",
            chat_id="g-dashboard-c",
            chat_name="未分配群-C",
            group_num=8,
        )
        self.db.conn.commit()

        _make_tx(
            self.db,
            platform="wechat",
            group_key="wechat:g-dashboard-a",
            chat_id="g-dashboard-a",
            chat_name="客户群-A",
            sender_id="u-a",
            sender_name="Alice",
            input_sign=1,
            amount=400,
            category="rmb",
            rate=None,
            rmb_value=400,
            raw="rmb+400",
            created_at="2026-03-19 12:00:00",
        )
        _make_tx(
            self.db,
            platform="wechat",
            group_key="wechat:g-dashboard-a",
            chat_id="g-dashboard-a",
            chat_name="客户群-A",
            sender_id="u-a",
            sender_name="Alice",
            input_sign=1,
            amount=50,
            category="steam",
            rate=12.5,
            rmb_value=100,
            raw="steam 100u",
            created_at="2026-03-20 09:00:00",
            usd_amount=1250,
            unit_face_value=50,
            unit_count=25,
        )
        _make_tx(
            self.db,
            platform="wechat",
            group_key="wechat:g-dashboard-a",
            chat_id="g-dashboard-a",
            chat_name="客户群-A",
            sender_id="u-a",
            sender_name="Alice",
            input_sign=-1,
            amount=45,
            category="rmb",
            rate=None,
            rmb_value=-45,
            raw="-45rmb",
            created_at="2026-03-20 09:20:00",
        )
        _make_tx(
            self.db,
            platform="wechat",
            group_key="wechat:g-dashboard-b",
            chat_id="g-dashboard-b",
            chat_name="供应商群-B",
            sender_id="u-b",
            sender_name="Bob",
            input_sign=1,
            amount=300,
            category="rmb",
            rate=None,
            rmb_value=300,
            raw="rmb+300",
            created_at="2026-03-19 13:00:00",
        )
        _make_tx(
            self.db,
            platform="wechat",
            group_key="wechat:g-dashboard-c",
            chat_id="g-dashboard-c",
            chat_name="未分配群-C",
            sender_id="u-c",
            sender_name="Carol",
            input_sign=1,
            amount=105,
            category="rmb",
            rate=None,
            rmb_value=105,
            raw="rmb+105",
            created_at="2026-03-18 18:00:00",
        )

        AccountingPeriodService(self.db).close_period(
            start_at="2026-03-20 08:00:00",
            end_at="2026-03-20 10:00:00",
            closed_by="finance-a",
        )

    def tearDown(self) -> None:
        self.db.close()
        self.tempdir.cleanup()

    def test_dashboard_cards_report_total_balance_today_profit_and_total_usd(self) -> None:
        service = AnalyticsService(self.db)

        payload = service.build_dashboard_summary(today="2026-03-20")

        self.assertEqual(round(payload["current_total_balance"], 2), 860.00)
        self.assertEqual(round(payload["today_realized_profit"], 2), 55.00)
        self.assertEqual(round(payload["today_total_usd_amount"], 2), 1250.00)
        self.assertEqual(payload["unassigned_group_count"], 1)


class WorkbenchAnalyticsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tempdir.name) / "analytics-workbench.db"
        self.db = BookkeepingDB(self.db_path)
        self.db.set_group(
            platform="wechat",
            group_key="wechat:g-workbench",
            chat_id="g-workbench",
            chat_name="工作台群",
            group_num=6,
        )
        self.db.conn.execute(
            "UPDATE groups SET business_role = ? WHERE group_key = ?",
            ("customer", "wechat:g-workbench"),
        )
        self.db.conn.commit()

        _make_tx(
            self.db,
            platform="wechat",
            group_key="wechat:g-workbench",
            chat_id="g-workbench",
            chat_name="工作台群",
            sender_id="u-w",
            sender_name="Wendy",
            input_sign=1,
            amount=20,
            category="rmb",
            rate=None,
            rmb_value=20,
            raw="rmb+20",
            created_at="2026-03-20 07:30:00",
        )
        _make_tx(
            self.db,
            platform="wechat",
            group_key="wechat:g-workbench",
            chat_id="g-workbench",
            chat_name="工作台群",
            sender_id="u-w",
            sender_name="Wendy",
            input_sign=1,
            amount=20,
            category="steam",
            rate=12,
            rmb_value=50,
            raw="steam 50u",
            created_at="2026-03-20 08:20:00",
            usd_amount=600,
            unit_face_value=20,
            unit_count=30,
        )
        _make_tx(
            self.db,
            platform="wechat",
            group_key="wechat:g-workbench",
            chat_id="g-workbench",
            chat_name="工作台群",
            sender_id="u-w",
            sender_name="Wendy",
            input_sign=-1,
            amount=15,
            category="rmb",
            rate=None,
            rmb_value=-15,
            raw="-15rmb",
            created_at="2026-03-20 09:20:00",
        )

    def tearDown(self) -> None:
        self.db.close()
        self.tempdir.cleanup()

    def test_period_workbench_returns_selected_period_summary_and_card_stats(self) -> None:
        period_id = AccountingPeriodService(self.db).close_period(
            start_at="2026-03-20 08:00:00",
            end_at="2026-03-20 10:00:00",
            closed_by="finance-a",
        )

        payload = AnalyticsService(self.db).build_period_workbench(period_id=period_id)

        self.assertEqual(payload["selected_period"]["id"], period_id)
        self.assertEqual(round(payload["summary"]["profit"], 2), 35.00)
        self.assertEqual(payload["card_stats"][0]["card_type"], "steam")
        self.assertGreaterEqual(len(payload["periods"]), 1)


class HistoryAnalyticsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tempdir.name) / "analytics-history.db"
        self.db = BookkeepingDB(self.db_path)

        self.db.set_group(
            platform="wechat",
            group_key="wechat:g-history-a",
            chat_id="g-history-a",
            chat_name="历史群-A",
            group_num=1,
        )
        self.db.set_group(
            platform="wechat",
            group_key="wechat:g-history-b",
            chat_id="g-history-b",
            chat_name="历史群-B",
            group_num=2,
        )
        self.db.conn.execute(
            "UPDATE groups SET business_role = ? WHERE group_key IN (?, ?)",
            ("customer", "wechat:g-history-a", "wechat:g-history-b"),
        )
        self.db.conn.commit()

        _make_tx(
            self.db,
            platform="wechat",
            group_key="wechat:g-history-a",
            chat_id="g-history-a",
            chat_name="历史群-A",
            sender_id="u-ha",
            sender_name="Henry",
            input_sign=1,
            amount=20,
            category="steam",
            rate=10,
            rmb_value=30,
            raw="steam-mar-1",
            created_at="2026-03-05 08:30:00",
            usd_amount=500,
            unit_face_value=20,
            unit_count=25,
        )
        _make_tx(
            self.db,
            platform="wechat",
            group_key="wechat:g-history-a",
            chat_id="g-history-a",
            chat_name="历史群-A",
            sender_id="u-ha",
            sender_name="Henry",
            input_sign=-1,
            amount=20,
            category="rmb",
            rate=None,
            rmb_value=-20,
            raw="-20rmb",
            created_at="2026-03-05 08:45:00",
        )
        AccountingPeriodService(self.db).close_period(
            start_at="2026-03-05 08:00:00",
            end_at="2026-03-05 09:00:00",
            closed_by="finance-h1",
        )

        _make_tx(
            self.db,
            platform="wechat",
            group_key="wechat:g-history-b",
            chat_id="g-history-b",
            chat_name="历史群-B",
            sender_id="u-hb",
            sender_name="Helen",
            input_sign=1,
            amount=15,
            category="steam",
            rate=10,
            rmb_value=25,
            raw="steam-mar-2",
            created_at="2026-03-20 08:30:00",
            usd_amount=300,
            unit_face_value=15,
            unit_count=20,
        )
        _make_tx(
            self.db,
            platform="wechat",
            group_key="wechat:g-history-b",
            chat_id="g-history-b",
            chat_name="历史群-B",
            sender_id="u-hb",
            sender_name="Helen",
            input_sign=1,
            amount=10,
            category="psn",
            rate=10,
            rmb_value=15,
            raw="psn-mar-2",
            created_at="2026-03-20 08:40:00",
            usd_amount=200,
            unit_face_value=10,
            unit_count=20,
        )
        AccountingPeriodService(self.db).close_period(
            start_at="2026-03-20 08:00:00",
            end_at="2026-03-20 09:00:00",
            closed_by="finance-h2",
        )

    def tearDown(self) -> None:
        self.db.close()
        self.tempdir.cleanup()

    def test_history_analysis_filters_periods_by_date_range_and_sorts_card_totals(self) -> None:
        payload = AnalyticsService(self.db).build_history_analysis(
            start_date="2026-03-01",
            end_date="2026-03-31",
            card_keyword="steam",
            sort_by="usd_amount",
        )

        self.assertEqual(len(payload["period_rows"]), 2)
        self.assertEqual(payload["card_rankings"][0]["card_type"], "steam")
        self.assertEqual(payload["range"]["start_date"], "2026-03-01")


if __name__ == "__main__":
    unittest.main()
