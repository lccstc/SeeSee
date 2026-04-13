from __future__ import annotations

import json
import unittest

from bookkeeping_core.database import BookkeepingDB
from bookkeeping_core.quote_candidates import QuoteCandidateMessage, QuoteCandidateRow
from tests.support.postgres_test_case import PostgresTestCase


def _normalize_json_field(value):
    return json.loads(value) if isinstance(value, str) else value


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
                cursor.execute("DROP TABLE quote_candidate_rows")
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

            count_row = db.conn.execute(
                "SELECT COUNT(*) AS cnt FROM quote_price_rows"
            ).fetchone()
            self.assertEqual(int(count_row["cnt"]), 0)
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
