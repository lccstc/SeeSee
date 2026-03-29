from __future__ import annotations

import csv
import io
import unittest

from bookkeeping_core.database import BookkeepingDB
from bookkeeping_core.periods import AccountingPeriodService
from bookkeeping_core.reconciliation import (
    ISSUE_EDITED_UNREVIEWED,
    ISSUE_MISSING_RATE,
    ISSUE_PENDING_RECONCILIATION,
    ISSUE_RATE_FORMULA_ERROR,
    ReconciliationService,
)
from tests.support.postgres_test_case import PostgresTestCase


class ReconciliationServiceTests(PostgresTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.db = BookkeepingDB(self.make_dsn("reconciliation-service"))
        self.db.set_group(
            platform="wechat",
            group_key="wechat:g-customer",
            chat_id="g-customer",
            chat_name="客户群-对账",
            group_num=5,
        )
        self.db.set_group(
            platform="wechat",
            group_key="wechat:g-vendor",
            chat_id="g-vendor",
            chat_name="供应商群-对账",
            group_num=2,
        )
        self.db.conn.execute(
            "UPDATE groups SET business_role = ? WHERE group_key = ?",
            ("customer", "wechat:g-customer"),
        )
        self.db.conn.execute(
            "UPDATE groups SET business_role = ? WHERE group_key = ?",
            ("vendor", "wechat:g-vendor"),
        )
        self.db.conn.commit()

        self.db.add_transaction(
            platform="wechat",
            group_key="wechat:g-customer",
            group_num=5,
            chat_id="g-customer",
            chat_name="客户群-对账",
            sender_id="u-settled",
            sender_name="Settled",
            message_id="msg-settled",
            input_sign=1,
            amount=100,
            category="rmb",
            rate=None,
            rmb_value=100,
            raw="+100rmb",
            created_at="2026-03-20 09:00:00",
        )
        self.period_id = AccountingPeriodService(self.db).close_period(
            start_at="2026-03-20 08:00:00",
            end_at="2026-03-20 09:30:00",
            closed_by="finance",
        )

        self.formula_tx_id = self.db.add_transaction(
            platform="wechat",
            group_key="wechat:g-customer",
            group_num=5,
            chat_id="g-customer",
            chat_name="客户群-对账",
            sender_id="u-formula",
            sender_name="Formula",
            message_id="msg-formula",
            input_sign=1,
            amount=50,
            category="xb",
            rate=5,
            rmb_value=-260,
            usd_amount=50,
            raw="+50xb5",
            created_at="2026-03-21 10:00:00",
        )
        self.missing_rate_tx_id = self.db.add_transaction(
            platform="wechat",
            group_key="wechat:g-vendor",
            group_num=2,
            chat_id="g-vendor",
            chat_name="供应商群-对账",
            sender_id="u-missing-rate",
            sender_name="Missing",
            message_id="msg-missing-rate",
            input_sign=1,
            amount=20,
            category="it",
            rate=None,
            rmb_value=-100,
            usd_amount=20,
            raw="+20it",
            created_at="2026-03-21 10:05:00",
        )
        self.edited_tx_id = self.db.add_transaction(
            platform="wechat",
            group_key="wechat:g-customer",
            group_num=5,
            chat_id="g-customer",
            chat_name="客户群-对账",
            sender_id="u-edited",
            sender_name="Edited",
            message_id="msg-edited",
            input_sign=1,
            amount=50,
            category="xb",
            rate=4.9,
            rmb_value=-245,
            usd_amount=50,
            raw="+50xb4.9",
            created_at="2026-03-21 10:10:00",
        )
        self.db.update_transaction_fields(
            transaction_id=self.edited_tx_id,
            sender_name="Edited-Web",
            amount=50,
            category="xb",
            rate=5,
            rmb_value=-250,
            usd_amount=50,
        )
        self.db.add_transaction_edit_log(
            transaction_id=self.edited_tx_id,
            edited_by="finance-web",
            note="修正汇率",
            before_json="{}",
            after_json="{}",
        )
        self.db.add_finance_adjustment_entry(
            period_id=None,
            linked_transaction_id=self.formula_tx_id,
            group_key="wechat:g-customer",
            business_role="customer",
            card_type="fee",
            usd_amount=0,
            rate=None,
            rmb_amount=15,
            note="补录手续费",
            created_by="finance-web",
        )
        self.combination_id = self.db.save_group_combination(
            name="财务总览",
            group_numbers=[2, 5],
            note="客户+供应商",
            created_by="finance-web",
        )

    def tearDown(self) -> None:
        self.db.close()
        super().tearDown()

    def test_realtime_ledger_marks_formula_missing_rate_and_edited_rows(self) -> None:
        payload = ReconciliationService(self.db).build_ledger_payload(scope="realtime")

        self.assertEqual(payload["summary"]["unreconciled_count"], 4)
        self.assertEqual(payload["summary"]["rate_formula_error_count"], 1)
        self.assertEqual(payload["summary"]["missing_rate_count"], 1)
        self.assertEqual(payload["summary"]["edited_unreviewed_count"], 1)

        formula_row = next(row for row in payload["rows"] if row["row_type"] == "transaction" and row["row_id"] == self.formula_tx_id)
        self.assertIn(ISSUE_PENDING_RECONCILIATION, formula_row["issue_flags"])
        self.assertIn(ISSUE_RATE_FORMULA_ERROR, formula_row["issue_flags"])
        self.assertEqual(round(float(formula_row["variance_rmb"]), 2), -10.0)

        missing_rate_row = next(row for row in payload["rows"] if row["row_id"] == self.missing_rate_tx_id)
        self.assertIn(ISSUE_MISSING_RATE, missing_rate_row["issue_flags"])

        edited_row = next(row for row in payload["rows"] if row["row_id"] == self.edited_tx_id)
        self.assertIn(ISSUE_EDITED_UNREVIEWED, edited_row["issue_flags"])
        self.assertEqual(edited_row["edit_note"], "修正汇率")

        adjustment_row = next(row for row in payload["rows"] if row["row_type"] == "finance_adjustment")
        self.assertEqual(adjustment_row["card_type"], "fee")
        self.assertIn(ISSUE_PENDING_RECONCILIATION, adjustment_row["issue_flags"])

    def test_issue_filter_and_period_scope_are_supported(self) -> None:
        service = ReconciliationService(self.db)

        formula_only = service.build_ledger_payload(scope="realtime", issue_type="rate_formula_error")
        self.assertEqual(len(formula_only["rows"]), 1)
        self.assertEqual(formula_only["rows"][0]["row_id"], self.formula_tx_id)

        period_payload = service.build_ledger_payload(scope="period", period_id=self.period_id)
        self.assertEqual(period_payload["selected_period_id"], self.period_id)
        self.assertTrue(period_payload["rows"])
        self.assertTrue(all(row["period_status"] == "settled" for row in period_payload["rows"]))

    def test_combination_group_num_filters_and_summary_export_are_supported(self) -> None:
        self.db.set_group(
            platform="wechat",
            group_key="wechat:g-customer-extra",
            chat_id="g-customer-extra",
            chat_name="客户群-对账-额外",
            group_num=5,
        )
        self.db.conn.execute(
            "UPDATE groups SET business_role = ? WHERE group_key = ?",
            ("customer", "wechat:g-customer-extra"),
        )
        self.db.conn.commit()
        extra_tx_id = self.db.add_transaction(
            platform="wechat",
            group_key="wechat:g-customer-extra",
            group_num=5,
            chat_id="g-customer-extra",
            chat_name="客户群-对账-额外",
            sender_id="u-extra",
            sender_name="Extra",
            message_id="msg-extra",
            input_sign=1,
            amount=30,
            category="steam",
            rate=5,
            rmb_value=-150,
            usd_amount=30,
            raw="+30steam5",
            created_at="2026-03-21 10:20:00",
        )

        service = ReconciliationService(self.db)

        combination_payload = service.build_ledger_payload(scope="realtime", combination_id=self.combination_id)
        self.assertEqual(combination_payload["filters"]["combination_id"], self.combination_id)
        self.assertEqual(combination_payload["available_group_nums"], [2, 5])
        self.assertEqual(set(combination_payload["selected_combination"]["group_numbers"]), {2, 5})
        self.assertEqual({int(row["group_num"]) for row in combination_payload["rows"]}, {2, 5})

        group_num_payload = service.build_ledger_payload(scope="realtime", group_num=5)
        self.assertTrue(group_num_payload["rows"])
        self.assertEqual({int(row["group_num"]) for row in group_num_payload["rows"]}, {5})

        drilled_payload = service.build_ledger_payload(
            scope="realtime",
            combination_id=self.combination_id,
            group_key="wechat:g-customer-extra",
        )
        self.assertEqual(len(drilled_payload["rows"]), 1)
        self.assertEqual(drilled_payload["rows"][0]["row_id"], extra_tx_id)

        csv_text = service.export_ledger_csv(
            scope="realtime",
            combination_id=self.combination_id,
            export_mode="summary",
        )
        summary_rows = list(csv.DictReader(io.StringIO(csv_text)))
        self.assertEqual(
            {(row["business_role"], row["card_type"], row["row_count"]) for row in summary_rows},
            {
                ("customer", "fee", "1"),
                ("customer", "steam", "1"),
                ("customer", "xb", "2"),
                ("vendor", "it", "1"),
            },
        )
        self.assertTrue(all(row["combination_name"] == "财务总览" for row in summary_rows))


if __name__ == "__main__":
    unittest.main()
