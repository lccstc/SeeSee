from __future__ import annotations

import json
import unittest

from bookkeeping_core.database import BookkeepingDB
from bookkeeping_core.quote_candidates import QuoteCandidateMessage, QuoteCandidateRow
from bookkeeping_core.quote_validation import (
    QuoteValidationRowResult,
    QuoteValidationRun,
    VALIDATOR_VERSION_V1,
    build_validation_reason,
)
from tests.support.postgres_test_case import PostgresTestCase


def _normalize_json_field(value):
    return json.loads(value) if isinstance(value, str) else value


def _make_validation_candidate(*, message_id: str) -> QuoteCandidateMessage:
    return QuoteCandidateMessage(
        platform="wechat",
        source_group_key="wechat:validation-room",
        chat_id="validation-room",
        chat_name="验证报价群",
        message_id=message_id,
        source_name="Validator Source",
        sender_id="wxid-validator",
        sender_display="Validator Source",
        raw_message="[Apple]\nUS 100 95.5\nUK 50 0\nJP 10 9.1",
        message_time="2026-04-14 11:15:00",
        parser_kind="strict-section",
        parser_template="validator_template_v1",
        parser_version="candidate-v1",
        confidence=0.92,
        parse_status="parsed",
        message_fingerprint=f"fp-{message_id}",
        snapshot_hypothesis="delta_update",
        snapshot_hypothesis_reason="validator persistence regression fixture",
        rejection_reasons=[{"code": "validator_pending"}],
        run_kind="runtime",
        replay_of_quote_document_id=None,
        rows=[
            QuoteCandidateRow(
                row_ordinal=1,
                source_line="US 100 95.5",
                source_line_index=1,
                line_confidence=0.98,
                normalized_sku_key="Apple|USD|100|physical",
                normalization_status="normalized",
                row_publishable=False,
                publishability_basis="validator_pending",
                restriction_parse_status="clear",
                card_type="Apple",
                country_or_currency="USD",
                amount_range="100",
                multiplier="1x",
                form_factor="physical",
                price=95.5,
                quote_status="candidate",
                restriction_text="",
                field_sources={"source_line": "US 100 95.5"},
                rejection_reasons=[{"code": "validator_pending"}],
                parser_template="validator_template_v1",
                parser_version="candidate-v1",
            ),
            QuoteCandidateRow(
                row_ordinal=2,
                source_line="UK 50 0",
                source_line_index=2,
                line_confidence=0.83,
                normalized_sku_key="Apple|GBP|50|physical",
                normalization_status="normalized",
                row_publishable=False,
                publishability_basis="validator_pending",
                restriction_parse_status="clear",
                card_type="Apple",
                country_or_currency="GBP",
                amount_range="50",
                multiplier="1x",
                form_factor="physical",
                price=0,
                quote_status="candidate",
                restriction_text="",
                field_sources={"source_line": "UK 50 0"},
                rejection_reasons=[{"code": "validator_pending"}],
                parser_template="validator_template_v1",
                parser_version="candidate-v1",
            ),
            QuoteCandidateRow(
                row_ordinal=3,
                source_line="JP 10 9.1",
                source_line_index=3,
                line_confidence=0.61,
                normalized_sku_key="Apple|JPY|10|physical",
                normalization_status="partial",
                row_publishable=False,
                publishability_basis="validator_pending",
                restriction_parse_status="ambiguous",
                card_type="Apple",
                country_or_currency="JPY",
                amount_range="10",
                multiplier="1x",
                form_factor="physical",
                price=9.1,
                quote_status="candidate",
                restriction_text="ask before reload",
                field_sources={"source_line": "JP 10 9.1"},
                rejection_reasons=[{"code": "validator_pending"}],
                parser_template="validator_template_v1",
                parser_version="candidate-v1",
            ),
        ],
    )


