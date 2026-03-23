from __future__ import annotations

import io
import json
import unittest
from urllib.parse import urlencode
from wsgiref.util import setup_testing_defaults

from bookkeeping_core.database import BookkeepingDB
from bookkeeping_core.periods import AccountingPeriodService
from bookkeeping_web.app import create_app
from tests.support.postgres_test_case import PostgresTestCase


class WebAppTests(PostgresTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.db_dsn = self.make_dsn("web-app")
        self.db = BookkeepingDB(self.db_dsn)
        self.db.add_admin("finance-web", "system", "bootstrap")
        self.db.set_group(
            platform="wechat",
            group_key="wechat:g-100",
            chat_id="g-100",
            chat_name="客户群-Web",
            group_num=5,
        )
        self.db.add_transaction(
            platform="wechat",
            group_key="wechat:g-100",
            group_num=5,
            chat_id="g-100",
            chat_name="客户群-Web",
            sender_id="u-web",
            sender_name="Web",
            message_id="msg-web",
            input_sign=1,
            amount=300,
            category="rmb",
            rate=None,
            rmb_value=300,
            raw="rmb+300",
            created_at="2026-03-20 09:00:00",
        )
        self.period_id = AccountingPeriodService(self.db).close_period(
            start_at="2026-03-20 08:00:00",
            end_at="2026-03-20 09:30:00",
            closed_by="finance-web",
        )
        self.app = create_app(self.db_dsn, core_token="core-secret")

    def tearDown(self) -> None:
        self.db.close()
        super().tearDown()

    def _request(
        self,
        method: str,
        path: str,
        payload: dict | None = None,
        headers: dict[str, str] | None = None,
        query_string: str | None = None,
    ) -> tuple[int, dict]:
        body = b""
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
        environ = {}
        setup_testing_defaults(environ)
        environ["REQUEST_METHOD"] = method
        environ["PATH_INFO"] = path
        environ["QUERY_STRING"] = query_string or ""
        environ["CONTENT_LENGTH"] = str(len(body))
        environ["wsgi.input"] = io.BytesIO(body)
        if body:
            environ["CONTENT_TYPE"] = "application/json"
        for key, value in (headers or {}).items():
            environ[f"HTTP_{key.upper().replace('-', '_')}"] = value

        response = {"status": 500, "body": b""}

        def start_response(status: str, headers: list[tuple[str, str]]) -> None:
            response["status"] = int(status.split(" ", 1)[0])

        chunks = self.app(environ, start_response)
        response["body"] = b"".join(chunks)
        return response["status"], json.loads(response["body"].decode("utf-8"))

    def _request_with_headers(
        self,
        method: str,
        path: str,
        payload: dict | None = None,
        headers: dict[str, str] | None = None,
        query_string: str | None = None,
    ) -> tuple[int, dict[str, str], dict]:
        body = b""
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
        environ = {}
        setup_testing_defaults(environ)
        environ["REQUEST_METHOD"] = method
        environ["PATH_INFO"] = path
        environ["QUERY_STRING"] = query_string or ""
        environ["CONTENT_LENGTH"] = str(len(body))
        environ["wsgi.input"] = io.BytesIO(body)
        if body:
            environ["CONTENT_TYPE"] = "application/json"
        for key, value in (headers or {}).items():
            environ[f"HTTP_{key.upper().replace('-', '_')}"] = value

        response = {"status": 500, "headers": {}, "body": b""}

        def start_response(status: str, response_headers: list[tuple[str, str]]) -> None:
            response["status"] = int(status.split(" ", 1)[0])
            response["headers"] = {key: value for key, value in response_headers}

        chunks = self.app(environ, start_response)
        response["body"] = b"".join(chunks)
        return (
            response["status"],
            response["headers"],
            json.loads(response["body"].decode("utf-8")),
        )

    def _request_text(self, method: str, path: str, *, query: dict[str, str | int] | None = None) -> tuple[int, str]:
        environ = {}
        setup_testing_defaults(environ)
        environ["REQUEST_METHOD"] = method
        environ["PATH_INFO"] = path
        environ["QUERY_STRING"] = urlencode(query or {})
        environ["CONTENT_LENGTH"] = "0"
        environ["wsgi.input"] = io.BytesIO(b"")

        response = {"status": 500, "body": b""}

        def start_response(status: str, headers: list[tuple[str, str]]) -> None:
            response["status"] = int(status.split(" ", 1)[0])

        chunks = self.app(environ, start_response)
        response["body"] = b"".join(chunks)
        return response["status"], response["body"].decode("utf-8")

    def test_dashboard_endpoint_returns_group_and_period_data(self) -> None:
        status, payload = self._request("GET", "/api/dashboard")
        self.assertEqual(status, 200)
        self.assertEqual(len(payload["current_groups"]), 1)
        self.assertEqual(len(payload["recent_periods"]), 1)
        self.assertIn("latest_transactions", payload)

    def test_runtime_endpoint_requires_bearer_token(self) -> None:
        status, payload = self._request(
            "POST",
            "/api/core/messages",
            {
                "platform": "wechat",
                "message_id": "msg-runtime-unauthorized",
                "chat_id": "g-100",
                "chat_name": "客户群-Web",
                "is_group": True,
                "sender_id": "finance-web",
                "sender_name": "Finance",
                "content_type": "text",
                "text": "/set 2",
            },
        )
        self.assertEqual(status, 401)
        self.assertEqual(payload["error"], "Unauthorized")

    def test_runtime_endpoint_rejects_non_boolean_is_group(self) -> None:
        status, payload = self._request(
            "POST",
            "/api/core/messages",
            {
                "platform": "wechat",
                "message_id": "msg-runtime-bad-bool",
                "chat_id": "g-100",
                "chat_name": "客户群-Web",
                "is_group": "false",
                "sender_id": "finance-web",
                "sender_name": "Finance",
                "content_type": "text",
                "text": "+100rmb",
            },
            headers={"Authorization": "Bearer core-secret"},
        )
        self.assertEqual(status, 400)
        self.assertIn("Bad payload", payload["error"])

    def test_dashboard_workbench_and_history_pages_render_and_fetch_json(self) -> None:
        for path in ("/", "/workbench", "/role-mapping", "/history"):
            status, html = self._request_text("GET", path)
            self.assertEqual(status, 200)
            self.assertIn("<main", html)

        status, workbench = self._request("GET", "/api/workbench", query_string=f"period_id={self.period_id}")
        self.assertEqual(status, 200)
        self.assertIn("summary", workbench)
        self.assertIn("transactions", workbench)

        status, history = self._request(
            "GET",
            "/api/history",
            query_string="start_date=2026-03-01&end_date=2026-03-31",
        )
        self.assertEqual(status, 200)
        self.assertIn("card_rankings", history)

    def test_workbench_api_supports_realtime_period_selector(self) -> None:
        status, payload = self._request("GET", "/api/workbench", query_string="period_id=realtime")
        self.assertEqual(status, 200)
        self.assertIsNone(payload["selected_period"])
        self.assertIn("live_window", payload)

    def test_role_mapping_page_contains_group_search_and_summary_controls(self) -> None:
        status, html = self._request_text("GET", "/role-mapping")
        self.assertEqual(status, 200)
        self.assertIn('id="role-current-search"', html)
        self.assertIn('id="role-current-search-clear"', html)
        self.assertIn('id="role-current-filter-summary"', html)

    def test_role_mapping_group_num_can_be_updated_via_web_api(self) -> None:
        status, payload = self._request(
            "POST",
            "/api/role-mapping/group-num",
            {
                "group_key": "wechat:g-100",
                "group_num": 8,
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(payload["group_key"], "wechat:g-100")
        self.assertEqual(payload["group_num"], 8)
        self.assertEqual(self.db.get_group_num("wechat:g-100"), 8)

    def test_core_actions_endpoint_exposes_outbound_action_count_header(self) -> None:
        status, headers, payload = self._request_with_headers(
            "POST",
            "/api/core/actions",
            {},
            headers={"Authorization": "Bearer core-secret"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(payload["actions"], [])
        self.assertEqual(headers["X-Outbound-Action-Count"], "0")

    def test_realtime_transaction_can_be_updated_via_web_api(self) -> None:
        transaction_id = self.db.add_transaction(
            platform="wechat",
            group_key="wechat:g-100",
            group_num=5,
            chat_id="g-100",
            chat_name="客户群-Web",
            sender_id="u-web-live",
            sender_name="Live",
            message_id="msg-web-live",
            input_sign=1,
            amount=50,
            category="xb",
            rate=4.9,
            rmb_value=-245,
            usd_amount=50,
            raw="50 xb 4.9",
            created_at="2026-03-20 10:00:00",
        )
        status, payload = self._request(
            "POST",
            "/api/transactions/update",
            {
                "transaction_id": transaction_id,
                "sender_name": "Live-Web-Edited",
                "amount": 50,
                "category": "xb",
                "rate": 5,
                "rmb_value": -250,
                "usd_amount": 50,
                "note": "修正实时账单",
                "edited_by": "finance-web",
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(payload["transaction_id"], transaction_id)

        transaction = self.db.get_transaction_by_id(transaction_id)
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction["sender_name"], "Live-Web-Edited")
        self.assertEqual(float(transaction["rate"]), 5.0)
        self.assertEqual(float(transaction["rmb_value"]), -250.0)
        self.assertEqual(transaction["parse_version"], "web-edit")

        status, workbench = self._request("GET", "/api/workbench", query_string="period_id=realtime")
        self.assertEqual(status, 200)
        realtime_row = next(row for row in workbench["transactions"] if int(row["id"]) == transaction_id)
        self.assertTrue(realtime_row["is_edited"])
        self.assertEqual(realtime_row["edited_by"], "finance-web")
        self.assertEqual(realtime_row["sender_name"], "Live-Web-Edited")
        self.assertEqual(realtime_row["parse_version"], "web-edit")

    def test_settle_all_endpoint_closes_current_realtime_transactions(self) -> None:
        self.db.add_transaction(
            platform="wechat",
            group_key="wechat:g-100",
            group_num=5,
            chat_id="g-100",
            chat_name="客户群-Web",
            sender_id="u-web-live-close",
            sender_name="Live-Close",
            message_id="msg-web-live-close",
            input_sign=1,
            amount=80,
            category="xb",
            rate=5,
            rmb_value=-400,
            usd_amount=80,
            raw="80 xb 5",
            created_at="2026-03-20 10:30:00",
        )
        status, payload = self._request(
            "POST",
            "/api/accounting-periods/settle-all",
            {
                "closed_by": "网页值班员",
            },
        )
        self.assertEqual(status, 200)
        self.assertTrue(payload["closed"])
        self.assertGreater(payload["period_id"], self.period_id)
        self.assertEqual(payload["queued_action_count"], 1)

        status, workbench = self._request("GET", "/api/workbench", query_string="period_id=realtime")
        self.assertEqual(status, 200)
        self.assertEqual(workbench["transactions"], [])
        queued = self.db.claim_outbound_actions()
        self.assertEqual(len(queued), 1)
        self.assertEqual(str(queued[0]["chat_id"]), "g-100")
        self.assertIn("Closing Balance", str(queued[0]["text"]))

    def test_group_broadcast_endpoint_queues_send_text_actions_for_target_group_number(self) -> None:
        self.db.set_group(
            platform="wechat",
            group_key="wechat:g-201",
            chat_id="g-201",
            chat_name="客户群-广播-A",
            group_num=1,
        )
        self.db.set_group(
            platform="wechat",
            group_key="wechat:g-202",
            chat_id="g-202",
            chat_name="客户群-广播-B",
            group_num=1,
        )

        status, payload = self._request(
            "POST",
            "/api/group-broadcasts",
            {
                "created_by": "网页值班员",
                "group_num": 1,
                "message": "今晚 8 点统一对账",
            },
        )

        self.assertEqual(status, 200)
        self.assertEqual(payload["group_num"], 1)
        self.assertEqual(payload["target_count"], 2)
        self.assertEqual(payload["queued_action_count"], 2)

        queued = self.db.claim_outbound_actions()
        self.assertEqual(len(queued), 2)
        self.assertEqual({str(row["chat_id"]) for row in queued}, {"g-201", "g-202"})
        self.assertEqual({str(row["text"]) for row in queued}, {"今晚 8 点统一对账"})

    def test_workbench_adjustment_updates_selected_period_read_model(self) -> None:
        status, payload = self._request(
            "POST",
            "/api/adjustments",
            {
                "period_id": self.period_id,
                "group_key": "wechat:g-100",
                "expense_delta": 25,
                "opening_delta": 0,
                "income_delta": 0,
                "closing_delta": -25,
                "note": "人工修正",
                "created_by": "finance-web",
            },
        )
        self.assertEqual(status, 200)
        self.assertGreater(payload["adjustment_id"], 0)

        status, workbench = self._request("GET", "/api/workbench", query_string=f"period_id={self.period_id}")
        self.assertEqual(status, 200)
        self.assertEqual(round(workbench["group_rows"][0]["expense"], 2), 25.00)
        self.assertEqual(round(workbench["group_rows"][0]["closing_balance"], 2), 275.00)

    def test_accounting_period_list_endpoint_serializes_postgres_values(self) -> None:
        status, payload = self._request("GET", "/api/accounting-periods")
        self.assertEqual(status, 200)
        self.assertEqual(len(payload["items"]), 1)
        self.assertIsInstance(payload["items"][0]["closed_at"], str)
        self.assertEqual(payload["items"][0]["closed_at"], "2026-03-20 09:30:00")


if __name__ == "__main__":
    unittest.main()
