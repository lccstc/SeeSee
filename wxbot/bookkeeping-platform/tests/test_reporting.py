from __future__ import annotations

import unittest

from bookkeeping_core.database import BookkeepingDB
from bookkeeping_core.periods import AccountingPeriodService
from bookkeeping_core.reporting import ReportingService
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
    rmb_value: float,
    raw: str,
) -> None:
    db.add_transaction(
        platform="wechat",
        group_key=group_key,
        group_num=db.get_group_num(group_key),
        chat_id=chat_id,
        chat_name=chat_name,
        sender_id="u-reporting",
        sender_name="Reporting",
        message_id=f"msg-{created_at}",
        input_sign=input_sign,
        amount=amount,
        category="rmb",
        rate=None,
        rmb_value=rmb_value,
        raw=raw,
        created_at=created_at,
    )


class ReportingTests(PostgresTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.db = self.make_db("reporting")
        self.db.set_group(
            platform="wechat",
            group_key="wechat:g-reporting",
            chat_id="g-reporting",
            chat_name="报表群",
            group_num=5,
        )

    def tearDown(self) -> None:
        self.db.close()
        super().tearDown()

    def test_get_period_group_rows_reads_only_current_accounting_periods(self) -> None:
        _make_tx(
            self.db,
            group_key="wechat:g-reporting",
            chat_id="g-reporting",
            chat_name="报表群",
            created_at="2026-03-19 09:00:00",
            input_sign=1,
            amount=500,
            rmb_value=500,
            raw="+500rmb",
        )
        _make_tx(
            self.db,
            group_key="wechat:g-reporting",
            chat_id="g-reporting",
            chat_name="报表群",
            created_at="2026-03-19 10:00:00",
            input_sign=-1,
            amount=120,
            rmb_value=-120,
            raw="-120rmb",
        )

        period_id = AccountingPeriodService(self.db).close_period(
            start_at="2026-03-19 08:00:00",
            end_at="2026-03-19 10:30:00",
            closed_by="finance-reporting",
        )

        rows = ReportingService(self.db).get_period_group_rows(period_id)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["period_id"], period_id)
        self.assertEqual(round(rows[0]["closing_balance"], 2), 380.00)

    def test_dashboard_payload_uses_only_accounting_period_rows(self) -> None:
        payload = ReportingService(self.db).build_dashboard_payload()
        self.assertEqual(payload["recent_periods"], [])

    def test_period_rows_count_adjustments_from_current_period_id(self) -> None:
        _make_tx(
            self.db,
            group_key="wechat:g-reporting",
            chat_id="g-reporting",
            chat_name="报表群",
            created_at="2026-03-19 09:00:00",
            input_sign=1,
            amount=200,
            rmb_value=200,
            raw="+200rmb",
        )
        period_id = AccountingPeriodService(self.db).close_period(
            start_at="2026-03-19 08:00:00",
            end_at="2026-03-19 09:30:00",
            closed_by="finance-reporting",
        )
        self.db.add_manual_adjustment(
            period_id=period_id,
            group_key="wechat:g-reporting",
            opening_delta=0,
            income_delta=10,
            expense_delta=0,
            closing_delta=10,
            note="补差",
            created_by="finance-reporting",
        )

        rows = ReportingService(self.db).get_period_group_rows(period_id)
        self.assertEqual(rows[0]["adjustment_count"], 1)


if __name__ == "__main__":
    unittest.main()