class PostgresBackendTests(PostgresTestCase):
    def test_bookkeeping_db_rejects_sqlite_runtime_path(self) -> None:
        with self.assertRaisesRegex(ValueError, "PostgreSQL DSN"):
            BookkeepingDB("/tmp/bookkeeping.db")

    def test_bookkeeping_db_uses_current_schema_for_basic_reads_and_writes(
        self,
    ) -> None:
        db = self.make_db("backend-basic")
        try:
            db.set_group(
                platform="wechat",
                group_key="wechat:g-pg",
                chat_id="g-pg",
                chat_name="PG客户群",
                group_num=9,
            )
            tx_id = db.add_transaction(
                platform="wechat",
                group_key="wechat:g-pg",
                group_num=9,
                chat_id="g-pg",
                chat_name="PG客户群",
                sender_id="u-pg",
                sender_name="Postgres",
                message_id="msg-pg-1",
                input_sign=1,
                amount=88,
                category="rmb",
                rate=None,
                rmb_value=88,
                raw="rmb+88",
                created_at="2026-03-20 10:00:00",
            )
            self.assertGreater(tx_id, 0)
            history = db.get_history("wechat:g-pg", 10)
            self.assertEqual(len(history), 1)
            self.assertEqual(history[0]["chat_name"], "PG客户群")
        finally:
            db.close()

    def test_bookkeeping_db_fails_fast_when_schema_is_missing(self) -> None:
        schema_name = self._schema_name("blank")
        self._create_schema(schema_name)
        blank_dsn = self._dsn_with_search_path(schema_name)

        with self.assertRaisesRegex(RuntimeError, "PostgreSQL schema mismatch"):
            BookkeepingDB(blank_dsn)

    def test_bookkeeping_db_fails_fast_when_candidate_schema_is_missing(self) -> None:
        import psycopg

        schema_name = self._schema_name("candidate-missing")
        self._create_schema(schema_name)
        self._apply_schema(schema_name)
        broken_dsn = self._dsn_with_search_path(schema_name)

        with psycopg.connect(broken_dsn, autocommit=True) as conn:
            with conn.cursor() as cursor:
                cursor.execute("DROP TABLE quote_candidate_rows CASCADE")
                cursor.execute(
                    """
                    ALTER TABLE quote_documents
                    DROP COLUMN parser_kind,
                    DROP COLUMN message_fingerprint,
                    DROP COLUMN snapshot_hypothesis,
                    DROP COLUMN snapshot_hypothesis_reason,
                    DROP COLUMN rejection_reasons_json,
                    DROP COLUMN run_kind,
                    DROP COLUMN replay_of_quote_document_id
                    """
                )

        with self.assertRaisesRegex(RuntimeError, "PostgreSQL schema mismatch"):
            BookkeepingDB(broken_dsn)

    def test_bookkeeping_db_fails_fast_when_validator_schema_is_missing(self) -> None:
        import psycopg

        schema_name = self._schema_name("validator-missing")
        self._create_schema(schema_name)
        self._apply_schema(schema_name)
        broken_dsn = self._dsn_with_search_path(schema_name)

        with psycopg.connect(broken_dsn, autocommit=True) as conn:
            with conn.cursor() as cursor:
                cursor.execute("DROP TABLE quote_validation_row_results")
                cursor.execute(
                    """
                    ALTER TABLE quote_validation_runs
                    DROP COLUMN validator_version,
                    DROP COLUMN message_decision,
                    DROP COLUMN summary_json
                    """
                )

        with self.assertRaisesRegex(RuntimeError, "PostgreSQL schema mismatch"):
            BookkeepingDB(broken_dsn)

    def test_bookkeeping_db_close_method_is_available(self) -> None:
        db = self.make_db("backend-close")
        db.set_group(
            platform="wechat",
            group_key="wechat:g-close",
            chat_id="g-close",
            chat_name="Close Test",
            group_num=1,
        )
        db.close()

    def test_record_parse_result_and_query_parse_results(self) -> None:
        db = self.make_db("backend-parse-results")
        try:
            db.record_parse_result(
                platform="wechat",
                chat_id="room-1",
                message_id="msg-1",
                classification="transaction_like",
                parse_status="parsed",
                raw_text="+100rmb",
            )
            db.record_parse_result(
                platform="wechat",
                chat_id="room-1",
                message_id="msg-2",
                classification="normal_chat",
                parse_status="ignored",
                raw_text="hello",
            )
            db.record_parse_result(
                platform="whatsapp",
                chat_id="room-2",
                message_id="msg-3",
                classification="command",
                parse_status="parsed",
                raw_text="/set 2",
            )

            rows, total = db.query_parse_results()
            self.assertEqual(total, 3)
            self.assertEqual(len(rows), 3)

            rows, total = db.query_parse_results(platform="wechat")
            self.assertEqual(total, 2)
            self.assertEqual(len(rows), 2)

            rows, total = db.query_parse_results(classification="transaction_like")
            self.assertEqual(total, 1)
            self.assertEqual(rows[0]["message_id"], "msg-1")

            rows, total = db.query_parse_results(parse_status="ignored")
            self.assertEqual(total, 1)
            self.assertEqual(rows[0]["message_id"], "msg-2")
        finally:
            db.close()

    def test_record_parse_result_updates_on_conflict(self) -> None:
        db = self.make_db("backend-parse-results-update")
        try:
            db.record_parse_result(
                platform="wechat",
                chat_id="room-update",
                message_id="msg-update",
                classification="normal_chat",
                parse_status="ignored",
                raw_text="original",
            )

            db.record_parse_result(
                platform="wechat",
                chat_id="room-update",
                message_id="msg-update",
                classification="transaction_like",
                parse_status="parsed",
                raw_text="updated",
            )

            rows, total = db.query_parse_results(
                platform="wechat", chat_id="room-update"
            )
            self.assertEqual(total, 1)
            self.assertEqual(rows[0]["classification"], "transaction_like")
            self.assertEqual(rows[0]["parse_status"], "parsed")
            self.assertEqual(rows[0]["raw_text"], "updated")
        finally:
            db.close()

    def test_record_quote_candidate_bundle_persists_header_and_row_evidence(self) -> None:
        db = self.make_db("backend-quote-candidates")
        try:
            candidate = QuoteCandidateMessage(
                platform="wechat",
                source_group_key="wechat:quote-room",
                chat_id="quote-room",
                chat_name="供应商报价群",
                message_id="msg-candidate-1",
                source_name="Alice Supplier",
                sender_id="wxid-alice",
                sender_display="Alice Supplier",
                raw_message="[Apple]\nUS 100 95.5",
                message_time="2026-04-14 10:30:00",
                parser_kind="strict-section",
                parser_template="apple_us_v1",
                parser_version="candidate-v1",
                confidence=0.97,
                parse_status="parsed",
                message_fingerprint="fp-quote-001",
                snapshot_hypothesis="delta_update",
                snapshot_hypothesis_reason="single sku update line",
                rejection_reasons=[{"code": "needs-validator", "detail": "Phase 1 candidate only"}],
                run_kind="runtime",
                replay_of_quote_document_id=None,
                rows=[
                    QuoteCandidateRow(
                        row_ordinal=1,
                        source_line="US 100 95.5",
                        source_line_index=1,
                        line_confidence=0.97,
                        normalized_sku_key="Apple|USD|100|physical",
                        normalization_status="normalized",
                        row_publishable=False,
                        publishability_basis="validator_pending",
                        restriction_parse_status="clear",
                        card_type="Apple",
                        country_or_currency="USD",
                        amount_range="100",
                        multiplier="1x",
                        form_factor="physical",
                        price=95.5,
                        quote_status="candidate",
                        restriction_text="",
                        field_sources={
                            "card_type": {
                                "source_line": "US 100 95.5",
                                "raw_fragment": "Apple",
                            },
                            "price": {
                                "source_line": "US 100 95.5",
                                "raw_fragment": "95.5",
                            },
                        },
                        rejection_reasons=[{"code": "validator_pending"}],
                        parser_template="apple_us_v1",
                        parser_version="candidate-v1",
                    )
                ],
            )

            quote_document_id = db.record_quote_candidate_bundle(candidate=candidate)

            header = db.conn.execute(
                "SELECT * FROM quote_documents WHERE id = ?",
                (quote_document_id,),
            ).fetchone()
            self.assertIsNotNone(header)
            assert header is not None
            self.assertEqual(header["raw_text"], candidate.raw_message)
            self.assertEqual(header["source_name"], candidate.sender_display)
            self.assertEqual(header["sender_id"], candidate.sender_id)
            self.assertEqual(header["message_time"].isoformat(sep=" "), "2026-04-14 10:30:00")
            self.assertEqual(header["parser_kind"], candidate.parser_kind)
            self.assertEqual(float(header["confidence"]), candidate.confidence)
            self.assertEqual(header["message_fingerprint"], candidate.message_fingerprint)
            self.assertEqual(header["snapshot_hypothesis"], candidate.snapshot_hypothesis)
            self.assertEqual(
                header["snapshot_hypothesis_reason"],
                candidate.snapshot_hypothesis_reason,
            )
            self.assertEqual(header["run_kind"], candidate.run_kind)
            self.assertEqual(
                _normalize_json_field(header["rejection_reasons_json"]),
                candidate.rejection_reasons,
            )

            rows = db.list_quote_candidate_rows(quote_document_id=quote_document_id)
            self.assertEqual(len(rows), 1)
            row = rows[0]
            self.assertEqual(row["source_line"], "US 100 95.5")
            self.assertEqual(row["row_ordinal"], 1)
            self.assertEqual(row["normalized_sku_key"], "Apple|USD|100|physical")
            self.assertEqual(row["publishability_basis"], "validator_pending")
            self.assertEqual(
                _normalize_json_field(row["field_sources_json"]),
                candidate.rows[0].field_sources,
            )
            self.assertEqual(
                _normalize_json_field(row["rejection_reasons_json"]),
                candidate.rows[0].rejection_reasons,
            )

            fk_rows = db.conn.execute(
                """
                SELECT tc.table_name, kcu.column_name, ccu.table_name AS foreign_table_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                 AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                 AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                  AND tc.table_name IN ('quote_documents', 'quote_candidate_rows')
                ORDER BY tc.table_name, kcu.column_name
                """
            ).fetchall()
            fk_map = {
                (str(item["table_name"]), str(item["column_name"])): str(
                    item["foreign_table_name"]
                )
                for item in fk_rows
            }
            self.assertEqual(
                fk_map[("quote_candidate_rows", "quote_document_id")],
                "quote_documents",
            )
            self.assertEqual(
                fk_map[("quote_documents", "replay_of_quote_document_id")],
                "quote_documents",
            )

            count_row = db.conn.execute(
                "SELECT COUNT(*) AS cnt FROM quote_price_rows"
            ).fetchone()
            self.assertEqual(int(count_row["cnt"]), 0)
        finally:
            db.close()

    def test_record_quote_validation_run_persists_row_decisions(self) -> None:
        db = self.make_db("backend-quote-validation")
        try:
            quote_document_id = db.record_quote_candidate_bundle(
                candidate=_make_validation_candidate(
                    message_id="msg-validation-1"
                )
            )
            candidate_rows = db.list_quote_candidate_rows(
                quote_document_id=quote_document_id
            )
            validation_run_id = db.record_quote_validation_run(
                validation_run=QuoteValidationRun(
                    quote_document_id=quote_document_id,
                    validator_version=VALIDATOR_VERSION_V1,
                    run_kind="runtime",
                    message_decision="mixed_outcome",
                    validation_status="completed",
                    summary={
                        "message_codes": [
                            build_validation_reason(
                                "validation_mixed_outcome",
                                detail="publishable, rejected, and held rows all present",
                            )
                        ],
                        "candidate_row_ids": [
                            int(candidate_row["id"]) for candidate_row in candidate_rows
                        ],
                    },
                    row_results=[
                        QuoteValidationRowResult(
                            quote_candidate_row_id=int(candidate_rows[0]["id"]),
                            row_ordinal=1,
                            schema_status="passed",
                            business_status="passed",
                            final_decision="publishable",
                            decision_basis="schema_and_business_passed",
                        ),
                        QuoteValidationRowResult(
                            quote_candidate_row_id=int(candidate_rows[1]["id"]),
                            row_ordinal=2,
                            schema_status="failed",
                            business_status="skipped",
                            final_decision="rejected",
                            decision_basis="schema_failed",
                            rejection_reasons=[
                                build_validation_reason(
                                    "schema_invalid_price",
                                    detail="price must be positive",
                                    context={"value": "0"},
                                ),
                                build_validation_reason(
                                    "business_quote_status_not_active",
                                    detail="candidate status has not been promoted yet",
                                ),
                            ],
                        ),
                        QuoteValidationRowResult(
                            quote_candidate_row_id=int(candidate_rows[2]["id"]),
                            row_ordinal=3,
                            schema_status="passed",
                            business_status="held",
                            final_decision="held",
                            decision_basis="manual_review_required",
                            hold_reasons=[
                                build_validation_reason(
                                    "business_low_confidence_hold",
                                    detail="line confidence below safe publish threshold",
                                    context={"line_confidence": "0.61"},
                                ),
                                build_validation_reason(
                                    "business_ambiguous_restriction_hold",
                                    detail="restriction text is not machine-safe yet",
                                ),
                            ],
                        ),
                    ],
                )
            )

            latest_run = db.get_latest_quote_validation_run(
                quote_document_id=quote_document_id
            )
            self.assertIsNotNone(latest_run)
            assert latest_run is not None
            self.assertEqual(int(latest_run["id"]), validation_run_id)
            self.assertEqual(latest_run["validator_version"], VALIDATOR_VERSION_V1)
            self.assertEqual(latest_run["message_decision"], "mixed_outcome")
            self.assertEqual(latest_run["validation_status"], "completed")
            self.assertEqual(int(latest_run["candidate_row_count"]), 3)
            self.assertEqual(int(latest_run["publishable_row_count"]), 1)
            self.assertEqual(int(latest_run["rejected_row_count"]), 1)
            self.assertEqual(int(latest_run["held_row_count"]), 1)
            self.assertEqual(
                _normalize_json_field(latest_run["summary_json"]),
                {
                    "message_codes": [
                        {
                            "code": "validation_mixed_outcome",
                            "detail": "publishable, rejected, and held rows all present",
                        }
                    ],
                    "candidate_row_ids": [
                        int(candidate_row["id"]) for candidate_row in candidate_rows
                    ],
                },
            )

            row_results = db.list_quote_validation_row_results(
                validation_run_id=validation_run_id
            )
            self.assertEqual(len(row_results), 3)
            self.assertEqual(int(row_results[0]["quote_candidate_row_id"]), int(candidate_rows[0]["id"]))
            self.assertEqual(row_results[0]["final_decision"], "publishable")
            self.assertEqual(
                _normalize_json_field(row_results[1]["rejection_reasons_json"]),
                [
                    {
                        "code": "schema_invalid_price",
                        "detail": "price must be positive",
                        "context": {"value": "0"},
                    },
                    {
                        "code": "business_quote_status_not_active",
                        "detail": "candidate status has not been promoted yet",
                    },
                ],
            )
            self.assertEqual(
                _normalize_json_field(row_results[2]["hold_reasons_json"]),
                [
                    {
                        "code": "business_low_confidence_hold",
                        "detail": "line confidence below safe publish threshold",
                        "context": {"line_confidence": "0.61"},
                    },
                    {
                        "code": "business_ambiguous_restriction_hold",
                        "detail": "restriction text is not machine-safe yet",
                    },
                ],
            )

            original_candidate_rows = db.list_quote_candidate_rows(
                quote_document_id=quote_document_id
            )
            self.assertEqual(
                _normalize_json_field(original_candidate_rows[1]["rejection_reasons_json"]),
                [{"code": "validator_pending"}],
            )

            fk_rows = db.conn.execute(
                """
                SELECT tc.table_name, kcu.column_name, ccu.table_name AS foreign_table_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                 AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                 AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                  AND tc.table_name IN ('quote_validation_runs', 'quote_validation_row_results')
                ORDER BY tc.table_name, kcu.column_name
                """
            ).fetchall()
            fk_map = {
                (str(item["table_name"]), str(item["column_name"])): str(
                    item["foreign_table_name"]
                )
                for item in fk_rows
            }
            self.assertEqual(
                fk_map[("quote_validation_runs", "quote_document_id")],
                "quote_documents",
            )
            self.assertEqual(
                fk_map[("quote_validation_row_results", "validation_run_id")],
                "quote_validation_runs",
            )
            self.assertEqual(
                fk_map[("quote_validation_row_results", "quote_candidate_row_id")],
                "quote_candidate_rows",
            )

            count_row = db.conn.execute(
                "SELECT COUNT(*) AS cnt FROM quote_price_rows"
            ).fetchone()
            self.assertEqual(int(count_row["cnt"]), 0)
        finally:
            db.close()


