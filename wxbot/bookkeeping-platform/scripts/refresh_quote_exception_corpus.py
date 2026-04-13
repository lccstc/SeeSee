from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from urllib.request import urlopen


def _normalize_text(value: Any) -> str:
    return str(value or "").replace("\u00a0", " ").strip()


def _looks_token_only(text: str) -> bool:
    token = text.replace("\n", "").replace(" ", "")
    return bool(token) and re.fullmatch(r"[A-Za-z0-9]{12,}", token) is not None


def _line_count(text: str) -> int:
    return len([line for line in _normalize_text(text).splitlines() if line.strip()])


def _contains_any(text: str, needles: tuple[str, ...]) -> bool:
    haystack = _normalize_text(text)
    return any(needle in haystack for needle in needles)


def _has_context_dependent_numeric_row(text: str) -> bool:
    numeric_row = re.compile(
        r"^\s*(?:\+?\d+(?:[-/]\s*\d+)*|\d+\+)\s*(?:=|【| )",
        re.MULTILINE,
    )
    return numeric_row.search(_normalize_text(text)) is not None


def _bucket_flags(row: dict[str, Any]) -> dict[str, bool]:
    raw_text = _normalize_text(row.get("raw_text"))
    source_line = _normalize_text(row.get("source_line"))
    line_count = _line_count(raw_text)
    has_rule_text = _contains_any(
        raw_text,
        ("#", "问价", "先问", "发前问", "规则", "勿发", "ask", "不拿", "不结账"),
    )
    return {
        "multi_section_board": line_count >= 10
        or raw_text.count("【") >= 3
        or _contains_any(raw_text, ("======", "----------------", "————————", "Price updates")),
        "long_board_message": line_count >= 8,
        "quote_plus_rule_text": has_rule_text
        and bool(re.search(r"\d(?:\.\d+)?", raw_text)),
        "manual_or_ask_lines": _contains_any(
            raw_text,
            ("问价", "先问", "发前问", "ask", "手动报价", "请勿直发"),
        ),
        "update_or_shift_message": _contains_any(
            raw_text,
            ("单独更新", "更新", "晚班", "Price updates", "广告更新"),
        ),
        "context_dependent_numeric_rows": _has_context_dependent_numeric_row(raw_text),
        "short_header_like_source_line": len(source_line) <= 20
        or source_line.startswith("【")
        or source_line.startswith("#"),
        "token_only_source_line": _looks_token_only(source_line),
    }


def _bucket_member(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "exception_id": int(row.get("id") or 0),
        "chat_id": _normalize_text(row.get("chat_id")),
        "chat_name": _normalize_text(row.get("chat_name")),
        "reason": _normalize_text(row.get("reason")),
        "source_line": _normalize_text(row.get("source_line")),
    }


def build_exception_corpus_index(
    payload: dict[str, Any],
    *,
    source: str,
    fetched_at: str,
) -> dict[str, Any]:
    rows = list(payload.get("rows") or [])
    total = int(payload.get("open_total") or payload.get("total") or len(rows))
    reason_counts = Counter(_normalize_text(row.get("reason")) for row in rows)

    chat_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        chat_rows[_normalize_text(row.get("chat_id"))].append(row)

    top_chats = [
        {
            "chat_id": chat_id,
            "chat_name": _normalize_text(group[0].get("chat_name")),
            "count": len(group),
            "reasons": dict(
                sorted(Counter(_normalize_text(item.get("reason")) for item in group).items())
            ),
        }
        for chat_id, group in chat_rows.items()
    ]
    top_chats.sort(key=lambda item: (-int(item["count"]), item["chat_id"]))

    bucket_members: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        member = _bucket_member(row)
        for bucket_name, enabled in _bucket_flags(row).items():
            if enabled:
                bucket_members[bucket_name].append(member)

    bucket_summaries = {}
    for bucket_name in (
        "multi_section_board",
        "long_board_message",
        "quote_plus_rule_text",
        "manual_or_ask_lines",
        "update_or_shift_message",
        "context_dependent_numeric_rows",
        "short_header_like_source_line",
        "token_only_source_line",
    ):
        members = sorted(
            bucket_members.get(bucket_name, []),
            key=lambda item: (-int(item["exception_id"]), item["chat_id"]),
        )
        bucket_summaries[bucket_name] = {
            "count": len(members),
            "members": members,
        }

    return {
        "snapshot": {
            "kind": "generated",
            "source": source,
            "fetched_at": fetched_at,
        },
        "total_open_exceptions": total,
        "chat_count": len(chat_rows),
        "top_8_exception_count": sum(item["count"] for item in top_chats[:8]),
        "reason_counts": dict(sorted(reason_counts.items())),
        "top_exception_chats": top_chats,
        "top_exception_chat_ids": [item["chat_id"] for item in top_chats[:8]],
        "long_tail_chat_ids": [item["chat_id"] for item in top_chats[8:]],
        "bucket_summaries": bucket_summaries,
    }


def _load_payload_from_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_payload_from_url(url: str) -> dict[str, Any]:
    with urlopen(url, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Refresh quote exception corpus fixtures.")
    parser.add_argument("--source-json", help="Offline quote exception export JSON.")
    parser.add_argument("--source-url", help="Quote exception API endpoint.")
    parser.add_argument("--output-dir", required=True, help="Directory that receives index.json.")
    parser.add_argument(
        "--fetched-at",
        default="generated",
        help="Timestamp label stored in the normalized index.",
    )
    args = parser.parse_args(argv)
    if bool(args.source_json) == bool(args.source_url):
        parser.error("exactly one of --source-json or --source-url is required")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.source_json:
        payload = _load_payload_from_json(Path(args.source_json))
        source = f"json:{Path(args.source_json).name}"
    else:
        payload = _load_payload_from_url(args.source_url)
        source = args.source_url
    normalized = build_exception_corpus_index(
        payload,
        source=source,
        fetched_at=args.fetched_at,
    )
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "index.json").write_text(
        json.dumps(normalized, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
