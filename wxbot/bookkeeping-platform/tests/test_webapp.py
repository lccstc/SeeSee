from __future__ import annotations

import csv
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
        close_app = getattr(self.app, "close", None)
        if callable(close_app):
            close_app()
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

        def start_response(
            status: str, response_headers: list[tuple[str, str]]
        ) -> None:
            response["status"] = int(status.split(" ", 1)[0])
            response["headers"] = {key: value for key, value in response_headers}

        chunks = self.app(environ, start_response)
        response["body"] = b"".join(chunks)
        return (
            response["status"],
            response["headers"],
            json.loads(response["body"].decode("utf-8")),
        )

    def _request_text(
        self, method: str, path: str, *, query: dict[str, str | int] | None = None
    ) -> tuple[int, str]:
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

    def _request_raw(
        self,
        method: str,
        path: str,
        *,
        query: dict[str, str | int] | None = None,
    ) -> tuple[int, dict[str, str], bytes]:
        environ = {}
        setup_testing_defaults(environ)
        environ["REQUEST_METHOD"] = method
        environ["PATH_INFO"] = path
        environ["QUERY_STRING"] = urlencode(query or {})
        environ["CONTENT_LENGTH"] = "0"
        environ["wsgi.input"] = io.BytesIO(b"")

        response = {"status": 500, "headers": {}, "body": b""}

        def start_response(status: str, headers: list[tuple[str, str]]) -> None:
            response["status"] = int(status.split(" ", 1)[0])
            response["headers"] = {key: value for key, value in headers}

        chunks = self.app(environ, start_response)
        response["body"] = b"".join(chunks)
        return response["status"], response["headers"], response["body"]

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

    def test_incoming_messages_requires_auth(self) -> None:
        status, payload = self._request("GET", "/api/incoming-messages")
        self.assertEqual(status, 401)
        self.assertEqual(payload["error"], "Unauthorized")

    def test_incoming_messages_returns_empty_list(self) -> None:
        status, payload = self._request(
            "GET",
            "/api/incoming-messages",
            headers={"Authorization": "Bearer core-secret"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(payload["messages"], [])
        self.assertEqual(payload["total"], 0)
        self.assertEqual(payload["limit"], 50)
        self.assertEqual(payload["offset"], 0)

    def test_incoming_messages_returns_stored_messages(self) -> None:
        self.db.record_incoming_message(
            platform="whatsapp",
            group_key="whatsapp:chat-123",
            chat_id="chat-123",
            chat_name="Test Chat",
            message_id="msg-incoming-test",
            is_group=False,
            sender_id="user-456",
            sender_name="Test User",
            sender_kind="user",
            content_type="text",
            text="hello world",
            from_self=False,
            received_at="2026-04-07T10:00:00",
            raw_payload={"test": True},
        )
        status, payload = self._request(
            "GET",
            "/api/incoming-messages",
            headers={"Authorization": "Bearer core-secret"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(len(payload["messages"]), 1)
        self.assertEqual(payload["total"], 1)
        self.assertEqual(payload["messages"][0]["platform"], "whatsapp")
        self.assertEqual(payload["messages"][0]["text"], "hello world")

    def test_incoming_messages_filters_by_platform(self) -> None:
        self.db.record_incoming_message(
            platform="whatsapp",
            group_key="whatsapp:chat-1",
            chat_id="chat-1",
            chat_name="Chat 1",
            message_id="msg-wa-1",
            is_group=False,
            sender_id="user-1",
            sender_name="User 1",
            sender_kind="user",
            content_type="text",
            text="wa message",
            from_self=False,
            received_at="2026-04-07T10:00:00",
            raw_payload={},
        )
        self.db.record_incoming_message(
            platform="wechat",
            group_key="wechat:chat-2",
            chat_id="chat-2",
            chat_name="Chat 2",
            message_id="msg-wx-1",
            is_group=False,
            sender_id="user-2",
            sender_name="User 2",
            sender_kind="user",
            content_type="text",
            text="wechat message",
            from_self=False,
            received_at="2026-04-07T11:00:00",
            raw_payload={},
        )
        status, payload = self._request(
            "GET",
            "/api/incoming-messages",
            headers={"Authorization": "Bearer core-secret"},
            query_string="platform=whatsapp",
        )
        self.assertEqual(status, 200)
        self.assertEqual(len(payload["messages"]), 1)
        self.assertEqual(payload["messages"][0]["platform"], "whatsapp")

    def test_incoming_messages_pagination(self) -> None:
        for i in range(5):
            self.db.record_incoming_message(
                platform="test",
                group_key=f"test:chat-{i}",
                chat_id=f"chat-{i}",
                chat_name=f"Chat {i}",
                message_id=f"msg-{i}",
                is_group=False,
                sender_id=f"user-{i}",
                sender_name=f"User {i}",
                sender_kind="user",
                content_type="text",
                text=f"message {i}",
                from_self=False,
                received_at="2026-04-07T10:00:00",
                raw_payload={},
            )
        status, payload = self._request(
            "GET",
            "/api/incoming-messages",
            headers={"Authorization": "Bearer core-secret"},
            query_string="limit=2&offset=1",
        )
        self.assertEqual(status, 200)
        self.assertEqual(len(payload["messages"]), 2)
        self.assertEqual(payload["total"], 5)
        self.assertEqual(payload["limit"], 2)
        self.assertEqual(payload["offset"], 1)

    def test_incoming_messages_with_transactions_requires_auth(self) -> None:
        status, payload = self._request(
            "GET", "/api/incoming-messages/with-transactions"
        )
        self.assertEqual(status, 401)
        self.assertEqual(payload["error"], "Unauthorized")

    def test_incoming_messages_with_transactions_returns_null_when_no_transaction(
        self,
    ) -> None:
        self.db.record_incoming_message(
            platform="whatsapp",
            group_key="whatsapp:chat-wtx-1",
            chat_id="chat-wtx-1",
            chat_name="Test Chat",
            message_id="msg-wtx-no-tx",
            is_group=False,
            sender_id="user-1",
            sender_name="User 1",
            sender_kind="user",
            content_type="text",
            text="hello",
            from_self=False,
            received_at="2026-04-07T10:00:00",
            raw_payload={},
        )
        status, payload = self._request(
            "GET",
            "/api/incoming-messages/with-transactions",
            headers={"Authorization": "Bearer core-secret"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(len(payload["messages"]), 1)
        self.assertIsNone(payload["messages"][0]["transaction"])

    def test_incoming_messages_with_transactions_returns_linked_transaction(
        self,
    ) -> None:
        self.db.record_incoming_message(
            platform="whatsapp",
            group_key="whatsapp:chat-wtx-2",
            chat_id="chat-wtx-2",
            chat_name="Test Chat 2",
            message_id="msg-wtx-with-tx",
            is_group=False,
            sender_id="user-2",
            sender_name="User 2",
            sender_kind="user",
            content_type="text",
            text="+100rmb",
            from_self=False,
            received_at="2026-04-07T10:00:00",
            raw_payload={},
        )
        tx_id = self.db.add_transaction(
            platform="whatsapp",
            group_key="whatsapp:chat-wtx-2",
            group_num=1,
            chat_id="chat-wtx-2",
            chat_name="Test Chat 2",
            sender_id="user-2",
            sender_name="User 2",
            message_id="msg-wtx-with-tx",
            input_sign=1,
            amount=100,
            category="rmb",
            rate=None,
            rmb_value=100,
            raw="+100rmb",
        )
        status, payload = self._request(
            "GET",
            "/api/incoming-messages/with-transactions",
            headers={"Authorization": "Bearer core-secret"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(len(payload["messages"]), 1)
        tx = payload["messages"][0]["transaction"]
        self.assertIsNotNone(tx)
        self.assertEqual(tx["id"], tx_id)
        self.assertEqual(tx["category"], "rmb")
        self.assertEqual(tx["input_sign"], 1)

    def test_parse_results_requires_auth(self) -> None:
        status, payload = self._request("GET", "/api/parse-results")

        self.assertEqual(status, 401)
        self.assertEqual(payload["error"], "Unauthorized")

    def test_parse_results_returns_empty_list(self) -> None:
        status, payload = self._request(
            "GET",
            "/api/parse-results",
            headers={"Authorization": "Bearer core-secret"},
        )

        self.assertEqual(status, 200)
        self.assertEqual(payload["results"], [])
        self.assertEqual(payload["total"], 0)

    def test_parse_results_returns_stored_results(self) -> None:
        self.db.record_parse_result(
            platform="whatsapp",
            chat_id="chat-1",
            message_id="msg-1",
            classification="transaction_like",
            parse_status="parsed",
            raw_text="+100rmb",
        )
        self.db.record_parse_result(
            platform="whatsapp",
            chat_id="chat-1",
            message_id="msg-2",
            classification="normal_chat",
            parse_status="ignored",
            raw_text="hello",
        )

        status, payload = self._request(
            "GET",
            "/api/parse-results",
            headers={"Authorization": "Bearer core-secret"},
        )

        self.assertEqual(status, 200)
        self.assertEqual(payload["total"], 2)
        self.assertEqual(payload["results"][0]["message_id"], "msg-2")
        self.assertEqual(payload["results"][0]["classification"], "normal_chat")
        self.assertEqual(payload["results"][1]["message_id"], "msg-1")
        self.assertEqual(payload["results"][1]["parse_status"], "parsed")

    def test_parse_results_filters_by_classification(self) -> None:
        self.db.record_parse_result(
            platform="whatsapp",
            chat_id="chat-1",
            message_id="msg-1",
            classification="transaction_like",
            parse_status="parsed",
            raw_text="+100rmb",
        )
        self.db.record_parse_result(
            platform="whatsapp",
            chat_id="chat-1",
            message_id="msg-2",
            classification="command",
            parse_status="ignored",
            raw_text="/bal",
        )

        status, payload = self._request(
            "GET",
            "/api/parse-results",
            headers={"Authorization": "Bearer core-secret"},
            query_string="classification=command",
        )

        self.assertEqual(status, 200)
        self.assertEqual(payload["total"], 1)
        self.assertEqual(len(payload["results"]), 1)
        self.assertEqual(payload["results"][0]["message_id"], "msg-2")

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
        for path in ("/", "/workbench", "/role-mapping", "/reconciliation", "/history"):
            status, html = self._request_text("GET", path)
            self.assertEqual(status, 200)
            self.assertIn("<main", html)

        status, workbench = self._request(
            "GET", "/api/workbench", query_string=f"period_id={self.period_id}"
        )
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
        status, payload = self._request(
            "GET", "/api/workbench", query_string="period_id=realtime"
        )
        self.assertEqual(status, 200)
        self.assertIsNone(payload["selected_period"])
        self.assertIn("live_window", payload)

    def test_role_mapping_page_contains_group_search_and_summary_controls(self) -> None:
        status, html = self._request_text("GET", "/role-mapping")
        self.assertEqual(status, 200)
        self.assertIn('id="role-current-search"', html)
        self.assertIn('id="role-current-search-clear"', html)
        self.assertIn('id="role-current-filter-summary"', html)

    def test_reconciliation_page_contains_filter_and_adjustment_controls(self) -> None:
        status, html = self._request_text("GET", "/reconciliation")
        self.assertEqual(status, 200)
        self.assertIn('id="reconciliation-filter-form"', html)
        self.assertIn('id="reconciliation-adjustment-form"', html)
        self.assertIn('id="reconciliation-export-detail-link"', html)
        self.assertIn('id="reconciliation-export-summary-link"', html)
        self.assertIn('id="reconciliation-combination"', html)
        self.assertIn('id="reconciliation-group-num"', html)

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

        status, workbench = self._request(
            "GET", "/api/workbench", query_string="period_id=realtime"
        )
        self.assertEqual(status, 200)
        realtime_row = next(
            row for row in workbench["transactions"] if int(row["id"]) == transaction_id
        )
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

        status, workbench = self._request(
            "GET", "/api/workbench", query_string="period_id=realtime"
        )
        self.assertEqual(status, 200)
        self.assertEqual(workbench["transactions"], [])
        queued = self.db.claim_outbound_actions()
        self.assertEqual(len(queued), 1)
        self.assertEqual(str(queued[0]["chat_id"]), "g-100")
        self.assertIn("Closing Balance", str(queued[0]["text"]))

    def test_group_broadcast_endpoint_queues_send_text_actions_for_target_group_number(
        self,
    ) -> None:
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

        status, workbench = self._request(
            "GET", "/api/workbench", query_string=f"period_id={self.period_id}"
        )
        self.assertEqual(status, 200)
        self.assertEqual(round(workbench["group_rows"][0]["expense"], 2), 25.00)
        self.assertEqual(
            round(workbench["group_rows"][0]["closing_balance"], 2), 275.00
        )

    def test_reconciliation_adjustment_endpoint_persists_entry_and_shows_in_period_scope(
        self,
    ) -> None:
        status, payload = self._request(
            "POST",
            "/api/reconciliation/adjustments",
            {
                "period_id": self.period_id,
                "group_key": "wechat:g-100",
                "business_role": "customer",
                "card_type": "fee",
                "usd_amount": 0,
                "rate": "",
                "rmb_amount": 18,
                "note": "补录手续费",
                "created_by": "finance-web",
            },
        )
        self.assertEqual(status, 200)
        self.assertGreater(payload["adjustment_id"], 0)

        status, ledger = self._request(
            "GET",
            "/api/reconciliation/ledger",
            query_string=f"scope=period&period_id={self.period_id}",
        )
        self.assertEqual(status, 200)
        adjustment_row = next(
            row for row in ledger["rows"] if row["row_type"] == "finance_adjustment"
        )
        self.assertEqual(adjustment_row["card_type"], "fee")
        self.assertEqual(round(adjustment_row["rmb_value"], 2), 18.0)
        self.assertEqual(adjustment_row["note"], "补录手续费")

    def test_reconciliation_ledger_supports_range_scope_and_csv_export(self) -> None:
        live_tx_id = self.db.add_transaction(
            platform="wechat",
            group_key="wechat:g-100",
            group_num=5,
            chat_id="g-100",
            chat_name="客户群-Web",
            sender_id="u-web-live-range",
            sender_name="Live-Range",
            message_id="msg-web-live-range",
            input_sign=1,
            amount=50,
            category="xb",
            rate=5,
            rmb_value=-250,
            usd_amount=50,
            raw="+50xb5",
            created_at="2026-03-20 10:10:00",
        )
        self.db.add_finance_adjustment_entry(
            period_id=None,
            linked_transaction_id=live_tx_id,
            group_key="wechat:g-100",
            business_role="customer",
            card_type="fee",
            usd_amount=0,
            rate=None,
            rmb_amount=12,
            note="实时补差",
            created_by="finance-web",
        )

        status, ledger = self._request(
            "GET",
            "/api/reconciliation/ledger",
            query_string="scope=range&start_date=2026-03-20&end_date=2026-03-20",
        )
        self.assertEqual(status, 200)
        self.assertGreaterEqual(len(ledger["rows"]), 2)
        self.assertEqual(ledger["range"]["start_date"], "2026-03-20")
        self.assertEqual(ledger["range"]["end_date"], "2026-03-20")

        status, headers, body = self._request_raw(
            "GET",
            "/api/reconciliation/export",
            query={
                "scope": "range",
                "start_date": "2026-03-20",
                "end_date": "2026-03-20",
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(headers["Content-Type"], "text/csv; charset=utf-8")
        csv_text = body.decode("utf-8-sig")
        self.assertIn("row_type,row_id,period_id,period_status", csv_text)
        self.assertIn("finance_adjustment_entries", csv_text)

    def test_reconciliation_ledger_supports_combination_group_num_and_summary_export(
        self,
    ) -> None:
        self.db.set_group(
            platform="wechat",
            group_key="wechat:g-200",
            chat_id="g-200",
            chat_name="供应商群-Web",
            group_num=2,
        )
        self.db.conn.execute(
            "UPDATE groups SET business_role = ? WHERE group_key = ?",
            ("vendor", "wechat:g-200"),
        )
        self.db.conn.commit()
        self.db.add_transaction(
            platform="wechat",
            group_key="wechat:g-200",
            group_num=2,
            chat_id="g-200",
            chat_name="供应商群-Web",
            sender_id="u-web-vendor",
            sender_name="Vendor-Web",
            message_id="msg-web-vendor",
            input_sign=1,
            amount=40,
            category="it",
            rate=5,
            rmb_value=-200,
            usd_amount=40,
            raw="+40it5",
            created_at="2026-03-20 10:15:00",
        )
        combination_id = self.db.save_group_combination(
            name="财务组合-Web",
            group_numbers=[2, 5],
            note="组合导出",
            created_by="finance-web",
        )

        status, ledger = self._request(
            "GET",
            "/api/reconciliation/ledger",
            query_string=f"scope=range&start_date=2026-03-20&end_date=2026-03-20&combination_id={combination_id}",
        )
        self.assertEqual(status, 200)
        self.assertEqual(ledger["filters"]["combination_id"], combination_id)
        self.assertEqual(set(ledger["available_group_nums"]), {2, 5})
        self.assertEqual({int(row["group_num"]) for row in ledger["rows"]}, {2, 5})

        status, drilled = self._request(
            "GET",
            "/api/reconciliation/ledger",
            query_string="scope=range&start_date=2026-03-20&end_date=2026-03-20&group_num=5&group_key=wechat:g-100",
        )
        self.assertEqual(status, 200)
        self.assertTrue(drilled["rows"])
        self.assertEqual(
            {row["group_key"] for row in drilled["rows"]}, {"wechat:g-100"}
        )

        status, headers, body = self._request_raw(
            "GET",
            "/api/reconciliation/export",
            query={
                "scope": "range",
                "start_date": "2026-03-20",
                "end_date": "2026-03-20",
                "combination_id": combination_id,
                "export_mode": "summary",
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(headers["Content-Type"], "text/csv; charset=utf-8")
        rows = list(csv.DictReader(io.StringIO(body.decode("utf-8-sig"))))
        self.assertEqual(
            {
                (row["business_role"], row["card_type"], row["row_count"])
                for row in rows
            },
            {
                ("customer", "rmb", "1"),
                ("vendor", "it", "1"),
            },
        )
        self.assertTrue(all(row["combination_name"] == "财务组合-Web" for row in rows))

    def test_accounting_period_list_endpoint_serializes_postgres_values(self) -> None:
        status, payload = self._request("GET", "/api/accounting-periods")
        self.assertEqual(status, 200)
        self.assertEqual(len(payload["items"]), 1)
        self.assertIsInstance(payload["items"][0]["closed_at"], str)
        self.assertEqual(payload["items"][0]["closed_at"], "2026-03-20 09:30:00")

    def test_message_inspector_returns_combined_view(self) -> None:
        self.db.record_incoming_message(
            platform="wechat",
            group_key="wechat:g-100",
            chat_id="g-100",
            chat_name="客户群-Web",
            message_id="msg-inspect-1",
            is_group=True,
            sender_id="u-inspect",
            sender_name="Inspect",
            sender_kind="user",
            content_type="text",
            text="+50rmb",
            from_self=False,
            received_at="2026-03-20 11:00:00",
            raw_payload={},
        )
        self.db.record_parse_result(
            platform="wechat",
            chat_id="g-100",
            message_id="msg-inspect-1",
            classification="transaction_like",
            parse_status="parsed",
            raw_text="+50rmb",
        )
        self.db.add_transaction(
            platform="wechat",
            group_key="wechat:g-100",
            group_num=5,
            chat_id="g-100",
            chat_name="客户群-Web",
            sender_id="u-inspect",
            sender_name="Inspect",
            message_id="msg-inspect-1",
            input_sign=1,
            amount=50,
            category="rmb",
            rate=None,
            rmb_value=50,
            raw="+50rmb",
            created_at="2026-03-20 11:00:00",
        )
        status, payload = self._request(
            "GET",
            "/api/message-inspector",
            headers={"Authorization": "Bearer core-secret"},
            query_string="platform=wechat&chat_id=g-100&message_id=msg-inspect-1",
        )
        self.assertEqual(status, 200)
        self.assertEqual(payload["message"]["message_id"], "msg-inspect-1")
        self.assertEqual(payload["parse_result"]["classification"], "transaction_like")
        self.assertIsNotNone(payload["transaction"])
        self.assertGreater(payload["transaction"]["id"], 0)
        self.assertIn("50", payload["transaction"]["amount"])

    def test_message_inspector_returns_null_for_missing_parse_and_transaction(
        self,
    ) -> None:
        self.db.record_incoming_message(
            platform="whatsapp",
            group_key="whatsapp:chat-inspect",
            chat_id="chat-inspect",
            chat_name="Inspect Chat",
            message_id="msg-inspect-no-tx",
            is_group=False,
            sender_id="user-inspect",
            sender_name="Inspect User",
            sender_kind="user",
            content_type="text",
            text="hello",
            from_self=False,
            received_at="2026-04-07T10:00:00",
            raw_payload={},
        )
        status, payload = self._request(
            "GET",
            "/api/message-inspector",
            headers={"Authorization": "Bearer core-secret"},
            query_string="platform=whatsapp&chat_id=chat-inspect&message_id=msg-inspect-no-tx",
        )
        self.assertEqual(status, 200)
        self.assertEqual(payload["message"]["message_id"], "msg-inspect-no-tx")
        self.assertIsNone(payload["parse_result"])
        self.assertIsNone(payload["transaction"])

    def test_message_inspector_requires_all_params(self) -> None:
        for missing in ("platform", "chat_id", "message_id"):
            query = "platform=wechat&chat_id=g-100&message_id=msg-1"
            query = query.replace(f"{missing}=", f"X{missing}=")
            status, payload = self._request(
                "GET",
                "/api/message-inspector",
                headers={"Authorization": "Bearer core-secret"},
                query_string=query,
            )
            self.assertEqual(status, 400)

    def test_message_inspector_requires_auth(self) -> None:
        status, payload = self._request(
            "GET",
            "/api/message-inspector",
            query_string="platform=wechat&chat_id=g-100&message_id=msg-1",
        )
        self.assertEqual(status, 401)

    def test_difference_trace_returns_full_trace_with_all_fields(self) -> None:
        self.db.record_incoming_message(
            platform="wechat",
            group_key="wechat:g-100",
            chat_id="g-100",
            chat_name="客户群-Web",
            message_id="msg-trace-full",
            is_group=True,
            sender_id="u-trace",
            sender_name="Trace",
            sender_kind="user",
            content_type="text",
            text="+100rmb",
            from_self=False,
            received_at="2026-03-20 12:00:00",
            raw_payload={},
        )
        self.db.record_parse_result(
            platform="wechat",
            chat_id="g-100",
            message_id="msg-trace-full",
            classification="transaction_like",
            parse_status="parsed",
            raw_text="+100rmb",
        )
        tx_id = self.db.add_transaction(
            platform="wechat",
            group_key="wechat:g-100",
            group_num=5,
            chat_id="g-100",
            chat_name="客户群-Web",
            sender_id="u-trace",
            sender_name="Trace",
            message_id="msg-trace-full",
            input_sign=1,
            amount=100,
            category="rmb",
            rate=None,
            rmb_value=100,
            raw="+100rmb",
            created_at="2026-03-20 12:00:00",
        )
        status, payload = self._request(
            "GET",
            "/api/difference-trace",
            headers={"Authorization": "Bearer core-secret"},
            query_string=f"transaction_id={tx_id}",
        )
        self.assertEqual(status, 200)
        self.assertIn("transaction", payload)
        self.assertIn("message", payload)
        self.assertIn("parse_result", payload)
        self.assertIn("issue_flags", payload)
        self.assertIn("latest_edit", payload)
        self.assertIn("trace_status", payload)
        self.assertEqual(payload["transaction"]["id"], tx_id)
        self.assertEqual(payload["trace_status"]["captured"], True)
        self.assertEqual(payload["trace_status"]["parsed"], True)
        self.assertEqual(payload["trace_status"]["posted"], True)

    def test_difference_trace_returns_transaction_without_message_parse(self) -> None:
        tx_id = self.db.add_transaction(
            platform="wechat",
            group_key="wechat:g-100",
            group_num=5,
            chat_id="g-100",
            chat_name="客户群-Web",
            sender_id="u-no-msg",
            sender_name="NoMsg",
            message_id="msg-no-msg",
            input_sign=-1,
            amount=50,
            category="xb",
            rate=5,
            rmb_value=-250,
            usd_amount=50,
            raw="-50xb5",
            created_at="2026-03-20 13:00:00",
        )
        status, payload = self._request(
            "GET",
            "/api/difference-trace",
            headers={"Authorization": "Bearer core-secret"},
            query_string=f"transaction_id={tx_id}",
        )
        self.assertEqual(status, 200)
        self.assertIn("transaction", payload)
        self.assertEqual(payload["transaction"]["id"], tx_id)
        self.assertIsNone(payload["message"])
        self.assertIsNone(payload["parse_result"])
        self.assertIn("trace_status", payload)
        self.assertEqual(payload["trace_status"]["captured"], True)
        self.assertEqual(payload["trace_status"]["parsed"], False)
        self.assertEqual(payload["trace_status"]["posted"], True)
        self.assertIn("issue_flags", payload)

    def test_difference_trace_requires_transaction_id(self) -> None:
        status, payload = self._request(
            "GET",
            "/api/difference-trace",
            headers={"Authorization": "Bearer core-secret"},
        )
        self.assertEqual(status, 400)
        self.assertIn("transaction_id", payload["error"])

    def test_difference_trace_requires_auth(self) -> None:
        status, payload = self._request(
            "GET",
            "/api/difference-trace",
            query_string="transaction_id=1",
        )
        self.assertEqual(status, 401)
        self.assertEqual(payload["error"], "Unauthorized")

    def test_difference_trace_returns_404_for_missing_transaction(self) -> None:
        status, payload = self._request(
            "GET",
            "/api/difference-trace",
            headers={"Authorization": "Bearer core-secret"},
            query_string="transaction_id=999999",
        )
        self.assertEqual(status, 404)
        self.assertIn("transaction", payload["error"])


if __name__ == "__main__":
    unittest.main()
