from __future__ import annotations

import unittest

from bookkeeping_core.database import BookkeepingDB
from bookkeeping_core.periods import AccountingPeriodService
from bookkeeping_core.analytics import AnalyticsService
from tests.support.bookkeeping_replay import build_runtime_card_scenario, replay_runtime_scenario
from tests.support.postgres_test_case import PostgresTestCase


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


class DashboardAnalyticsTests(PostgresTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.db = BookkeepingDB(self.make_dsn("analytics-dashboard"))

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
        super().tearDown()

    def test_dashboard_cards_report_total_balance_today_profit_and_total_usd(self) -> None:
        service = AnalyticsService(self.db)

        payload = service.build_dashboard_summary(today="2026-03-20")

        self.assertEqual(round(payload["current_total_balance"], 2), 860.00)
        self.assertEqual(round(payload["today_realized_profit"], 2), 100.00)
        self.assertEqual(round(payload["today_total_usd_amount"], 2), 1250.00)
        self.assertEqual(round(payload["today_customer_card_rmb_amount"], 2), 100.00)
        self.assertEqual(round(payload["today_vendor_card_rmb_amount"], 2), 0.00)
        self.assertEqual(payload["unassigned_group_count"], 0)

    def test_dashboard_cards_ignore_today_live_transactions_for_realized_profit(self) -> None:
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
            category="xb",
            rate=5.0,
            rmb_value=-250,
            raw="+50xb5",
            created_at="2026-03-20 10:30:00",
        )

        payload = AnalyticsService(self.db).build_dashboard_summary(today="2026-03-20")

        self.assertEqual(payload["range_label"], "2026-03-20 结算账期")
        self.assertEqual(round(payload["today_realized_profit"], 2), 100.00)
        self.assertEqual(round(payload["today_total_usd_amount"], 2), 1250.00)

    def test_dashboard_summary_uses_group_number_defaults_and_chinese_role_aliases(self) -> None:
        db = BookkeepingDB(self.make_dsn("analytics-dashboard-role-mapping"))
        try:
            db.set_group(
                platform="whatsapp",
                group_key="whatsapp:g-internal",
                chat_id="g-internal",
                chat_name="内部群",
                group_num=1,
            )
            db.add_transaction(
                platform="whatsapp",
                group_key="whatsapp:g-internal",
                group_num=1,
                chat_id="g-internal",
                chat_name="内部群",
                sender_id="u-internal",
                sender_name="Internal",
                message_id="internal-1",
                input_sign=1,
                amount=100,
                category="rmb",
                rate=None,
                rmb_value=100,
                raw="rmb+100",
                created_at="2026-03-23 09:00:00",
            )
            db.set_group(
                platform="whatsapp",
                group_key="whatsapp:g-customer",
                chat_id="g-customer",
                chat_name="客户群",
                group_num=5,
            )
            db.add_transaction(
                platform="whatsapp",
                group_key="whatsapp:g-customer",
                group_num=5,
                chat_id="g-customer",
                chat_name="客户群",
                sender_id="u-customer",
                sender_name="Customer",
                message_id="customer-1",
                input_sign=1,
                amount=300,
                category="rmb",
                rate=None,
                rmb_value=300,
                raw="rmb+300",
                created_at="2026-03-23 09:05:00",
            )
            db.set_group(
                platform="whatsapp",
                group_key="whatsapp:g-vendor",
                chat_id="g-vendor",
                chat_name="供应商群",
                group_num=9,
            )
            db.conn.execute(
                "UPDATE groups SET business_role = ? WHERE group_key = ?",
                ("供应商", "whatsapp:g-vendor"),
            )
            db.add_transaction(
                platform="whatsapp",
                group_key="whatsapp:g-vendor",
                group_num=9,
                chat_id="g-vendor",
                chat_name="供应商群",
                sender_id="u-vendor",
                sender_name="Vendor",
                message_id="vendor-1",
                input_sign=1,
                amount=80,
                category="rmb",
                rate=None,
                rmb_value=80,
                raw="rmb+80",
                created_at="2026-03-23 09:10:00",
            )
            db.conn.commit()

            payload = AnalyticsService(db).build_dashboard_summary(today="2026-03-23")

            self.assertEqual(round(payload["current_total_balance"], 2), 380.00)
            self.assertEqual(payload["unassigned_group_count"], 0)
        finally:
            db.close()

    def test_latest_transactions_follow_current_group_mapping_not_stale_transaction_group_num(self) -> None:
        db = BookkeepingDB(self.make_dsn("analytics-latest-role-refresh"))
        try:
            db.set_group(
                platform="whatsapp",
                group_key="whatsapp:g-role-refresh",
                chat_id="g-role-refresh",
                chat_name="角色刷新群",
                group_num=1,
            )
            tx_id = db.add_transaction(
                platform="whatsapp",
                group_key="whatsapp:g-role-refresh",
                group_num=1,
                chat_id="g-role-refresh",
                chat_name="角色刷新群",
                sender_id="u-role-refresh",
                sender_name="Role Refresh",
                message_id="role-refresh-1",
                input_sign=1,
                amount=50,
                category="xb",
                rate=5,
                rmb_value=-250,
                raw="+50xb5",
                created_at="2026-03-23 09:00:00",
            )
            self.assertGreater(tx_id, 0)
            db.set_group(
                platform="whatsapp",
                group_key="whatsapp:g-role-refresh",
                chat_id="g-role-refresh",
                chat_name="角色刷新群",
                group_num=2,
            )

            rows = AnalyticsService(db).build_latest_transactions(limit=1)

            self.assertEqual(rows[0]["group_num"], 2)
            self.assertEqual(rows[0]["business_role"], "vendor")
        finally:
            db.close()


