from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from bookkeeping_core.template_engine import build_group_parser_template_from_gold_fixture
from tests.support.quote_exception_corpus import is_fixture_approved, load_gold_fixture


FIXTURE_ALIASES: dict[str, str] = {
    "sk_steam_price_update": "sk_steam_simple_full_243",
    "yingzi_steam_razer": "shadow_steam_razer_full_238",
    "yangyang_supermarket_updates": "yangyang_supermarket_board_236",
    "wanrui_xbox_rules": "wanrui_xbox_roblox_full_235",
    "qh_delta_numeric_update": "qh_delta_us_uk_239",
    "xixi_multi_section_itunes_xbox_razer": "xiyi_itunes_xbox_razer_full_198",
    "yangyang_nordstrom_pic_code": "yangyang_nordstrom_delta_230",
    "wannuo_xb_shorthand": "wannuo_xbox_shorthand_174",
}


def resolve_bootstrap_fixture_name(fixture_name: str) -> str:
    normalized = str(fixture_name or "").strip()
    if not normalized:
        raise ValueError("fixture name is required")
    return FIXTURE_ALIASES.get(normalized, normalized)


def supported_bootstrap_fixture_names() -> list[str]:
    return sorted(FIXTURE_ALIASES)


def _common_fixture_value(rows: list[dict[str, Any]], key: str) -> str:
    values = {
        str(item.get(key) or "").strip()
        for item in rows
        if str(item.get(key) or "").strip()
    }
    if len(values) != 1:
        return ""
    return next(iter(values))


def _publishable_fixture_rows(fixture: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in fixture.get("expected_rows") or []:
        if str(row.get("row_decision") or "") != "publishable":
            continue
        if not row.get("price") or not row.get("card_type") or not row.get("country_or_currency"):
            continue
        rows.append(dict(row))
    return rows


def build_bootstrap_profile_payload(
    *,
    fixture_name: str,
    platform: str,
    chat_id: str,
    chat_name: str = "",
) -> dict[str, Any]:
    canonical_fixture_name = resolve_bootstrap_fixture_name(fixture_name)
    if not is_fixture_approved(canonical_fixture_name):
        raise ValueError(
            f"fixture '{fixture_name}' is not approved for bootstrap generation"
        )
    fixture = load_gold_fixture(canonical_fixture_name)
    publishable_rows = _publishable_fixture_rows(fixture)
    if not publishable_rows:
        raise ValueError(
            f"fixture '{canonical_fixture_name}' has no publishable rows for bootstrap generation"
        )
    return {
        "platform": platform,
        "chat_id": chat_id,
        "chat_name": chat_name or str(fixture.get("chat_name") or chat_id),
        "default_card_type": _common_fixture_value(publishable_rows, "card_type"),
        "default_country_or_currency": _common_fixture_value(
            publishable_rows, "country_or_currency"
        ),
        "default_form_factor": _common_fixture_value(publishable_rows, "form_factor")
        or "不限",
        "default_multiplier": "",
        "parser_template": "group-parser",
        "stale_after_minutes": 120,
        "note": (
            "bootstrap fixture="
            f"{fixture_name} canonical={canonical_fixture_name} "
            "candidate-only coverage seed"
        ),
        "fixture_name": fixture_name,
        "canonical_fixture_name": canonical_fixture_name,
        "template_config": build_group_parser_template_from_gold_fixture(fixture),
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a deterministic group-parser-v1 profile payload from an approved "
            "quote exception corpus fixture."
        )
    )
    parser.add_argument("--fixture", required=True, help="Approved fixture name or supported alias")
    parser.add_argument("--platform", required=True, help="Platform to bind in quote_group_profiles")
    parser.add_argument("--chat-id", required=True, help="Chat ID to bind in quote_group_profiles")
    parser.add_argument("--chat-name", default="", help="Optional chat name override")
    parser.add_argument("--output", default="", help="Optional file path; defaults to stdout")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        payload = build_bootstrap_profile_payload(
            fixture_name=args.fixture,
            platform=args.platform,
            chat_id=args.chat_id,
            chat_name=args.chat_name,
        )
    except (KeyError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
