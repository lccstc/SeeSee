from __future__ import annotations

import json
from pathlib import Path
from typing import Any


_FIXTURE_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "quote_exception_corpus"


def _load_json_fixture(name: str) -> dict[str, Any]:
    return json.loads((_FIXTURE_DIR / name).read_text(encoding="utf-8"))


def load_exception_corpus_index() -> dict[str, Any]:
    return _load_json_fixture("index.json")


def list_top_exception_chats(limit: int = 8) -> list[dict[str, Any]]:
    index = load_exception_corpus_index()
    return list(index.get("top_exception_chats") or [])[:limit]


def list_bucket_members(bucket_name: str) -> list[dict[str, Any]]:
    index = load_exception_corpus_index()
    bucket = (index.get("bucket_summaries") or {}).get(bucket_name) or {}
    return list(bucket.get("members") or [])


def load_gold_samples() -> list[dict[str, Any]]:
    gold = _load_json_fixture("gold_top8.json")
    return list(gold.get("fixtures") or [])


def load_gold_fixture(fixture_name: str) -> dict[str, Any]:
    for fixture in load_gold_samples():
        if str(fixture.get("fixture_name") or "") == fixture_name:
            return fixture
    raise KeyError(f"unknown gold fixture: {fixture_name}")


def load_approved_gold_fixtures() -> list[dict[str, Any]]:
    approved = _load_json_fixture("approved_top8.json")
    approved_names = set(approved.get("approved_fixture_names") or [])
    return [fixture for fixture in load_gold_samples() if fixture.get("fixture_name") in approved_names]


def is_fixture_approved(fixture_name: str) -> bool:
    approved = _load_json_fixture("approved_top8.json")
    return fixture_name in set(approved.get("approved_fixture_names") or [])
