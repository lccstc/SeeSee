from __future__ import annotations

import io
import json
import sys
import tempfile
import types
import unittest
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode
from wsgiref.util import setup_testing_defaults

from bookkeeping_core.database import BookkeepingDB
from bookkeeping_web.app import create_app
from tests.support.bookkeeping_replay import build_runtime_card_scenario, replay_runtime_scenario
from tests.test_postgres_backend import _FakeCursor, _FakePsycopgConnection


class WebAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tempdir.name) / "web.db"
        self.db = BookkeepingDB(self.db_path)
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
        settled = self.db.get_unsettled_transactions("wechat:g-100")
        self.db.settle_transactions("wechat", "wechat:g-100", settled, "finance-web", settled_at="2026-03-20 09:30:00")
        self.app = create_app(self.db_path, sync_token="sync-secret")

    def tearDown(self) -> None:
        self.db.close()
        self.tempdir.cleanup()

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
            header_key = f"HTTP_{key.upper().replace('-', '_')}"
            environ[header_key] = value

        response = {"status": 500, "body": b""}

        def start_response(status: str, headers: list[tuple[str, str]]) -> None:
            response["status"] = int(status.split(" ", 1)[0])

        chunks = self.app(environ, start_response)
        response["body"] = b"".join(chunks)
        return response["status"], json.loads(response["body"].decode("utf-8"))

    def _request_text(
        self,
        method: str,
        path: str,
        *,
        query: dict[str, str | int] | None = None,
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

    def test_dashboard_endpoint_returns_group_and_period_data(self) -> None:
        status, payload = self._request("GET", "/api/dashboard")
        self.assertEqual(status, 200)
        self.assertEqual(len(payload["current_groups"]), 1)
        self.assertEqual(payload["current_groups"][0]["chat_name"], "客户群-Web")
        self.assertEqual(len(payload["recent_periods"]), 1)

    def test_accounting_period_close_and_list_endpoints_work(self) -> None:
        status, payload = self._request(
            "POST",
            "/api/accounting-periods/close",
            {
                "start_at": "2026-03-20 08:00:00",
                "end_at": "2026-03-20 10:00:00",
                "closed_by": "finance-web",
                "note": "Web 关闭账期",
            },
        )
        self.assertEqual(status, 200)
        self.assertGreater(payload["period_id"], 0)

        status, periods = self._request("GET", "/api/accounting-periods")
        self.assertEqual(status, 200)
        self.assertEqual(len(periods["items"]), 1)
        self.assertEqual(int(periods["items"][0]["id"]), payload["period_id"])
        self.assertEqual(str(periods["items"][0]["closed_by"]), "finance-web")

        status, dashboard = self._request("GET", "/api/dashboard")
        self.assertEqual(status, 200)
        self.assertEqual(len(dashboard["recent_periods"]), 1)
        self.assertEqual(int(dashboard["recent_periods"][0]["period_id"]), payload["period_id"])
        self.assertEqual(round(float(dashboard["recent_periods"][0]["closing_balance"]), 2), 300.00)

    def test_accounting_period_list_endpoint_returns_recent_20(self) -> None:
        for index in range(22):
            self.db.insert_accounting_period(
                start_at=f"2026-03-19 {index:02d}:00:00",
                end_at=f"2026-03-19 {index:02d}:30:00",
                closed_at=f"2026-03-19 {index:02d}:30:00",
                closed_by=f"finance-{index}",
                note=f"period-{index}",
                has_adjustment=0,
                snapshot_version=1,
            )
        self.db.conn.commit()

        status, payload = self._request("GET", "/api/accounting-periods")
        self.assertEqual(status, 200)
        self.assertEqual(len(payload["items"]), 20)
        self.assertEqual(payload["items"][0]["note"], "period-21")
        self.assertEqual(payload["items"][-1]["note"], "period-2")

    def test_adjustment_endpoint_creates_adjustment(self) -> None:
        settlement_id = self.db.get_settlements("wechat:g-100", 1)[0]["id"]
        status, payload = self._request(
            "POST",
            "/api/adjustments",
            {
                "settlement_id": settlement_id,
                "group_key": "wechat:g-100",
                "opening_delta": 0,
                "income_delta": 0,
                "expense_delta": 50,
                "closing_delta": -50,
                "note": "后台修正",
                "created_by": "finance-manager",
            },
        )
        self.assertEqual(status, 200)
        self.assertGreater(payload["adjustment_id"], 0)

        status, dashboard = self._request("GET", "/api/dashboard")
        self.assertEqual(status, 200)
        self.assertEqual(round(dashboard["recent_periods"][0]["closing_balance"], 2), 250.00)

    def test_group_combination_endpoint_persists_rollup_definition(self) -> None:
        status, payload = self._request(
            "POST",
            "/api/group-combinations",
            {
                "name": "客户总览",
                "group_numbers": [5, 7],
                "note": "财务客户口径",
                "created_by": "finance-manager",
            },
        )
        self.assertEqual(status, 200)
        self.assertGreater(payload["combination_id"], 0)

        status, dashboard = self._request("GET", "/api/dashboard")
        self.assertEqual(status, 200)
        self.assertEqual(len(dashboard["combinations"]), 1)
        self.assertEqual(dashboard["combinations"][0]["label"], "客户总览")

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

    def test_runtime_endpoint_processes_set_command_and_persists_group(self) -> None:
        status, payload = self._request(
            "POST",
            "/api/core/messages",
            {
                "platform": "wechat",
                "message_id": "msg-runtime-set-1",
                "chat_id": "g-100",
                "chat_name": "客户群-Web",
                "is_group": True,
                "sender_id": "finance-web",
                "sender_name": "Finance",
                "content_type": "text",
                "text": "/set 2",
            },
            headers={"Authorization": "Bearer sync-secret"},
        )
        self.assertEqual(status, 200)
        self.assertIn("actions", payload)
        self.assertEqual(
            payload["actions"],
            [
                {
                    "action_type": "send_text",
                    "chat_id": "g-100",
                    "text": "✅ This group assigned to Group 2\nOnly groups with numbers can use bookkeeping",
                }
            ],
        )

        group = self.db.get_group_by_key("wechat:g-100")
        self.assertIsNotNone(group)
        self.assertEqual(int(group["group_num"]), 2)

    def test_runtime_endpoint_accepts_bootstrap_master_users_from_app_config(self) -> None:
        app = create_app(self.db_path, sync_token="sync-secret", runtime_master_users=["bootstrap-wa"])

        body = json.dumps(
            {
                "platform": "whatsapp",
                "message_id": "msg-runtime-set-bootstrap",
                "chat_id": "12036340001@g.us",
                "chat_name": "WhatsApp测试群",
                "is_group": True,
                "sender_id": "bootstrap-wa",
                "sender_name": "Bootstrap WA",
                "content_type": "text",
                "text": "/set 2",
            }
        ).encode("utf-8")

        environ = {}
        setup_testing_defaults(environ)
        environ["REQUEST_METHOD"] = "POST"
        environ["PATH_INFO"] = "/api/core/messages"
        environ["CONTENT_LENGTH"] = str(len(body))
        environ["CONTENT_TYPE"] = "application/json"
        environ["HTTP_AUTHORIZATION"] = "Bearer sync-secret"
        environ["wsgi.input"] = io.BytesIO(body)

        response = {"status": 500, "body": b""}

        def start_response(status: str, headers: list[tuple[str, str]]) -> None:
            response["status"] = int(status.split(" ", 1)[0])

        chunks = app(environ, start_response)
        response["body"] = b"".join(chunks)
        payload = json.loads(response["body"].decode("utf-8"))

        self.assertEqual(response["status"], 200)
        self.assertEqual(
            payload["actions"],
            [
                {
                    "action_type": "send_text",
                    "chat_id": "12036340001@g.us",
                    "text": "✅ This group assigned to Group 2\nOnly groups with numbers can use bookkeeping",
                }
            ],
        )

        group = self.db.get_group_by_key("whatsapp:12036340001@g.us")
        self.assertIsNotNone(group)
        self.assertEqual(int(group["group_num"]), 2)

    def test_runtime_endpoint_processes_transaction_message(self) -> None:
        self.db.set_group(
            platform="wechat",
            group_key="wechat:g-200",
            chat_id="g-200",
            chat_name="交易群-Web",
            group_num=3,
        )
        status, payload = self._request(
            "POST",
            "/api/core/messages",
            {
                "platform": "wechat",
                "message_id": "msg-runtime-tx-1",
                "chat_id": "g-200",
                "chat_name": "交易群-Web",
                "is_group": True,
                "sender_id": "finance-web",
                "sender_name": "Finance",
                "content_type": "text",
                "text": "+100rmb",
            },
            headers={"Authorization": "Bearer sync-secret"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(len(payload["actions"]), 1)
        self.assertEqual(payload["actions"][0]["action_type"], "send_text")
        self.assertEqual(payload["actions"][0]["chat_id"], "g-200")
        self.assertEqual(payload["actions"][0]["text"], "✅ +100.00\n📊 Balance: +100.00")

    def test_runtime_endpoint_deduplicates_replayed_message_id(self) -> None:
        payload = {
            "platform": "wechat",
            "message_id": "msg-runtime-tx-dup",
            "chat_id": "g-200",
            "chat_name": "交易群-Web",
            "is_group": True,
            "sender_id": "finance-web",
            "sender_name": "Finance",
            "content_type": "text",
            "text": "+100rmb",
        }
        self.db.set_group(
            platform="wechat",
            group_key="wechat:g-200",
            chat_id="g-200",
            chat_name="交易群-Web",
            group_num=3,
        )

        status, first = self._request(
            "POST",
            "/api/core/messages",
            payload,
            headers={"Authorization": "Bearer sync-secret"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(len(first["actions"]), 1)

        status, second = self._request(
            "POST",
            "/api/core/messages",
            payload,
            headers={"Authorization": "Bearer sync-secret"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(second["actions"], [])

        history = self.db.get_history("wechat:g-200", 10)
        self.assertEqual(len(history), 1)

    def test_runtime_endpoint_rejects_non_boolean_is_group(self) -> None:
        status, payload = self._request(
            "POST",
            "/api/core/messages",
            {
                "platform": "wechat",
                "message_id": "msg-runtime-bad-bool",
                "chat_id": "g-200",
                "chat_name": "交易群-Web",
                "is_group": "false",
                "sender_id": "finance-web",
                "sender_name": "Finance",
                "content_type": "text",
                "text": "+100rmb",
            },
            headers={"Authorization": "Bearer sync-secret"},
        )
        self.assertEqual(status, 400)
        self.assertIn("Bad payload", payload["error"])

    def test_dashboard_workbench_and_history_pages_render_and_fetch_json(self) -> None:
        period_id = self._request(
            "POST",
            "/api/accounting-periods/close",
            {
                "start_at": "2026-03-20 08:00:00",
                "end_at": "2026-03-20 10:00:00",
                "closed_by": "finance-web",
            },
        )[1]["period_id"]

        for path in ("/", "/workbench", "/history"):
            status, html = self._request_text("GET", path)
            self.assertEqual(status, 200)
            self.assertIn("<main", html)

        status, workbench = self._request("GET", "/api/workbench", query_string=f"period_id={period_id}")
        self.assertEqual(status, 200)
        self.assertIn("summary", workbench)

        status, history = self._request(
            "GET",
            "/api/history",
            query_string="start_date=2026-03-01&end_date=2026-03-31",
        )
        self.assertEqual(status, 200)
        self.assertIn("card_rankings", history)

    def test_workbench_and_history_endpoints_return_non_empty_card_sections_after_runtime_replay(self) -> None:
        period_id = replay_runtime_scenario(
            self.db,
            build_runtime_card_scenario(
                message_prefix="webapp-runtime-replay",
                chat_id="g-web-runtime",
                chat_name="回放卡片群-Web",
                group_num=6,
                business_role="customer",
            ),
        )

        status, workbench = self._request("GET", "/api/workbench", query_string=f"period_id={period_id}")
        self.assertEqual(status, 200)
        self.assertGreater(len(workbench["card_stats"]), 0)
        self.assertEqual(workbench["card_stats"][0]["card_type"], "steam")

        status, history = self._request(
            "GET",
            "/api/history",
            query_string="start_date=2026-03-01&end_date=2026-03-31&card_keyword=steam&sort_by=usd_amount",
        )
        self.assertEqual(status, 200)
        self.assertGreater(len(history["card_rankings"]), 0)
        self.assertEqual(history["card_rankings"][0]["card_type"], "steam")

    def test_sync_events_route_is_no_longer_supported(self) -> None:
        status, payload = self._request("POST", "/api/sync/events", {"events": []})
        self.assertEqual(status, 404)
        self.assertEqual(payload["error"], "Unknown path: /api/sync/events")

    def test_readme_no_longer_mentions_sync_events_interface(self) -> None:
        readme_text = Path(__file__).resolve().parents[1].joinpath("README.md").read_text(encoding="utf-8")
        self.assertNotIn("/api/sync/events", readme_text)

class _WebFakePsycopgConnection(_FakePsycopgConnection):
    def execute(self, sql: str, params=()):
        translated = sql.replace("%s", "?")
        if translated.strip() == "SELECT * FROM accounting_periods ORDER BY id ASC":
            rows = self._conn.execute(translated, params).fetchall()
            return _FakeCursor(
                rows=[
                    {
                        "id": int(row["id"]),
                        "start_at": datetime.fromisoformat(str(row["start_at"])),
                        "end_at": datetime.fromisoformat(str(row["end_at"])),
                        "closed_at": datetime.fromisoformat(str(row["closed_at"])),
                        "closed_by": row["closed_by"],
                        "note": row["note"],
                        "has_adjustment": int(row["has_adjustment"] or 0),
                        "snapshot_version": int(row["snapshot_version"] or 1),
                    }
                    for row in rows
                ]
            )
        return super().execute(sql, params)


class PostgresWebAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self._original_psycopg = sys.modules.get("psycopg")
        fake_module = types.ModuleType("psycopg")

        def _connect(dsn: str):
            return _WebFakePsycopgConnection(dsn)

        fake_module.connect = _connect
        sys.modules["psycopg"] = fake_module
        self.app = create_app("postgresql://bookkeeping:test@localhost:5432/bookkeeping", sync_token="sync-secret")

    def tearDown(self) -> None:
        if self._original_psycopg is None:
            sys.modules.pop("psycopg", None)
        else:
            sys.modules["psycopg"] = self._original_psycopg

    def _request(self, method: str, path: str, payload: dict | None = None) -> tuple[int, dict]:
        body = b""
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
        environ = {}
        setup_testing_defaults(environ)
        environ["REQUEST_METHOD"] = method
        environ["PATH_INFO"] = path
        environ["CONTENT_LENGTH"] = str(len(body))
        environ["wsgi.input"] = io.BytesIO(body)
        if body:
            environ["CONTENT_TYPE"] = "application/json"

        response = {"status": 500, "body": b""}

        def start_response(status: str, headers: list[tuple[str, str]]) -> None:
            response["status"] = int(status.split(" ", 1)[0])

        chunks = self.app(environ, start_response)
        response["body"] = b"".join(chunks)
        return response["status"], json.loads(response["body"].decode("utf-8"))

    def test_accounting_period_list_endpoint_serializes_postgres_values(self) -> None:
        status, payload = self._request("GET", "/api/accounting-periods")
        self.assertEqual(status, 200)
        self.assertEqual(len(payload["items"]), 2)
        self.assertIsInstance(payload["items"][0]["closed_at"], str)
        self.assertEqual(payload["items"][0]["closed_at"], "2026-03-19 08:00:00")


if __name__ == "__main__":
    unittest.main()