class WorkbenchAnalyticsTests(PostgresTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.db = BookkeepingDB(self.make_dsn("analytics-workbench"))
        self.period_id = replay_runtime_scenario(
            self.db,
            build_runtime_card_scenario(
                message_prefix="analytics-workbench",
                chat_id="g-workbench",
                chat_name="工作台群",
                group_num=6,
                business_role="customer",
            ),
        )

    def tearDown(self) -> None:
        self.db.close()
        super().tearDown()

    def test_period_workbench_returns_selected_period_summary_and_card_stats(self) -> None:
        payload = AnalyticsService(self.db).build_period_workbench(period_id=self.period_id)

        self.assertEqual(payload["selected_period"]["id"], self.period_id)
        self.assertEqual(round(payload["summary"]["profit"], 2), 50.00)
        self.assertEqual(round(payload["summary"]["customer_card_rmb_amount"], 2), 50.00)
        self.assertEqual(round(payload["summary"]["vendor_card_rmb_amount"], 2), 0.00)
        self.assertEqual(payload["card_stats"][0]["card_type"], "steam")
        self.assertGreaterEqual(len(payload["periods"]), 1)

    def test_period_workbench_transactions_follow_current_unclosed_window(self) -> None:
        self.db.add_transaction(
            platform="wechat",
            group_key="wechat:g-workbench",
            group_num=6,
            chat_id="g-workbench",
            chat_name="工作台群",
            sender_id="finance-live",
            sender_name="Finance Live",
            message_id="analytics-workbench-live",
            input_sign=1,
            amount=88,
            category="steam",
            rate=2.2,
            rmb_value=88,
            raw="steam+88 2.2",
            parse_version="2",
            usd_amount=1200,
            unit_face_value=20,
            unit_count=60,
            created_at="2026-03-20 10:30:00",
        )

        payload = AnalyticsService(self.db).build_period_workbench(period_id=self.period_id)

        self.assertEqual(payload["live_window"]["transaction_count"], 1)
        self.assertEqual(payload["live_window"]["start_at"], "2026-03-20 10:00:00")
        self.assertGreaterEqual(len(payload["transactions"]), 1)
        row = payload["transactions"][0]
        self.assertEqual(row["message_id"], "analytics-workbench-live")
        self.assertEqual(row["sender_name"], "Finance Live")
        self.assertEqual(row["period_status"], "unsettled")
        self.assertIn("parse_version", row)
        self.assertIn("raw", row)
        self.assertIn("usd_amount", row)
        self.assertIn("unit_face_value", row)
        self.assertIn("unit_count", row)

    def test_period_workbench_live_window_resets_after_close(self) -> None:
        self.db.add_transaction(
            platform="wechat",
            group_key="wechat:g-workbench",
            group_num=6,
            chat_id="g-workbench",
            chat_name="工作台群",
            sender_id="finance-live",
            sender_name="Finance Live",
            message_id="analytics-workbench-reset",
            input_sign=1,
            amount=66,
            category="rmb",
            rate=None,
            rmb_value=66,
            raw="rmb+66",
            created_at="2026-03-20 10:30:00",
        )

        next_period_id = AccountingPeriodService(self.db).close_period(
            start_at="2026-03-20 10:00:00",
            end_at="2026-03-20 11:00:00",
            closed_by="finance-next",
        )
        payload = AnalyticsService(self.db).build_period_workbench(period_id=next_period_id)

        self.assertEqual(payload["live_window"]["transaction_count"], 0)
        self.assertEqual(payload["transactions"], [])

    def test_period_workbench_summary_falls_back_to_live_window_before_first_close(self) -> None:
        db = BookkeepingDB(self.make_dsn("analytics-workbench-live-only"))
        try:
            db.set_group(
                platform="whatsapp",
                group_key="whatsapp:g-live-a",
                chat_id="g-live-a",
                chat_name="实时群-A",
                group_num=1,
            )
            db.set_group(
                platform="whatsapp",
                group_key="whatsapp:g-live-b",
                chat_id="g-live-b",
                chat_name="实时群-B",
                group_num=2,
            )
            db.add_transaction(
                platform="whatsapp",
                group_key="whatsapp:g-live-a",
                group_num=1,
                chat_id="g-live-a",
                chat_name="实时群-A",
                sender_id="u-live-a",
                sender_name="Live A",
                message_id="live-a-1",
                input_sign=1,
                amount=50,
                category="xb",
                rate=5,
                rmb_value=-250,
                raw="+50xb5",
                created_at="2026-03-23 04:44:06",
            )
            db.add_transaction(
                platform="whatsapp",
                group_key="whatsapp:g-live-b",
                group_num=2,
                chat_id="g-live-b",
                chat_name="实时群-B",
                sender_id="u-live-b",
                sender_name="Live B",
                message_id="live-b-1",
                input_sign=1,
                amount=50,
                category="xb",
                rate=5,
                rmb_value=-250,
                raw="+50xb5",
                created_at="2026-03-23 04:45:35",
            )

            payload = AnalyticsService(db).build_period_workbench(period_id=None)

            self.assertIsNone(payload["selected_period"])
            self.assertEqual(payload["live_window"]["transaction_count"], 2)
            self.assertEqual(payload["summary"]["group_count"], 1)
            self.assertEqual(payload["summary"]["transaction_count"], 1)
            self.assertEqual(round(payload["summary"]["profit"], 2), -250.00)
            self.assertEqual(round(payload["summary"]["total_usd_amount"], 2), 50.00)
            self.assertEqual(len(payload["group_rows"]), 1)
            self.assertEqual(payload["group_rows"][0]["chat_name"], "实时群-B")
            self.assertEqual(payload["group_rows"][0]["business_role"], "vendor")
            self.assertEqual(payload["group_rows"][0]["transaction_count"], 1)
            self.assertEqual(len(payload["card_stats"]), 1)
            self.assertEqual(payload["card_stats"][0]["business_role"], "vendor")
            self.assertEqual(payload["card_stats"][0]["card_type"], "xb")
        finally:
            db.close()

    def test_period_workbench_live_summary_excludes_internal_groups_from_profit(self) -> None:
        db = BookkeepingDB(self.make_dsn("analytics-workbench-live-role-filter"))
        try:
            db.set_group(
                platform="whatsapp",
                group_key="whatsapp:g-internal",
                chat_id="g-internal",
                chat_name="内部群",
                group_num=1,
            )
            db.add_transaction(
                platform="whatsapp",
                group_key="whatsapp:g-internal",
                group_num=1,
                chat_id="g-internal",
                chat_name="内部群",
                sender_id="u-internal",
                sender_name="Internal",
                message_id="live-internal-1",
                input_sign=1,
                amount=120,
                category="rmb",
                rate=None,
                rmb_value=120,
                raw="rmb+120",
                created_at="2026-03-23 04:44:06",
            )
            db.set_group(
                platform="whatsapp",
                group_key="whatsapp:g-customer",
                chat_id="g-customer",
                chat_name="客户群",
                group_num=5,
            )
            db.add_transaction(
                platform="whatsapp",
                group_key="whatsapp:g-customer",
                group_num=5,
                chat_id="g-customer",
                chat_name="客户群",
                sender_id="u-customer",
                sender_name="Customer",
                message_id="live-customer-1",
                input_sign=1,
                amount=50,
                category="steam",
                rate=4,
                rmb_value=200,
                raw="steam+50 4",
                usd_amount=1000,
                unit_face_value=10,
                unit_count=100,
                created_at="2026-03-23 04:45:35",
            )

            payload = AnalyticsService(db).build_period_workbench(period_id=None)

            self.assertEqual(payload["summary"]["group_count"], 1)
            self.assertEqual(payload["summary"]["transaction_count"], 1)
            self.assertEqual(round(payload["summary"]["profit"], 2), 200.00)
            self.assertEqual(round(payload["summary"]["customer_card_rmb_amount"], 2), 200.00)
            self.assertEqual(round(payload["summary"]["vendor_card_rmb_amount"], 2), 0.00)
        finally:
            db.close()

    def test_period_workbench_live_summary_uses_absolute_customer_and_vendor_card_amounts(self) -> None:
        db = BookkeepingDB(self.make_dsn("analytics-workbench-live-absolute-card-profit"))
        try:
            db.set_group(
                platform="whatsapp",
                group_key="whatsapp:g-customer-profit",
                chat_id="g-customer-profit",
                chat_name="客户群-利润",
                group_num=5,
            )
            db.set_group(
                platform="whatsapp",
                group_key="whatsapp:g-vendor-profit",
                chat_id="g-vendor-profit",
                chat_name="供应商群-利润",
                group_num=2,
            )
            db.add_transaction(
                platform="whatsapp",
                group_key="whatsapp:g-customer-profit",
                group_num=5,
                chat_id="g-customer-profit",
                chat_name="客户群-利润",
                sender_id="u-customer-profit",
                sender_name="Customer Profit",
                message_id="live-customer-profit-1",
                input_sign=1,
                amount=50,
                category="xb",
                rate=5,
                rmb_value=-250,
                raw="+50xb5",
                created_at="2026-03-23 05:00:00",
            )
            db.add_transaction(
                platform="whatsapp",
                group_key="whatsapp:g-vendor-profit",
                group_num=2,
                chat_id="g-vendor-profit",
                chat_name="供应商群-利润",
                sender_id="u-vendor-profit",
                sender_name="Vendor Profit",
                message_id="live-vendor-profit-1",
                input_sign=1,
                amount=50,
                category="xb",
                rate=4.9,
                rmb_value=-245,
                raw="+50xb4.9",
                created_at="2026-03-23 05:01:00",
            )

            payload = AnalyticsService(db).build_period_workbench(period_id=None)

            self.assertEqual(round(payload["summary"]["customer_card_rmb_amount"], 2), 250.00)
            self.assertEqual(round(payload["summary"]["vendor_card_rmb_amount"], 2), 245.00)
            self.assertEqual(round(payload["summary"]["profit"], 2), 5.00)
            self.assertEqual(payload["role_card_breakdown"]["customer"]["rows"][0]["card_type"], "xb")
            self.assertEqual(payload["role_card_breakdown"]["vendor"]["rows"][0]["card_type"], "xb")
        finally:
            db.close()


class KnifeNettingAnalyticsTests(PostgresTestCase):
    def test_live_card_stats_net_out_correction_pairs_by_input_sign(self) -> None:
        db = BookkeepingDB(self.make_dsn("analytics-knife-netting-live"))
        try:
            db.set_group(
                platform="whatsapp",
                group_key="whatsapp:g-knife-netting",
                chat_id="g-knife-netting",
                chat_name="刀数对冲群",
                group_num=2,
            )
            db.conn.execute(
                "UPDATE groups SET business_role = ? WHERE group_key = ?",
                ("vendor", "whatsapp:g-knife-netting"),
            )
            db.conn.commit()

            # Correction flow: +300 -> -300 -> +300(new rate), should net to 300 in knife stats.
            _make_tx(
                db,
                platform="whatsapp",
                group_key="whatsapp:g-knife-netting",
                chat_id="g-knife-netting",
                chat_name="刀数对冲群",
                sender_id="u-knife",
                sender_name="Knife",
                input_sign=1,
                amount=300,
                category="it",
                rate=5.57,
                rmb_value=-1671,
                raw="+300it5.57",
                created_at="2026-03-25 09:00:00",
                usd_amount=300,
                unit_count=300,
            )
            _make_tx(
                db,
                platform="whatsapp",
                group_key="whatsapp:g-knife-netting",
                chat_id="g-knife-netting",
                chat_name="刀数对冲群",
                sender_id="u-knife",
                sender_name="Knife",
                input_sign=-1,
                amount=300,
                category="it",
                rate=5.57,
                rmb_value=1671,
                raw="-300it5.57",
                created_at="2026-03-25 09:01:00",
                usd_amount=300,
                unit_count=300,
            )
            _make_tx(
                db,
                platform="whatsapp",
                group_key="whatsapp:g-knife-netting",
                chat_id="g-knife-netting",
                chat_name="刀数对冲群",
                sender_id="u-knife",
                sender_name="Knife",
                input_sign=1,
                amount=300,
                category="it",
                rate=5.63,
                rmb_value=-1689,
                raw="+300it5.63",
                created_at="2026-03-25 09:02:00",
                usd_amount=300,
                unit_count=300,
            )

            payload = AnalyticsService(db).build_period_workbench(period_id=None)
            vendor = payload["role_card_breakdown"]["vendor"]

            self.assertEqual(round(float(vendor["total_usd_amount"]), 2), 300.00)
            self.assertEqual(round(float(vendor["total_unit_count"]), 2), 300.00)
            self.assertEqual(round(float(vendor["total_display_rmb_amount"]), 2), 1689.00)
        finally:
            db.close()


class HistoryAnalyticsTests(PostgresTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.db = BookkeepingDB(self.make_dsn("analytics-history"))
        replay_runtime_scenario(
            self.db,
            build_runtime_card_scenario(
                message_prefix="analytics-history-a",
                chat_id="g-history-a",
                chat_name="历史群-A",
                group_num=1,
                business_role="vendor",
                start_at="2026-03-05 08:00:00",
                end_at="2026-03-05 09:00:00",
                closed_by="finance-h1",
                opening_created_at="2026-03-05 07:30:00",
                card_created_at="2026-03-05 08:30:00",
                expense_created_at="2026-03-05 08:45:00",
                card_rate=1.5,
                card_rmb_value=30.0,
                card_usd_amount=500.0,
                card_unit_count=25.0,
                expense_amount=20.0,
            ),
        )
        replay_runtime_scenario(
            self.db,
            build_runtime_card_scenario(
                message_prefix="analytics-history-b",
                chat_id="g-history-b",
                chat_name="历史群-B",
                group_num=2,
                business_role="customer",
                start_at="2026-03-20 08:00:00",
                end_at="2026-03-20 09:00:00",
                closed_by="finance-h2",
                opening_created_at="2026-03-20 07:30:00",
                card_created_at="2026-03-20 08:30:00",
                expense_created_at="2026-03-20 08:40:00",
                card_amount=15.0,
                card_rate=2.0,
                card_rmb_value=25.0,
                card_usd_amount=300.0,
                card_unit_face_value=15.0,
                card_unit_count=20.0,
                expense_amount=5.0,
            ),
        )

    def tearDown(self) -> None:
        self.db.close()
        super().tearDown()

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


class MockReplayWorkbenchTests(PostgresTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.db = BookkeepingDB(self.make_dsn("analytics-runtime-replay"))

    def tearDown(self) -> None:
        self.db.close()
        super().tearDown()

    def test_runtime_replay_generates_workbench_and_history_card_sections(self) -> None:
        scenario = build_runtime_card_scenario(business_role="vendor")
        period_id = replay_runtime_scenario(self.db, scenario)

        workbench = AnalyticsService(self.db).build_period_workbench(period_id=period_id)
        history = AnalyticsService(self.db).build_history_analysis(
            start_date="2026-03-01",
            end_date="2026-03-31",
            card_keyword="steam",
            sort_by="usd_amount",
        )

        self.assertGreater(len(workbench["card_stats"]), 0)
        self.assertGreater(len(history["card_rankings"]), 0)


if __name__ == "__main__":
    unittest.main()
