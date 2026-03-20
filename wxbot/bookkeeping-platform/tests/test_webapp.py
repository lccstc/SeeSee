from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path
from wsgiref.util import setup_testing_defaults

from bookkeeping_core.database import BookkeepingDB
from bookkeeping_web.app import create_app


class WebAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tempdir.name) / "web.db"
        self.db = BookkeepingDB(self.db_path)
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
    ) -> tuple[int, dict]:
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
        for key, value in (headers or {}).items():
            header_key = f"HTTP_{key.upper().replace('-', '_')}"
            environ[header_key] = value

        response = {"status": 500, "body": b""}

        def start_response(status: str, headers: list[tuple[str, str]]) -> None:
            response["status"] = int(status.split(" ", 1)[0])

        chunks = self.app(environ, start_response)
        response["body"] = b"".join(chunks)
        return response["status"], json.loads(response["body"].decode("utf-8"))

    def test_dashboard_endpoint_returns_group_and_period_data(self) -> None:
        status, payload = self._request("GET", "/api/dashboard")
        self.assertEqual(status, 200)
        self.assertEqual(len(payload["current_groups"]), 1)
        self.assertEqual(payload["current_groups"][0]["chat_name"], "客户群-Web")
        self.assertEqual(len(payload["recent_periods"]), 1)

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

    def test_sync_endpoint_requires_bearer_token(self) -> None:
        status, payload = self._request(
            "POST",
            "/api/sync/events",
            {
                "events": [
                    {
                        "event_id": "evt-unauthorized",
                        "event_type": "group.set",
                        "schema_version": 1,
                        "platform": "whatsapp",
                        "source_machine": "wa-node-01",
                        "occurred_at": "2026-03-20T10:15:30Z",
                        "payload": {
                            "group_id": "12036340001@g.us",
                            "group_num": 7,
                            "chat_name": "供应商群-A",
                        },
                    }
                ]
            },
        )
        self.assertEqual(status, 401)
        self.assertEqual(payload["error"], "Unauthorized")

    def test_sync_endpoint_ingests_events_and_keeps_idempotency(self) -> None:
        event = {
            "event_id": "evt-tx-created-1",
            "event_type": "transaction.created",
            "schema_version": 1,
            "platform": "whatsapp",
            "source_machine": "wa-node-01",
            "occurred_at": "2026-03-20T10:15:30Z",
            "payload": {
                "group_id": "12036349999@g.us",
                "group_num": 2,
                "chat_name": "供应商群-B",
                "sender_id": "+85212345678",
                "sender_name": "+85212345678",
                "source_transaction_id": 501,
                "input_sign": 1,
                "amount": 100,
                "category": "rmb",
                "rate": None,
                "rmb_value": 100,
                "raw": "rmb+100",
                "created_at": "2026-03-20 10:15:30",
            },
        }

        status, payload = self._request(
            "POST",
            "/api/sync/events",
            {"events": [event]},
            headers={"Authorization": "Bearer sync-secret"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(payload["accepted"], 1)
        self.assertEqual(payload["duplicates"], 0)

        groups = self.db.get_all_groups()
        synced_group = [row for row in groups if row["group_key"] == "whatsapp:12036349999@g.us"]
        self.assertEqual(len(synced_group), 1)
        self.assertEqual(int(synced_group[0]["group_num"]), 2)

        history = self.db.get_history("whatsapp:12036349999@g.us", 10)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["message_id"], "whatsapp-local-tx-501")

        status, payload = self._request(
            "POST",
            "/api/sync/events",
            {"events": [event]},
            headers={"Authorization": "Bearer sync-secret"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(payload["accepted"], 0)
        self.assertEqual(payload["duplicates"], 1)

        history = self.db.get_history("whatsapp:12036349999@g.us", 10)
        self.assertEqual(len(history), 1)


if __name__ == "__main__":
    unittest.main()
