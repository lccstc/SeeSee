from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts.refresh_quote_exception_corpus import main as refresh_corpus_main
from tests.support.quote_exception_corpus import (
    is_fixture_approved,
    list_bucket_members,
    list_top_exception_chats,
    load_approved_gold_fixtures,
    load_exception_corpus_index,
    load_gold_samples,
)


_SAMPLE_PAYLOAD = {
    "total": 4,
    "open_total": 4,
    "rows": [
        {
            "id": 10,
            "chat_id": "chat-a",
            "chat_name": "Chat A",
            "reason": "strict_match_failed",
            "source_line": "50=5.25",
            "raw_text": "#VIP广告更新\n50=5.25\n100/150=5.41\n#急卡勿发",
        },
        {
            "id": 11,
            "chat_id": "chat-a",
            "chat_name": "Chat A",
            "reason": "strict_match_failed",
            "source_line": "【Board】",
            "raw_text": "【苹果】\nUS:100-500=5.3\n【XBOX】\nUS:10-250图密【5.1】",
        },
        {
            "id": 12,
            "chat_id": "chat-b",
            "chat_name": "Chat B",
            "reason": "missing_group_template",
            "source_line": "单独更新",
            "raw_text": "单独更新\n300/400/500=5.42\n100/150=5.37\n#连卡不要拆开发",
        },
        {
            "id": 13,
            "chat_id": "chat-c",
            "chat_name": "Chat C",
            "reason": "missing_group_template",
            "source_line": "X2RGQCYDM6D278KN",
            "raw_text": "X2RGQCYDM6D278KN",
        },
    ],
}


class TestQuoteExceptionCorpusIndex(unittest.TestCase):
    def test_loads_planning_baseline_metadata_and_top_rankings(self):
        index = load_exception_corpus_index()

        self.assertEqual(index["total_open_exceptions"], 226)
        self.assertEqual(index["chat_count"], 25)
        self.assertEqual(index["top_8_exception_count"], 159)
        self.assertEqual(index["reason_counts"]["missing_group_template"], 149)
        self.assertEqual(index["reason_counts"]["strict_match_failed"], 77)

        top_chats = list_top_exception_chats()
        self.assertEqual(len(top_chats), 8)
        self.assertEqual(top_chats[0]["chat_id"], "C-556-【飞鸿FHS028】-IT❤")
        self.assertEqual(top_chats[0]["count"], 36)

    def test_long_tail_buckets_remain_visible(self):
        members = list_bucket_members("token_only_source_line")
        self.assertEqual([member["exception_id"] for member in members], [177, 208])
        self.assertEqual(members[0]["chat_id"], "B08-C-513【青松】IT-XiXi-AQSS")

        context_members = list_bucket_members("context_dependent_numeric_rows")
        self.assertIn(174, [member["exception_id"] for member in context_members])

    def test_refresh_cli_accepts_json_and_url_sources_and_writes_normalized_shape(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            source_path = tmp_path / "payload.json"
            source_path.write_text(
                json.dumps(_SAMPLE_PAYLOAD, ensure_ascii=False),
                encoding="utf-8",
            )

            json_output = tmp_path / "json-output"
            rc = refresh_corpus_main(
                [
                    "--source-json",
                    str(source_path),
                    "--output-dir",
                    str(json_output),
                    "--fetched-at",
                    "unit-json",
                ]
            )
            self.assertEqual(rc, 0)
            json_index = json.loads((json_output / "index.json").read_text(encoding="utf-8"))
            self.assertEqual(json_index["total_open_exceptions"], 4)
            self.assertEqual(json_index["chat_count"], 3)
            self.assertEqual(json_index["top_exception_chats"][0]["chat_id"], "chat-a")
            self.assertIn("token_only_source_line", json_index["bucket_summaries"])

            url_output = tmp_path / "url-output"

            mock_response = mock.MagicMock()
            mock_response.read.return_value = json.dumps(
                _SAMPLE_PAYLOAD,
                ensure_ascii=False,
            ).encode("utf-8")
            mock_context = mock.MagicMock()
            mock_context.__enter__.return_value = mock_response
            mock_context.__exit__.return_value = False

            with mock.patch(
                "scripts.refresh_quote_exception_corpus.urlopen",
                return_value=mock_context,
            ):
                rc = refresh_corpus_main(
                    [
                        "--source-url",
                        "http://unit.test/payload.json",
                        "--output-dir",
                        str(url_output),
                        "--fetched-at",
                        "unit-url",
                    ]
                )
                self.assertEqual(rc, 0)
                url_index = json.loads(
                    (url_output / "index.json").read_text(encoding="utf-8")
                )

            self.assertEqual(url_index["snapshot"]["source"], "http://unit.test/payload.json")
            self.assertEqual(url_index["top_8_exception_count"], 4)
            self.assertEqual(
                url_index["reason_counts"],
                {
                    "missing_group_template": 2,
                    "strict_match_failed": 2,
                },
            )


class TestQuoteExceptionGoldFixtures(unittest.TestCase):
    _APPROVED_IDS = {244, 242, 241, 222, 169, 243, 238, 236}

    def test_curated_fixtures_cover_required_exception_ids(self):
        fixtures = load_gold_samples()
        expected_ids = {
            244,
            242,
            241,
            222,
            169,
            243,
            238,
            236,
            235,
            239,
            198,
            230,
            174,
            177,
        }
        self.assertEqual({fixture["exception_id"] for fixture in fixtures}, expected_ids)

    def test_every_fixture_contains_message_and_row_level_decisions(self):
        fixtures = load_gold_samples()
        for fixture in fixtures:
            self.assertIn(fixture["message_decision"], {"full_snapshot", "delta_update", "unresolved"})
            expected_status = "approved" if fixture["exception_id"] in self._APPROVED_IDS else "pending_review"
            self.assertEqual(fixture["approval_status"], expected_status)
            self.assertTrue(fixture["expected_sections"])
            self.assertTrue(fixture["expected_rows"])
            for row in fixture["expected_rows"]:
                self.assertIn("card_type", row)
                self.assertIn("country_or_currency", row)
                self.assertIn("amount_range", row)
                self.assertIn("form_factor", row)
                self.assertIn("price", row)
                self.assertIn(row["row_decision"], {"publishable", "held", "rejected"})

    def test_all_snapshot_top_chats_have_curated_coverage(self):
        fixtures = load_gold_samples()
        covered_chats = {fixture["chat_id"] for fixture in fixtures}
        snapshot_top_chats = {
            chat["chat_id"]
            for chat in list_top_exception_chats()
        }
        self.assertTrue(snapshot_top_chats.issubset(covered_chats))

    def test_approved_manifest_only_references_known_fixtures(self):
        fixtures = load_gold_samples()
        fixture_names = {fixture["fixture_name"] for fixture in fixtures}
        approved_fixtures = load_approved_gold_fixtures()

        self.assertEqual({fixture["exception_id"] for fixture in approved_fixtures}, self._APPROVED_IDS)
        self.assertTrue(all(fixture["fixture_name"] in fixture_names for fixture in approved_fixtures))
        self.assertTrue(all(is_fixture_approved(fixture["fixture_name"]) for fixture in approved_fixtures))
        self.assertFalse(is_fixture_approved("nonexistent_fixture"))
