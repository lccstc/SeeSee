from __future__ import annotations

import csv
import io
import json
import os
import unittest
from datetime import datetime
from unittest.mock import patch
from urllib.parse import urlencode
from wsgiref.util import setup_testing_defaults

from bookkeeping_core.database import BookkeepingDB
from bookkeeping_core.periods import AccountingPeriodService
from bookkeeping_core.quote_snapshot import SNAPSHOT_DELTA_UPDATE, SNAPSHOT_FULL_SNAPSHOT
from bookkeeping_web.app import create_app
from tests.support.postgres_test_case import PostgresTestCase


class WebRepairStatusTextTests(unittest.TestCase):
    def test_annotate_quote_exception_repair_status_text_stays_proof_only(self) -> None:
        from bookkeeping_web.app import _annotate_quote_exception_repair_status_text

        class _FakeDB:
            def get_quote_repair_case_summary(self, *, repair_case_id: int):
                return {
                    "attempt_count": 3,
                    "escalation_state": "ready",
                }

        rows = [
            {
                "id": 1,
                "repair_case_id": 9,
                "repair_case": {
                    "lifecycle_state": "escalated",
                },
            }
        ]
        _annotate_quote_exception_repair_status_text(db=_FakeDB(), rows=rows)
        self.assertIn("未改动报价墙", rows[0]["repair_case"]["status_text"])
        self.assertIn("升级", rows[0]["repair_case"]["status_text"])


class WebJsonResponseTests(unittest.TestCase):
    def test_respond_json_serializes_nested_datetime_values(self) -> None:
        from bookkeeping_web.app import _respond_json

        captured = {}

        def start_response(status, headers):
            captured["status"] = status
            captured["headers"] = headers

        chunks = _respond_json(
            start_response,
            200,
            {
                "rows": [{"created_at": datetime(2026, 4, 15, 23, 58, 30)}],
                "nested": {"confirmed_at": datetime(2026, 4, 15, 23, 59, 31)},
            },
        )
        payload = json.loads(b"".join(chunks).decode("utf-8"))

        self.assertEqual(captured["status"], "200 OK")
        self.assertEqual(payload["rows"][0]["created_at"], "2026-04-15 23:58:30")
        self.assertEqual(payload["nested"]["confirmed_at"], "2026-04-15 23:59:31")


def _make_repair_candidate(
    *,
    message_id: str,
    raw_message: str,
    row_specs: list[dict[str, object]],
    run_kind: str,
    replay_of_quote_document_id: int | None,
):
    from bookkeeping_core.quote_candidates import QuoteCandidateMessage, QuoteCandidateRow

    rows = []
    for index, spec in enumerate(row_specs, start=1):
        rows.append(
            QuoteCandidateRow(
                row_ordinal=index,
                source_line=str(spec["source_line"]),
                source_line_index=index - 1,
                line_confidence=float(spec.get("line_confidence", 0.98)),
                normalized_sku_key=str(
                    spec.get(
                        "normalized_sku_key",
                        f"Apple|USD|{100 * index}|physical",
                    )
                ),
                normalization_status=str(spec.get("normalization_status", "normalized")),
                row_publishable=bool(spec.get("row_publishable", False)),
                publishability_basis=str(
                    spec.get("publishability_basis", "validator_pending")
                ),
                restriction_parse_status=str(
                    spec.get("restriction_parse_status", "clear")
                ),
                card_type=str(spec.get("card_type", "Apple")),
                country_or_currency=str(spec.get("country_or_currency", "USD")),
                amount_range=str(spec.get("amount_range", str(100 * index))),
                multiplier=str(spec.get("multiplier", "1x")),
                form_factor=str(spec.get("form_factor", "physical")),
                price=float(spec.get("price", 95.5 + index)),
                quote_status=str(spec.get("quote_status", "candidate")),
                restriction_text=str(spec.get("restriction_text", "")),
                field_sources={"source_line": str(spec["source_line"])},
                rejection_reasons=list(spec.get("rejection_reasons", [])),
                parser_template=str(spec.get("parser_template", "repair-template-v1")),
                parser_version=str(spec.get("parser_version", "candidate-v1")),
            )
        )
    return QuoteCandidateMessage(
        platform="wechat",
        source_group_key="wechat:g-web-repair",
        chat_id="g-web-repair",
        chat_name="Repair Replay 群",
        message_id=message_id,
        source_name="报价员",
        sender_id="seller-web-repair",
        sender_display="报价员",
        raw_message=raw_message,
        message_time="2026-04-14 19:00:00",
        parser_kind="group-parser",
        parser_template="repair-template-v1",
        parser_version="candidate-v1",
        confidence=0.97,
        parse_status="parsed",
        message_fingerprint=f"fingerprint-{message_id}",
        snapshot_hypothesis="delta_update",
        snapshot_hypothesis_reason="repair baseline regression",
        rejection_reasons=[],
        run_kind=run_kind,
        replay_of_quote_document_id=replay_of_quote_document_id,
        rows=rows,
    )