class RepairCaseTests(PostgresTestCase):
    def test_packaging_quote_exception_creates_one_repair_case_per_exception(self) -> None:
        from bookkeeping_core.repair_cases import package_quote_repair_case

        db = self.make_db("repair-case-idempotent")
        try:
            db.upsert_quote_group_profile(
                platform="wechat",
                chat_id="repair-room",
                chat_name="修复报价群",
                default_card_type="Apple",
                default_country_or_currency="USD",
                default_form_factor="横白卡",
                default_multiplier="1x",
                parser_template="repair-template-v1",
                template_config=json.dumps(
                    {"version": "repair-template-v1", "sections": ["Apple"]},
                    ensure_ascii=False,
                ),
            )
            quote_document_id = db.record_quote_candidate_bundle(
                candidate=_make_validation_candidate(message_id="repair-msg-1")
            )
            candidate_rows = db.list_quote_candidate_rows(
                quote_document_id=quote_document_id
            )
            validation_run_id = db.record_quote_validation_run(
                validation_run=QuoteValidationRun(
                    quote_document_id=quote_document_id,
                    validator_version=VALIDATOR_VERSION_V1,
                    run_kind="runtime",
                    message_decision="no_publish",
                    validation_status="completed",
                    summary={
                        "message_reasons": [
                            build_validation_reason(
                                "validation_only_failure",
                                detail="repair-case packaging regression",
                            )
                        ]
                    },
                    row_results=[
                        QuoteValidationRowResult(
                            quote_candidate_row_id=int(candidate_rows[0]["id"]),
                            row_ordinal=1,
                            schema_status="passed",
                            business_status="held",
                            final_decision="held",
                            decision_basis="manual_review_required",
                            hold_reasons=[
                                build_validation_reason(
                                    "business_low_confidence_hold",
                                    detail="line confidence below publish threshold",
                                )
                            ],
                        )
                    ],
                )
            )
            exception_id = db.record_quote_exception(
                quote_document_id=quote_document_id,
                platform="wechat",
                source_group_key="wechat:repair-room",
                chat_id="repair-room",
                chat_name="修复报价群",
                source_name="Repair Source",
                sender_id="wxid-repair",
                reason="strict_match_failed",
                source_line="US 100 95.5",
                raw_text="[Apple]\nUS 100 95.5\nUK 50 0",
                message_time="2026-04-14 11:15:00",
                parser_template="repair-template-v1",
                parser_version="candidate-v1",
                confidence=0.41,
            )

            first_case = package_quote_repair_case(db=db, exception_id=exception_id)
            second_case = package_quote_repair_case(db=db, exception_id=exception_id)

            self.assertEqual(int(first_case["id"]), int(second_case["id"]))
            count_row = db.conn.execute(
                "SELECT COUNT(*) AS cnt FROM quote_repair_cases WHERE origin_exception_id = ?",
                (exception_id,),
            ).fetchone()
            self.assertEqual(int(count_row["cnt"]), 1)

            stored_case = db.conn.execute(
                "SELECT * FROM quote_repair_cases WHERE origin_exception_id = ?",
                (exception_id,),
            ).fetchone()
            self.assertIsNotNone(stored_case)
            assert stored_case is not None
            self.assertEqual(int(stored_case["origin_quote_document_id"]), quote_document_id)
            self.assertEqual(int(stored_case["origin_validation_run_id"]), validation_run_id)
            self.assertEqual(str(stored_case["lifecycle_state"]), "packaged")
        finally:
            db.close()

    def test_packaging_freezes_origin_and_group_profile_snapshots(self) -> None:
        from bookkeeping_core.repair_cases import package_quote_repair_case

        db = self.make_db("repair-case-snapshots")
        try:
            profile_id = db.upsert_quote_group_profile(
                platform="wechat",
                chat_id="repair-snapshot-room",
                chat_name="修复快照群",
                default_card_type="Apple",
                default_country_or_currency="USD",
                default_form_factor="横白卡",
                default_multiplier="1x",
                parser_template="repair-template-v2",
                template_config=json.dumps(
                    {"version": "repair-template-v2", "sections": ["Apple", "Xbox"]},
                    ensure_ascii=False,
                ),
            )
            quote_document_id = db.record_quote_candidate_bundle(
                candidate=_make_validation_candidate(message_id="repair-msg-2")
            )
            validation_run_id = db.record_quote_validation_run(
                validation_run=QuoteValidationRun(
                    quote_document_id=quote_document_id,
                    validator_version=VALIDATOR_VERSION_V1,
                    run_kind="runtime",
                    message_decision="no_publish",
                    validation_status="completed",
                    summary={
                        "message_reasons": [
                            build_validation_reason(
                                "validator_rejected_only",
                                detail="all rows rejected",
                            )
                        ]
                    },
                )
            )
            exception_id = db.record_quote_exception(
                quote_document_id=quote_document_id,
                platform="wechat",
                source_group_key="wechat:repair-snapshot-room",
                chat_id="repair-snapshot-room",
                chat_name="修复快照群",
                source_name="Repair Source",
                sender_id="wxid-repair",
                reason="missing_group_template",
                source_line="【Apple】",
                raw_text="[Apple]\nUS 100 95.5",
                message_time="2026-04-14 11:20:00",
                parser_template="group-parser",
                parser_version="candidate-v1",
                confidence=0.0,
            )

            package_quote_repair_case(db=db, exception_id=exception_id)

            stored_case = db.conn.execute(
                "SELECT * FROM quote_repair_cases WHERE origin_exception_id = ?",
                (exception_id,),
            ).fetchone()
            self.assertIsNotNone(stored_case)
            assert stored_case is not None
            self.assertEqual(int(stored_case["group_profile_id"]), profile_id)
            self.assertEqual(str(stored_case["raw_message_snapshot"]), "[Apple]\nUS 100 95.5")
            self.assertEqual(str(stored_case["source_line_snapshot"]), "【Apple】")
            self.assertEqual(int(stored_case["origin_quote_document_id"]), quote_document_id)
            self.assertEqual(int(stored_case["origin_validation_run_id"]), validation_run_id)
            self.assertEqual(str(stored_case["current_failure_reason"]), "missing_group_template")

            profile_snapshot = _normalize_json_field(
                stored_case["profile_snapshot_json"]
            )
            self.assertEqual(profile_snapshot["parser_template"], "repair-template-v2")
            self.assertEqual(profile_snapshot["default_card_type"], "Apple")
            self.assertEqual(profile_snapshot["template_config"]["version"], "repair-template-v2")

            validation_summary = _normalize_json_field(
                stored_case["validation_summary_json"]
            )
            self.assertEqual(
                validation_summary["message_reasons"][0]["code"],
                "validator_rejected_only",
            )

            exception_row = db.get_quote_exception(exception_id=exception_id)
            self.assertEqual(str(exception_row["reason"]), "missing_group_template")
            self.assertEqual(str(exception_row["resolution_status"]), "open")

            latest_run = db.get_latest_quote_validation_run(
                quote_document_id=quote_document_id
            )
            self.assertEqual(int(latest_run["id"]), validation_run_id)
        finally:
            db.close()

    def test_validation_only_failure_packaging_tracks_validator_lineage(self) -> None:
        from bookkeeping_core.repair_cases import package_quote_repair_case

        db = self.make_db("repair-case-validation-only")
        try:
            quote_document_id = db.record_quote_candidate_bundle(
                candidate=_make_validation_candidate(message_id="repair-msg-3")
            )
            validation_run_id = db.record_quote_validation_run(
                validation_run=QuoteValidationRun(
                    quote_document_id=quote_document_id,
                    validator_version=VALIDATOR_VERSION_V1,
                    run_kind="runtime",
                    message_decision="no_publish",
                    validation_status="completed",
                    summary={
                        "message_reasons": [
                            build_validation_reason(
                                "message_no_candidate_rows",
                                detail="candidate bundle persisted with zero publishable rows",
                            )
                        ],
                        "row_decision_counts": {
                            "publishable": 0,
                            "rejected": 0,
                            "held": 0,
                        },
                    },
                )
            )
            exception_id = db.record_quote_exception(
                quote_document_id=quote_document_id,
                platform="wechat",
                source_group_key="wechat:repair-validation-only",
                chat_id="repair-validation-only",
                chat_name="纯校验失败群",
                source_name="Validator",
                sender_id="wxid-validator",
                reason="validator_no_publish",
                source_line="[Apple]",
                raw_text="[Apple]",
                message_time="2026-04-14 11:30:00",
                parser_template="validator_template_v1",
                parser_version="candidate-v1",
                confidence=0.0,
            )

            repair_case = package_quote_repair_case(db=db, exception_id=exception_id)

            self.assertEqual(int(repair_case["origin_exception_id"]), exception_id)
            self.assertEqual(int(repair_case["origin_quote_document_id"]), quote_document_id)
            self.assertEqual(int(repair_case["origin_validation_run_id"]), validation_run_id)
            self.assertEqual(str(repair_case["lifecycle_state"]), "packaged")
            self.assertEqual(str(repair_case["current_failure_reason"]), "validator_no_publish")
        finally:
            db.close()

    def test_create_baseline_attempt_is_idempotent_and_links_case_once(self) -> None:
        from bookkeeping_core.repair_cases import (
            create_baseline_repair_attempt,
            package_quote_repair_case,
        )

        db = self.make_db("repair-case-baseline-idempotent")
        try:
            profile_id = db.upsert_quote_group_profile(
                platform="wechat",
                chat_id="repair-baseline-room",
                chat_name="基线回放群",
                default_card_type="Apple",
                default_country_or_currency="USD",
                default_form_factor="横白卡",
                default_multiplier="1x",
                parser_template="repair-template-baseline",
                template_config=json.dumps(
                    {"version": "repair-template-baseline", "sections": ["Apple"]},
                    ensure_ascii=False,
                ),
            )
            origin_document_id = db.record_quote_candidate_bundle(
                candidate=_make_validation_candidate(message_id="repair-baseline-origin")
            )
            origin_validation_run_id = db.record_quote_validation_run(
                validation_run=QuoteValidationRun(
                    quote_document_id=origin_document_id,
                    validator_version=VALIDATOR_VERSION_V1,
                    run_kind="runtime",
                    message_decision="no_publish",
                    validation_status="completed",
                    summary={"message_reasons": [build_validation_reason("strict_match_failed")]},
                )
            )
            exception_id = db.record_quote_exception(
                quote_document_id=origin_document_id,
                platform="wechat",
                source_group_key="wechat:repair-baseline-room",
                chat_id="repair-baseline-room",
                chat_name="基线回放群",
                source_name="Repair Source",
                sender_id="wxid-repair",
                reason="strict_match_failed",
                source_line="US 100 95.5",
                raw_text="[Apple]\nUS 100 95.5",
                message_time="2026-04-14 12:00:00",
                parser_template="repair-template-baseline",
                parser_version="candidate-v1",
                confidence=0.52,
            )
            repair_case = package_quote_repair_case(db=db, exception_id=exception_id)

            baseline_document_id = db.record_quote_candidate_bundle(
                candidate=_make_validation_candidate(message_id="repair-baseline-replay")
            )
            baseline_validation_run_id = db.record_quote_validation_run(
                validation_run=QuoteValidationRun(
                    quote_document_id=baseline_document_id,
                    validator_version=VALIDATOR_VERSION_V1,
                    run_kind="replay",
                    message_decision="no_publish",
                    validation_status="completed",
                    summary={"message_reasons": [build_validation_reason("strict_match_failed")]},
                )
            )

            first_attempt = create_baseline_repair_attempt(
                db=db,
                repair_case_id=int(repair_case["id"]),
                replay_result={
                    "replayed": True,
                    "reason": "",
                    "quote_document_id": baseline_document_id,
                    "validation_run_id": baseline_validation_run_id,
                    "remaining_lines": ["US 100 95.5"],
                    "mutated_active_facts": False,
                    "comparison": {
                        "classification": "same",
                        "origin_row_count": 3,
                        "attempt_row_count": 3,
                        "origin_message_decision": "no_publish",
                        "attempt_message_decision": "no_publish",
                        "exception_count": 0,
                    },
                },
            )
            second_attempt = create_baseline_repair_attempt(
                db=db,
                repair_case_id=int(repair_case["id"]),
                replay_result={
                    "replayed": True,
                    "reason": "",
                    "quote_document_id": baseline_document_id + 99,
                    "validation_run_id": baseline_validation_run_id + 99,
                    "remaining_lines": ["should-not-overwrite"],
                    "mutated_active_facts": False,
                    "comparison": {"classification": "worse"},
                },
            )

            self.assertEqual(int(first_attempt["id"]), int(second_attempt["id"]))
            self.assertEqual(int(first_attempt["attempt_number"]), 0)
            self.assertEqual(str(first_attempt["attempt_kind"]), "baseline")
            count_row = db.conn.execute(
                """
                SELECT COUNT(*) AS cnt
                FROM quote_repair_case_attempts
                WHERE repair_case_id = ?
                """,
                (int(repair_case["id"]),),
            ).fetchone()
            self.assertEqual(int(count_row["cnt"]), 1)

            stored_case = db.conn.execute(
                "SELECT * FROM quote_repair_cases WHERE id = ?",
                (int(repair_case["id"]),),
            ).fetchone()
            self.assertIsNotNone(stored_case)
            assert stored_case is not None
            self.assertEqual(int(stored_case["baseline_attempt_id"]), int(first_attempt["id"]))
            self.assertEqual(int(stored_case["group_profile_id"]), profile_id)
            self.assertEqual(int(stored_case["origin_quote_document_id"]), origin_document_id)
            self.assertEqual(
                int(stored_case["origin_validation_run_id"]), origin_validation_run_id
            )
        finally:
            db.close()

    def test_create_baseline_attempt_persists_lineage_and_frozen_snapshots(self) -> None:
        from bookkeeping_core.repair_cases import (
            create_baseline_repair_attempt,
            package_quote_repair_case,
        )

        db = self.make_db("repair-case-baseline-lineage")
        try:
            profile_id = db.upsert_quote_group_profile(
                platform="wechat",
                chat_id="repair-baseline-lineage",
                chat_name="基线谱系群",
                default_card_type="Apple",
                default_country_or_currency="USD",
                default_form_factor="横白卡",
                default_multiplier="1x",
                parser_template="repair-template-lineage",
                template_config=json.dumps(
                    {"version": "repair-template-lineage", "sections": ["Apple", "Xbox"]},
                    ensure_ascii=False,
                ),
            )
            origin_document_id = db.record_quote_candidate_bundle(
                candidate=_make_validation_candidate(message_id="repair-lineage-origin")
            )
            origin_validation_run_id = db.record_quote_validation_run(
                validation_run=QuoteValidationRun(
                    quote_document_id=origin_document_id,
                    validator_version=VALIDATOR_VERSION_V1,
                    run_kind="runtime",
                    message_decision="no_publish",
                    validation_status="completed",
                    summary={
                        "message_reasons": [
                            build_validation_reason("validator_rejected_only")
                        ]
                    },
                )
            )
            exception_id = db.record_quote_exception(
                quote_document_id=origin_document_id,
                platform="wechat",
                source_group_key="wechat:repair-baseline-lineage",
                chat_id="repair-baseline-lineage",
                chat_name="基线谱系群",
                source_name="Repair Source",
                sender_id="wxid-repair",
                reason="missing_group_template",
                source_line="[Apple]",
                raw_text="[Apple]\nUS 100 95.5",
                message_time="2026-04-14 12:05:00",
                parser_template="group-parser",
                parser_version="candidate-v1",
                confidence=0.0,
            )
            repair_case = package_quote_repair_case(db=db, exception_id=exception_id)

            baseline_document_id = db.record_quote_candidate_bundle(
                candidate=_make_validation_candidate(message_id="repair-lineage-replay")
            )
            baseline_validation_run_id = db.record_quote_validation_run(
                validation_run=QuoteValidationRun(
                    quote_document_id=baseline_document_id,
                    validator_version=VALIDATOR_VERSION_V1,
                    run_kind="replay",
                    message_decision="held_only",
                    validation_status="completed",
                    summary={
                        "message_reasons": [
                            build_validation_reason(
                                "business_low_confidence_hold",
                                detail="replay still conservative",
                            )
                        ]
                    },
                )
            )

            attempt = create_baseline_repair_attempt(
                db=db,
                repair_case_id=int(repair_case["id"]),
                replay_result={
                    "replayed": True,
                    "reason": "",
                    "quote_document_id": baseline_document_id,
                    "validation_run_id": baseline_validation_run_id,
                    "remaining_lines": ["leftover-a", "leftover-b"],
                    "mutated_active_facts": False,
                    "comparison": {
                        "classification": "better",
                        "origin_row_count": 0,
                        "attempt_row_count": 3,
                        "origin_message_decision": "no_publish",
                        "attempt_message_decision": "held_only",
                        "exception_count": 1,
                    },
                },
            )

            stored_attempt = db.conn.execute(
                "SELECT * FROM quote_repair_case_attempts WHERE id = ?",
                (int(attempt["id"]),),
            ).fetchone()
            self.assertIsNotNone(stored_attempt)
            assert stored_attempt is not None
            self.assertEqual(int(stored_attempt["repair_case_id"]), int(repair_case["id"]))
            self.assertEqual(int(stored_attempt["quote_document_id"]), baseline_document_id)
            self.assertEqual(
                int(stored_attempt["validation_run_id"]), baseline_validation_run_id
            )
            self.assertEqual(
                int(stored_attempt["replayed_from_quote_document_id"]), origin_document_id
            )
            self.assertEqual(int(stored_attempt["group_profile_id"]), profile_id)
            self.assertEqual(str(stored_attempt["outcome_state"]), "completed")
            self.assertEqual(str(stored_attempt["failure_note"]), "")

            profile_snapshot = _normalize_json_field(
                stored_attempt["profile_snapshot_json"]
            )
            self.assertEqual(profile_snapshot["parser_template"], "repair-template-lineage")
            self.assertEqual(
                profile_snapshot["template_config"]["version"], "repair-template-lineage"
            )

            remaining_lines = _normalize_json_field(stored_attempt["remaining_lines_json"])
            self.assertEqual(remaining_lines, ["leftover-a", "leftover-b"])

            summary = _normalize_json_field(stored_attempt["attempt_summary_json"])
            self.assertEqual(summary["comparison"]["classification"], "better")
            self.assertEqual(summary["mutated_active_facts"], False)

            stored_case = db.conn.execute(
                "SELECT * FROM quote_repair_cases WHERE id = ?",
                (int(repair_case["id"]),),
            ).fetchone()
            self.assertIsNotNone(stored_case)
            assert stored_case is not None
            self.assertEqual(int(stored_case["origin_quote_document_id"]), origin_document_id)
            self.assertEqual(
                int(stored_case["origin_validation_run_id"]), origin_validation_run_id
            )
            self.assertEqual(int(stored_case["baseline_attempt_id"]), int(attempt["id"]))
        finally:
            db.close()

    def test_create_baseline_attempt_records_blocked_outcome_for_missing_prerequisites(
        self,
    ) -> None:
        from bookkeeping_core.repair_cases import (
            create_baseline_repair_attempt,
            package_quote_repair_case,
        )

        db = self.make_db("repair-case-baseline-blocked")
        try:
            origin_document_id = db.record_quote_candidate_bundle(
                candidate=_make_validation_candidate(message_id="repair-blocked-origin")
            )
            db.record_quote_validation_run(
                validation_run=QuoteValidationRun(
                    quote_document_id=origin_document_id,
                    validator_version=VALIDATOR_VERSION_V1,
                    run_kind="runtime",
                    message_decision="no_publish",
                    validation_status="completed",
                    summary={"message_reasons": [build_validation_reason("missing_group_template")]},
                )
            )
            exception_id = db.record_quote_exception(
                quote_document_id=origin_document_id,
                platform="wechat",
                source_group_key="wechat:repair-blocked-room",
                chat_id="repair-blocked-room",
                chat_name="基线阻塞群",
                source_name="Repair Source",
                sender_id="wxid-repair",
                reason="missing_group_template",
                source_line="[Apple]",
                raw_text="[Apple]\nUS 100 95.5",
                message_time="2026-04-14 12:10:00",
                parser_template="group-parser",
                parser_version="candidate-v1",
                confidence=0.0,
            )
            repair_case = package_quote_repair_case(db=db, exception_id=exception_id)

            attempt = create_baseline_repair_attempt(
                db=db,
                repair_case_id=int(repair_case["id"]),
                replay_result={
                    "replayed": False,
                    "reason": "missing_group_profile",
                    "rows": 0,
                    "exceptions": 0,
                    "mutated_active_facts": False,
                    "comparison": {"classification": "blocked"},
                },
            )

            self.assertEqual(str(attempt["attempt_kind"]), "baseline")
            self.assertEqual(int(attempt["attempt_number"]), 0)
            self.assertEqual(str(attempt["outcome_state"]), "blocked")
            summary = _normalize_json_field(attempt["attempt_summary_json"])
            self.assertEqual(summary["comparison"]["classification"], "blocked")
            self.assertEqual(summary["blocked_reason"], "missing_group_profile")
            self.assertEqual(summary["mutated_active_facts"], False)
            self.assertEqual(str(attempt["failure_note"]), "missing_group_profile")

            stored_case = db.conn.execute(
                "SELECT * FROM quote_repair_cases WHERE id = ?",
                (int(repair_case["id"]),),
            ).fetchone()
            self.assertIsNotNone(stored_case)
            assert stored_case is not None
            self.assertEqual(int(stored_case["baseline_attempt_id"]), int(attempt["id"]))
            self.assertEqual(int(stored_case["origin_quote_document_id"]), origin_document_id)
        finally:
            db.close()

    def test_record_quote_repair_attempt_is_append_only_and_escalates_after_third_failure(
        self,
    ) -> None:
        from bookkeeping_core.repair_cases import (
            REPAIR_CASE_STATE_ESCALATED,
            REPAIR_CASE_STATE_READY_FOR_ATTEMPT,
            advance_quote_repair_case_state,
            create_baseline_repair_attempt,
            package_quote_repair_case,
            record_quote_repair_attempt,
        )

        db = self.make_db("repair-case-attempt-history")
        try:
            db.upsert_quote_group_profile(
                platform="wechat",
                chat_id="repair-attempt-history",
                chat_name="尝试历史群",
                default_card_type="Apple",
                default_country_or_currency="USD",
                default_form_factor="physical",
                default_multiplier="1x",
                parser_template="repair-template-attempts",
                template_config=json.dumps(
                    {"version": "repair-template-attempts", "sections": ["Apple"]},
                    ensure_ascii=False,
                ),
            )
            origin_document_id = db.record_quote_candidate_bundle(
                candidate=_make_validation_candidate(message_id="repair-attempt-origin")
            )
            db.record_quote_validation_run(
                validation_run=QuoteValidationRun(
                    quote_document_id=origin_document_id,
                    validator_version=VALIDATOR_VERSION_V1,
                    run_kind="runtime",
                    message_decision="no_publish",
                    validation_status="completed",
                    summary={"message_reasons": [build_validation_reason("strict_match_failed")]},
                )
            )
            exception_id = db.record_quote_exception(
                quote_document_id=origin_document_id,
                platform="wechat",
                source_group_key="wechat:repair-attempt-history",
                chat_id="repair-attempt-history",
                chat_name="尝试历史群",
                source_name="Repair Source",
                sender_id="wxid-repair",
                reason="strict_match_failed",
                source_line="US 100 95.5",
                raw_text="[Apple]\nUS 100 95.5",
                message_time="2026-04-14 12:15:00",
                parser_template="repair-template-attempts",
                parser_version="candidate-v1",
                confidence=0.4,
            )
            repair_case = package_quote_repair_case(db=db, exception_id=exception_id)
            baseline_attempt = create_baseline_repair_attempt(
                db=db,
                repair_case_id=int(repair_case["id"]),
                replay_result={
                    "replayed": True,
                    "reason": "",
                    "rows": 1,
                    "exceptions": 0,
                    "remaining_lines": ["US 100 95.5"],
                    "mutated_active_facts": False,
                    "message_decision": "no_publish",
                    "publishable_row_count": 0,
                    "held_row_count": 0,
                    "rejected_row_count": 1,
                    "comparison": {"classification": "same"},
                },
            )
            advance_quote_repair_case_state(
                db=db,
                repair_case_id=int(repair_case["id"]),
                next_state=REPAIR_CASE_STATE_READY_FOR_ATTEMPT,
            )

            first_attempt = record_quote_repair_attempt(
                db=db,
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
            second_attempt = record_quote_repair_attempt(
                db=db,
                repair_case_id=int(repair_case["id"]),
                trigger="manual_retry",
                replay_result={
                    "replayed": True,
                    "reason": "strict-match-regressed",
                    "rows": 0,
                    "exceptions": 1,
                    "remaining_lines": ["US 100 95.5", "UK 50 48.0"],
                    "mutated_active_facts": False,
                    "message_decision": "no_publish",
                    "publishable_row_count": 0,
                    "held_row_count": 0,
                    "rejected_row_count": 0,
                    "comparison": {"classification": "worse"},
                },
            )
            third_attempt = record_quote_repair_attempt(
                db=db,
                repair_case_id=int(repair_case["id"]),
                trigger="manual_retry",
                replay_result={
                    "replayed": True,
                    "reason": "strict-match-third-failure",
                    "rows": 0,
                    "exceptions": 1,
                    "remaining_lines": ["US 100 95.5", "UK 50 48.0", "JP 10 9.1"],
                    "mutated_active_facts": False,
                    "message_decision": "no_publish",
                    "publishable_row_count": 0,
                    "held_row_count": 0,
                    "rejected_row_count": 0,
                    "comparison": {"classification": "same"},
                },
            )

            refreshed_baseline = db.get_quote_repair_case_attempt(
                attempt_id=int(baseline_attempt["id"])
            )
            self.assertIsNotNone(refreshed_baseline)
            assert refreshed_baseline is not None
            self.assertEqual(int(refreshed_baseline["attempt_number"]), 0)
            self.assertEqual(str(refreshed_baseline["attempt_kind"]), "baseline")
            self.assertEqual(str(refreshed_baseline["failure_note"]), "")

            self.assertEqual(int(first_attempt["attempt_number"]), 1)
            self.assertEqual(int(second_attempt["attempt_number"]), 2)
            self.assertEqual(str(first_attempt["failure_note"]), "strict-match-still-failing")
            self.assertEqual(str(second_attempt["failure_note"]), "strict-match-regressed")

            stored_case = db.get_quote_repair_case(repair_case_id=int(repair_case["id"]))
            self.assertIsNotNone(stored_case)
            assert stored_case is not None
            self.assertEqual(str(stored_case["lifecycle_state"]), REPAIR_CASE_STATE_ESCALATED)
            summary = _normalize_json_field(stored_case["case_summary_json"])
            self.assertEqual(summary["attempt_count"], 3)
            self.assertEqual(summary["last_attempt_outcome"], "completed")
            self.assertEqual(summary["escalation_state"], "ready")
            self.assertIsNone(summary["closed_at"])
            self.assertEqual(len(summary["failure_log_json"]), 3)
            self.assertEqual(
                [entry["attempt_number"] for entry in summary["failure_log_json"]],
                [1, 2, 3],
            )
            self.assertEqual(
                [entry["failure_note"] for entry in summary["failure_log_json"]],
                [
                    "strict-match-still-failing",
                    "strict-match-regressed",
                    "strict-match-third-failure",
                ],
            )
            self.assertEqual(int(third_attempt["attempt_number"]), 3)
        finally:
            db.close()

    def test_begin_quote_repair_remediation_attempt_persists_pending_metadata(self) -> None:
        from bookkeeping_core.remediation import (
            REMEDIATION_ATTEMPT_KIND,
            REMEDIATION_OUTCOME_PENDING,
            begin_quote_repair_remediation_attempt,
        )
        from bookkeeping_core.repair_cases import (
            REPAIR_CASE_STATE_READY_FOR_ATTEMPT,
            advance_quote_repair_case_state,
            create_baseline_repair_attempt,
            package_quote_repair_case,
        )

        db = self.make_db("repair-remediation-pending")
        try:
            db.upsert_quote_group_profile(
                platform="wechat",
                chat_id="repair-remediation-pending",
                chat_name="修复补丁群",
                default_card_type="Apple",
                default_country_or_currency="USD",
                default_form_factor="physical",
                default_multiplier="1x",
                parser_template="repair-template-remediation",
                template_config=json.dumps(
                    {"version": "repair-template-remediation", "sections": ["Apple"]},
                    ensure_ascii=False,
                ),
            )
            origin_document_id = db.record_quote_candidate_bundle(
                candidate=_make_validation_candidate(message_id="repair-remediation-origin")
            )
            db.record_quote_validation_run(
                validation_run=QuoteValidationRun(
                    quote_document_id=origin_document_id,
                    validator_version=VALIDATOR_VERSION_V1,
                    run_kind="runtime",
                    message_decision="no_publish",
                    validation_status="completed",
                    summary={"message_reasons": [build_validation_reason("strict_match_failed")]},
                )
            )
            exception_id = db.record_quote_exception(
                quote_document_id=origin_document_id,
                platform="wechat",
                source_group_key="wechat:repair-remediation-pending",
                chat_id="repair-remediation-pending",
                chat_name="修复补丁群",
                source_name="Repair Source",
                sender_id="wxid-remediation",
                reason="strict_match_failed",
                source_line="US 100 95.5",
                raw_text="[Apple]\nUS 100 95.5",
                message_time="2026-04-14 12:35:00",
                parser_template="repair-template-remediation",
                parser_version="candidate-v1",
                confidence=0.4,
            )
            repair_case = package_quote_repair_case(db=db, exception_id=exception_id)
            create_baseline_repair_attempt(
                db=db,
                repair_case_id=int(repair_case["id"]),
                replay_result={
                    "replayed": True,
                    "reason": "",
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
            advance_quote_repair_case_state(
                db=db,
                repair_case_id=int(repair_case["id"]),
                next_state=REPAIR_CASE_STATE_READY_FOR_ATTEMPT,
            )

            attempt = begin_quote_repair_remediation_attempt(
                db=db,
                repair_case_id=int(repair_case["id"]),
                trigger="subagent_retry",
                proposal_scope="group_profile",
                proposal_kind="template_patch",
            )

            self.assertEqual(str(attempt["attempt_kind"]), REMEDIATION_ATTEMPT_KIND)
            self.assertEqual(int(attempt["attempt_number"]), 1)
            self.assertEqual(str(attempt["outcome_state"]), REMEDIATION_OUTCOME_PENDING)
            summary = _normalize_json_field(attempt["attempt_summary_json"])
            self.assertEqual(summary["protocol"], "quote_remediation_v1")
            self.assertEqual(summary["proposal_scope"], "group_profile")
            self.assertEqual(summary["proposal_kind"], "template_patch")
            self.assertEqual(summary["comparison"]["classification"], "pending")
            self.assertEqual(summary["history_read"]["required"], False)
            self.assertEqual(summary["history_read"]["consumed"], True)
            stored_case = db.get_quote_repair_case(repair_case_id=int(repair_case["id"]))
            assert stored_case is not None
            case_summary = _normalize_json_field(stored_case["case_summary_json"])
            self.assertEqual(case_summary["attempt_count"], 1)
            self.assertEqual(case_summary["remediation_attempt_limit"], 3)
            self.assertEqual(case_summary["remediation_attempts_remaining"], 2)
        finally:
            db.close()

    def test_begin_quote_repair_remediation_attempt_requires_history_fingerprint(self) -> None:
        from bookkeeping_core.remediation import (
            begin_quote_repair_remediation_attempt,
            build_quote_repair_history_fingerprint,
        )
        from bookkeeping_core.repair_cases import (
            REPAIR_CASE_STATE_READY_FOR_ATTEMPT,
            advance_quote_repair_case_state,
            create_baseline_repair_attempt,
            package_quote_repair_case,
            record_quote_repair_attempt,
        )

        db = self.make_db("repair-remediation-history")
        try:
            db.upsert_quote_group_profile(
                platform="wechat",
                chat_id="repair-remediation-history",
                chat_name="修复历史群",
                default_card_type="Apple",
                default_country_or_currency="USD",
                default_form_factor="physical",
                default_multiplier="1x",
                parser_template="repair-template-history",
                template_config=json.dumps(
                    {"version": "repair-template-history", "sections": ["Apple"]},
                    ensure_ascii=False,
                ),
            )
            origin_document_id = db.record_quote_candidate_bundle(
                candidate=_make_validation_candidate(message_id="repair-remediation-history")
            )
            db.record_quote_validation_run(
                validation_run=QuoteValidationRun(
                    quote_document_id=origin_document_id,
                    validator_version=VALIDATOR_VERSION_V1,
                    run_kind="runtime",
                    message_decision="no_publish",
                    validation_status="completed",
                    summary={"message_reasons": [build_validation_reason("strict_match_failed")]},
                )
            )
            exception_id = db.record_quote_exception(
                quote_document_id=origin_document_id,
                platform="wechat",
                source_group_key="wechat:repair-remediation-history",
                chat_id="repair-remediation-history",
                chat_name="修复历史群",
                source_name="Repair Source",
                sender_id="wxid-remediation",
                reason="strict_match_failed",
                source_line="US 100 95.5",
                raw_text="[Apple]\nUS 100 95.5",
                message_time="2026-04-14 12:36:00",
                parser_template="repair-template-history",
                parser_version="candidate-v1",
                confidence=0.4,
            )
            repair_case = package_quote_repair_case(db=db, exception_id=exception_id)
            create_baseline_repair_attempt(
                db=db,
                repair_case_id=int(repair_case["id"]),
                replay_result={
                    "replayed": True,
                    "reason": "",
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
            advance_quote_repair_case_state(
                db=db,
                repair_case_id=int(repair_case["id"]),
                next_state=REPAIR_CASE_STATE_READY_FOR_ATTEMPT,
            )
            record_quote_repair_attempt(
                db=db,
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

            with self.assertRaisesRegex(ValueError, "prior history"):
                begin_quote_repair_remediation_attempt(
                    db=db,
                    repair_case_id=int(repair_case["id"]),
                    trigger="subagent_retry",
                    proposal_scope="group_profile",
                    proposal_kind="template_patch",
                )

            summary = db.get_quote_repair_case_summary(repair_case_id=int(repair_case["id"]))
            assert summary is not None
            attempt = begin_quote_repair_remediation_attempt(
                db=db,
                repair_case_id=int(repair_case["id"]),
                trigger="subagent_retry",
                proposal_scope="group_profile",
                proposal_kind="template_patch",
                history_read={
                    "attempt_count": summary["attempt_count"],
                    "failure_log_count": len(summary["failure_log_json"]),
                    "history_fingerprint": build_quote_repair_history_fingerprint(
                        failure_log=list(summary["failure_log_json"]),
                        last_attempt_number=summary["last_attempt_number"],
                    ),
                    "failure_notes": [
                        entry["failure_note"] for entry in summary["failure_log_json"]
                    ],
                },
            )
            self.assertEqual(int(attempt["attempt_number"]), 2)
        finally:
            db.close()

    def test_begin_quote_repair_remediation_attempt_rejects_fourth_attempt(self) -> None:
        from bookkeeping_core.remediation import begin_quote_repair_remediation_attempt
        from bookkeeping_core.repair_cases import (
            REPAIR_CASE_STATE_ESCALATED,
            REPAIR_CASE_STATE_READY_FOR_ATTEMPT,
            advance_quote_repair_case_state,
            create_baseline_repair_attempt,
            package_quote_repair_case,
            record_quote_repair_attempt,
        )

        db = self.make_db("repair-remediation-max-attempts")
        try:
            db.upsert_quote_group_profile(
                platform="wechat",
                chat_id="repair-remediation-max-attempts",
                chat_name="修复上限群",
                default_card_type="Apple",
                default_country_or_currency="USD",
                default_form_factor="physical",
                default_multiplier="1x",
                parser_template="repair-template-max-attempts",
                template_config=json.dumps(
                    {"version": "repair-template-max-attempts", "sections": ["Apple"]},
                    ensure_ascii=False,
                ),
            )
            origin_document_id = db.record_quote_candidate_bundle(
                candidate=_make_validation_candidate(message_id="repair-remediation-max")
            )
            db.record_quote_validation_run(
                validation_run=QuoteValidationRun(
                    quote_document_id=origin_document_id,
                    validator_version=VALIDATOR_VERSION_V1,
                    run_kind="runtime",
                    message_decision="no_publish",
                    validation_status="completed",
                    summary={"message_reasons": [build_validation_reason("strict_match_failed")]},
                )
            )
            exception_id = db.record_quote_exception(
                quote_document_id=origin_document_id,
                platform="wechat",
                source_group_key="wechat:repair-remediation-max-attempts",
                chat_id="repair-remediation-max-attempts",
                chat_name="修复上限群",
                source_name="Repair Source",
                sender_id="wxid-remediation",
                reason="strict_match_failed",
                source_line="US 100 95.5",
                raw_text="[Apple]\nUS 100 95.5",
                message_time="2026-04-14 12:37:00",
                parser_template="repair-template-max-attempts",
                parser_version="candidate-v1",
                confidence=0.4,
            )
            repair_case = package_quote_repair_case(db=db, exception_id=exception_id)
            create_baseline_repair_attempt(
                db=db,
                repair_case_id=int(repair_case["id"]),
                replay_result={
                    "replayed": True,
                    "reason": "",
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
            advance_quote_repair_case_state(
                db=db,
                repair_case_id=int(repair_case["id"]),
                next_state=REPAIR_CASE_STATE_READY_FOR_ATTEMPT,
            )
            for failure_note in ("first", "second", "third"):
                record_quote_repair_attempt(
                    db=db,
                    repair_case_id=int(repair_case["id"]),
                    trigger="manual_retry",
                    replay_result={
                        "replayed": True,
                        "reason": failure_note,
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
            stored_case = db.get_quote_repair_case(repair_case_id=int(repair_case["id"]))
            assert stored_case is not None
            self.assertEqual(str(stored_case["lifecycle_state"]), REPAIR_CASE_STATE_ESCALATED)
            with self.assertRaisesRegex(ValueError, "maximum remediation attempts exceeded"):
                begin_quote_repair_remediation_attempt(
                    db=db,
                    repair_case_id=int(repair_case["id"]),
                    trigger="subagent_retry",
                    proposal_scope="group_profile",
                    proposal_kind="template_patch",
                    history_read={
                        "attempt_count": 3,
                        "failure_log_count": 3,
                        "history_fingerprint": "stale",
                        "failure_notes": ["first", "second", "third"],
                    },
                )
        finally:
            db.close()

    def test_advance_quote_repair_case_state_rejects_illegal_transitions(self) -> None:
        from bookkeeping_core.repair_cases import (
            REPAIR_CASE_STATE_CLOSED_IGNORED,
            REPAIR_CASE_STATE_PACKAGED,
            advance_quote_repair_case_state,
            package_quote_repair_case,
        )

        db = self.make_db("repair-case-illegal-transition")
        try:
            origin_document_id = db.record_quote_candidate_bundle(
                candidate=_make_validation_candidate(message_id="repair-illegal-origin")
            )
            exception_id = db.record_quote_exception(
                quote_document_id=origin_document_id,
                platform="wechat",
                source_group_key="wechat:repair-illegal-transition",
                chat_id="repair-illegal-transition",
                chat_name="非法转换群",
                source_name="Repair Source",
                sender_id="wxid-repair",
                reason="missing_group_template",
                source_line="[Apple]",
                raw_text="[Apple]\nUS 100 95.5",
                message_time="2026-04-14 12:20:00",
                parser_template="group-parser",
                parser_version="candidate-v1",
                confidence=0.0,
            )
            repair_case = package_quote_repair_case(db=db, exception_id=exception_id)
            advance_quote_repair_case_state(
                db=db,
                repair_case_id=int(repair_case["id"]),
                next_state=REPAIR_CASE_STATE_CLOSED_IGNORED,
            )

            with self.assertRaisesRegex(ValueError, "illegal repair case transition"):
                advance_quote_repair_case_state(
                    db=db,
                    repair_case_id=int(repair_case["id"]),
                    next_state=REPAIR_CASE_STATE_PACKAGED,
                )
        finally:
            db.close()

    def test_record_quote_repair_attempt_can_mark_case_attempt_succeeded_without_absorption(
        self,
    ) -> None:
        from bookkeeping_core.repair_cases import (
            REPAIR_CASE_STATE_ATTEMPT_SUCCEEDED,
            REPAIR_CASE_STATE_READY_FOR_ATTEMPT,
            advance_quote_repair_case_state,
            create_baseline_repair_attempt,
            package_quote_repair_case,
            record_quote_repair_attempt,
        )

        db = self.make_db("repair-case-attempt-succeeded")
        try:
            profile_id = db.upsert_quote_group_profile(
                platform="wechat",
                chat_id="repair-attempt-succeeded",
                chat_name="成功尝试群",
                default_card_type="Apple",
                default_country_or_currency="USD",
                default_form_factor="physical",
                default_multiplier="1x",
                parser_template="repair-template-succeeded",
                template_config=json.dumps(
                    {"version": "repair-template-succeeded", "sections": ["Apple"]},
                    ensure_ascii=False,
                ),
            )
            origin_document_id = db.record_quote_candidate_bundle(
                candidate=_make_validation_candidate(message_id="repair-succeeded-origin")
            )
            db.record_quote_validation_run(
                validation_run=QuoteValidationRun(
                    quote_document_id=origin_document_id,
                    validator_version=VALIDATOR_VERSION_V1,
                    run_kind="runtime",
                    message_decision="no_publish",
                    validation_status="completed",
                    summary={"message_reasons": [build_validation_reason("strict_match_failed")]},
                )
            )
            exception_id = db.record_quote_exception(
                quote_document_id=origin_document_id,
                platform="wechat",
                source_group_key="wechat:repair-attempt-succeeded",
                chat_id="repair-attempt-succeeded",
                chat_name="成功尝试群",
                source_name="Repair Source",
                sender_id="wxid-repair",
                reason="strict_match_failed",
                source_line="US 100 95.5",
                raw_text="[Apple]\nUS 100 95.5",
                message_time="2026-04-14 12:25:00",
                parser_template="repair-template-succeeded",
                parser_version="candidate-v1",
                confidence=0.3,
            )
            repair_case = package_quote_repair_case(db=db, exception_id=exception_id)
            create_baseline_repair_attempt(
                db=db,
                repair_case_id=int(repair_case["id"]),
                replay_result={
                    "replayed": True,
                    "reason": "",
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
            advance_quote_repair_case_state(
                db=db,
                repair_case_id=int(repair_case["id"]),
                next_state=REPAIR_CASE_STATE_READY_FOR_ATTEMPT,
            )

            attempt = record_quote_repair_attempt(
                db=db,
                repair_case_id=int(repair_case["id"]),
                trigger="manual_retry",
                replay_result={
                    "replayed": True,
                    "reason": "",
                    "rows": 2,
                    "exceptions": 0,
                    "remaining_lines": [],
                    "mutated_active_facts": False,
                    "message_decision": "held_only",
                    "publishable_row_count": 0,
                    "held_row_count": 2,
                    "rejected_row_count": 0,
                    "comparison": {"classification": "better"},
                },
            )

            stored_case = db.get_quote_repair_case(repair_case_id=int(repair_case["id"]))
            self.assertIsNotNone(stored_case)
            assert stored_case is not None
            self.assertEqual(
                str(stored_case["lifecycle_state"]),
                REPAIR_CASE_STATE_ATTEMPT_SUCCEEDED,
            )
            self.assertEqual(int(stored_case["group_profile_id"]), profile_id)
            profile = db.get_quote_group_profile(
                platform="wechat",
                chat_id="repair-attempt-succeeded",
            )
            self.assertIsNotNone(profile)
            assert profile is not None
            self.assertEqual(str(profile["parser_template"]), "repair-template-succeeded")
            self.assertEqual(int(attempt["attempt_number"]), 1)
            summary = _normalize_json_field(stored_case["case_summary_json"])
            self.assertEqual(summary["attempt_count"], 1)
            self.assertEqual(summary["failure_log_json"], [])
            self.assertEqual(summary["escalation_state"], "not_ready")
            self.assertIsNone(summary["closed_at"])
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
