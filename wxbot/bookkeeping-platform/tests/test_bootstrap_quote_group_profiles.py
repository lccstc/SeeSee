from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from bookkeeping_core.template_engine import TemplateConfig, parse_message_with_template
from scripts.bootstrap_quote_group_profiles import (
    build_bootstrap_profile_payload,
    main as bootstrap_main,
    resolve_bootstrap_fixture_name,
    supported_bootstrap_fixture_names,
)
from tests.support.quote_exception_corpus import load_gold_fixture


class BootstrapQuoteGroupProfilesTests(unittest.TestCase):
    def test_supported_aliases_include_required_top_volume_names(self) -> None:
        aliases = set(supported_bootstrap_fixture_names())
        self.assertTrue(
            {"sk_steam_price_update", "yingzi_steam_razer", "yangyang_supermarket_updates"}.issubset(
                aliases
            )
        )
        self.assertEqual(
            resolve_bootstrap_fixture_name("sk_steam_price_update"),
            "sk_steam_simple_full_243",
        )

    def test_build_payload_for_approved_alias_emits_group_parser_template(self) -> None:
        payload = build_bootstrap_profile_payload(
            fixture_name="sk_steam_price_update",
            platform="wechat",
            chat_id="room-bootstrap-sk",
        )
        fixture = load_gold_fixture(payload["canonical_fixture_name"])

        self.assertEqual(payload["parser_template"], "group-parser")
        self.assertEqual(payload["template_config"]["version"], "group-parser-v1")
        self.assertTrue(payload["template_config"]["sections"])
        self.assertEqual(payload["canonical_fixture_name"], "sk_steam_simple_full_243")

        template = TemplateConfig.from_json(
            json.dumps(payload["template_config"], ensure_ascii=False)
        )
        parsed = parse_message_with_template(
            str(fixture["raw_text"]),
            template,
            platform="wechat",
            chat_id="room-bootstrap-sk",
            chat_name="SK Steam",
            message_id="fixture-bootstrap-1",
            source_name="报价员",
            sender_id="seller-1",
            source_group_key="wechat:room-bootstrap-sk",
            message_time="2026-04-14 16:00:00",
        )
        self.assertGreaterEqual(len(parsed.rows), 3)
        self.assertEqual(parsed.parser_version, "group-parser-v1")

    def test_cli_accepts_exact_fixture_name_and_writes_json_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "bootstrap.json"
            rc = bootstrap_main(
                [
                    "--fixture",
                    "shadow_steam_razer_full_238",
                    "--platform",
                    "wechat",
                    "--chat-id",
                    "room-shadow",
                    "--output",
                    str(output_path),
                ]
            )

            self.assertEqual(rc, 0)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["parser_template"], "group-parser")
            self.assertEqual(payload["template_config"]["version"], "group-parser-v1")
            self.assertTrue(payload["template_config"]["sections"])

    def test_cli_rejects_unapproved_fixture_before_runtime_wiring(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            rc = bootstrap_main(
                [
                    "--fixture",
                    "wannuo_xb_shorthand",
                    "--platform",
                    "wechat",
                    "--chat-id",
                    "room-unapproved",
                ]
            )

        self.assertEqual(rc, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("not approved", stderr.getvalue())

    def test_generator_does_not_touch_profile_persistence(self) -> None:
        with patch(
            "bookkeeping_core.database.BookkeepingDB.upsert_quote_group_profile",
            side_effect=AssertionError("generator must not write profiles"),
        ):
            payload = build_bootstrap_profile_payload(
                fixture_name="yangyang_supermarket_updates",
                platform="wechat",
                chat_id="room-yangyang",
            )

        self.assertEqual(payload["canonical_fixture_name"], "yangyang_supermarket_board_236")
        self.assertEqual(payload["template_config"]["version"], "group-parser-v1")