def _json_field(value):
    return json.loads(value) if isinstance(value, str) else value


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

        def start_response(status: str, headers: list[tuple[str, str]], exc_info=None) -> None:
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
            status: str, response_headers: list[tuple[str, str]], exc_info=None
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

    def _get_quote_document_by_id(self, quote_document_id: int):
        return self.db.conn.execute(
            """
            SELECT *
            FROM quote_documents
            WHERE id = ?
            """,
            (quote_document_id,),
        ).fetchone()

    def _get_quote_document(
        self,
        *,
        platform: str,
        chat_id: str,
        message_id: str,
    ):
        return self.db.conn.execute(
            """
            SELECT *
            FROM quote_documents
            WHERE platform = ? AND chat_id = ? AND message_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (platform, chat_id, message_id),
        ).fetchone()

    def _count_rows(
        self,
        table_name: str,
        where_clause: str = "",
        params: tuple[object, ...] = (),
    ) -> int:
        row = self.db.conn.execute(
            f"SELECT COUNT(*) AS cnt FROM {table_name} {where_clause}",
            params,
        ).fetchone()
        return int(row["cnt"] or 0)

    def _upsert_bootstrap_profile(
        self,
        *,
        fixture_name: str,
        platform: str,
        chat_id: str,
        chat_name: str,
    ) -> dict:
        from scripts.bootstrap_quote_group_profiles import build_bootstrap_profile_payload

        payload = build_bootstrap_profile_payload(
            fixture_name=fixture_name,
            platform=platform,
            chat_id=chat_id,
            chat_name=chat_name,
        )
        self.db.upsert_quote_group_profile(
            platform=platform,
            chat_id=chat_id,
            chat_name=chat_name,
            default_card_type=str(payload["default_card_type"]),
            default_country_or_currency=str(payload["default_country_or_currency"]),
            default_form_factor=str(payload["default_form_factor"]),
            default_multiplier=str(payload["default_multiplier"]),
            parser_template=str(payload["parser_template"]),
            stale_after_minutes=int(payload["stale_after_minutes"]),
            note=str(payload["note"]),
            template_config=json.dumps(payload["template_config"], ensure_ascii=False),
        )
        return payload

    def test_dashboard_endpoint_returns_group_and_period_data(self) -> None:
        status, payload = self._request("GET", "/api/dashboard")
        self.assertEqual(status, 200)
        self.assertEqual(len(payload["current_groups"]), 1)
        self.assertEqual(len(payload["recent_periods"]), 1)
        self.assertIn("latest_transactions", payload)

    def test_quotes_page_renders_board_and_exception_sections(self) -> None:
        status, body = self._request_text("GET", "/quotes")
        self.assertEqual(status, 200)
        self.assertIn("报价墙", body)
        self.assertIn("组实时", body)
        self.assertIn('id="quote-filter-form"', body)
        self.assertIn('id="quote-board-table"', body)
        self.assertIn('id="quote-experimental-summary"', body)
        self.assertIn('id="quote-wall-update-count"', body)
        self.assertIn('id="quote-watchlist-grid"', body)
        self.assertIn('id="quote-promotion-gate"', body)
        self.assertIn('id="quote-promotion-criteria"', body)
        self.assertIn('id="quote-profile-table"', body)
        self.assertIn('id="quote-inquiry-table"', body)
        self.assertIn('id="quote-ranking-table"', body)
        self.assertIn('id="quote-exception-cards"', body)
        self.assertIn('id="quote-harvest-modal"', body)
        self.assertIn('id="quote-evidence-modal"', body)
        self.assertIn('id="quote-failure-dictionary-form"', body)
        self.assertIn('id="quote-failure-dictionary-list"', body)
        self.assertIn('id="quote-profile-edit-modal"', body)
        self.assertIn("异常整理台", body)
        self.assertIn("验证工作台", body)
        self.assertIn("修复词典", body)
        self.assertIn("标准模板整理", body)
        self.assertIn("超市卡", body)
        self.assertIn("分段收割", body)
        self.assertIn("切换到分段收割", body)
        self.assertIn("保存这一段并继续", body)
        self.assertIn("验证详情", body)
        self.assertIn("quote-harvest-side-header", body)
        self.assertIn("quote-harvest-workspace-scroll", body)
        self.assertIn("quote-harvest-rows-scroll", body)
        self.assertIn("quote-modal-wide", body)
        self.assertIn("编辑模板", body)
        self.assertIn("确认整版", body)
        self.assertIn("确认局部", body)
        self.assertIn("短回复上下文", body)
        self.assertIn("异常区", body)
        self.assertIn("人工整理", body)
        self.assertIn("生成预览", body)
        self.assertIn("默认只看待处理异常", body)
        self.assertIn("骨架 1 / N", body)
        self.assertIn("未改动报价墙", body)
        self.assertIn("继续补一段并生成候选重放", body)
        self.assertNotIn("继续补一段并上墙", body)
        self.assertNotIn("并已上墙", body)
        self.assertIn("/api/quotes/evidence", body)
        self.assertIn("/api/quotes/failure-dictionary", body)

    def test_experimental_wall_mode_updates_board_through_core_without_downstream_actions(
        self,
    ) -> None:
        from bookkeeping_core.quote_candidates import QuoteCandidateMessage, QuoteCandidateRow

        self.db.set_group(
            platform="wechat",
            group_key="wechat:g-web-experimental",
            chat_id="g-web-experimental",
            chat_name="实验报价群",
            group_num=5,
        )
        self.db.upsert_quote_group_profile(
            platform="wechat",
            chat_id="g-web-experimental",
            chat_name="实验报价群",
            default_card_type="Apple",
            default_country_or_currency="USD",
            default_form_factor="横白卡",
            parser_template="group-parser",
            template_config=json.dumps(
                {
                    "version": "group-parser-v1",
                    "defaults": {
                        "card_type": "Apple",
                        "country_or_currency": "USD",
                        "form_factor": "横白卡",
                    },
                    "sections": [],
                },
                ensure_ascii=False,
            ),
        )

        candidate = QuoteCandidateMessage(
            platform="wechat",
            source_group_key="wechat:g-web-experimental",
            chat_id="g-web-experimental",
            chat_name="实验报价群",
            message_id="msg-web-experimental-1",
            source_name="报价员",
            sender_id="u-web-experimental",
            sender_display="报价员",
            raw_message="[Apple]\n100=5.18",
            message_time="2026-04-15 13:10:00",
            parser_kind="group-parser",
            parser_template="group-parser",
            parser_version="group-parser-v1",
            confidence=0.99,
            parse_status="parsed",
            message_fingerprint="web-experimental-fingerprint",
            snapshot_hypothesis="unresolved",
            snapshot_hypothesis_reason="phase08-webapp",
            rows=[
                QuoteCandidateRow(
                    row_ordinal=1,
                    source_line="100=5.18",
                    source_line_index=1,
                    line_confidence=0.98,
                    normalized_sku_key="Apple|USD|100|横白卡",
                    normalization_status="normalized",
                    row_publishable=False,
                    publishability_basis="parser_prevalidation",
                    restriction_parse_status="parsed",
                    card_type="Apple",
                    country_or_currency="USD",
                    amount_range="100",
                    multiplier=None,
                    form_factor="横白卡",
                    price=5.18,
                    quote_status="active",
                    restriction_text="",
                )
            ],
        )

        with patch.dict(
            os.environ,
            {"BOOKKEEPING_QUOTE_WALL_MODE": "experimental_active_wall"},
            clear=False,
        ), patch(
            "bookkeeping_core.quotes.should_attempt_template_quote_capture",
            return_value=True,
        ), patch(
            "bookkeeping_core.quotes._parse_quote_message_to_candidate_details",
            return_value=(candidate, [], []),
        ):
            status, payload = self._request(
                "POST",
                "/api/core/messages",
                {
                    "platform": "wechat",
                    "message_id": "msg-web-experimental-1",
                    "chat_id": "g-web-experimental",
                    "chat_name": "实验报价群",
                    "is_group": True,
                    "sender_id": "u-web-experimental",
                    "sender_name": "报价员",
                    "content_type": "text",
                    "text": "[Apple]\\n100=5.18",
                    "received_at": "2026-04-15 13:10:00",
                },
                headers={"Authorization": "Bearer core-secret"},
            )
            self.assertEqual(status, 200)
            self.assertEqual(payload["actions"], [])

            status, board = self._request(
                "GET",
                "/api/quotes/board",
                query_string="source_group_key=wechat:g-web-experimental",
            )

        self.assertEqual(status, 200)
        self.assertEqual(
            board["experimental_wall"]["mode"],
            "experimental_active_wall",
        )
        self.assertTrue(board["experimental_wall"]["real_wall_updates_enabled"])
        self.assertFalse(board["experimental_wall"]["downstream_actions_enabled"])
        self.assertIn("experimental_wall_overview", board)
        self.assertIn("experimental_wall_gate", board)
        self.assertIn("metrics", board["experimental_wall_overview"])
        self.assertIn("watchlist", board["experimental_wall_overview"])
        self.assertIn("criteria", board["experimental_wall_gate"])
        self.assertGreaterEqual(len(board["rows"]), 1)

    def test_quote_dictionary_page_and_api_require_admin_password_for_writes(self) -> None:
        status, body = self._request_text("GET", "/quote-dictionary")
        self.assertEqual(status, 200)
        self.assertIn("标准映射台", body)
        self.assertIn('id="quote-dictionary-form"', body)

        status, payload = self._request("GET", "/api/quotes/dictionary")
        self.assertEqual(status, 200)
        self.assertTrue(any(row["source"] == "builtin" for row in payload["rows"]))

        old_password = os.environ.get("QUOTE_ADMIN_PASSWORD")
        os.environ["QUOTE_ADMIN_PASSWORD"] = "dict-secret"
        try:
            status, rejected = self._request(
                "POST",
                "/api/quotes/dictionary",
                {
                    "category": "country_currency",
                    "alias": "香港",
                    "canonical_value": "HKD",
                    "admin_password": "wrong",
                },
            )
            self.assertEqual(status, 400)
            self.assertIn("admin password", rejected["error"])

            status, created = self._request(
                "POST",
                "/api/quotes/dictionary",
                {
                    "category": "country_currency",
                    "alias": "香港",
                    "canonical_value": "HKD",
                    "admin_password": "dict-secret",
                },
            )
            self.assertEqual(status, 200)
            self.assertGreater(created["alias_id"], 0)

            status, payload = self._request("GET", "/api/quotes/dictionary")
            self.assertEqual(status, 200)
            custom = next(
                row
                for row in payload["rows"]
                if row.get("source") == "custom" and row.get("alias") == "香港"
            )
            self.assertEqual(custom["canonical_value"], "HKD")

            status, disabled = self._request(
                "POST",
                "/api/quotes/dictionary/disable",
                {"id": created["alias_id"], "admin_password": "dict-secret"},
            )
            self.assertEqual(status, 200)
            self.assertEqual(disabled["updated"], 1)

            status, created_form = self._request(
                "POST",
                "/api/quotes/dictionary",
                {
                    "category": "form_factor",
                    "alias": "电子",
                    "canonical_value": "Code",
                    "admin_password": "dict-secret",
                },
            )
            self.assertEqual(status, 200)
            self.assertGreater(created_form["alias_id"], 0)

            status, filtered = self._request(
                "GET",
                "/api/quotes/dictionary",
                query_string="category=form_factor&include_builtin=0",
            )
            self.assertEqual(status, 200)
            self.assertEqual(filtered["total"], 1)
            self.assertEqual(filtered["rows"][0]["alias"], "电子")
            self.assertEqual(filtered["rows"][0]["canonical_input"], "Code")
            self.assertEqual(filtered["rows"][0]["canonical_value"], "代码")
        finally:
            if old_password is None:
                os.environ.pop("QUOTE_ADMIN_PASSWORD", None)
            else:
                os.environ["QUOTE_ADMIN_PASSWORD"] = old_password

    def test_quote_group_profile_delete_requires_admin_password_and_removes_profile(self) -> None:
        old_password = os.environ.get("QUOTE_ADMIN_PASSWORD")
        os.environ["QUOTE_ADMIN_PASSWORD"] = "profile-delete-secret"
        try:
            profile_id = self.db.upsert_quote_group_profile(
                platform="wechat",
                chat_id="g-delete-profile",
                chat_name="待删模板群",
                default_card_type="Apple",
                default_country_or_currency="USD",
                default_form_factor="横白卡",
                default_multiplier="",
                parser_template="strict-section-v1",
                stale_after_minutes=30,
                note="to be deleted",
                template_config='{"version":"strict-section-v1","sections":[]}',
            )

            status, payload = self._request(
                "POST",
                "/api/quotes/group-profiles/delete",
                {"id": profile_id},
            )
            self.assertEqual(status, 400)
            self.assertIn("Bad payload", payload["error"])

            status, payload = self._request(
                "POST",
                "/api/quotes/group-profiles/delete",
                {"id": profile_id, "admin_password": "wrong"},
            )
            self.assertEqual(status, 400)
            self.assertIn("admin password is invalid", payload["error"])

            status, payload = self._request(
                "POST",
                "/api/quotes/group-profiles/delete",
                {"id": profile_id, "admin_password": "profile-delete-secret"},
            )
            self.assertEqual(status, 200)
            self.assertTrue(payload["deleted"])
            self.assertIsNone(
                self.db.get_quote_group_profile(platform="wechat", chat_id="g-delete-profile")
            )
        finally:
            if old_password is None:
                os.environ.pop("QUOTE_ADMIN_PASSWORD", None)
            else:
                os.environ["QUOTE_ADMIN_PASSWORD"] = old_password

    def test_quote_delete_endpoint_is_disabled_and_leaves_active_facts_untouched(self) -> None:
        quote_document_id = self.db.record_quote_document(
            platform="wechat",
            source_group_key="wechat:g-100",
            chat_id="g-100",
            chat_name="客户群-Web",
            message_id="msg-delete-disabled",
            source_name="报价员",
            sender_id="seller-delete-disabled",
            raw_text="US 100 95.5",
            message_time="2026-04-15 11:00:00",
            parser_template="group-parser",
            parser_version="group-parser-v1",
            confidence=0.9,
            parse_status="parsed",
        )
        quote_id = self.db.upsert_quote_price_row_with_history(
            quote_document_id=quote_document_id,
            message_id="msg-delete-disabled",
            platform="wechat",
            source_group_key="wechat:g-100",
            chat_id="g-100",
            chat_name="客户群-Web",
            source_name="报价员",
            sender_id="seller-delete-disabled",
            card_type="Apple",
            country_or_currency="USD",
            amount_range="100",
            multiplier=None,
            form_factor="physical",
            price=95.5,
            quote_status="active",
            restriction_text="",
            source_line="US 100 95.5",
            raw_text="US 100 95.5",
            message_time="2026-04-15 11:00:00",
            effective_at="2026-04-15 11:00:00",
            expires_at=None,
            parser_template="group-parser",
            parser_version="group-parser-v1",
            confidence=0.9,
        )

        status, payload = self._request("POST", "/api/quotes/delete", {"id": quote_id})

        self.assertEqual(status, 409)
        self.assertFalse(payload["deleted"])
        self.assertIn("未改动报价墙", payload["error"])
        self.assertEqual(
            self._count_rows("quote_price_rows", "WHERE id = ?", (quote_id,)),
            1,
        )

    def test_quote_board_endpoint_returns_empty_payload_by_default(self) -> None:
        status, payload = self._request("GET", "/api/quotes/board")
        self.assertEqual(status, 200)
        self.assertEqual(payload["rows"], [])
        self.assertEqual(payload["total"], 0)

    def test_quote_board_distinguishes_discrete_and_range_amounts(self) -> None:
        discrete_doc_id = self.db.record_quote_document(
            platform="wechat",
            source_group_key="wechat:g-100",
            chat_id="g-100",
            chat_name="客户群-Web",
            message_id="msg-discrete-old",
            source_name="报价员",
            sender_id="u-web",
            raw_text="100 / 150=5.30",
            message_time="2026-04-11 08:00:00",
            parser_template="strict-section",
            parser_version="strict-section-v1",
            confidence=1.0,
            parse_status="parsed",
        )
        self.db.upsert_quote_price_row_with_history(
            quote_document_id=discrete_doc_id,
            message_id="msg-discrete-old",
            platform="wechat",
            source_group_key="wechat:g-100",
            chat_id="g-100",
            chat_name="客户群-Web",
            source_name="报价员",
            sender_id="u-web",
            card_type="Apple",
            country_or_currency="USD",
            amount_range="100 / 150",
            multiplier=None,
            form_factor="横白卡",
            price=5.30,
            quote_status="active",
            restriction_text="",
            source_line="100 / 150=5.30",
            raw_text="100 / 150=5.30",
            message_time="2026-04-11 08:00:00",
            effective_at="2026-04-11 08:00:00",
            expires_at=None,
            parser_template="strict-section",
            parser_version="strict-section-v1",
            confidence=1.0,
        )
        discrete_new_doc_id = self.db.record_quote_document(
            platform="wechat",
            source_group_key="wechat:g-100",
            chat_id="g-100",
            chat_name="客户群-Web",
            message_id="msg-discrete-new",
            source_name="报价员",
            sender_id="u-web",
            raw_text="100/150=5.43",
            message_time="2026-04-11 09:00:00",
            parser_template="strict-section",
            parser_version="strict-section-v1",
            confidence=1.0,
            parse_status="parsed",
        )
        self.db.upsert_quote_price_row_with_history(
            quote_document_id=discrete_new_doc_id,
            message_id="msg-discrete-new",
            platform="wechat",
            source_group_key="wechat:g-100",
            chat_id="g-100",
            chat_name="客户群-Web",
            source_name="报价员",
            sender_id="u-web",
            card_type="Apple",
            country_or_currency="USD",
            amount_range="100/150",
            multiplier=None,
            form_factor="横白卡",
            price=5.43,
            quote_status="active",
            restriction_text="",
            source_line="100/150=5.43",
            raw_text="100/150=5.43",
            message_time="2026-04-11 09:00:00",
            effective_at="2026-04-11 09:00:00",
            expires_at=None,
            parser_template="strict-section",
            parser_version="strict-section-v1",
            confidence=1.0,
        )
        range_doc_id = self.db.record_quote_document(
            platform="wechat",
            source_group_key="wechat:g-100",
            chat_id="g-100",
            chat_name="客户群-Web",
            message_id="msg-range",
            source_name="报价员",
            sender_id="u-web",
            raw_text="100-150=5.40",
            message_time="2026-04-11 09:10:00",
            parser_template="strict-section",
            parser_version="strict-section-v1",
            confidence=1.0,
            parse_status="parsed",
        )
        self.db.upsert_quote_price_row_with_history(
            quote_document_id=range_doc_id,
            message_id="msg-range",
            platform="wechat",
            source_group_key="wechat:g-100",
            chat_id="g-100",
            chat_name="客户群-Web",
            source_name="报价员",
            sender_id="u-web",
            card_type="Apple",
            country_or_currency="USD",
            amount_range="100-150",
            multiplier=None,
            form_factor="横白卡",
            price=5.40,
            quote_status="active",
            restriction_text="",
            source_line="100-150=5.40",
            raw_text="100-150=5.40",
            message_time="2026-04-11 09:10:00",
            effective_at="2026-04-11 09:10:00",
            expires_at=None,
            parser_template="strict-section",
            parser_version="strict-section-v1",
            confidence=1.0,
        )

        status, payload = self._request("GET", "/api/quotes/board")
        self.assertEqual(status, 200)
        rows = [
            row for row in payload["rows"]
            if row["card_type"] == "Apple"
            and row["country_or_currency"] == "USD"
            and row["form_factor"] == "横白卡"
        ]
        self.assertTrue(any(row["amount_range"] == "100/150" for row in rows))
        self.assertTrue(any(row["amount_range"] == "100-150" for row in rows))
        discrete_row = next(row for row in rows if row["amount_range"] == "100/150")
        range_row = next(row for row in rows if row["amount_range"] == "100-150")
        self.assertEqual(discrete_row["price"], 5.43)
        self.assertEqual(discrete_row["change_status"], "up")
        self.assertEqual(range_row["price"], 5.4)

        status, ranking = self._request(
            "GET",
            "/api/quotes/rankings",
            query_string="card_type=Apple&country_or_currency=USD&amount_range=100/150&form_factor=横白卡",
        )
        self.assertEqual(status, 200)
        self.assertEqual(ranking["total"], 2)
        self.assertTrue(all(row["amount_range"] == "100/150" for row in ranking["rows"]))

    def test_quote_board_and_exceptions_use_current_group_chat_name(self) -> None:
        quote_document_id = self.db.record_quote_document(
            platform="wechat",
            source_group_key="wechat:g-100",
            chat_id="g-100",
            chat_name="客户群-Web",
            message_id="msg-quote-name-old",
            source_name="报价员",
            sender_id="u-web",
            raw_text="50=5.3",
            message_time="2026-04-11 09:00:00",
            parser_template="group-parser",
            parser_version="group-parser-v1",
            confidence=1.0,
            parse_status="parsed",
        )
        self.db.upsert_quote_price_row_with_history(
            quote_document_id=quote_document_id,
            message_id="msg-quote-name-old",
            platform="wechat",
            source_group_key="wechat:g-100",
            chat_id="g-100",
            chat_name="客户群-Web",
            source_name="报价员",
            sender_id="u-web",
            card_type="Apple",
            country_or_currency="USD",
            amount_range="50",
            multiplier=None,
            form_factor="横白卡",
            price=5.3,
            quote_status="active",
            restriction_text="",
            source_line="50=5.3",
            raw_text="50=5.3",
            message_time="2026-04-11 09:00:00",
            effective_at="2026-04-11 09:00:00",
            expires_at=None,
            parser_template="group-parser",
            parser_version="group-parser-v1",
            confidence=1.0,
        )
        self.db.record_quote_exception(
            quote_document_id=quote_document_id,
            platform="wechat",
            source_group_key="wechat:g-100",
            chat_id="g-100",
            chat_name="客户群-Web",
            source_name="报价员",
            sender_id="u-web",
            reason="strict_match_failed",
            source_line="100/150=5.43",
            raw_text="100/150=5.43",
            message_time="2026-04-11 09:01:00",
            parser_template="group-parser",
            parser_version="group-parser-v1",
            confidence=0.0,
        )
        self.db.set_group(
            platform="wechat",
            group_key="wechat:g-100",
            chat_id="g-100",
            chat_name="客户群-Web-新",
            group_num=5,
        )

        status, board_payload = self._request("GET", "/api/quotes/board")
        self.assertEqual(status, 200)
        self.assertEqual(board_payload["rows"][0]["chat_name"], "客户群-Web-新")

        status, exception_payload = self._request("GET", "/api/quotes/exceptions")
        self.assertEqual(status, 200)
        self.assertEqual(exception_payload["rows"][0]["chat_name"], "客户群-Web-新")

    def test_quote_history_and_exception_endpoints_accept_filters(self) -> None:
        status, history_payload = self._request(
            "GET",
            "/api/quotes/history",
            query_string="card_type=Steam&country_or_currency=USD&source_group_key=wechat:g-1&limit=5&offset=2",
        )
        self.assertEqual(status, 200)
        self.assertEqual(history_payload["rows"], [])
        self.assertEqual(history_payload["total"], 0)
        self.assertEqual(history_payload["limit"], 5)
        self.assertEqual(history_payload["offset"], 2)
        self.assertEqual(history_payload["filters"]["card_type"], "Steam")
        self.assertEqual(history_payload["filters"]["country_or_currency"], "USD")
        self.assertEqual(history_payload["filters"]["source_group_key"], "wechat:g-1")

        status, exception_payload = self._request(
            "GET",
            "/api/quotes/exceptions",
            query_string="limit=7&offset=1",
        )
        self.assertEqual(status, 200)
        self.assertEqual(exception_payload["rows"], [])
        self.assertEqual(exception_payload["total"], 0)
        self.assertEqual(exception_payload["open_total"], 0)
        self.assertEqual(exception_payload["handled_total"], 0)
        self.assertEqual(exception_payload["limit"], 7)
        self.assertEqual(exception_payload["offset"], 1)
        self.assertEqual(exception_payload["resolution_status"], "open")

    def test_quote_like_message_without_group_template_enters_exception_queue(self) -> None:
        from bookkeeping_core.contracts import NormalizedMessageEnvelope
        from bookkeeping_core.quotes import QuoteCaptureService

        self.db.set_group(
            platform="whatsapp",
            group_key="whatsapp:group-no-template@g.us",
            chat_id="group-no-template@g.us",
            chat_name="新改名客人群",
            group_num=5,
        )

        service = QuoteCaptureService(self.db)
        result = service.capture_from_message(
            NormalizedMessageEnvelope.from_dict(
                {
                    "platform": "whatsapp",
                    "message_id": "msg-no-template-1",
                    "chat_id": "group-no-template@g.us",
                    "chat_name": "新改名客人群",
                    "is_group": True,
                    "sender_id": "seller-1",
                    "sender_name": "Seller",
                    "sender_kind": "user",
                    "content_type": "text",
                    "text": "【iTunes CAD】\n15-90=5.0\n100/150=5.42",
                    "received_at": "2026-04-11 07:10:00",
                }
            )
        )

        self.assertTrue(result["captured"])
        self.assertEqual(result["rows"], 0)
        self.assertEqual(result["exceptions"], 1)
        self.assertEqual(result["parse_status"], "empty")

        payload = self.db.list_quote_exceptions(limit=10, offset=0, resolution_status="all")
        self.assertEqual(payload["total"], 1)
        self.assertEqual(payload["rows"][0]["reason"], "missing_group_template")
        self.assertEqual(payload["rows"][0]["chat_name"], "新改名客人群")

    def test_quote_like_message_from_supplier_group_does_not_enter_exception_queue(self) -> None:
        from bookkeeping_core.contracts import NormalizedMessageEnvelope
        from bookkeeping_core.quotes import QuoteCaptureService

        self.db.set_group(
            platform="whatsapp",
            group_key="whatsapp:group-supplier@g.us",
            chat_id="group-supplier@g.us",
            chat_name="供应商群",
            group_num=2,
        )

        service = QuoteCaptureService(self.db)
        result = service.capture_from_message(
            NormalizedMessageEnvelope.from_dict(
                {
                    "platform": "whatsapp",
                    "message_id": "msg-supplier-1",
                    "chat_id": "group-supplier@g.us",
                    "chat_name": "供应商群",
                    "is_group": True,
                    "sender_id": "seller-2",
                    "sender_name": "Supplier",
                    "sender_kind": "user",
                    "content_type": "text",
                    "text": "【iTunes CAD】\n15-90=5.0\n100/150=5.42",
                    "received_at": "2026-04-11 07:15:00",
                }
            )
        )

        self.assertFalse(result["captured"])
        self.assertEqual(result["rows"], 0)
        self.assertEqual(result["exceptions"], 0)

        payload = self.db.list_quote_exceptions(limit=10, offset=0, resolution_status="all")
        self.assertEqual(payload["total"], 0)

    def test_quote_exception_endpoint_defaults_to_open_page_with_stats(self) -> None:
        open_id = self.db.record_quote_exception(
            quote_document_id=0,
            platform="wechat",
            source_group_key="wechat:g-ex-list",
            chat_id="g-ex-list",
            chat_name="异常分页群",
            source_name="客人",
            sender_id="u-open",
            reason="strict_match_failed",
            source_line="50=5.3",
            raw_text="50=5.3",
            message_time="2026-04-08 10:00:00",
            parser_template="group-parser",
            parser_version="quote-v1",
            confidence=0.0,
        )
        ignored_id = self.db.record_quote_exception(
            quote_document_id=0,
            platform="wechat",
            source_group_key="wechat:g-ex-list",
            chat_id="g-ex-list",
            chat_name="异常分页群",
            source_name="客人",
            sender_id="u-ignored",
            reason="strict_match_failed",
            source_line="100=5.4",
            raw_text="100=5.4",
            message_time="2026-04-08 10:05:00",
            parser_template="group-parser",
            parser_version="quote-v1",
            confidence=0.0,
        )
        self.assertGreater(open_id, 0)
        self.assertGreater(ignored_id, 0)
        self.db.resolve_quote_exception(
            exception_id=ignored_id,
            resolution_status="ignored",
            resolution_note=self.db.encode_quote_exception_suppression_note(
                source_group_key="wechat:g-ex-list",
                reason="strict_match_failed",
                source_line="100=5.4",
                raw_text="100=5.4",
                note="manual ignore",
            ),
        )

        status, payload = self._request("GET", "/api/quotes/exceptions")
        self.assertEqual(status, 200)
        self.assertEqual(payload["resolution_status"], "open")
        self.assertEqual(payload["total"], 1)
        self.assertEqual(payload["open_total"], 1)
        self.assertEqual(payload["handled_total"], 1)
        self.assertEqual(payload["limit"], 10)
        self.assertEqual(payload["offset"], 0)
        self.assertFalse(payload["has_prev"])
        self.assertFalse(payload["has_next"])
        self.assertEqual(len(payload["rows"]), 1)
        self.assertEqual(payload["rows"][0]["id"], open_id)

        status, all_payload = self._request(
            "GET",
            "/api/quotes/exceptions",
            query_string="resolution_status=all&limit=1&offset=1",
        )
        self.assertEqual(status, 200)
        self.assertEqual(all_payload["resolution_status"], "all")
        self.assertEqual(all_payload["total"], 2)
        self.assertEqual(all_payload["open_total"], 1)
        self.assertEqual(all_payload["handled_total"], 1)
        self.assertTrue(all_payload["has_prev"])

    def test_quote_capture_skips_balance_like_message_in_template_group(self) -> None:
        from bookkeeping_core.contracts import NormalizedMessageEnvelope
        from bookkeeping_core.quotes import QuoteCaptureService

        self.db.set_group(
            platform="whatsapp",
            group_key="whatsapp:group-balance@g.us",
            chat_id="group-balance@g.us",
            chat_name="Steam 报价群",
            group_num=5,
        )
        self.db.upsert_quote_group_profile(
            platform="whatsapp",
            chat_id="group-balance@g.us",
            chat_name="Steam 报价群",
            default_card_type="Steam",
            default_country_or_currency="USD",
            default_form_factor="横白卡",
            parser_template="group-parser",
            template_config=json.dumps(
                {"version": "group-parser-v1", "defaults": {}, "sections": []},
                ensure_ascii=False,
            ),
        )

        service = QuoteCaptureService(self.db)
        result = service.capture_from_message(
            NormalizedMessageEnvelope.from_dict(
                {
                    "platform": "whatsapp",
                    "message_id": "msg-balance-skip",
                    "chat_id": "group-balance@g.us",
                    "chat_name": "Steam 报价群",
                    "is_group": True,
                    "sender_id": "seller-1",
                    "sender_name": "Seller",
                    "content_type": "text",
                    "text": "当前账单金额: -26646.17\n+200*5.73=1146",
                    "received_at": "2026-04-11 07:15:00",
                }
            )
        )

        self.assertFalse(result["captured"])
        payload = self.db.list_quote_exceptions(limit=10, offset=0, resolution_status="all")
        self.assertEqual(payload["total"], 0)

    def test_ignored_quote_exception_suppresses_same_content_but_not_other_groups(self) -> None:
        from bookkeeping_core.contracts import NormalizedMessageEnvelope
        from bookkeeping_core.quotes import QuoteCaptureService
        from tests.support.quote_exception_corpus import load_gold_fixture

        self.db.set_group(
            platform="whatsapp",
            group_key="whatsapp:group-ignore@g.us",
            chat_id="group-ignore@g.us",
            chat_name="新改名客人群",
            group_num=5,
        )
        self.db.set_group(
            platform="whatsapp",
            group_key="whatsapp:group-ignore-2@g.us",
            chat_id="group-ignore-2@g.us",
            chat_name="另一个客人群",
            group_num=5,
        )
        service = QuoteCaptureService(self.db)
        fixture = load_gold_fixture("wannuo_xbox_shorthand_174")
        payload = {
            "platform": "whatsapp",
            "chat_name": "新改名客人群",
            "is_group": True,
            "sender_id": "seller-1",
            "sender_name": "Seller",
            "content_type": "text",
            "text": str(fixture["raw_text"]),
            "received_at": "2026-04-11 07:10:00",
        }

        first = service.capture_from_message(
            NormalizedMessageEnvelope.from_dict(
                {
                    **payload,
                    "message_id": "msg-ignore-1",
                    "chat_id": "group-ignore@g.us",
                }
            )
        )
        self.assertTrue(first["captured"])
        all_payload = self.db.list_quote_exceptions(limit=10, offset=0, resolution_status="all")
        self.assertEqual(all_payload["total"], 1)
        self.assertEqual(str(all_payload["rows"][0]["resolution_status"]), "open")
        exception_id = int(all_payload["rows"][0]["id"])

        status, resolve_payload = self._request(
            "POST",
            "/api/quotes/exceptions/resolve",
            {"exception_id": exception_id, "resolution_status": "ignored"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(resolve_payload["updated"], 1)

        second = service.capture_from_message(
            NormalizedMessageEnvelope.from_dict(
                {
                    **payload,
                    "message_id": "msg-ignore-2",
                    "chat_id": "group-ignore@g.us",
                    "received_at": "2026-04-11 07:20:00",
                }
            )
        )
        self.assertFalse(second["captured"])
        all_payload = self.db.list_quote_exceptions(limit=20, offset=0, resolution_status="all")
        self.assertEqual(all_payload["total"], 1)

        third = service.capture_from_message(
            NormalizedMessageEnvelope.from_dict(
                {
                    **payload,
                    "message_id": "msg-ignore-3",
                    "chat_id": "group-ignore-2@g.us",
                    "chat_name": "另一个客人群",
                    "received_at": "2026-04-11 07:30:00",
                }
            )
        )
        self.assertTrue(third["captured"])
        cross_group_payload = self.db.list_quote_exceptions(
            limit=20,
            offset=0,
            resolution_status="all",
        )
        self.assertEqual(cross_group_payload["total"], 2)

    def test_quote_inquiry_and_exception_resolution_endpoints(self) -> None:
        status, inquiry_payload = self._request(
            "POST",
            "/api/quotes/inquiries",
            {
                "platform": "wechat",
                "chat_id": "g-inquiry",
                "chat_name": "询价群",
                "card_type": "it",
                "country_or_currency": "uk",
                "amount_range": "10",
            },
        )
        self.assertEqual(status, 200)
        self.assertGreater(inquiry_payload["inquiry_id"], 0)
        status, inquiries_payload = self._request("GET", "/api/quotes/inquiries")
        self.assertEqual(status, 200)
        self.assertEqual(inquiries_payload["rows"][0]["card_type"], "Apple")
        self.assertEqual(inquiries_payload["rows"][0]["country_or_currency"], "GBP")

        status, ranking_payload = self._request(
            "GET",
            "/api/quotes/rankings",
            query_string="card_type=Apple&country_or_currency=GBP&amount_range=10&form_factor=%E4%B8%8D%E9%99%90",
        )
        self.assertEqual(status, 200)
        self.assertEqual(ranking_payload["rows"], [])

        status, match_payload = self._request(
            "GET",
            "/api/quotes/matches",
            query_string="card_type=it&country_or_currency=us&amount=250",
        )
        self.assertEqual(status, 200)
        self.assertEqual(match_payload["filters"]["card_type"], "Apple")
        self.assertEqual(match_payload["filters"]["country_or_currency"], "USD")

        status, profile_payload = self._request(
            "POST",
            "/api/quotes/group-profiles",
            {
                "platform": "wechat",
                "chat_id": "g-profile",
                "chat_name": "模板群",
                "default_card_type": "it",
                "parser_template": "apple_modifier_sheet",
                "stale_after_minutes": 30,
            },
        )
        self.assertEqual(status, 200)
        self.assertGreater(profile_payload["profile_id"], 0)
        status, profiles = self._request("GET", "/api/quotes/group-profiles")
        self.assertEqual(status, 200)
        self.assertEqual(profiles["rows"][0]["default_card_type"], "Apple")

        exception_id = self.db.record_quote_exception(
            quote_document_id=0,
            platform="wechat",
            source_group_key="wechat:g-ex",
            chat_id="g-ex",
            chat_name="异常群",
            source_name="客人",
            sender_id="u-ex",
            reason="missing_context",
            source_line="uk 10",
            raw_text="uk 10",
            message_time="2026-04-08 10:00:00",
            parser_template="simple_sheet",
            parser_version="quote-v1",
            confidence=0.4,
        )
        status, resolve_payload = self._request(
            "POST",
            "/api/quotes/exceptions/resolve",
            {"exception_id": exception_id, "resolution_status": "ignored"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(resolve_payload["updated"], 1)

        attach_exception_id = self.db.record_quote_exception(
            quote_document_id=0,
            platform="wechat",
            source_group_key="wechat:g-ex",
            chat_id="g-ex",
            chat_name="异常群",
            source_name="客人",
            sender_id="u-ex",
            reason="blocked_or_question_line",
            source_line="雷蛇待定卡不加账！！",
            raw_text="雷蛇待定卡不加账！！",
            message_time="2026-04-08 10:00:00",
            parser_template="section_sheet",
            parser_version="quote-v1",
            confidence=0.45,
        )
        status, attach_payload = self._request(
            "POST",
            "/api/quotes/exceptions/resolve",
            {"exception_id": attach_exception_id, "resolution_status": "attached"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(attach_payload["status"], "no_target_rows")

    def test_quote_exception_harvest_preview_and_save(self) -> None:
        old_password = os.environ.get("QUOTE_ADMIN_PASSWORD")
        os.environ["QUOTE_ADMIN_PASSWORD"] = "harvest-secret"
        try:
            self.db.set_group(
                platform="wechat",
                group_key="wechat:g-harvest",
                chat_id="g-harvest",
                chat_name="收编群",
                group_num=5,
            )
            quote_document_id = self.db.record_quote_document(
                platform="wechat",
                source_group_key="wechat:g-harvest",
                chat_id="g-harvest",
                chat_name="收编群",
                message_id="msg-harvest",
                source_name="报价员",
                sender_id="u-harvest",
                raw_text="Apple USA\n10-50=5.20\n使用时间3分钟\n100-200=5.40",
                message_time="2026-04-08 10:00:00",
                parser_template="data-engine",
                parser_version="data-engine-v1",
                confidence=0.0,
                parse_status="empty",
            )
            exception_id = self.db.record_quote_exception(
                quote_document_id=quote_document_id,
                platform="wechat",
                source_group_key="wechat:g-harvest",
                chat_id="g-harvest",
                chat_name="收编群",
                source_name="报价员",
                sender_id="u-harvest",
                reason="strict_match_failed",
                source_line="10-50=5.20\n100-200=5.40",
                raw_text="Apple USA\n10-50=5.20\n使用时间3分钟\n100-200=5.40",
                message_time="2026-04-08 10:00:00",
                parser_template="data-engine",
                parser_version="data-engine-v1",
                confidence=0.0,
            )

            preview_payload = {
                "exception_id": exception_id,
                "section_start_line": 0,
                "section_end_line": 3,
                "defaults": {
                    "section_label": "Apple USA",
                    "priority": 10,
                    "card_type": "it",
                    "country_or_currency": "us",
                    "form_factor": "card",
                },
                "rows": [
                    {"source_line_index": 1, "amount": "10-50", "price": "5.20"},
                    {"source_line_index": 3, "amount": "100-200", "price": "5.40"},
                ],
                "ignored_line_indexes": [],
            }
            status, preview = self._request(
                "POST",
                "/api/quotes/exceptions/harvest-preview",
                preview_payload,
            )
            self.assertEqual(status, 200)
            self.assertTrue(preview["can_save"])
            self.assertTrue(preview["is_latest_for_group"])
            self.assertEqual(len(preview["preview_rows"]), 2)
            self.assertEqual(preview["preview_rows"][0]["card_type"], "Apple")
            self.assertEqual(preview["preview_rows"][0]["country_or_currency"], "USD")

            status, saved = self._request(
                "POST",
                "/api/quotes/exceptions/harvest-save",
                {**preview_payload, "admin_password": "harvest-secret"},
            )
            self.assertEqual(status, 200)
            self.assertTrue(saved["saved"])
            self.assertTrue(saved["replay"]["replayed"])
            self.assertFalse(saved["replay"]["mutated_active_facts"])
            self.assertEqual(saved["replay"]["rows"], 2)
            self.assertTrue(saved["resolved_fully"])
            self.assertEqual(saved["remaining_lines"], [])
            self.assertEqual(saved["restriction_lines_attached"], ["使用时间3分钟"])
            replay_document_id = int(saved["replay"]["quote_document_id"])
            self.assertGreater(int(saved["replay"]["validation_run_id"]), 0)
            self.assertNotEqual(replay_document_id, quote_document_id)
            replay_document = self._get_quote_document_by_id(replay_document_id)
            self.assertIsNotNone(replay_document)
            self.assertEqual(replay_document["run_kind"], "replay")
            self.assertEqual(replay_document["replay_of_quote_document_id"], quote_document_id)
            self.assertGreater(float(replay_document["confidence"]), 0.0)
            replay_candidate_rows = self.db.list_quote_candidate_rows(
                quote_document_id=replay_document_id
            )
            self.assertEqual(len(replay_candidate_rows), 2)
            validation_run = self.db.get_latest_quote_validation_run(
                quote_document_id=replay_document_id
            )
            self.assertIsNotNone(validation_run)
            assert validation_run is not None
            self.assertEqual(int(validation_run["id"]), int(saved["replay"]["validation_run_id"]))
            self.assertEqual(str(validation_run["run_kind"]), "replay")
            self.assertEqual(str(validation_run["message_decision"]), "publishable_rows_available")
            self.assertEqual(int(validation_run["publishable_row_count"]), 2)
            validation_rows = self.db.list_quote_validation_row_results(
                validation_run_id=int(validation_run["id"])
            )
            self.assertEqual(len(validation_rows), 2)
            self.assertTrue(
                all(str(row["final_decision"]) == "publishable" for row in validation_rows)
            )
            publishable_rows = self.db.list_publishable_quote_candidate_rows(
                quote_document_id=replay_document_id
            )
            self.assertEqual(len(publishable_rows), 2)
            self.assertTrue(
                all(
                    int(row["validation_run_id"])
                    == int(saved["replay"]["validation_run_id"])
                    for row in publishable_rows
                )
            )
            self.assertTrue(
                all(str(row["final_decision"]) == "publishable" for row in publishable_rows)
            )

            status, board = self._request("GET", "/api/quotes/board")
            self.assertEqual(status, 200)
            self.assertEqual(board["rows"], [])

            profile = self.db.get_quote_group_profile(platform="wechat", chat_id="g-harvest")
            self.assertEqual(profile["parser_template"], "strict-section-v1")
            self.assertIn('"version": "strict-section-v1"', profile["template_config"])
        finally:
            if old_password is None:
                os.environ.pop("QUOTE_ADMIN_PASSWORD", None)
            else:
                os.environ["QUOTE_ADMIN_PASSWORD"] = old_password

    def test_replay_helper_uses_validator_publishable_rows_for_mixed_results(self) -> None:
        from bookkeeping_core.quote_candidates import (
            QuoteCandidateMessage,
            QuoteCandidateRow,
        )
        from bookkeeping_web.app import _replay_latest_quote_document_with_current_template

        self.db.set_group(
            platform="wechat",
            group_key="wechat:g-replay-mixed",
            chat_id="g-replay-mixed",
            chat_name="回放混合校验群",
            group_num=5,
        )
        self.db.upsert_quote_group_profile(
            platform="wechat",
            chat_id="g-replay-mixed",
            chat_name="回放混合校验群",
            default_card_type="Apple",
            default_country_or_currency="USD",
            default_form_factor="横白卡",
            parser_template="group-parser",
            template_config=json.dumps(
                {"version": "group-parser-v1", "defaults": {}, "sections": []},
                ensure_ascii=False,
            ),
        )
        quote_document_id = self.db.record_quote_document(
            platform="wechat",
            source_group_key="wechat:g-replay-mixed",
            chat_id="g-replay-mixed",
            chat_name="回放混合校验群",
            message_id="msg-replay-mixed-origin",
            source_name="报价员",
            sender_id="seller-replay",
            raw_text="origin replay mixed text",
            message_time="2026-04-14 15:00:00",
            parser_template="group-parser",
            parser_version="group-parser-v1",
            confidence=0.0,
            parse_status="exception",
        )
        exception_id = self.db.record_quote_exception_unless_suppressed(
            quote_document_id=quote_document_id,
            platform="wechat",
            source_group_key="wechat:g-replay-mixed",
            chat_id="g-replay-mixed",
            chat_name="回放混合校验群",
            source_name="报价员",
            sender_id="seller-replay",
            reason="strict_match_failed",
            source_line="origin replay mixed text",
            raw_text="origin replay mixed text",
            message_time="2026-04-14 15:00:00",
            parser_template="group-parser",
            parser_version="group-parser-v1",
            confidence=0.0,
        )
        self.assertGreater(int(exception_id), 0)
        exc_row = self.db.conn.execute(
            """
            SELECT *
            FROM quote_parse_exceptions
            WHERE id = ?
            """,
            (int(exception_id),),
        ).fetchone()
        self.assertIsNotNone(exc_row)
        assert exc_row is not None

        def build_replay_candidate(*, message_id: str, replay_of_quote_document_id: int) -> QuoteCandidateMessage:
            return QuoteCandidateMessage(
                platform="wechat",
                source_group_key="wechat:g-replay-mixed",
                chat_id="g-replay-mixed",
                chat_name="回放混合校验群",
                message_id=message_id,
                source_name="报价员",
                sender_id="seller-replay",
                sender_display="报价员",
                raw_message="patched replay mixed candidate",
                message_time="2026-04-14 15:00:00",
                parser_kind="group-parser",
                parser_template="group-parser",
                parser_version="group-parser-v1",
                confidence=0.99,
                parse_status="parsed",
                message_fingerprint="replay-mixed-fingerprint",
                snapshot_hypothesis="unresolved",
                snapshot_hypothesis_reason="phase1-default",
                run_kind="replay",
                replay_of_quote_document_id=replay_of_quote_document_id,
                rows=[
                    QuoteCandidateRow(
                        row_ordinal=1,
                        source_line="US=5.10",
                        source_line_index=0,
                        line_confidence=0.99,
                        normalized_sku_key="Apple|USD|100|横白卡",
                        normalization_status="normalized",
                        row_publishable=False,
                        publishability_basis="parser_prevalidation",
                        restriction_parse_status="parsed",
                        card_type="Apple",
                        country_or_currency="USD",
                        amount_range="100",
                        multiplier=None,
                        form_factor="横白卡",
                        price=5.10,
                        quote_status="active",
                        restriction_text="",
                    ),
                    QuoteCandidateRow(
                        row_ordinal=2,
                        source_line="UK=6.20",
                        source_line_index=1,
                        line_confidence=0.60,
                        normalized_sku_key="Apple|GBP|100|横白卡",
                        normalization_status="normalized",
                        row_publishable=True,
                        publishability_basis="parser_prevalidation",
                        restriction_parse_status="parsed",
                        card_type="Apple",
                        country_or_currency="GBP",
                        amount_range="100",
                        multiplier=None,
                        form_factor="横白卡",
                        price=6.20,
                        quote_status="active",
                        restriction_text="",
                    ),
                    QuoteCandidateRow(
                        row_ordinal=3,
                        source_line="Razer 100=7.10",
                        source_line_index=2,
                        line_confidence=0.97,
                        normalized_sku_key="Razer|USD|100|不限",
                        normalization_status="normalized",
                        row_publishable=True,
                        publishability_basis="parser_prevalidation",
                        restriction_parse_status="parsed",
                        card_type="Razer",
                        country_or_currency="USD",
                        amount_range="100",
                        multiplier=None,
                        form_factor="不限",
                        price=7.10,
                        quote_status="inactive",
                        restriction_text="",
                    ),
                ],
            )

        def _patched_parse_quote_message_to_candidate(**kwargs):
            return build_replay_candidate(
                message_id=str(kwargs["message_id_override"]),
                replay_of_quote_document_id=int(kwargs["replay_of_quote_document_id"]),
            )

        def _patched_parse_quote_message_to_candidate_details(**kwargs):
            candidate = build_replay_candidate(
                message_id=str(kwargs["message_id_override"]),
                replay_of_quote_document_id=int(kwargs["replay_of_quote_document_id"]),
            )
            return candidate, [], []

        with patch(
            "bookkeeping_core.quotes.parse_quote_message_to_candidate",
            side_effect=_patched_parse_quote_message_to_candidate,
        ), patch(
            "bookkeeping_core.quotes._parse_quote_message_to_candidate_details",
            side_effect=_patched_parse_quote_message_to_candidate_details,
        ):
            replay = _replay_latest_quote_document_with_current_template(
                self.db,
                exc_row=dict(exc_row),
                record_exceptions=False,
            )

        self.assertTrue(replay["replayed"])
        self.assertFalse(replay["mutated_active_facts"])
        replay_document_id = int(replay["quote_document_id"])
        validation_run = self.db.get_latest_quote_validation_run(
            quote_document_id=replay_document_id
        )
        self.assertIsNotNone(validation_run)
        assert validation_run is not None
        self.assertEqual(str(validation_run["run_kind"]), "replay")
        self.assertEqual(int(validation_run["publishable_row_count"]), 1)
        self.assertEqual(int(validation_run["rejected_row_count"]), 1)
        self.assertEqual(int(validation_run["held_row_count"]), 1)

        publishable_rows = self.db.list_publishable_quote_candidate_rows(
            quote_document_id=replay_document_id
        )
        self.assertEqual(len(publishable_rows), 1)
        self.assertEqual(str(publishable_rows[0]["source_line"]), "US=5.10")
        self.assertFalse(bool(publishable_rows[0]["row_publishable"]))
        self.assertEqual(str(publishable_rows[0]["decision_basis"]), "business_validation")

        quote_price_row_count = self._count_rows(
            "quote_price_rows",
            "WHERE quote_document_id = ?",
            (replay_document_id,),
        )
        self.assertEqual(quote_price_row_count, 0)

    def test_quote_exception_harvest_save_keeps_exception_open_when_replay_still_fails(self) -> None:
        old_password = os.environ.get("QUOTE_ADMIN_PASSWORD")
        os.environ["QUOTE_ADMIN_PASSWORD"] = "harvest-secret"
        try:
            self.db.set_group(
                platform="wechat",
                group_key="wechat:g-harvest-replay-fail",
                chat_id="g-harvest-replay-fail",
                chat_name="收编群-重放失败",
                group_num=5,
            )
            quote_document_id = self.db.record_quote_document(
                platform="wechat",
                source_group_key="wechat:g-harvest-replay-fail",
                chat_id="g-harvest-replay-fail",
                chat_name="收编群-重放失败",
                message_id="msg-harvest-replay-fail",
                source_name="报价员",
                sender_id="u-harvest",
                raw_text="Apple USA\n10-50=5.20",
                message_time="2026-04-08 11:00:00",
                parser_template="data-engine",
                parser_version="data-engine-v1",
                confidence=0.0,
                parse_status="empty",
            )
            exception_id = self.db.record_quote_exception(
                quote_document_id=quote_document_id,
                platform="wechat",
                source_group_key="wechat:g-harvest-replay-fail",
                chat_id="g-harvest-replay-fail",
                chat_name="收编群-重放失败",
                source_name="报价员",
                sender_id="u-harvest",
                reason="strict_match_failed",
                source_line="10-50=5.20",
                raw_text="Apple USA\n10-50=5.20",
                message_time="2026-04-08 11:00:00",
                parser_template="data-engine",
                parser_version="data-engine-v1",
                confidence=0.0,
            )

            preview_payload = {
                "exception_id": exception_id,
                "section_start_line": 0,
                "section_end_line": 1,
                "defaults": {
                    "section_label": "Apple USA",
                    "priority": 10,
                    "card_type": "it",
                    "country_or_currency": "us",
                    "form_factor": "card",
                },
                "rows": [
                    {"source_line_index": 1, "amount": "10-50", "price": "5.20"},
                ],
                "ignored_line_indexes": [],
            }
            status, preview = self._request(
                "POST",
                "/api/quotes/exceptions/harvest-preview",
                preview_payload,
            )
            self.assertEqual(status, 200)
            self.assertTrue(preview["can_save"])
            self.assertTrue(preview["is_latest_for_group"])

            with patch(
                "bookkeeping_web.app._replay_latest_quote_document_with_current_template"
            ) as replay_mock:
                replay_mock.return_value = {
                    "replayed": True,
                    "rows": 1,
                    "exceptions": 1,
                    "quote_document_id": quote_document_id + 1,
                    "remaining_lines": ["10-50=5.20"],
                    "mutated_active_facts": False,
                }
                status, saved = self._request(
                    "POST",
                    "/api/quotes/exceptions/harvest-save",
                    {**preview_payload, "admin_password": "harvest-secret"},
                )

            self.assertEqual(status, 200)
            self.assertTrue(saved["replay"]["replayed"])
            self.assertFalse(saved["resolved_fully"])
            self.assertEqual(saved["remaining_lines"], ["10-50=5.20"])
            replay_mock.assert_called_once()
            self.assertTrue(replay_mock.call_args.kwargs["record_exceptions"])

            exception_row = self.db.get_quote_exception(exception_id=exception_id)
            self.assertEqual(exception_row["resolution_status"], "open")
            self.assertIn("replay_exceptions=1", str(exception_row["resolution_note"]))
            self.assertEqual(str(exception_row["source_line"]), "10-50=5.20")
        finally:
            if old_password is None:
                os.environ.pop("QUOTE_ADMIN_PASSWORD", None)
            else:
                os.environ["QUOTE_ADMIN_PASSWORD"] = old_password

    def test_quote_exception_harvest_save_keeps_same_exception_open_for_remaining_sections(self) -> None:
        old_password = os.environ.get("QUOTE_ADMIN_PASSWORD")
        os.environ["QUOTE_ADMIN_PASSWORD"] = "harvest-secret"
        try:
            self.db.set_group(
                platform="wechat",
                group_key="wechat:g-harvest-mixed",
                chat_id="g-harvest-mixed",
                chat_name="混合收编群",
                group_num=5,
            )
            raw_text = (
                "=======UK快卡=======\n"
                "UK图密 20-250=6.0（5倍数）\n"
                "UK图密100-500=6.35（50倍数）\n"
                "#连卡先问，不要直接发！！\n"
                "#35分钟内赎回会撤账\n"
                "================\n"
                "【iTunes CAD】---快加\n"
                "3.9收100-300  50倍数\n"
                "#40分钟赎回不结算\n"
                "#连卡有卡先问不要直接发\n"
                "================\n"
                "英国6.55收100-250卡图\n"
                "法国5.4收50-250卡图\n"
                "#以上国家50倍数其他面值问#\n"
                "-------不限购国家--------\n"
                "墨西哥=0.265（500+）\n"
                "葡/希/卢5.05收50倍数图密\n"
                "#发前问#代码纸质问#连卡问\n"
            )
            quote_document_id = self.db.record_quote_document(
                platform="wechat",
                source_group_key="wechat:g-harvest-mixed",
                chat_id="g-harvest-mixed",
                chat_name="混合收编群",
                message_id="msg-harvest-mixed",
                source_name="报价员",
                sender_id="u-harvest-mixed",
                raw_text=raw_text,
                message_time="2026-04-11 10:00:00",
                parser_template="data-engine",
                parser_version="data-engine-v1",
                confidence=0.0,
                parse_status="empty",
            )
            exception_id = self.db.record_quote_exception(
                quote_document_id=quote_document_id,
                platform="wechat",
                source_group_key="wechat:g-harvest-mixed",
                chat_id="g-harvest-mixed",
                chat_name="混合收编群",
                source_name="报价员",
                sender_id="u-harvest-mixed",
                reason="strict_match_failed",
                source_line=(
                    "UK图密 20-250=6.0（5倍数）\n"
                    "UK图密100-500=6.35（50倍数）\n"
                    "3.9收100-300  50倍数\n"
                    "英国6.55收100-250卡图\n"
                    "法国5.4收50-250卡图\n"
                    "墨西哥=0.265（500+）\n"
                    "葡/希/卢5.05收50倍数图密"
                ),
                raw_text=raw_text,
                message_time="2026-04-11 10:00:00",
                parser_template="data-engine",
                parser_version="data-engine-v1",
                confidence=0.0,
            )

            first_preview_payload = {
                "exception_id": exception_id,
                "section_start_line": 0,
                "section_end_line": 5,
                "defaults": {
                    "section_label": "UK快卡",
                    "priority": 10,
                    "card_type": "Apple",
                    "country_or_currency": "GBP",
                    "form_factor": "card",
                },
                "rows": [
                    {"source_line_index": 1, "amount": "20-250", "price": "6.0"},
                    {"source_line_index": 2, "amount": "100-500", "price": "6.35"},
                ],
                "ignored_line_indexes": [],
            }
            status, first_preview = self._request(
                "POST",
                "/api/quotes/exceptions/harvest-preview",
                first_preview_payload,
            )
            self.assertEqual(status, 200)
            self.assertTrue(first_preview["can_save"])
            self.assertEqual(
                [item["line"] for item in first_preview["restriction_candidates"]],
                ["#连卡先问,不要直接发！！", "#35分钟内赎回会撤账"],
            )

            status, first_saved = self._request(
                "POST",
                "/api/quotes/exceptions/harvest-save",
                {**first_preview_payload, "admin_password": "harvest-secret"},
            )
            self.assertEqual(status, 200)
            self.assertTrue(first_saved["saved"])
            self.assertFalse(first_saved["resolved_fully"])
            self.assertEqual(
                first_saved["restriction_lines_attached"],
                ["#连卡先问,不要直接发！！", "#35分钟内赎回会撤账"],
            )
            self.assertIn("3.9收100-300 50倍数", first_saved["remaining_lines"])
            self.assertIn("英国6.55收100-250卡图", first_saved["remaining_lines"])
            self.assertIn("葡/希/卢5.05收50倍数图密", first_saved["remaining_lines"])

            exception_row = self.db.get_quote_exception(exception_id=exception_id)
            self.assertEqual(exception_row["resolution_status"], "open")
            self.assertIn("英国6.55收100-250卡图", exception_row["source_line"])
            self.assertNotIn("UK图密 20-250=6.0", exception_row["source_line"])

            second_preview_payload = {
                "exception_id": exception_id,
                "section_start_line": 6,
                "section_end_line": 10,
                "defaults": {
                    "section_label": "iTunes CAD",
                    "priority": 20,
                    "card_type": "Apple",
                    "country_or_currency": "CAD",
                    "form_factor": "card",
                },
                "rows": [
                    {"source_line_index": 7, "amount": "100-300", "price": "3.9"},
                ],
                "ignored_line_indexes": [],
            }
            status, second_saved = self._request(
                "POST",
                "/api/quotes/exceptions/harvest-save",
                {**second_preview_payload, "admin_password": "harvest-secret"},
            )
            self.assertEqual(status, 200)
            self.assertTrue(second_saved["saved"])
            self.assertFalse(second_saved["resolved_fully"])
            self.assertIn("英国6.55收100-250卡图", second_saved["remaining_lines"])
            self.assertIn("墨西哥=0.265(500+)", second_saved["remaining_lines"])
            self.assertIn("葡/希/卢5.05收50倍数图密", second_saved["remaining_lines"])
            self.assertNotIn("3.9收100-300 50倍数", second_saved["remaining_lines"])

            status, board = self._request("GET", "/api/quotes/board")
            self.assertEqual(status, 200)
            self.assertEqual(board["rows"], [])
        finally:
            if old_password is None:
                os.environ.pop("QUOTE_ADMIN_PASSWORD", None)
            else:
                os.environ["QUOTE_ADMIN_PASSWORD"] = old_password

    def test_quote_exception_harvest_save_does_not_advance_unselected_same_shape_section(self) -> None:
        old_password = os.environ.get("QUOTE_ADMIN_PASSWORD")
        os.environ["QUOTE_ADMIN_PASSWORD"] = "harvest-secret"
        try:
            self.db.set_group(
                platform="wechat",
                group_key="wechat:g-harvest-same-shape",
                chat_id="g-harvest-same-shape",
                chat_name="同骨架混合群",
                group_num=5,
            )
            raw_text = (
                "=======UK快卡=======\n"
                "6.0收20-250\n"
                "6.35收100-500\n"
                "================\n"
                "=======CAD快加=======\n"
                "3.9收20-250\n"
                "4.1收100-500\n"
                "================\n"
            )
            quote_document_id = self.db.record_quote_document(
                platform="wechat",
                source_group_key="wechat:g-harvest-same-shape",
                chat_id="g-harvest-same-shape",
                chat_name="同骨架混合群",
                message_id="msg-harvest-same-shape",
                source_name="报价员",
                sender_id="u-harvest-same-shape",
                raw_text=raw_text,
                message_time="2026-04-11 11:00:00",
                parser_template="data-engine",
                parser_version="data-engine-v1",
                confidence=0.0,
                parse_status="empty",
            )
            exception_id = self.db.record_quote_exception(
                quote_document_id=quote_document_id,
                platform="wechat",
                source_group_key="wechat:g-harvest-same-shape",
                chat_id="g-harvest-same-shape",
                chat_name="同骨架混合群",
                source_name="报价员",
                sender_id="u-harvest-same-shape",
                reason="strict_match_failed",
                source_line="6.0收20-250\n6.35收100-500\n3.9收20-250\n4.1收100-500",
                raw_text=raw_text,
                message_time="2026-04-11 11:00:00",
                parser_template="data-engine",
                parser_version="data-engine-v1",
                confidence=0.0,
            )
            payload = {
                "exception_id": exception_id,
                "section_start_line": 0,
                "section_end_line": 3,
                "defaults": {
                    "section_label": "UK快卡",
                    "priority": 10,
                    "card_type": "Apple",
                    "country_or_currency": "GBP",
                    "form_factor": "card",
                },
                "rows": [
                    {"source_line_index": 1, "amount": "20-250", "price": "6.0"},
                    {"source_line_index": 2, "amount": "100-500", "price": "6.35"},
                ],
                "ignored_line_indexes": [],
            }
            status, saved = self._request(
                "POST",
                "/api/quotes/exceptions/harvest-save",
                {**payload, "admin_password": "harvest-secret"},
            )
            self.assertEqual(status, 200)
            self.assertTrue(saved["saved"])
            self.assertFalse(saved["resolved_fully"])
            self.assertEqual(saved["saved_line_indexes"], [0, 1, 2, 3])
            self.assertIn("3.9收20-250", saved["remaining_lines"])
            self.assertIn("4.1收100-500", saved["remaining_lines"])

            exception_row = self.db.get_quote_exception(exception_id=exception_id)
            self.assertEqual(exception_row["resolution_status"], "open")
            self.assertEqual(
                exception_row["source_line"],
                "3.9收20-250\n4.1收100-500",
            )

            status, board = self._request("GET", "/api/quotes/board")
            self.assertEqual(status, 200)
            self.assertEqual(board["rows"], [])
        finally:
            if old_password is None:
                os.environ.pop("QUOTE_ADMIN_PASSWORD", None)
            else:
                os.environ["QUOTE_ADMIN_PASSWORD"] = old_password

    def test_quote_exception_harvest_multi_section_final_save_creates_replay_candidate_only(
        self,
    ) -> None:
        old_password = os.environ.get("QUOTE_ADMIN_PASSWORD")
        os.environ["QUOTE_ADMIN_PASSWORD"] = "harvest-secret"
        try:
            self.db.set_group(
                platform="wechat",
                group_key="wechat:g-harvest-finalize",
                chat_id="g-harvest-finalize",
                chat_name="多段完成群",
                group_num=5,
            )
            raw_text = (
                "=======UK快卡=======\n"
                "6.0收20-250\n"
                "6.35收100-500\n"
                "================\n"
                "【iTunes CAD】\n"
                "3.9收20-250\n"
                "4.1收100-500\n"
                "================\n"
            )
            quote_document_id = self.db.record_quote_document(
                platform="wechat",
                source_group_key="wechat:g-harvest-finalize",
                chat_id="g-harvest-finalize",
                chat_name="多段完成群",
                message_id="msg-harvest-finalize",
                source_name="报价员",
                sender_id="u-harvest-finalize",
                raw_text=raw_text,
                message_time="2026-04-11 12:00:00",
                parser_template="data-engine",
                parser_version="data-engine-v1",
                confidence=0.0,
                parse_status="empty",
            )
            exception_id = self.db.record_quote_exception(
                quote_document_id=quote_document_id,
                platform="wechat",
                source_group_key="wechat:g-harvest-finalize",
                chat_id="g-harvest-finalize",
                chat_name="多段完成群",
                source_name="报价员",
                sender_id="u-harvest-finalize",
                reason="strict_match_failed",
                source_line="6.0收20-250\n6.35收100-500\n3.9收20-250\n4.1收100-500",
                raw_text=raw_text,
                message_time="2026-04-11 12:00:00",
                parser_template="data-engine",
                parser_version="data-engine-v1",
                confidence=0.0,
            )

            first_payload = {
                "exception_id": exception_id,
                "section_start_line": 0,
                "section_end_line": 3,
                "defaults": {
                    "section_label": "UK快卡",
                    "priority": 10,
                    "card_type": "Apple",
                    "country_or_currency": "GBP",
                    "form_factor": "card",
                },
                "rows": [
                    {"source_line_index": 1, "amount": "20-250", "price": "6.0"},
                    {"source_line_index": 2, "amount": "100-500", "price": "6.35"},
                ],
                "ignored_line_indexes": [],
            }
            status, first_saved = self._request(
                "POST",
                "/api/quotes/exceptions/harvest-save",
                {**first_payload, "admin_password": "harvest-secret"},
            )
            self.assertEqual(status, 200)
            self.assertFalse(first_saved["resolved_fully"])
            self.assertFalse(first_saved["replay"]["replayed"])

            second_payload = {
                "exception_id": exception_id,
                "section_start_line": 4,
                "section_end_line": 7,
                "defaults": {
                    "section_label": "iTunes CAD",
                    "priority": 20,
                    "card_type": "Apple",
                    "country_or_currency": "CAD",
                    "form_factor": "card",
                },
                "rows": [
                    {"source_line_index": 5, "amount": "20-250", "price": "3.9"},
                    {"source_line_index": 6, "amount": "100-500", "price": "4.1"},
                ],
                "ignored_line_indexes": [],
            }
            status, second_saved = self._request(
                "POST",
                "/api/quotes/exceptions/harvest-save",
                {**second_payload, "admin_password": "harvest-secret"},
            )
            self.assertEqual(status, 200)
            self.assertTrue(second_saved["resolved_fully"])
            self.assertTrue(second_saved["replay"]["replayed"])
            self.assertFalse(second_saved["replay"]["mutated_active_facts"])
            self.assertEqual(second_saved["replay"]["rows"], 4)
            self.assertEqual(second_saved["remaining_lines"], [])
            replay_document_id = int(second_saved["replay"]["quote_document_id"])
            self.assertNotEqual(replay_document_id, quote_document_id)
            replay_document = self._get_quote_document_by_id(replay_document_id)
            self.assertIsNotNone(replay_document)
            self.assertEqual(replay_document["run_kind"], "replay")
            self.assertEqual(replay_document["replay_of_quote_document_id"], quote_document_id)
            replay_candidate_rows = self.db.list_quote_candidate_rows(
                quote_document_id=replay_document_id
            )
            self.assertEqual(len(replay_candidate_rows), 4)

            status, board = self._request("GET", "/api/quotes/board")
            self.assertEqual(status, 200)
            self.assertEqual(board["rows"], [])
        finally:
            if old_password is None:
                os.environ.pop("QUOTE_ADMIN_PASSWORD", None)
            else:
                os.environ["QUOTE_ADMIN_PASSWORD"] = old_password

    def test_quote_exception_harvest_save_can_append_missing_section_after_resolved_with_replay_candidates(
        self,
    ) -> None:
        old_password = os.environ.get("QUOTE_ADMIN_PASSWORD")
        os.environ["QUOTE_ADMIN_PASSWORD"] = "harvest-secret"
        try:
            self.db.set_group(
                platform="wechat",
                group_key="wechat:g-harvest-append-after-resolved",
                chat_id="g-harvest-append-after-resolved",
                chat_name="补漏群",
                group_num=5,
            )
            raw_text = (
                "=======UK快卡=======\n"
                "6.0收20-250\n"
                "6.35收100-500\n"
                "================\n"
                "【iTunes CAD】\n"
                "3.9收15-90\n"
                "================\n"
            )
            quote_document_id = self.db.record_quote_document(
                platform="wechat",
                source_group_key="wechat:g-harvest-append-after-resolved",
                chat_id="g-harvest-append-after-resolved",
                chat_name="补漏群",
                message_id="msg-harvest-append-after-resolved",
                source_name="报价员",
                sender_id="u-harvest-append-after-resolved",
                raw_text=raw_text,
                message_time="2026-04-11 13:00:00",
                parser_template="data-engine",
                parser_version="data-engine-v1",
                confidence=0.0,
                parse_status="empty",
            )
            exception_id = self.db.record_quote_exception(
                quote_document_id=quote_document_id,
                platform="wechat",
                source_group_key="wechat:g-harvest-append-after-resolved",
                chat_id="g-harvest-append-after-resolved",
                chat_name="补漏群",
                source_name="报价员",
                sender_id="u-harvest-append-after-resolved",
                reason="strict_match_failed",
                source_line="6.0收20-250\n6.35收100-500",
                raw_text=raw_text,
                message_time="2026-04-11 13:00:00",
                parser_template="data-engine",
                parser_version="data-engine-v1",
                confidence=0.0,
            )

            first_payload = {
                "exception_id": exception_id,
                "section_start_line": 0,
                "section_end_line": 3,
                "defaults": {
                    "section_label": "UK快卡",
                    "priority": 10,
                    "card_type": "Apple",
                    "country_or_currency": "GBP",
                    "form_factor": "card",
                },
                "rows": [
                    {"source_line_index": 1, "amount": "20-250", "price": "6.0"},
                    {"source_line_index": 2, "amount": "100-500", "price": "6.35"},
                ],
                "ignored_line_indexes": [],
            }
            status, first_saved = self._request(
                "POST",
                "/api/quotes/exceptions/harvest-save",
                {**first_payload, "admin_password": "harvest-secret"},
            )
            self.assertEqual(status, 200)
            self.assertFalse(first_saved["resolved_fully"])
            self.assertTrue(first_saved["replay"]["replayed"])
            self.assertFalse(first_saved["replay"]["mutated_active_facts"])
            self.assertEqual(first_saved["replay"]["rows"], 2)
            self.assertGreater(first_saved["replay"]["exceptions"], 0)
            first_replay_document_id = int(first_saved["replay"]["quote_document_id"])
            self.assertNotEqual(first_replay_document_id, quote_document_id)
            first_replay_document = self._get_quote_document_by_id(first_replay_document_id)
            self.assertIsNotNone(first_replay_document)
            self.assertEqual(first_replay_document["run_kind"], "replay")
            self.assertEqual(
                first_replay_document["replay_of_quote_document_id"],
                quote_document_id,
            )
            first_replay_candidate_rows = self.db.list_quote_candidate_rows(
                quote_document_id=first_replay_document_id
            )
            self.assertEqual(len(first_replay_candidate_rows), 2)
            exception_row_after_first_save = self.db.get_quote_exception(
                exception_id=exception_id
            )
            self.assertEqual(exception_row_after_first_save["resolution_status"], "open")

            second_payload = {
                "exception_id": exception_id,
                "section_start_line": 4,
                "section_end_line": 6,
                "defaults": {
                    "section_label": "iTunes CAD",
                    "priority": 20,
                    "card_type": "Apple",
                    "country_or_currency": "CAD",
                    "form_factor": "code",
                },
                "rows": [
                    {"source_line_index": 5, "amount": "15-90", "price": "3.9"},
                ],
                "ignored_line_indexes": [],
            }
            status, second_saved = self._request(
                "POST",
                "/api/quotes/exceptions/harvest-save",
                {**second_payload, "admin_password": "harvest-secret"},
            )
            self.assertEqual(status, 200)
            self.assertTrue(second_saved["saved"])
            self.assertTrue(second_saved["resolved_fully"])
            self.assertTrue(second_saved["replay"]["replayed"])
            self.assertFalse(second_saved["replay"]["mutated_active_facts"])
            self.assertEqual(second_saved["replay"]["rows"], 3)
            second_replay_document_id = int(second_saved["replay"]["quote_document_id"])
            self.assertNotEqual(second_replay_document_id, quote_document_id)
            replay_document = self._get_quote_document_by_id(second_replay_document_id)
            self.assertIsNotNone(replay_document)
            self.assertEqual(replay_document["run_kind"], "replay")
            self.assertEqual(replay_document["replay_of_quote_document_id"], quote_document_id)
            replay_candidate_rows = self.db.list_quote_candidate_rows(
                quote_document_id=second_replay_document_id
            )
            self.assertEqual(len(replay_candidate_rows), 3)

            status, board = self._request("GET", "/api/quotes/board")
            self.assertEqual(status, 200)
            self.assertEqual(board["rows"], [])
        finally:
            if old_password is None:
                os.environ.pop("QUOTE_ADMIN_PASSWORD", None)
            else:
                os.environ["QUOTE_ADMIN_PASSWORD"] = old_password

    def test_quote_exception_result_preview_and_save(self) -> None:
        old_password = os.environ.get("QUOTE_ADMIN_PASSWORD")
        os.environ["QUOTE_ADMIN_PASSWORD"] = "result-secret"
        try:
            self.db.set_group(
                platform="wechat",
                group_key="wechat:g-result",
                chat_id="g-result",
                chat_name="整理群",
                group_num=5,
            )
            quote_document_id = self.db.record_quote_document(
                platform="wechat",
                source_group_key="wechat:g-result",
                chat_id="g-result",
                chat_name="整理群",
                message_id="msg-result",
                source_name="报价员",
                sender_id="u-result",
                raw_text=(
                    "【 影子steam价格表】\n"
                    "美金USD :5.20\n"
                    "欧元EUR :6.00\n"
                    "英镑GBP :6.85\n"
                    "加元CAD :3.75\n"
                    "澳元AUD :3.65\n"
                    "新西兰NZD ：3.05\n"
                    "瑞士CHF ：6.40\n"
                    "波兰PLN  :1.39\n"
                    "*\n"
                    "报其他国家按到账美金*5.20\n"
                    "【影子】\n"
                    "=== 雷蛇/Razer ===\n"
                    "美  USD ：5.78\n"
                    "新 加 坡 ：4.32\n"
                    "加 拿 大 ：4.20\n"
                    "澳大利亚：4.07\n"
                    "新西兰   ：3.25\n"
                    "马来西亚：1.48\n"
                    "推荐客户有🧧（200-2000)\n"
                    "上不封顶"
                ),
                message_time="2026-04-08 10:00:00",
                parser_template="data-engine",
                parser_version="data-engine-v1",
                confidence=0.0,
                parse_status="empty",
            )
            exception_id = self.db.record_quote_exception(
                quote_document_id=quote_document_id,
                platform="wechat",
                source_group_key="wechat:g-result",
                chat_id="g-result",
                chat_name="整理群",
                source_name="报价员",
                sender_id="u-result",
                reason="strict_match_failed",
                source_line="美金USD:5.20\n欧元EUR:6.00\n美 USD:5.78",
                raw_text=(
                    "【 影子steam价格表】\n"
                    "美金USD :5.20\n"
                    "欧元EUR :6.00\n"
                    "英镑GBP :6.85\n"
                    "加元CAD :3.75\n"
                    "澳元AUD :3.65\n"
                    "新西兰NZD ：3.05\n"
                    "瑞士CHF ：6.40\n"
                    "波兰PLN  :1.39\n"
                    "*\n"
                    "报其他国家按到账美金*5.20\n"
                    "【影子】\n"
                    "=== 雷蛇/Razer ===\n"
                    "美  USD ：5.78\n"
                    "新 加 坡 ：4.32\n"
                    "加 拿 大 ：4.20\n"
                    "澳大利亚：4.07\n"
                    "新西兰   ：3.25\n"
                    "马来西亚：1.48\n"
                    "推荐客户有🧧（200-2000)\n"
                    "上不封顶"
                ),
                message_time="2026-04-08 10:00:00",
                parser_template="data-engine",
                parser_version="data-engine-v1",
                confidence=0.0,
            )

            result_template_text = (
                "[默认]\n"
                "形态=card\n"
                "\n"
                "[Steam]\n"
                "USD=5.20\n"
                "EUR=6.00\n"
                "GBP=6.85\n"
                "CAD=3.75\n"
                "AUD=3.65\n"
                "NZD=3.05\n"
                "CHF=6.40\n"
                "PLN=1.39\n"
                "\n"
                "[Razer]\n"
                "USD=5.78\n"
                "SGD=4.32\n"
                "CAD=4.20\n"
                "AUD=4.07\n"
                "NZD=3.25\n"
                "MYR=1.48\n"
            )

            status, preview = self._request(
                "POST",
                "/api/quotes/exceptions/result-preview",
                {
                    "exception_id": exception_id,
                    "result_template_text": result_template_text,
                },
            )
            self.assertEqual(status, 200)
            self.assertTrue(preview["can_save"])
            self.assertEqual(len(preview["preview_rows"]), 14)
            self.assertEqual(len(preview["derived_sections"]), 2)
            self.assertTrue(preview["strict_replay_ok"])
            self.assertTrue(any(item == "报其他国家按到账美金*5.20" for item in preview["notes"]))

            status, saved = self._request(
                "POST",
                "/api/quotes/exceptions/result-save",
                {
                    "exception_id": exception_id,
                    "result_template_text": result_template_text,
                    "admin_password": "result-secret",
                },
            )
            self.assertEqual(status, 200)
            self.assertTrue(saved["saved"])
            self.assertFalse(saved["applied"])
            self.assertTrue(saved["strict_replay_ok"])

            profile = self.db.get_quote_group_profile(platform="wechat", chat_id="g-result")
            self.assertEqual(profile["parser_template"], "group-parser")
            self.assertIn('"version": "group-parser-v1"', profile["template_config"])

            status, board = self._request("GET", "/api/quotes/board")
            self.assertEqual(status, 200)
            self.assertEqual(len(board["rows"]), 0)
        finally:
            if old_password is None:
                os.environ.pop("QUOTE_ADMIN_PASSWORD", None)
            else:
                os.environ["QUOTE_ADMIN_PASSWORD"] = old_password

    def test_quote_exception_result_preview_and_save_supports_bracket_quote_cards(self) -> None:
        from bookkeeping_core.template_engine import TemplateConfig, parse_message_with_template

        old_password = os.environ.get("QUOTE_ADMIN_PASSWORD")
        os.environ["QUOTE_ADMIN_PASSWORD"] = "result-secret"
        try:
            self.db.set_group(
                platform="wechat",
                group_key="wechat:g-bracket-result",
                chat_id="g-bracket-result",
                chat_name="Steam蒸汽",
                group_num=5,
            )
            raw_text = (
                "【Steam蒸汽】\n"
                "USD-10-200【5.03】\n"
                "UK【6.75】  EUR【5.89】\n"
                "CAD【3.62】 AUD【3.54】\n"
                "NZD【2.92】CHF【6.37】\n"
                "其余国家按到账美金*5.02\n"
                "====================\n"
                "【苹果-快加/快刷】\n"
                "US-300-500   白卡   【5.38】 \n"
                "US-200-450   白卡   【5.38】 \n"
                "US-100/150   白卡   【5.38】   \n"
                "US-20-90       白卡   【5.2】 5倍数 \n"
                "US-25-145    卡密    【5.11】 5倍数\n"
                "※刷不过 退卡  竖卡不要※\n"
            )
            quote_document_id = self.db.record_quote_document(
                platform="wechat",
                source_group_key="wechat:g-bracket-result",
                chat_id="g-bracket-result",
                chat_name="Steam蒸汽",
                message_id="msg-bracket-result",
                source_name="报价员",
                sender_id="u-bracket-result",
                raw_text=raw_text,
                message_time="2026-04-12 10:00:00",
                parser_template="data-engine",
                parser_version="data-engine-v1",
                confidence=0.0,
                parse_status="empty",
            )
            exception_id = self.db.record_quote_exception(
                quote_document_id=quote_document_id,
                platform="wechat",
                source_group_key="wechat:g-bracket-result",
                chat_id="g-bracket-result",
                chat_name="Steam蒸汽",
                source_name="报价员",
                sender_id="u-bracket-result",
                reason="strict_match_failed",
                source_line="USD-10-200【5.03】\nUK【6.75】  EUR【5.89】\nUS-300-500 白卡 【5.38】",
                raw_text=raw_text,
                message_time="2026-04-12 10:00:00",
                parser_template="data-engine",
                parser_version="data-engine-v1",
                confidence=0.0,
            )

            result_template_text = (
                "[默认]\n"
                "国家 / 币种=USD\n"
                "形态=不限\n"
                "\n"
                "[Steam]\n"
                "10-200=5.03\n"
                "GBP=6.75\n"
                "EUR=5.89\n"
                "CAD=3.62\n"
                "AUD=3.54\n"
                "NZD=2.92\n"
                "CHF=6.37\n"
                "\n"
                "[默认]\n"
                "国家 / 币种=USD\n"
                "形态=横白卡\n"
                "\n"
                "[Apple]\n"
                "300-500=5.38\n"
                "200-450=5.38\n"
                "100/150=5.38\n"
                "20-90=5.2\n"
                "\n"
                "[默认]\n"
                "国家 / 币种=USD\n"
                "形态=代码\n"
                "\n"
                "[Apple]\n"
                "25-145=5.11\n"
                "\n"
                "[说明]\n"
                "其余国家按到账美金*5.02\n"
                "刷不过退卡，竖卡不要\n"
            )

            status, preview = self._request(
                "POST",
                "/api/quotes/exceptions/result-preview",
                {
                    "exception_id": exception_id,
                    "result_template_text": result_template_text,
                },
            )
            self.assertEqual(status, 200)
            self.assertTrue(preview["can_save"])
            self.assertEqual(len(preview["preview_rows"]), 12)
            self.assertEqual(len(preview["derived_sections"]), 3)
            self.assertTrue(preview["strict_replay_ok"])
            self.assertTrue(any(item == "其余国家按到账美金*5.02" for item in preview["notes"]))

            status, saved = self._request(
                "POST",
                "/api/quotes/exceptions/result-save",
                {
                    "exception_id": exception_id,
                    "result_template_text": result_template_text,
                    "admin_password": "result-secret",
                },
            )
            self.assertEqual(status, 200)
            self.assertTrue(saved["saved"])
            self.assertTrue(saved["strict_replay_ok"])

            profile = self.db.get_quote_group_profile(platform="wechat", chat_id="g-bracket-result")
            self.assertEqual(profile["parser_template"], "group-parser")
            template = TemplateConfig.from_json(str(profile["template_config"] or ""))
            parsed = parse_message_with_template(
                raw_text,
                template,
                platform="wechat",
                chat_id="g-bracket-result",
                chat_name="Steam蒸汽",
                message_id="msg-bracket-result",
                source_name="报价员",
                sender_id="u-bracket-result",
                source_group_key="wechat:g-bracket-result",
                message_time="2026-04-12 10:00:00",
            )
            self.assertEqual(len(parsed.rows), 12)
            self.assertFalse(parsed.exceptions)
            self.assertTrue(any(row.card_type == "Steam" and row.country_or_currency == "GBP" for row in parsed.rows))
            self.assertTrue(
                any(
                    row.card_type == "Apple"
                    and row.amount_range == "100-150"
                    and row.form_factor == "横白卡"
                    for row in parsed.rows
                )
            )
            self.assertTrue(
                any(
                    row.card_type == "Apple"
                    and row.amount_range == "25-145"
                    and row.form_factor == "代码"
                    for row in parsed.rows
                )
            )
        finally:
            if old_password is None:
                os.environ.pop("QUOTE_ADMIN_PASSWORD", None)
            else:
                os.environ["QUOTE_ADMIN_PASSWORD"] = old_password

    def test_quote_exception_result_preview_uses_chat_name_card_type_fallback(self) -> None:
        self.db.set_group(
            platform="wechat",
            group_key="wechat:g-steam-fallback",
            chat_id="g-steam-fallback",
            chat_name="Steam 夜班群",
            group_num=6,
        )
        quote_document_id = self.db.record_quote_document(
            platform="wechat",
            source_group_key="wechat:g-steam-fallback",
            chat_id="g-steam-fallback",
            chat_name="Steam 夜班群",
            message_id="msg-steam-fallback",
            source_name="报价员",
            sender_id="u-steam-fallback",
            raw_text=(
                "#晚班更新\n"
                "US\n"
                "10-195=5.25（5倍数）\n"
                "----------------------------\n"
                "50=5.3\n"
                "100/150=5.43\n"
                "200- 450=5.44（50倍数）\n"
                "300/400/500=5.45\n"
                "【2- 8分钟反馈】\n"
                "【有扫卡记录的提醒我下。】\n"
                "------------------------------\n"
                "\n"
                "wovxteqeox"
            ),
            message_time="2026-04-11 02:00:00",
            parser_template="data-engine",
            parser_version="data-engine-v1",
            confidence=0.0,
            parse_status="empty",
        )
        exception_id = self.db.record_quote_exception(
            quote_document_id=quote_document_id,
            platform="wechat",
            source_group_key="wechat:g-steam-fallback",
            chat_id="g-steam-fallback",
            chat_name="Steam 夜班群",
            source_name="报价员",
            sender_id="u-steam-fallback",
            reason="strict_match_failed",
            source_line="10-195=5.25\n50=5.3\n100/150=5.43",
            raw_text=(
                "#晚班更新\n"
                "US\n"
                "10-195=5.25（5倍数）\n"
                "----------------------------\n"
                "50=5.3\n"
                "100/150=5.43\n"
                "200- 450=5.44（50倍数）\n"
                "300/400/500=5.45\n"
                "【2- 8分钟反馈】\n"
                "【有扫卡记录的提醒我下。】\n"
                "------------------------------\n"
                "\n"
                "wovxteqeox"
            ),
            message_time="2026-04-11 02:00:00",
            parser_template="data-engine",
            parser_version="data-engine-v1",
            confidence=0.0,
        )

        status, preview = self._request(
            "POST",
            "/api/quotes/exceptions/result-preview",
            {
                "exception_id": exception_id,
                "result_template_text": (
                    "[默认]\n"
                    "国家 / 币种=USD\n"
                    "形态=横白卡\n"
                    "\n"
                    "[Steam]\n"
                    "10-195=5.25\n"
                    "50=5.3\n"
                    "100/150=5.43\n"
                    "200-450=5.44\n"
                    "300/400/500=5.45\n"
                ),
            },
        )
        self.assertEqual(status, 200)
        self.assertTrue(preview["can_save"])
        self.assertTrue(any("已按群名“Steam 夜班群”回退" in item for item in preview["warnings"]))
        self.assertTrue(preview["strict_replay_ok"])
        self.assertEqual(len(preview["preview_rows"]), 5)
        self.assertTrue(
            any(
                row["amount"] == "200-450"
                and row["price"] == "5.44"
                and row["country_or_currency"] == "USD"
                for row in preview["preview_rows"]
            )
        )

    def test_quote_exception_result_preview_prefers_group_profile_default_card_type(self) -> None:
        self.db.set_group(
            platform="wechat",
            group_key="wechat:g-it-fallback",
            chat_id="g-it-fallback",
            chat_name="C-523【QH-IT-设备组-禁赎回",
            group_num=5,
        )
        self.db.upsert_quote_group_profile(
            platform="wechat",
            chat_id="g-it-fallback",
            chat_name="C-523【QH-IT-设备组-禁赎回",
            default_card_type="Apple",
            default_country_or_currency="USD",
            default_form_factor="不限",
            default_multiplier="",
            parser_template="strict-section-v1",
            stale_after_minutes=30,
            note="",
            template_config='{"version":"strict-section-v1","defaults":{},"sections":[]}',
        )
        quote_document_id = self.db.record_quote_document(
            platform="wechat",
            source_group_key="wechat:g-it-fallback",
            chat_id="g-it-fallback",
            chat_name="C-523【QH-IT-设备组-禁赎回",
            message_id="msg-it-fallback",
            source_name="报价员",
            sender_id="u-it-fallback",
            raw_text=(
                "#US秒刷更新\n"
                "10-195=5.15（5倍数）\n"
                "50=5.3\n"
                "100/150=5.4\n"
                "200-450=5.42（50倍）\n"
            ),
            message_time="2026-04-14 00:57:36",
            parser_template="strict-section",
            parser_version="strict-section-v1",
            confidence=0.0,
            parse_status="empty",
        )
        exception_id = self.db.record_quote_exception(
            quote_document_id=quote_document_id,
            platform="wechat",
            source_group_key="wechat:g-it-fallback",
            chat_id="g-it-fallback",
            chat_name="C-523【QH-IT-设备组-禁赎回",
            source_name="报价员",
            sender_id="u-it-fallback",
            reason="strict_match_failed",
            source_line="10-195=5.15\n50=5.3\n100/150=5.4\n200-450=5.42",
            raw_text=(
                "#US秒刷更新\n"
                "10-195=5.15（5倍数）\n"
                "50=5.3\n"
                "100/150=5.4\n"
                "200-450=5.42（50倍）\n"
            ),
            message_time="2026-04-14 00:57:36",
            parser_template="strict-section",
            parser_version="strict-section-v1",
            confidence=0.0,
        )

        status, preview = self._request(
            "POST",
            "/api/quotes/exceptions/result-preview",
            {
                "exception_id": exception_id,
                "result_template_text": (
                    "[默认]\n"
                    "国家 / 币种=USD\n"
                    "形态=不限\n\n"
                    "[unknown]\n"
                    "10-195=5.15\n"
                    "50=5.3\n"
                    "100/150=5.4\n"
                    "200-450=5.42\n"
                ),
            },
        )
        self.assertEqual(status, 200)
        self.assertTrue(preview["can_save"])
        self.assertTrue(all(row["card_type"] == "Apple" for row in preview["preview_rows"]))

    def test_quote_exception_result_preview_supports_second_defaults_block_for_same_card(self) -> None:
        self.db.set_group(
            platform="wechat",
            group_key="wechat:g-itunes-code",
            chat_id="g-itunes-code",
            chat_name="C-502CH-143-夕希&臻韵IT收卡群",
            group_num=5,
        )
        quote_document_id = self.db.record_quote_document(
            platform="wechat",
            source_group_key="wechat:g-itunes-code",
            chat_id="g-itunes-code",
            chat_name="C-502CH-143-夕希&臻韵IT收卡群",
            message_id="msg-itunes-code",
            source_name="报价员",
            sender_id="u-itunes-code",
            raw_text=(
                "=【#iTunes 快刷】==\n"
                "白25-175=5.2【5倍】快加审图\n"
                "100-150=5.42【50倍】只要稳卡\n"
                "200-450=5.42【50倍】只要稳卡\n"
                "300-400=5.42【100倍】 只要稳卡\n"
                "500=5.42【100倍】 只要稳卡\n"
                "纯代码15-90=5.0【5倍】只要稳卡\n"
                "#快速网单1-5分钟\n"
            ),
            message_time="2026-04-11 03:28:35",
            parser_template="data-engine",
            parser_version="data-engine-v1",
            confidence=0.0,
            parse_status="empty",
        )
        exception_id = self.db.record_quote_exception(
            quote_document_id=quote_document_id,
            platform="wechat",
            source_group_key="wechat:g-itunes-code",
            chat_id="g-itunes-code",
            chat_name="C-502CH-143-夕希&臻韵IT收卡群",
            source_name="报价员",
            sender_id="u-itunes-code",
            reason="strict_match_failed",
            source_line="白25-175=5.2\n纯代码15-90=5.0",
            raw_text=(
                "=【#iTunes 快刷】==\n"
                "白25-175=5.2【5倍】快加审图\n"
                "100-150=5.42【50倍】只要稳卡\n"
                "200-450=5.42【50倍】只要稳卡\n"
                "300-400=5.42【100倍】 只要稳卡\n"
                "500=5.42【100倍】 只要稳卡\n"
                "纯代码15-90=5.0【5倍】只要稳卡\n"
                "#快速网单1-5分钟\n"
            ),
            message_time="2026-04-11 03:28:35",
            parser_template="data-engine",
            parser_version="data-engine-v1",
            confidence=0.0,
        )

        status, preview = self._request(
            "POST",
            "/api/quotes/exceptions/result-preview",
            {
                "exception_id": exception_id,
                "result_template_text": (
                    "[默认]\n"
                    "国家 / 币种=USD\n"
                    "形态=横白卡\n"
                    "\n"
                    "[Apple]\n"
                    "25-175=5.2\n"
                    "100-150=5.42\n"
                    "200-450=5.42\n"
                    "300-400=5.42\n"
                    "500=5.42\n"
                    "\n"
                    "[默认]\n"
                    "国家 / 币种=USD\n"
                    "形态=代码\n"
                    "\n"
                    "[Apple]\n"
                    "15-90=5.0\n"
                ),
            },
        )

        self.assertEqual(status, 200)
        self.assertTrue(preview["can_save"])
        self.assertFalse(preview["errors"])
        self.assertTrue(preview["strict_replay_ok"])
        self.assertEqual(len(preview["derived_sections"]), 2)
        self.assertEqual(preview["derived_sections"][0]["defaults"]["form_factor"], "横白卡")
        self.assertEqual(preview["derived_sections"][1]["defaults"]["form_factor"], "代码")
        code_row = next(
            row for row in preview["preview_rows"] if row["amount"] == "15-90"
        )
        self.assertEqual(code_row["form_factor"], "代码")

    def test_quote_exception_result_save_rejects_fourth_group_parser_skeleton(self) -> None:
        old_password = os.environ.get("QUOTE_ADMIN_PASSWORD")
        os.environ["QUOTE_ADMIN_PASSWORD"] = "limit-secret"
        try:
            self.db.set_group(
                platform="wechat",
                group_key="wechat:g-limit",
                chat_id="g-limit",
                chat_name="骨架上限群",
                group_num=7,
            )
            self.db.upsert_quote_group_profile(
                platform="wechat",
                chat_id="g-limit",
                chat_name="骨架上限群",
                default_card_type="Apple",
                default_country_or_currency="USD",
                default_form_factor="横白卡",
                parser_template="group-parser",
                template_config=json.dumps(
                    {
                        "version": "group-parser-v1",
                        "defaults": {},
                        "sections": [
                            {
                                "id": "section-1",
                                "enabled": True,
                                "priority": 10,
                                "label": "Apple-1",
                                "defaults": {
                                    "card_type": "Apple",
                                    "country_or_currency": "USD",
                                    "form_factor": "横白卡",
                                },
                                "lines": [
                                    {
                                        "kind": "quote",
                                        "pattern": "{amount}={price}",
                                        "outputs": {
                                            "card_type": "Apple",
                                            "country_or_currency": "USD",
                                            "form_factor": "横白卡",
                                            "amount_range": "10-50",
                                        },
                                    }
                                ],
                            },
                            {
                                "id": "section-2",
                                "enabled": True,
                                "priority": 20,
                                "label": "Apple-2",
                                "defaults": {
                                    "card_type": "Apple",
                                    "country_or_currency": "USD",
                                    "form_factor": "横白卡",
                                },
                                "lines": [
                                    {
                                        "kind": "quote",
                                        "pattern": "{amount}={price}",
                                        "outputs": {
                                            "card_type": "Apple",
                                            "country_or_currency": "USD",
                                            "form_factor": "横白卡",
                                            "amount_range": "100-200",
                                        },
                                    }
                                ],
                            },
                            {
                                "id": "section-3",
                                "enabled": True,
                                "priority": 30,
                                "label": "Apple-3",
                                "defaults": {
                                    "card_type": "Apple",
                                    "country_or_currency": "USD",
                                    "form_factor": "横白卡",
                                },
                                "lines": [
                                    {
                                        "kind": "quote",
                                        "pattern": "{amount}={price}",
                                        "outputs": {
                                            "card_type": "Apple",
                                            "country_or_currency": "USD",
                                            "form_factor": "横白卡",
                                            "amount_range": "300-500",
                                        },
                                    }
                                ],
                            },
                        ],
                    },
                    ensure_ascii=False,
                ),
            )
            quote_document_id = self.db.record_quote_document(
                platform="wechat",
                source_group_key="wechat:g-limit",
                chat_id="g-limit",
                chat_name="骨架上限群",
                message_id="msg-limit",
                source_name="报价员",
                sender_id="u-limit",
                raw_text="50=5.3",
                message_time="2026-04-11 03:00:00",
                parser_template="data-engine",
                parser_version="data-engine-v1",
                confidence=0.0,
                parse_status="empty",
            )
            exception_id = self.db.record_quote_exception(
                quote_document_id=quote_document_id,
                platform="wechat",
                source_group_key="wechat:g-limit",
                chat_id="g-limit",
                chat_name="骨架上限群",
                source_name="报价员",
                sender_id="u-limit",
                reason="strict_match_failed",
                source_line="50=5.3",
                raw_text="50=5.3",
                message_time="2026-04-11 03:00:00",
                parser_template="data-engine",
                parser_version="data-engine-v1",
                confidence=0.0,
            )
            status, payload = self._request(
                "POST",
                "/api/quotes/exceptions/result-save",
                {
                    "exception_id": exception_id,
                    "result_template_text": (
                        "[默认]\n"
                        "国家 / 币种=USD\n"
                        "形态=横白卡\n"
                        "\n"
                        "[Apple]\n"
                        "50=5.3\n"
                    ),
                    "admin_password": "limit-secret",
                },
            )
            self.assertEqual(status, 400)
            self.assertIn("3 套骨架上限", payload["error"])
        finally:
            if old_password is None:
                os.environ.pop("QUOTE_ADMIN_PASSWORD", None)
            else:
                os.environ["QUOTE_ADMIN_PASSWORD"] = old_password

    def test_quote_exception_result_save_updates_unique_existing_group_section_at_limit(self) -> None:
        from bookkeeping_web.app import _merge_group_parser_template_config

        existing_raw = json.dumps(
            {
                "version": "group-parser-v1",
                "defaults": {},
                "sections": [
                    {
                        "id": "section-1",
                        "enabled": True,
                        "priority": 10,
                        "label": "Steam",
                        "defaults": {
                            "card_type": "Steam",
                            "country_or_currency": "USD",
                            "form_factor": "不限",
                        },
                        "lines": [
                            {
                                "kind": "quote",
                                "pattern": "USD {amount}={price}",
                                "outputs": {
                                    "card_type": "Steam",
                                    "country_or_currency": "USD",
                                    "form_factor": "不限",
                                    "amount_range": "10-200",
                                },
                            }
                        ],
                    },
                    {
                        "id": "section-2",
                        "enabled": True,
                        "priority": 20,
                        "label": "Apple",
                        "defaults": {
                            "card_type": "Apple",
                            "country_or_currency": "USD",
                            "form_factor": "横白卡",
                        },
                        "lines": [
                            {
                                "kind": "quote",
                                "pattern": "{amount}={price}",
                                "outputs": {
                                    "card_type": "Apple",
                                    "country_or_currency": "USD",
                                    "form_factor": "横白卡",
                                    "amount_range": "100-150",
                                },
                            }
                        ],
                    },
                    {
                        "id": "section-3",
                        "enabled": True,
                        "priority": 30,
                        "label": "Xbox",
                        "defaults": {
                            "card_type": "Xbox",
                            "country_or_currency": "USD",
                            "form_factor": "不限",
                        },
                        "lines": [
                            {
                                "kind": "quote",
                                "pattern": "US：{amount}={price}",
                                "outputs": {
                                    "card_type": "Xbox",
                                    "country_or_currency": "USD",
                                    "form_factor": "不限",
                                    "amount_range": "10-250",
                                },
                            }
                        ],
                    },
                ],
            },
            ensure_ascii=False,
        )

        merged = _merge_group_parser_template_config(
            existing_raw,
            derived_sections=[
                {
                    "label": "Xbox",
                    "priority": 10,
                    "defaults": {
                        "card_type": "Xbox",
                        "country_or_currency": "USD",
                        "form_factor": "不限",
                    },
                    "lines": [
                        {
                            "kind": "quote",
                            "pattern": "US：{amount}={price}",
                            "outputs": {
                                "card_type": "Xbox",
                                "country_or_currency": "USD",
                                "form_factor": "不限",
                                "amount_range": "10-250",
                            },
                        },
                        {
                            "kind": "quote",
                            "pattern": "UK【{price}】",
                            "outputs": {
                                "card_type": "Xbox",
                                "country_or_currency": "GBP",
                                "form_factor": "不限",
                                "amount_range": "不限",
                            },
                        },
                    ],
                }
            ],
            max_sections=3,
        )
        template = json.loads(merged)
        self.assertEqual(len(list(template.get("sections") or [])), 3)
        xbox_section = next(
            section
            for section in list(template.get("sections") or [])
            if str((section.get("defaults") or {}).get("card_type") or "") == "Xbox"
        )
        self.assertEqual(str(xbox_section.get("id") or ""), "section-3")
        self.assertTrue(
            any(
                str(((line.get("outputs") or {}).get("country_or_currency")) or "") == "GBP"
                for line in list(xbox_section.get("lines") or [])
            )
        )

    def test_quote_exception_result_save_supermarket_mode_allows_fourth_skeleton(self) -> None:
        old_password = os.environ.get("QUOTE_ADMIN_PASSWORD")
        os.environ["QUOTE_ADMIN_PASSWORD"] = "limit-secret"
        try:
            self.db.set_group(
                platform="wechat",
                group_key="wechat:g-supermarket-limit",
                chat_id="g-supermarket-limit",
                chat_name="超市卡上限群",
                group_num=7,
            )
            self.db.upsert_quote_group_profile(
                platform="wechat",
                chat_id="g-supermarket-limit",
                chat_name="超市卡上限群",
                default_card_type="Apple",
                default_country_or_currency="USD",
                default_form_factor="横白卡",
                parser_template="group-parser",
                template_config=json.dumps(
                    {
                        "version": "group-parser-v1",
                        "defaults": {},
                        "sections": [
                            {
                                "id": "section-1",
                                "enabled": True,
                                "priority": 10,
                                "label": "Apple-1",
                                "defaults": {
                                    "card_type": "Apple",
                                    "country_or_currency": "USD",
                                    "form_factor": "横白卡",
                                },
                                "lines": [
                                    {
                                        "kind": "quote",
                                        "pattern": "{amount}={price}",
                                        "outputs": {
                                            "card_type": "Apple",
                                            "country_or_currency": "USD",
                                            "form_factor": "横白卡",
                                            "amount_range": "10-50",
                                        },
                                    }
                                ],
                            },
                            {
                                "id": "section-2",
                                "enabled": True,
                                "priority": 20,
                                "label": "Apple-2",
                                "defaults": {
                                    "card_type": "Apple",
                                    "country_or_currency": "USD",
                                    "form_factor": "横白卡",
                                },
                                "lines": [
                                    {
                                        "kind": "quote",
                                        "pattern": "{amount}={price}",
                                        "outputs": {
                                            "card_type": "Apple",
                                            "country_or_currency": "USD",
                                            "form_factor": "横白卡",
                                            "amount_range": "100-200",
                                        },
                                    }
                                ],
                            },
                            {
                                "id": "section-3",
                                "enabled": True,
                                "priority": 30,
                                "label": "Apple-3",
                                "defaults": {
                                    "card_type": "Apple",
                                    "country_or_currency": "USD",
                                    "form_factor": "横白卡",
                                },
                                "lines": [
                                    {
                                        "kind": "quote",
                                        "pattern": "{amount}={price}",
                                        "outputs": {
                                            "card_type": "Apple",
                                            "country_or_currency": "USD",
                                            "form_factor": "横白卡",
                                            "amount_range": "300-500",
                                        },
                                    }
                                ],
                            },
                        ],
                    },
                    ensure_ascii=False,
                ),
            )
            quote_document_id = self.db.record_quote_document(
                platform="wechat",
                source_group_key="wechat:g-supermarket-limit",
                chat_id="g-supermarket-limit",
                chat_name="超市卡上限群",
                message_id="msg-supermarket-limit",
                source_name="报价员",
                sender_id="u-supermarket-limit",
                raw_text="50=5.3",
                message_time="2026-04-11 03:05:00",
                parser_template="data-engine",
                parser_version="data-engine-v1",
                confidence=0.0,
                parse_status="empty",
            )
            exception_id = self.db.record_quote_exception(
                quote_document_id=quote_document_id,
                platform="wechat",
                source_group_key="wechat:g-supermarket-limit",
                chat_id="g-supermarket-limit",
                chat_name="超市卡上限群",
                source_name="报价员",
                sender_id="u-supermarket-limit",
                reason="strict_match_failed",
                source_line="50=5.3",
                raw_text="50=5.3",
                message_time="2026-04-11 03:05:00",
                parser_template="data-engine",
                parser_version="data-engine-v1",
                confidence=0.0,
            )
            status, payload = self._request(
                "POST",
                "/api/quotes/exceptions/result-save",
                {
                    "exception_id": exception_id,
                    "result_template_text": (
                        "[默认]\n"
                        "国家 / 币种=USD\n"
                        "形态=横白卡\n"
                        "\n"
                        "[Apple]\n"
                        "50=5.3\n"
                    ),
                    "mode": "supermarket",
                    "admin_password": "limit-secret",
                },
            )
            self.assertEqual(status, 200)
            self.assertTrue(payload["saved"])
            self.assertEqual(payload["mode"], "supermarket")
            self.assertEqual(payload["parser_template"], "supermarket-card")

            profile = self.db.get_quote_group_profile(platform="wechat", chat_id="g-supermarket-limit")
            self.assertEqual(profile["parser_template"], "supermarket-card")
            config = json.loads(profile["template_config"])
            self.assertEqual(config["version"], "group-parser-v1")
            self.assertEqual(len(config["sections"]), 4)
        finally:
            if old_password is None:
                os.environ.pop("QUOTE_ADMIN_PASSWORD", None)
            else:
                os.environ["QUOTE_ADMIN_PASSWORD"] = old_password

    def test_saved_group_parser_matches_second_identical_message_via_runtime(self) -> None:
        old_password = os.environ.get("QUOTE_ADMIN_PASSWORD")
        os.environ["QUOTE_ADMIN_PASSWORD"] = "runtime-result-secret"
        try:
            self.db.set_group(
                platform="wechat",
                group_key="wechat:g-runtime-parser",
                chat_id="g-runtime-parser",
                chat_name="Steam 夜班群",
                group_num=8,
            )
            first_raw = (
                "#晚班更新\n"
                "US\n"
                "10-195=5.25（5倍数）\n"
                "----------------------------\n"
                "50=5.3\n"
                "100/150=5.43\n"
                "200- 450=5.44（50倍数）\n"
                "300/400/500=5.45\n"
                "【2- 8分钟反馈】\n"
                "【有扫卡记录的提醒我下。】\n"
                "------------------------------\n"
                "\n"
                "wovxteqeox"
            )
            quote_document_id = self.db.record_quote_document(
                platform="wechat",
                source_group_key="wechat:g-runtime-parser",
                chat_id="g-runtime-parser",
                chat_name="Steam 夜班群",
                message_id="msg-runtime-parser-seed",
                source_name="报价员",
                sender_id="u-runtime-parser",
                raw_text=first_raw,
                message_time="2026-04-11 03:20:00",
                parser_template="data-engine",
                parser_version="data-engine-v1",
                confidence=0.0,
                parse_status="empty",
            )
            exception_id = self.db.record_quote_exception(
                quote_document_id=quote_document_id,
                platform="wechat",
                source_group_key="wechat:g-runtime-parser",
                chat_id="g-runtime-parser",
                chat_name="Steam 夜班群",
                source_name="报价员",
                sender_id="u-runtime-parser",
                reason="strict_match_failed",
                source_line="10-195=5.25\n50=5.3\n100/150=5.43",
                raw_text=first_raw,
                message_time="2026-04-11 03:20:00",
                parser_template="data-engine",
                parser_version="data-engine-v1",
                confidence=0.0,
            )

            status, saved = self._request(
                "POST",
                "/api/quotes/exceptions/result-save",
                {
                    "exception_id": exception_id,
                    "result_template_text": (
                        "[默认]\n"
                        "国家 / 币种=USD\n"
                        "形态=横白卡\n"
                        "\n"
                        "[Steam]\n"
                        "10-195=5.25\n"
                        "50=5.3\n"
                        "100/150=5.43\n"
                        "200-450=5.44\n"
                        "300/400/500=5.45\n"
                    ),
                    "admin_password": "runtime-result-secret",
                },
            )
            self.assertEqual(status, 200)
            self.assertTrue(saved["saved"])

            second_raw = (
                "#晚班更新\n"
                "US\n"
                "10-195=5.35（5倍数）\n"
                "----------------------------\n"
                "50=5.4\n"
                "100/150=5.53\n"
                "200- 450=5.54（50倍数）\n"
                "300/400/500=5.55\n"
                "【2- 8分钟反馈】\n"
                "【有扫卡记录的提醒我下。】\n"
                "------------------------------\n"
                "\n"
                "wovxteqeox"
            )
            status, payload = self._request(
                "POST",
                "/api/core/messages",
                {
                    "platform": "wechat",
                    "message_id": "msg-runtime-parser-2",
                    "chat_id": "g-runtime-parser",
                    "chat_name": "Steam 夜班群",
                    "is_group": True,
                    "sender_id": "u-runtime-parser",
                    "sender_name": "报价员",
                    "content_type": "text",
                    "text": second_raw,
                    "received_at": "2026-04-11 03:30:00",
                },
                headers={"Authorization": "Bearer core-secret"},
            )
            self.assertEqual(status, 200)
            self.assertIn("actions", payload)

            status, board = self._request(
                "GET",
                "/api/quotes/board",
                query_string="source_group_key=wechat:g-runtime-parser",
            )
            self.assertEqual(status, 200)
            self.assertEqual(board["rows"], [])
            runtime_document = self._get_quote_document(
                platform="wechat",
                chat_id="g-runtime-parser",
                message_id="msg-runtime-parser-2",
            )
            self.assertIsNotNone(runtime_document)
            self.assertEqual(runtime_document["run_kind"], "runtime")
            self.assertIsNone(runtime_document["replay_of_quote_document_id"])
            runtime_candidate_rows = self.db.list_quote_candidate_rows(
                quote_document_id=int(runtime_document["id"])
            )
            self.assertEqual(len(runtime_candidate_rows), 5)
            self.assertTrue(
                any(
                    float(row["price"]) == 5.54 and row["amount_range"] == "200-450"
                    for row in runtime_candidate_rows
                )
            )
        finally:
            if old_password is None:
                os.environ.pop("QUOTE_ADMIN_PASSWORD", None)
            else:
                os.environ["QUOTE_ADMIN_PASSWORD"] = old_password

    def test_runtime_prefers_exact_chat_id_profile_over_older_same_name_profile(self) -> None:
        from bookkeeping_core.contracts import NormalizedMessageEnvelope
        from bookkeeping_core.quotes import QuoteCaptureService

        self.db.upsert_quote_group_profile(
            platform="whatsapp",
            chat_id="legacy-room",
            chat_name="#80093 steam 空 测试",
            default_card_type="Apple",
            default_country_or_currency="USD",
            default_form_factor="横白卡",
            parser_template="legacy-parser",
            template_config=json.dumps({"version": "tpl-v1", "defaults": {}, "price_lines": []}, ensure_ascii=False),
        )
        self.db.upsert_quote_group_profile(
            platform="whatsapp",
            chat_id="new-room@g.us",
            chat_name="#80093 steam 空 测试",
            default_card_type="Apple",
            default_country_or_currency="USD",
            default_form_factor="横白卡",
            parser_template="group-parser",
            template_config=json.dumps(
                {"version": "group-parser-v1", "defaults": {}, "sections": []},
                ensure_ascii=False,
            ),
        )

        service = QuoteCaptureService(self.db)
        envelope = NormalizedMessageEnvelope.from_dict(
            {
                "platform": "whatsapp",
                "message_id": "msg-same-name-profile",
                "chat_id": "new-room@g.us",
                "chat_name": "#80093 steam 空 测试",
                "is_group": True,
                "sender_id": "sender-1",
                "sender_name": "报价员",
                "content_type": "text",
                "text": "卡图：100/150=5.4",
                "received_at": "2026-04-11 04:00:00",
            }
        )

        profile = service._group_profile_for_envelope(envelope, envelope.text)

        self.assertEqual(profile.parser_template, "group-parser")
        self.assertIn("group-parser-v1", profile.template_config)

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
        self.assertIn('id="reconciliation-trace-panel"', html)
        self.assertIn('id="reconciliation-trace-status"', html)
        self.assertIn('id="reconciliation-export-detail-link"', html)
        self.assertIn('id="reconciliation-export-summary-link"', html)
        self.assertIn('id="reconciliation-combination"', html)
        self.assertIn('id="reconciliation-group-num"', html)
        self.assertIn('data-action="trace-row"', html)

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

    def test_reconciliation_difference_trace_alias_returns_trace_without_auth(
        self,
    ) -> None:
        tx_id = self.db.add_transaction(
            platform="wechat",
            group_key="wechat:g-100",
            group_num=5,
            chat_id="g-100",
            chat_name="客户群-Web",
            sender_id="u-trace-alias",
            sender_name="Trace Alias",
            message_id="msg-trace-alias",
            input_sign=1,
            amount=88,
            category="rmb",
            rate=None,
            rmb_value=88,
            raw="+88rmb",
            created_at="2026-03-20 14:00:00",
        )
        status, payload = self._request(
            "GET",
            "/api/reconciliation/difference-trace",
            query_string=f"transaction_id={tx_id}",
        )
        self.assertEqual(status, 200)
        self.assertEqual(payload["transaction"]["id"], tx_id)
        self.assertIn("trace_status", payload)

    def test_bootstrap_profile_replay_remains_candidate_only(self) -> None:
        from bookkeeping_web.app import _replay_latest_quote_document_with_current_template
        from tests.support.quote_exception_corpus import load_gold_fixture

        chat_id = "g-bootstrap-replay"
        chat_name = "Bootstrap Replay 群"
        self.db.set_group(
            platform="wechat",
            group_key=f"wechat:{chat_id}",
            chat_id=chat_id,
            chat_name=chat_name,
            group_num=5,
        )
        payload = self._upsert_bootstrap_profile(
            fixture_name="sk_steam_price_update",
            platform="wechat",
            chat_id=chat_id,
            chat_name=chat_name,
        )
        fixture = load_gold_fixture(str(payload["canonical_fixture_name"]))
        raw_text = str(fixture["raw_text"])
        first_line = raw_text.splitlines()[0]

        quote_document_id = self.db.record_quote_document(
            platform="wechat",
            source_group_key=f"wechat:{chat_id}",
            chat_id=chat_id,
            chat_name=chat_name,
            message_id="msg-bootstrap-replay-origin",
            source_name="报价员",
            sender_id="seller-bootstrap",
            raw_text=raw_text,
            message_time="2026-04-14 18:00:00",
            parser_template="group-parser",
            parser_version="group-parser-v1",
            confidence=0.0,
            parse_status="empty",
        )
        exception_id = self.db.record_quote_exception(
            quote_document_id=quote_document_id,
            platform="wechat",
            source_group_key=f"wechat:{chat_id}",
            chat_id=chat_id,
            chat_name=chat_name,
            source_name="报价员",
            sender_id="seller-bootstrap",
            reason="missing_group_template",
            source_line=first_line,
            raw_text=raw_text,
            message_time="2026-04-14 18:00:00",
            parser_template="group-parser",
            parser_version="group-parser-v1",
            confidence=0.0,
        )
        exc_row = self.db.get_quote_exception(exception_id=exception_id)
        self.assertIsNotNone(exc_row)
        assert exc_row is not None

        replay = _replay_latest_quote_document_with_current_template(
            self.db,
            exc_row=dict(exc_row),
            record_exceptions=False,
        )

        self.assertTrue(replay["replayed"])
        self.assertFalse(replay["mutated_active_facts"])
        self.assertGreater(int(replay["rows"]), 0)
        replay_document_id = int(replay["quote_document_id"])

        validation_run = self.db.get_latest_quote_validation_run(
            quote_document_id=replay_document_id
        )
        self.assertIsNotNone(validation_run)
        assert validation_run is not None
        self.assertGreater(int(validation_run["publishable_row_count"]), 0)

        candidate_rows = self.db.list_quote_candidate_rows(
            quote_document_id=replay_document_id
        )
        self.assertGreater(len(candidate_rows), 0)

        quote_price_row_count = self._count_rows(
            "quote_price_rows",
            "WHERE quote_document_id = ?",
            (replay_document_id,),
        )
        self.assertEqual(quote_price_row_count, 0)


class WebRepairCaseTests(PostgresTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.db_dsn = self.make_dsn("web-repair-case")
        self.db = BookkeepingDB(self.db_dsn)
        self.db.set_group(
            platform="wechat",
            group_key="wechat:g-web-repair",
            chat_id="g-web-repair",
            chat_name="Repair Replay 群",
            group_num=5,
        )
        self.app = create_app(self.db_dsn)

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

        def start_response(status: str, response_headers: list[tuple[str, str]]) -> None:
            response["status"] = int(status.split(" ", 1)[0])

        chunks = self.app(environ, start_response)
        response["body"] = b"".join(chunks)
        return response["status"], json.loads(response["body"].decode("utf-8"))

    def _count_rows(
        self,
        table_name: str,
        where_clause: str = "",
        params: tuple[object, ...] = (),
    ) -> int:
        row = self.db.conn.execute(
            f"SELECT COUNT(*) AS cnt FROM {table_name} {where_clause}",
            params,
        ).fetchone()
        return int(row["cnt"] or 0)

    def _upsert_bootstrap_profile(
        self,
        *,
        fixture_name: str,
        platform: str,
        chat_id: str,
        chat_name: str,
    ) -> dict:
        from scripts.bootstrap_quote_group_profiles import build_bootstrap_profile_payload

        payload = build_bootstrap_profile_payload(
            fixture_name=fixture_name,
            platform=platform,
            chat_id=chat_id,
            chat_name=chat_name,
        )
        self.db.upsert_quote_group_profile(
            platform=platform,
            chat_id=chat_id,
            chat_name=chat_name,
            default_card_type=str(payload["default_card_type"]),
            default_country_or_currency=str(payload["default_country_or_currency"]),
            default_form_factor=str(payload["default_form_factor"]),
            default_multiplier=str(payload["default_multiplier"]),
            parser_template=str(payload["parser_template"]),
            stale_after_minutes=int(payload["stale_after_minutes"]),
            note=str(payload["note"]),
            template_config=json.dumps(payload["template_config"], ensure_ascii=False),
        )
        return payload

    def _create_repair_case_with_baseline(
        self,
        *,
        exception_message_id: str,
        raw_message: str = "[Apple]\nUS 100 95.5",
        source_line: str = "US 100 95.5",
    ) -> tuple[int, dict, dict]:
        from bookkeeping_core.quote_validation import QuoteValidationRun
        from bookkeeping_core.repair_cases import (
            create_baseline_repair_attempt,
            package_quote_repair_case,
        )

        self.db.upsert_quote_group_profile(
            platform="wechat",
            chat_id="g-web-repair",
            chat_name="Repair Replay 群",
            default_card_type="Apple",
            default_country_or_currency="USD",
            default_form_factor="physical",
            default_multiplier="1x",
            parser_template="repair-template-v1",
            template_config=json.dumps(
                {"version": "repair-template-v1", "sections": ["Apple"]},
                ensure_ascii=False,
            ),
        )
        origin_document_id = self.db.record_quote_candidate_bundle(
            candidate=_make_repair_candidate(
                message_id=exception_message_id,
                raw_message=raw_message,
                row_specs=[{"source_line": source_line, "price": 95.5}],
                run_kind="runtime",
                replay_of_quote_document_id=None,
            )
        )
        self.db.record_quote_validation_run(
            validation_run=QuoteValidationRun(
                quote_document_id=origin_document_id,
                validator_version="validator-v1",
                run_kind="runtime",
                message_decision="no_publish",
                validation_status="completed",
                summary={"message_reasons": [{"code": "strict_match_failed"}]},
                row_results=[],
            )
        )
        exception_id = self.db.record_quote_exception(
            quote_document_id=origin_document_id,
            platform="wechat",
            source_group_key="wechat:g-web-repair",
            chat_id="g-web-repair",
            chat_name="Repair Replay 群",
            source_name="报价员",
            sender_id="seller-web-repair",
            reason="strict_match_failed",
            source_line=source_line,
            raw_text=raw_message,
            message_time="2026-04-14 21:00:00",
            parser_template="repair-template-v1",
            parser_version="candidate-v1",
            confidence=0.12,
        )
        repair_case = package_quote_repair_case(db=self.db, exception_id=exception_id)
        baseline_attempt = create_baseline_repair_attempt(
            db=self.db,
            repair_case_id=int(repair_case["id"]),
            replay_result={
                "replayed": True,
                "reason": "",
                "rows": 1,
                "exceptions": 0,
                "remaining_lines": [source_line],
                "mutated_active_facts": False,
                "message_decision": "no_publish",
                "publishable_row_count": 0,
                "held_row_count": 0,
                "rejected_row_count": 1,
                "comparison": {"classification": "same"},
            },
        )
        return exception_id, repair_case, baseline_attempt

    def test_create_baseline_repair_attempt_uses_replay_helper_and_persists_comparison(
        self,
    ) -> None:
        from bookkeeping_core.quote_validation import QuoteValidationRun
        from bookkeeping_core.repair_cases import (
            create_baseline_repair_attempt,
            package_quote_repair_case,
        )

        self.db.upsert_quote_group_profile(
            platform="wechat",
            chat_id="g-web-repair",
            chat_name="Repair Replay 群",
            default_card_type="Apple",
            default_country_or_currency="USD",
            default_form_factor="physical",
            default_multiplier="1x",
            parser_template="repair-template-v1",
            template_config=json.dumps(
                {"version": "repair-template-v1", "sections": ["Apple"]},
                ensure_ascii=False,
            ),
        )
        origin_document_id = self.db.record_quote_candidate_bundle(
            candidate=_make_repair_candidate(
                message_id="repair-origin-web",
                raw_message="[Apple]\nUS 100 95.5",
                row_specs=[{"source_line": "US 100 95.5", "price": 95.5}],
                run_kind="runtime",
                replay_of_quote_document_id=None,
            )
        )
        origin_candidate_rows = self.db.list_quote_candidate_rows(
            quote_document_id=origin_document_id
        )
        origin_validation_run_id = self.db.record_quote_validation_run(
            validation_run=QuoteValidationRun(
                quote_document_id=origin_document_id,
                validator_version="validator-v1",
                run_kind="runtime",
                message_decision="no_publish",
                validation_status="completed",
                summary={"message_reasons": [{"code": "strict_match_failed"}]},
                row_results=[],
            )
        )
        exception_id = self.db.record_quote_exception(
            quote_document_id=origin_document_id,
            platform="wechat",
            source_group_key="wechat:g-web-repair",
            chat_id="g-web-repair",
            chat_name="Repair Replay 群",
            source_name="报价员",
            sender_id="seller-web-repair",
            reason="strict_match_failed",
            source_line="US 100 95.5",
            raw_text="[Apple]\nUS 100 95.5",
            message_time="2026-04-14 19:00:00",
            parser_template="repair-template-v1",
            parser_version="candidate-v1",
            confidence=0.12,
        )
        repair_case = package_quote_repair_case(db=self.db, exception_id=exception_id)

        replay_document_id = self.db.record_quote_candidate_bundle(
            candidate=_make_repair_candidate(
                message_id="repair-baseline-web",
                raw_message="[Apple]\nUS 100 95.5\nUK 50 48.0",
                row_specs=[
                    {"source_line": "US 100 95.5", "price": 95.5},
                    {"source_line": "UK 50 48.0", "price": 48.0},
                ],
                run_kind="replay",
                replay_of_quote_document_id=origin_document_id,
            )
        )
        replay_validation_run_id = self.db.record_quote_validation_run(
            validation_run=QuoteValidationRun(
                quote_document_id=replay_document_id,
                validator_version="validator-v1",
                run_kind="replay",
                message_decision="held_only",
                validation_status="completed",
                summary={"message_reasons": [{"code": "business_low_confidence_hold"}]},
                row_results=[],
            )
        )

        with patch(
            "bookkeeping_web.app._replay_latest_quote_document_with_current_template"
        ) as replay_mock:
            replay_mock.return_value = {
                "replayed": True,
                "rows": 2,
                "exceptions": 0,
                "detected_exceptions": 0,
                "quote_document_id": replay_document_id,
                "validation_run_id": replay_validation_run_id,
                "remaining_lines": ["#manual-check"],
                "mutated_active_facts": False,
                "message_decision": "held_only",
                "publishable_row_count": 0,
                "held_row_count": 2,
                "rejected_row_count": 0,
            }
            attempt = create_baseline_repair_attempt(
                db=self.db,
                repair_case_id=int(repair_case["id"]),
                replay_result=None,
            )

        replay_mock.assert_called_once()
        self.assertFalse(replay_mock.call_args.kwargs["record_exceptions"])
        self.assertEqual(self._count_rows("quote_repair_cases"), 1)
        self.assertEqual(self._count_rows("quote_parse_exceptions"), 1)
        self.assertEqual(int(attempt["quote_document_id"]), replay_document_id)
        self.assertEqual(int(attempt["validation_run_id"]), replay_validation_run_id)
        self.assertEqual(str(attempt["outcome_state"]), "completed")

        summary = _json_field(attempt["attempt_summary_json"])
        self.assertEqual(summary["comparison"]["classification"], "better")
        self.assertEqual(summary["comparison"]["origin"]["row_count"], 1)
        self.assertEqual(summary["comparison"]["attempt"]["row_count"], 2)
        self.assertEqual(
            summary["comparison"]["origin"]["message_decision"], "no_publish"
        )
        self.assertEqual(
            summary["comparison"]["attempt"]["message_decision"], "held_only"
        )
        self.assertEqual(summary["comparison"]["attempt"]["exception_count"], 0)
        self.assertEqual(summary["comparison"]["attempt"]["remaining_lines"], ["#manual-check"])
        self.assertEqual(summary["mutated_active_facts"], False)

        stored_case = self.db.get_quote_repair_case(repair_case_id=int(repair_case["id"]))
        self.assertIsNotNone(stored_case)
        assert stored_case is not None
        self.assertEqual(int(stored_case["baseline_attempt_id"]), int(attempt["id"]))

        quote_price_row_count = self._count_rows(
            "quote_price_rows",
            "WHERE quote_document_id = ?",
            (replay_document_id,),
        )
        self.assertEqual(quote_price_row_count, 0)
        self.assertEqual(len(origin_candidate_rows), 1)
        self.assertGreater(origin_validation_run_id, 0)

    def test_create_baseline_repair_attempt_runs_live_candidate_only_replay_without_forking_cases(
        self,
    ) -> None:
        from bookkeeping_core.repair_cases import (
            create_baseline_repair_attempt,
            package_quote_repair_case,
        )
        from tests.support.quote_exception_corpus import load_gold_fixture

        payload = self._upsert_bootstrap_profile(
            fixture_name="sk_steam_price_update",
            platform="wechat",
            chat_id="g-web-repair",
            chat_name="Repair Replay 群",
        )
        fixture = load_gold_fixture(str(payload["canonical_fixture_name"]))
        raw_text = str(fixture["raw_text"])
        first_line = raw_text.splitlines()[0]

        origin_document_id = self.db.record_quote_document(
            platform="wechat",
            source_group_key="wechat:g-web-repair",
            chat_id="g-web-repair",
            chat_name="Repair Replay 群",
            message_id="msg-web-repair-origin",
            source_name="报价员",
            sender_id="seller-web-repair",
            raw_text=raw_text,
            message_time="2026-04-14 20:00:00",
            parser_template="group-parser",
            parser_version="group-parser-v1",
            confidence=0.0,
            parse_status="empty",
        )
        exception_id = self.db.record_quote_exception(
            quote_document_id=origin_document_id,
            platform="wechat",
            source_group_key="wechat:g-web-repair",
            chat_id="g-web-repair",
            chat_name="Repair Replay 群",
            source_name="报价员",
            sender_id="seller-web-repair",
            reason="missing_group_template",
            source_line=first_line,
            raw_text=raw_text,
            message_time="2026-04-14 20:00:00",
            parser_template="group-parser",
            parser_version="group-parser-v1",
            confidence=0.0,
        )
        repair_case = package_quote_repair_case(db=self.db, exception_id=exception_id)

        attempt = create_baseline_repair_attempt(
            db=self.db,
            repair_case_id=int(repair_case["id"]),
            replay_result=None,
        )

        self.assertEqual(self._count_rows("quote_repair_cases"), 1)
        self.assertEqual(self._count_rows("quote_parse_exceptions"), 1)
        self.assertTrue(int(attempt["quote_document_id"]) > 0)
        self.assertTrue(int(attempt["validation_run_id"]) > 0)

        summary = _json_field(attempt["attempt_summary_json"])
        self.assertTrue(summary["replayed"])
        self.assertEqual(summary["mutated_active_facts"], False)
        self.assertIn(
            summary["comparison"]["classification"],
            {"better", "same", "worse"},
        )
        self.assertGreaterEqual(summary["comparison"]["attempt"]["row_count"], 1)

        replay_document_id = int(attempt["quote_document_id"])
        validation_run = self.db.get_latest_quote_validation_run(
            quote_document_id=replay_document_id
        )
        self.assertIsNotNone(validation_run)
        assert validation_run is not None
        self.assertEqual(str(validation_run["run_kind"]), "replay")

        quote_price_row_count = self._count_rows(
            "quote_price_rows",
            "WHERE quote_document_id = ?",
            (replay_document_id,),
        )
        self.assertEqual(quote_price_row_count, 0)

    def test_quote_exceptions_endpoint_includes_compact_repair_summary(self) -> None:
        from bookkeeping_core.repair_cases import (
            REPAIR_CASE_STATE_READY_FOR_ATTEMPT,
            advance_quote_repair_case_state,
            record_quote_repair_attempt,
        )

        exception_id, repair_case, baseline_attempt = self._create_repair_case_with_baseline(
            exception_message_id="repair-summary-origin"
        )
        advance_quote_repair_case_state(
            db=self.db,
            repair_case_id=int(repair_case["id"]),
            next_state=REPAIR_CASE_STATE_READY_FOR_ATTEMPT,
        )
        record_quote_repair_attempt(
            db=self.db,
            repair_case_id=int(repair_case["id"]),
            trigger="manual_retry",
            replay_result={
                "replayed": True,
                "reason": "strict-match-still-failing",
                "rows": 1,
                "exceptions": 1,
                "remaining_lines": ["US 100 95.5"],
                "mutated_active_facts": False,
                "message_decision": "no_publish",
                "publishable_row_count": 0,
                "held_row_count": 0,
                "rejected_row_count": 1,
                "comparison": {"classification": "same"},
            },
        )

        status, payload = self._request(
            "GET",
            "/api/quotes/exceptions",
            query_string="resolution_status=all",
        )
        self.assertEqual(status, 200)
        row = next(item for item in payload["rows"] if int(item["id"]) == exception_id)
        self.assertEqual(int(row["repair_case_id"]), int(repair_case["id"]))
        self.assertEqual(row["repair_case"]["lifecycle_state"], "attempt_failed")
        self.assertEqual(row["repair_case"]["attempt_count"], 1)
        self.assertEqual(
            int(row["repair_case"]["baseline_attempt_id"]),
            int(baseline_attempt["id"]),
        )
        self.assertEqual(row["repair_case"]["last_attempt_outcome"], "completed")
        self.assertEqual(row["repair_case"]["escalation_state"], "retryable")

    def test_quote_exceptions_endpoint_includes_snapshot_decision_summary(self) -> None:
        origin_document_id = self.db.record_quote_candidate_bundle(
            candidate=_make_repair_candidate(
                message_id="snapshot-summary-origin",
                raw_message="[Apple]\nUS 100 95.5",
                row_specs=[{"source_line": "US 100 95.5", "price": 95.5}],
                run_kind="runtime",
                replay_of_quote_document_id=None,
            )
        )
        self.db.confirm_quote_snapshot_decision(
            quote_document_id=origin_document_id,
            resolved_decision=SNAPSHOT_FULL_SNAPSHOT,
            confirmed_by="qa-operator",
        )
        exception_id = self.db.record_quote_exception(
            quote_document_id=origin_document_id,
            platform="wechat",
            source_group_key="wechat:g-web-repair",
            chat_id="g-web-repair",
            chat_name="Repair Replay 群",
            source_name="报价员",
            sender_id="seller-web-repair",
            reason="strict_match_failed",
            source_line="US 100 95.5",
            raw_text="[Apple]\nUS 100 95.5",
            message_time="2026-04-14 19:00:00",
            parser_template="repair-template-v1",
            parser_version="candidate-v1",
            confidence=0.97,
        )

        status, payload = self._request(
            "GET",
            "/api/quotes/exceptions",
            query_string="resolution_status=all",
        )
        self.assertEqual(status, 200)
        row = next(item for item in payload["rows"] if int(item["id"]) == exception_id)
        self.assertEqual(row["snapshot_decision"]["system_hypothesis"], "delta_update")
        self.assertEqual(row["snapshot_decision"]["resolved_decision"], "full_snapshot")
        self.assertEqual(row["snapshot_decision"]["decision_source"], "operator")

    def test_snapshot_decision_confirm_endpoint_persists_without_mutating_quote_facts(
        self,
    ) -> None:
        old_password = os.environ.get("QUOTE_ADMIN_PASSWORD")
        os.environ["QUOTE_ADMIN_PASSWORD"] = "snapshot-secret"
        try:
            origin_document_id = self.db.record_quote_candidate_bundle(
                candidate=_make_repair_candidate(
                    message_id="snapshot-confirm-origin",
                    raw_message="[Apple]\nUS 100 95.5",
                    row_specs=[{"source_line": "US 100 95.5", "price": 95.5}],
                    run_kind="runtime",
                    replay_of_quote_document_id=None,
                )
            )
            status, payload = self._request(
                "POST",
                "/api/quotes/snapshot-decision/confirm",
                {
                    "quote_document_id": origin_document_id,
                    "resolved_decision": "full_snapshot",
                    "admin_password": "snapshot-secret",
                    "confirmed_by": "web-qa",
                },
            )
            self.assertEqual(status, 200)
            self.assertTrue(payload["saved"])
            self.assertIn("未改动报价墙", payload["status_text"])
            stored = self.db.get_quote_snapshot_decision(
                quote_document_id=origin_document_id
            )
            self.assertIsNotNone(stored)
            assert stored is not None
            self.assertEqual(str(stored["resolved_decision"]), "full_snapshot")
            self.assertEqual(str(stored["confirmed_by"]), "web-qa")
            quote_price_row_count = self._count_rows(
                "quote_price_rows",
                "WHERE quote_document_id = ?",
                (origin_document_id,),
            )
            self.assertEqual(quote_price_row_count, 0)
        finally:
            if old_password is None:
                os.environ.pop("QUOTE_ADMIN_PASSWORD", None)
            else:
                os.environ["QUOTE_ADMIN_PASSWORD"] = old_password

    def test_quote_evidence_endpoint_returns_read_only_message_level_payload(self) -> None:
        from bookkeeping_core.quote_validation import validate_quote_candidate_document

        self.db.upsert_quote_price_row_with_history(
            quote_document_id=900,
            message_id="seed-evidence-web-1",
            platform="wechat",
            source_group_key="wechat:g-web-repair",
            chat_id="g-web-repair",
            chat_name="Repair Replay 群",
            source_name="Seed Source",
            sender_id="seed-user",
            card_type="CVS",
            country_or_currency="USD",
            amount_range="50-500",
            multiplier=None,
            form_factor="physical",
            price=5.7,
            quote_status="active",
            restriction_text="",
            source_line="cvs 50-500 5.7",
            raw_text="cvs 50-500 5.7",
            message_time="2026-04-15 09:00:00",
            effective_at="2026-04-15 09:00:00",
            expires_at=None,
            parser_template="seed-template",
            parser_version="seed-v1",
            confidence=0.99,
        )
        self.db.upsert_quote_price_row_with_history(
            quote_document_id=901,
            message_id="seed-evidence-web-2",
            platform="wechat",
            source_group_key="wechat:g-web-repair",
            chat_id="g-web-repair",
            chat_name="Repair Replay 群",
            source_name="Seed Source",
            sender_id="seed-user",
            card_type="DG",
            country_or_currency="USD",
            amount_range="100-500",
            multiplier=None,
            form_factor="physical",
            price=5.8,
            quote_status="active",
            restriction_text="",
            source_line="dg 100-500 5.8",
            raw_text="dg 100-500 5.8",
            message_time="2026-04-15 09:00:00",
            effective_at="2026-04-15 09:00:00",
            expires_at=None,
            parser_template="seed-template",
            parser_version="seed-v1",
            confidence=0.99,
        )
        self.db.conn.commit()

        origin_document_id = self.db.record_quote_candidate_bundle(
            candidate=_make_repair_candidate(
                message_id="web-evidence-origin",
                raw_message="cvs 50-500 5.7\ndg 100-500 0",
                row_specs=[
                    {
                        "source_line": "cvs 50-500 5.7",
                        "card_type": "CVS",
                        "country_or_currency": "USD",
                        "amount_range": "50-500",
                        "multiplier": "",
                        "price": 5.7,
                        "quote_status": "active",
                    },
                    {
                        "source_line": "dg 100-500 0",
                        "card_type": "DG",
                        "country_or_currency": "USD",
                        "amount_range": "100-500",
                        "multiplier": "",
                        "price": 0.0,
                        "quote_status": "candidate",
                    },
                ],
                run_kind="runtime",
                replay_of_quote_document_id=None,
            )
        )
        validation_run = validate_quote_candidate_document(
            quote_document_id=origin_document_id,
            run_kind="runtime",
            candidate_document=self.db.get_quote_document(
                quote_document_id=origin_document_id
            ),
            candidate_rows=self.db.list_quote_candidate_rows(
                quote_document_id=origin_document_id
            ),
        )
        self.db.record_quote_validation_run(validation_run=validation_run)
        self.db.confirm_quote_snapshot_decision(
            quote_document_id=origin_document_id,
            resolved_decision=SNAPSHOT_DELTA_UPDATE,
            confirmed_by="web-operator",
        )

        status, payload = self._request(
            "GET",
            "/api/quotes/evidence",
            query_string=f"quote_document_id={origin_document_id}",
        )
        self.assertEqual(status, 200)
        self.assertTrue(payload["read_only"])
        self.assertEqual(int(payload["quote_document_id"]), origin_document_id)
        self.assertEqual(
            payload["publish_reasoning"]["status"], "delta_safe_upsert_only"
        )
        self.assertEqual(
            len(payload["validation"]["grouped_rows"]["publishable"]), 1
        )
        self.assertEqual(len(payload["validation"]["grouped_rows"]["rejected"]), 1)
        self.assertEqual(
            len(payload["publish_reasoning"]["untouched_active_rows"]), 1
        )
        self.assertIn("未改动报价墙", payload["publish_reasoning"]["summary_text"])

    def test_quote_evidence_endpoint_accepts_exception_id_indirection(self) -> None:
        from bookkeeping_core.quote_validation import QuoteValidationRun

        origin_document_id = self.db.record_quote_candidate_bundle(
            candidate=_make_repair_candidate(
                message_id="web-evidence-exception",
                raw_message="[Apple]\nUS 100 95.5",
                row_specs=[{"source_line": "US 100 95.5", "price": 95.5}],
                run_kind="runtime",
                replay_of_quote_document_id=None,
            )
        )
        self.db.record_quote_validation_run(
            validation_run=QuoteValidationRun(
                quote_document_id=origin_document_id,
                validator_version="validator-v1",
                run_kind="runtime",
                message_decision="no_publish",
                validation_status="completed",
                summary={"message_reasons": [{"code": "strict_match_failed"}]},
                row_results=[],
            )
        )
        exception_id = self.db.record_quote_exception(
            quote_document_id=origin_document_id,
            platform="wechat",
            source_group_key="wechat:g-web-repair",
            chat_id="g-web-repair",
            chat_name="Repair Replay 群",
            source_name="报价员",
            sender_id="seller-web-repair",
            reason="strict_match_failed",
            source_line="US 100 95.5",
            raw_text="[Apple]\nUS 100 95.5",
            message_time="2026-04-14 19:00:00",
            parser_template="repair-template-v1",
            parser_version="candidate-v1",
            confidence=0.12,
        )

        status, payload = self._request(
            "GET",
            "/api/quotes/evidence",
            query_string=f"exception_id={exception_id}",
        )
        self.assertEqual(status, 200)
        self.assertTrue(payload["read_only"])
        self.assertEqual(int(payload["quote_document_id"]), origin_document_id)
        self.assertEqual(int(payload["linked_exception"]["id"]), exception_id)
        self.assertTrue(payload["related_dictionary_entries"])
        self.assertEqual(
            payload["related_dictionary_entries"][0]["failure_code"],
            "strict_match_failed",
        )

    def test_quote_failure_dictionary_endpoint_returns_searchable_entries(self) -> None:
        status, payload = self._request(
            "GET",
            "/api/quotes/failure-dictionary",
            query_string="search=skeleton&limit=5",
        )
        self.assertEqual(status, 200)
        self.assertTrue(payload["read_only"])
        self.assertLessEqual(len(payload["rows"]), 5)
        self.assertTrue(
            any(
                row["failure_code"] == "auto_remediation_skeleton_expansion_blocked"
                for row in payload["rows"]
            )
        )
        entry = next(
            row
            for row in payload["rows"]
            if row["failure_code"] == "auto_remediation_skeleton_expansion_blocked"
        )
        self.assertIn("不要在已有群 profile 下默认扩骨架", entry["do_not_do"])
        self.assertIsInstance(entry["forbidden_fixes_json"], list)

    def test_quote_exception_resolve_endpoint_syncs_repair_case_ignore_reopen_and_resolve(
        self,
    ) -> None:
        exception_id, repair_case, _ = self._create_repair_case_with_baseline(
            exception_message_id="repair-resolve-origin"
        )

        status, ignored = self._request(
            "POST",
            "/api/quotes/exceptions/resolve",
            {"exception_id": exception_id, "resolution_status": "ignored"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(ignored["updated"], 1)
        stored_case = self.db.get_quote_repair_case(repair_case_id=int(repair_case["id"]))
        self.assertIsNotNone(stored_case)
        assert stored_case is not None
        self.assertEqual(str(stored_case["lifecycle_state"]), "closed_ignored")

        status, reopened = self._request(
            "POST",
            "/api/quotes/exceptions/resolve",
            {"exception_id": exception_id, "resolution_status": "open"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(reopened["updated"], 1)
        stored_case = self.db.get_quote_repair_case(repair_case_id=int(repair_case["id"]))
        self.assertIsNotNone(stored_case)
        assert stored_case is not None
        self.assertEqual(str(stored_case["lifecycle_state"]), "ready_for_attempt")

        status, resolved = self._request(
            "POST",
            "/api/quotes/exceptions/resolve",
            {"exception_id": exception_id, "resolution_status": "resolved"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(resolved["updated"], 1)
        stored_case = self.db.get_quote_repair_case(repair_case_id=int(repair_case["id"]))
        self.assertIsNotNone(stored_case)
        assert stored_case is not None
        self.assertEqual(str(stored_case["lifecycle_state"]), "closed_resolved")

    def test_quote_exception_harvest_save_appends_repair_attempt_history(self) -> None:
        old_password = os.environ.get("QUOTE_ADMIN_PASSWORD")
        os.environ["QUOTE_ADMIN_PASSWORD"] = "repair-secret"
        try:
            exception_id, repair_case, _ = self._create_repair_case_with_baseline(
                exception_message_id="repair-harvest-origin",
                raw_message="[Apple]\nUS 100 95.5",
                source_line="US 100 95.5",
            )

            with patch(
                "bookkeeping_web.app._build_quote_harvest_preview_payload"
            ) as preview_mock, patch(
                "bookkeeping_web.app._replay_latest_quote_document_with_current_template"
            ) as replay_mock:
                preview_mock.return_value = {
                    "can_save": True,
                    "derived_section": {
                        "label": "Apple",
                        "defaults": {
                            "card_type": "Apple",
                            "country_or_currency": "USD",
                            "form_factor": "physical",
                        },
                        "lines": [],
                    },
                    "preview_rows": [{"card_type": "Apple"}],
                    "is_latest_for_group": True,
                }
                replay_mock.return_value = {
                    "replayed": True,
                    "reason": "strict-match-still-failing",
                    "rows": 1,
                    "exceptions": 1,
                    "remaining_lines": ["US 100 95.5"],
                    "mutated_active_facts": False,
                    "message_decision": "no_publish",
                    "publishable_row_count": 0,
                    "held_row_count": 0,
                    "rejected_row_count": 1,
                    "comparison": {"classification": "same"},
                }
                status, saved = self._request(
                    "POST",
                    "/api/quotes/exceptions/harvest-save",
                    {
                        "exception_id": exception_id,
                        "section_start_line": 0,
                        "section_end_line": 1,
                        "admin_password": "repair-secret",
                    },
                )

            self.assertEqual(status, 200)
            self.assertTrue(saved["saved"])
            self.assertFalse(saved["resolved_fully"])
            stored_case = self.db.get_quote_repair_case(repair_case_id=int(repair_case["id"]))
            self.assertIsNotNone(stored_case)
            assert stored_case is not None
            self.assertEqual(str(stored_case["lifecycle_state"]), "attempt_failed")
            summary = _json_field(stored_case["case_summary_json"])
            self.assertEqual(summary["attempt_count"], 1)
            self.assertEqual(summary["failure_log_json"][0]["failure_note"], "strict-match-still-failing")
            self.assertEqual(summary["escalation_state"], "retryable")
        finally:
            if old_password is None:
                os.environ.pop("QUOTE_ADMIN_PASSWORD", None)
            else:
                os.environ["QUOTE_ADMIN_PASSWORD"] = old_password

    def test_quote_exception_result_save_closes_linked_repair_case(self) -> None:
        old_password = os.environ.get("QUOTE_ADMIN_PASSWORD")
        os.environ["QUOTE_ADMIN_PASSWORD"] = "repair-secret"
        try:
            exception_id, repair_case, _ = self._create_repair_case_with_baseline(
                exception_message_id="repair-result-origin"
            )

            with patch(
                "bookkeeping_web.app._build_quote_result_preview_payload"
            ) as preview_mock:
                preview_mock.return_value = {
                    "can_save": True,
                    "strict_replay_ok": True,
                    "derived_sections": [{"label": "Apple"}],
                    "preview_rows": [{"card_type": "Apple", "country_or_currency": "USD"}],
                    "notes": [],
                    "warnings": [],
                    "skeleton_summaries": [],
                    "result_template_text": "[Apple]\n100=95.5",
                    "draft_structure": {"defaults": {}},
                }
                status, saved = self._request(
                    "POST",
                    "/api/quotes/exceptions/result-save",
                    {
                        "exception_id": exception_id,
                        "result_template_text": "[Apple]\n100=95.5",
                        "admin_password": "repair-secret",
                    },
                )

            self.assertEqual(status, 200)
            self.assertTrue(saved["saved"])
            stored_case = self.db.get_quote_repair_case(repair_case_id=int(repair_case["id"]))
            self.assertIsNotNone(stored_case)
            assert stored_case is not None
            self.assertEqual(str(stored_case["lifecycle_state"]), "closed_resolved")
            summary = _json_field(stored_case["case_summary_json"])
            self.assertEqual(summary["attempt_count"], 0)
            closed_at_text = str(summary["closed_at"] or "")
            self.assertTrue(closed_at_text)
            self.assertTrue(
                closed_at_text.startswith(
                    str(stored_case["updated_at"] or "").split(".", 1)[0]
                )
            )
        finally:
            if old_password is None:
                os.environ.pop("QUOTE_ADMIN_PASSWORD", None)
            else:
                os.environ["QUOTE_ADMIN_PASSWORD"] = old_password


if __name__ == "__main__":
    unittest.main()
