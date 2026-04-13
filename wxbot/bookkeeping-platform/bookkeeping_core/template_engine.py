"""报价模板引擎 — 按群固定模板匹配提取变量。

核心理念："机场广播"模式：
- 固定文字做字面量匹配（锚点）
- {变量} 插槽做正则提取
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

import re

# Full-width → half-width mapping for common punctuation
_FULLWIDTH_TO_HALFWIDTH = str.maketrans({
    '\uff08': '(',   # （ → (
    '\uff09': ')',   # ） → )
    '\uff1d': '=',   # ＝ → =
    '\uff1a': ':',   # ： → :
    '\uff0c': ',',   # ， → ,
    '\uff0b': '+',   # ＋ → +
    '\uff0d': '-',   # － → -
    '\u3000': ' ',   # ideographic space → regular space
})

_DECORATION_CHARS = set('=─━═-~* ')
_GROUP_PARSER_VERSION = "group-parser-v1"
_GROUP_PARSER_MAX_SECTIONS = 3


def normalize_quote_text(line: str) -> str:
    """Pre-normalize a single quote line for strict template matching."""
    # full-width -> half-width
    line = line.translate(_FULLWIDTH_TO_HALFWIDTH)

    # Strip outer decoration from section header lines
    # e.g. "======【Roblox】======" → "【Roblox】"
    stripped = line.strip()
    if '【' in stripped and '】' in stripped:
        start = stripped.index('【')
        end = stripped.rindex('】') + 1
        prefix = stripped[:start]
        suffix = stripped[end:]
        if all(c in _DECORATION_CHARS for c in prefix) and all(c in _DECORATION_CHARS for c in suffix):
            line = stripped[start:end]

    # Normalize double+ equals to single (e.g. "==" → "=")
    line = re.sub(r'={2,}', '=', line)
    # Normalize whitespace around = and : delimiters
    line = re.sub(r'\s*=\s*', '=', line)
    line = re.sub(r'\s*:\s*', ':', line)

    # Collapse multiple spaces to single
    line = re.sub(r' {2,}', ' ', line)

    return line.strip()


def _clean_card_type(value: str) -> str:
    """Strip decoration characters from extracted card_type values."""
    return value.strip('=─━═-~* ')


def split_multi_quote_line(line: str) -> list[str]:
    """Split a line containing multiple country=price quotes.

    e.g. "巴西=1.03 新加坡=4.25" → ["巴西=1.03", "新加坡=4.25"]
    e.g. "加拿大=3.4(代码批量问)英国=6.15卡图" → ["加拿大=3.4(代码批量问)", "英国=6.15卡图"]
    """
    # Split at: digit/closing-paren + whitespace + word-chars followed by =
    # Or: digit/closing-paren directly followed by word-chars followed by =
    parts = re.split(
        r'(?<=[\d\)])[ \t]+(?=[A-Za-z\u4e00-\u9fff]+=)'
        r'|(?<=[\d\)])(?=[A-Za-z\u4e00-\u9fff]+=)',
        line,
    )
    return [p.strip() for p in parts if p.strip()]


_AMOUNT_PRICE_SEGMENT_RE = re.compile(r'([\d][\d\-/~]*)=([\d.]+)')


_BRACKET_PRICE_PAIR_RE = re.compile(
    r'(?P<label>[A-Za-z0-9\u4e00-\u9fff][A-Za-z0-9\u4e00-\u9fff\s/\-]*?)\s*[【\[]\s*(?P<price>\d+(?:\.\d+)?)\s*[】\]]'
)
_AMOUNT_TOKEN_RE = re.compile(
    r"\d+(?:\.\d+)?(?:\s*[/-]\s*\d+(?:\.\d+)?)+|\d+(?:\.\d+)?"
)


def _canonicalize_bracket_quote_line(label: str, price: str, tail: str) -> str | None:
    from .quotes import (
        _infer_country_or_currency,
        _infer_form_factor,
        normalize_quote_country_or_currency,
        normalize_quote_form_factor,
    )

    normalized_label = normalize_quote_text(label)
    if not normalized_label:
        return None

    country = normalize_quote_country_or_currency(_infer_country_or_currency(normalized_label) or "")
    form_factor = normalize_quote_form_factor(_infer_form_factor(normalized_label) or "")
    amount_match = _AMOUNT_TOKEN_RE.search(normalized_label)
    amount = normalize_strict_section_amount_label(amount_match.group(0)) if amount_match else ""

    parts: list[str] = []
    if country:
        parts.append(country)
    if amount:
        parts.append(amount)
    if form_factor and form_factor != "不限":
        parts.append(form_factor)
    if not parts:
        return None

    canonical = f'{" ".join(parts)}={price}'
    normalized_tail = normalize_quote_text(tail)
    if normalized_tail:
        canonical = f"{canonical}({normalized_tail.strip('()')})"
    return canonical


def _extract_bracket_quote_entries(line: str) -> list[dict[str, str]]:
    normalized = normalize_quote_text(line)
    if not normalized:
        return []
    matches = list(_BRACKET_PRICE_PAIR_RE.finditer(normalized))
    if not matches:
        return []
    if normalized[: matches[0].start()].strip():
        return []

    entries: list[dict[str, str]] = []
    for index, match in enumerate(matches):
        next_start = matches[index + 1].start() if index + 1 < len(matches) else len(normalized)
        between = normalized[match.end() : next_start]
        tail = between.strip() if index == len(matches) - 1 else ""
        if index < len(matches) - 1 and between.strip():
            return []
        source_line = normalized[match.start() : next_start].strip()
        canonical = _canonicalize_bracket_quote_line(
            str(match.group("label") or "").strip(),
            str(match.group("price") or "").strip(),
            tail,
        )
        if not canonical:
            return []
        entries.append(
            {
                "line": canonical,
                "source_line": source_line,
            }
        )
    return entries


def _extract_prefixed_amount_quote_entries(line: str) -> list[dict[str, str]]:
    normalized = normalize_quote_text(line)
    if not normalized:
        return []
    matches = list(_AMOUNT_PRICE_SEGMENT_RE.finditer(normalized))
    if len(matches) < 2:
        return []
    prefix = normalized[: matches[0].start()].strip()
    if not prefix or not re.search(r"[A-Za-z\u4e00-\u9fff]", prefix):
        return []

    entries: list[dict[str, str]] = []
    for index, match in enumerate(matches):
        next_start = matches[index + 1].start() if index + 1 < len(matches) else len(normalized)
        between = normalized[match.end() : next_start]
        if index < len(matches) - 1 and between.strip():
            return []
        if index == len(matches) - 1 and between.strip():
            return []
        amount = str(match.group(1) or "").strip()
        price = str(match.group(2) or "").strip()
        if not amount or not price:
            return []
        canonical = f"{prefix} {amount}={price}"
        entries.append(
            {
                "line": canonical,
                "source_line": canonical,
            }
        )
    return entries


def _normalized_virtual_quote_entries(line: str, *, split_multi_quotes: bool) -> list[dict[str, str]]:
    normalized = normalize_quote_text(line)
    if not normalized:
        return []
    bracket_entries = _extract_bracket_quote_entries(normalized)
    if bracket_entries:
        return bracket_entries
    if split_multi_quotes:
        prefixed_amount_entries = _extract_prefixed_amount_quote_entries(normalized)
        if prefixed_amount_entries:
            return prefixed_amount_entries
        return [{"line": item, "source_line": item} for item in split_multi_quote_line(normalized)]
    return [{"line": normalized, "source_line": normalized}]


def _normalized_virtual_lines(text: str, *, split_multi_quotes: bool) -> list[dict[str, Any]]:
    lines: list[dict[str, Any]] = []
    for raw_index, raw_line in enumerate(text.splitlines()):
        for item in _normalized_virtual_quote_entries(raw_line, split_multi_quotes=split_multi_quotes):
            lines.append(
                {
                    "raw_index": raw_index,
                    "line": str(item["line"]),
                    "source_line": str(item["source_line"]),
                }
            )
    return lines


@dataclass
class TemplateConfig:
    """群报价模板定义 (Data Engine v1)。"""
    version: str = "data-engine-v1"
    rules: list[dict[str, str]] = field(default_factory=list)
    defaults: dict[str, str | None] = field(default_factory=dict)
    sections: list[dict[str, Any]] = field(default_factory=list)
    
    @classmethod
    def from_json(cls, raw: str) -> "TemplateConfig":
        if not raw or not raw.strip():
            raise ValueError("empty template config")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON: {exc}") from exc
        return cls(
            version=data.get("version", "data-engine-v1"),
            rules=data.get("rules", []),
            defaults=data.get("defaults", {}),
            sections=data.get("sections", []),
        )

    def to_json(self) -> str:
        payload: dict[str, Any] = {
            "version": self.version,
            "defaults": self.defaults,
        }
        if self.version in {"strict-section-v1", _GROUP_PARSER_VERSION}:
            payload["sections"] = self.sections
        else:
            payload["rules"] = self.rules
        return json.dumps(payload, ensure_ascii=False)


def match_pattern(line: str, pattern: str) -> dict[str, str] | None:
    """将 pattern 中的 {name} 插槽替换为正则，进行绝对严格的字面量匹配。"""
    parts = re.split(r"\{(\w+)\}", pattern)
    if not parts:
        return None

    regex_parts: list[str] = []
    names: list[str] = []
    for i, part in enumerate(parts):
        if i % 2 == 0:
            if part:
                regex_parts.append(re.escape(part))
        else:
            names.append(part)
            # 严格匹配内容：任何非空字符，除了边界符号
            if part == "price":
                regex_parts.append(r"(\d+(?:\.\d+)?)")
            elif part == "country":
                regex_parts.append(r"([A-Za-z\u4e00-\u9fff]+)")
            elif part == "amount":
                regex_parts.append(r"([\d]+(?:\s*[.\-/]\s*[\d]+)*)")
            else:
                regex_parts.append(r"(.+?)")

    regex = "^" + "".join(regex_parts) + "$"
    m = re.match(regex, line.strip())
    if m is None:
        return None

    return {name: m.group(i + 1).strip() for i, name in enumerate(names)}


_STRICT_SECTION_VARIABLES = {"amount", "price"}
_GROUP_PARSER_VARIABLES = {"amount", "price", "country", "country_or_currency"}
_QUOTE_LIKE_RE = re.compile(
    r"(?:\d.*(?:=|:|￥|¥)|(?:=|:).*\d|\d+(?:\.\d+)?收|收.*\d|ask|暂停|task)",
    re.IGNORECASE,
)
_QUOTE_NOISE_KEYWORDS = (
    "balance",
    "closing balance",
    "current balance",
    "当前账单金额",
    "账单金额",
    "current bill amount",
)
_RESTRICTION_KEYWORDS = (
    "先问",
    "不要发",
    "赎回",
    "撤账",
    "不结算",
    "使用时间",
    "囤货",
    "发前问",
    "网单问",
    "卡密先问",
    "连卡",
    "散卡",
    "倍数",
    "代码纸质问",
    "有卡先问",
    "问",
)

_TOKEN_ONLY_LINE_RE = re.compile(r"^[A-Za-z0-9]{12,}$")
_SHORTHAND_QUOTE_RE = re.compile(
    r"^\+?(?P<amount>\d+(?:\s*[-/]\s*\d+)*)\s+(?P<card>[A-Za-z]{1,8})\s+(?P<price>\d+(?:\.\d+)?)$",
    re.IGNORECASE,
)
_PREFIXED_SCOPE_QUOTE_RE = re.compile(
    r"^(?P<label>[A-Za-z\u4e00-\u9fff ]+?)(?P<form_factor>横白卡图|横白卡|横白|卡图|图密|卡密|代码|电子|图|密)?(?P<amount>\d+(?:\s*[-/]\s*\d+)*)=(?P<price>\d+(?:\.\d+)?)",
    re.IGNORECASE,
)


def _split_quote_candidate_label_and_price(line: str) -> tuple[str, str]:
    separator_matches = list(re.finditer(r"[:：=]\s*(\d+(?:\.\d+)?)", line))
    if separator_matches:
        match = separator_matches[-1]
        return line[: match.start()].strip(" ：:=()（）"), match.group(1)
    trailing_match = re.search(r"(?P<label>.+?)(?P<price>\d+(?:\.\d+)?)\s*$", line)
    if trailing_match is None:
        return "", ""
    return trailing_match.group("label").strip(), trailing_match.group("price")


def _looks_like_amount_label(text: str) -> bool:
    compact = re.sub(r"\s+", "", str(text or ""))
    if not compact:
        return False
    return bool(
        re.fullmatch(r"(?:卡图|卡密|代码|电子|横白卡?|竖卡)?[:：]?\d+(?:\.\d+)?", compact)
        or re.fullmatch(
            r"(?:卡图|卡密|代码|电子|横白卡?|竖卡)?[:：]?\d+(?:\.\d+)?(?:[-/]\d+(?:\.\d+)?)+",
            compact,
        )
    )


def _has_quote_entity_signal(text: str) -> bool:
    from .quotes import _infer_card_type, _infer_country_or_currency, _infer_form_factor

    return bool(
        _infer_card_type(text)
        or _infer_country_or_currency(text)
        or _infer_form_factor(text)
    )


def looks_like_quote_line(line: str) -> bool:
    normalized = normalize_quote_text(line)
    if not normalized:
        return False
    if not re.search(r"\d", normalized):
        return False
    if normalized.startswith("#"):
        return False
    lowered = normalized.lower()
    if any(
        token in lowered
        for token in ("wechat", "whatsapp", "recommend", "suggestions", "complaints")
    ):
        return False
    if any(keyword in normalized or keyword in lowered for keyword in _QUOTE_NOISE_KEYWORDS):
        return False
    if _extract_bracket_quote_entries(normalized):
        return True
    label, price = _split_quote_candidate_label_and_price(normalized)
    if not label or not price:
        return False
    if any(symbol in label for symbol in ("*", "×")):
        return False
    if _has_quote_entity_signal(label) or _looks_like_amount_label(label):
        return True
    plain_label = re.sub(r"[\d\s:/=+\-]+", "", label)
    return bool(re.search(r"[A-Za-z\u4e00-\u9fff]", plain_label))


def is_restriction_candidate(line: str) -> bool:
    normalized = normalize_quote_text(line)
    if not normalized or looks_like_quote_line(normalized):
        return False
    if all(ch in _DECORATION_CHARS for ch in normalized):
        return False
    if normalized.startswith("#"):
        return True
    lowered = normalized.lower()
    return any(keyword in normalized or keyword in lowered for keyword in _RESTRICTION_KEYWORDS)


def _looks_token_only_line(line: str) -> bool:
    compact = normalize_quote_text(line).replace(" ", "")
    return bool(compact) and _TOKEN_ONLY_LINE_RE.fullmatch(compact) is not None


def _strip_leading_quote_decorators(line: str) -> str:
    return re.sub(r"^[^\w\u4e00-\u9fff【\[#\+]+", "", normalize_quote_text(line))


def classify_candidate_line(line: str) -> str:
    normalized = _strip_leading_quote_decorators(line)
    if not normalized:
        return "noise"
    if _looks_token_only_line(normalized):
        return "noise"
    if all(ch in _DECORATION_CHARS for ch in normalized):
        return "noise"
    if re.match(r"^[【\[].+[】\]]$", normalized):
        return "header"
    if looks_like_quote_line(normalized) or _SHORTHAND_QUOTE_RE.match(normalized):
        return "quote"
    lowered = normalized.lower()
    if normalized.startswith("#"):
        if any(token in normalized or token in lowered for token in ("问价", "先问", "发前问", "ask", "请勿直发")):
            return "inquiry"
        if any(token in normalized for token in ("更新", "Price updates", "快刷", "网单")):
            return "header"
        return "rule"
    if is_restriction_candidate(normalized):
        if any(token in normalized or token in lowered for token in ("问", "ask", "请勿直发")):
            return "inquiry"
        return "rule"
    from .quotes import _infer_card_type, _infer_country_or_currency, _infer_form_factor

    if (
        _infer_card_type(normalized)
        or _infer_country_or_currency(normalized)
        or _infer_form_factor(normalized)
    ):
        return "header"
    return "noise"


def _parse_shorthand_quote_line(line: str) -> dict[str, Any] | None:
    match = _SHORTHAND_QUOTE_RE.match(_strip_leading_quote_decorators(line))
    if match is None:
        return None
    return {
        "amount": str(match.group("amount") or "").strip(),
        "price": str(match.group("price") or "").strip(),
        "card_hint": str(match.group("card") or "").strip(),
        "country_hint": "",
        "form_factor_hint": "",
    }


def _parse_prefixed_scope_quote_line(line: str) -> dict[str, Any] | None:
    match = _PREFIXED_SCOPE_QUOTE_RE.match(_strip_leading_quote_decorators(line))
    if match is None:
        return None
    label = str(match.group("label") or "").strip()
    return {
        "amount": str(match.group("amount") or "").strip(),
        "price": str(match.group("price") or "").strip(),
        "card_hint": label,
        "country_hint": label,
        "form_factor_hint": str(match.group("form_factor") or "").strip(),
    }


def analyze_scoped_quote_lines(
    text: str,
    *,
    default_card_type: str = "",
    default_country_or_currency: str = "",
    default_form_factor: str = "",
) -> list[dict[str, Any]]:
    from .quotes import (
        _infer_card_type,
        _infer_country_or_currency,
        _infer_form_factor,
        normalize_quote_amount_range,
        normalize_quote_card_type,
        normalize_quote_country_or_currency,
        normalize_quote_form_factor,
    )

    analyses: list[dict[str, Any]] = []
    active_scope = {
        "card_type": normalize_quote_card_type(default_card_type),
        "country_or_currency": normalize_quote_country_or_currency(default_country_or_currency),
        "form_factor": normalize_quote_form_factor(default_form_factor or "不限"),
        "header_text": "",
        "header_line_index": None,
    }

    for line_index, raw_line in enumerate(str(text or "").splitlines()):
        source_line = normalize_quote_text(raw_line)
        if not source_line:
            continue
        line_type = classify_candidate_line(source_line)
        analysis: dict[str, Any] = {
            "source_line_index": line_index,
            "source_line": source_line,
            "line_type": line_type,
        }
        stripped_for_inference = _strip_leading_quote_decorators(source_line)
        explicit_card_type = normalize_quote_card_type(_infer_card_type(stripped_for_inference) or "")
        explicit_country = normalize_quote_country_or_currency(
            _infer_country_or_currency(stripped_for_inference) or ""
        )
        explicit_form_factor = normalize_quote_form_factor(_infer_form_factor(stripped_for_inference) or "")

        if line_type == "header":
            next_scope = {
                "card_type": explicit_card_type or active_scope["card_type"],
                "country_or_currency": explicit_country or active_scope["country_or_currency"],
                "form_factor": (
                    explicit_form_factor
                    if explicit_form_factor and explicit_form_factor != "不限"
                    else active_scope["form_factor"]
                ),
                "header_text": source_line,
                "header_line_index": line_index,
            }
            if next_scope["card_type"] or next_scope["country_or_currency"] or next_scope["form_factor"]:
                active_scope = next_scope
            analyses.append(analysis)
            continue

        if line_type != "quote":
            analyses.append(analysis)
            continue

        detection = auto_detect_line_type(stripped_for_inference)
        parsed_fields = dict(detection.get("fields") or {})
        custom_hints = _parse_prefixed_scope_quote_line(source_line) or _parse_shorthand_quote_line(source_line)
        if custom_hints:
            for key, value in custom_hints.items():
                parsed_fields.setdefault(key, value)
        if detection.get("type") != "price":
            if custom_hints is None:
                analyses.append(analysis)
                continue

        parsed_amount = normalize_quote_amount_range(str(parsed_fields.get("amount") or ""))
        try:
            price = float(str(parsed_fields.get("price") or "").strip())
        except ValueError:
            analyses.append(analysis)
            continue

        line_card_type = normalize_quote_card_type(
            _infer_card_type(str(parsed_fields.get("card_hint") or stripped_for_inference)) or explicit_card_type
        )
        line_country = normalize_quote_country_or_currency(
            str(parsed_fields.get("currency") or parsed_fields.get("country") or parsed_fields.get("country_hint") or explicit_country)
        )
        raw_line_form_factor = normalize_quote_form_factor(
            str(parsed_fields.get("form_factor") or parsed_fields.get("form_factor_hint") or explicit_form_factor or "")
        )
        if (
            line_card_type
            and line_country
            and not explicit_country
            and line_country == normalize_quote_country_or_currency(str(parsed_fields.get("country") or parsed_fields.get("country_hint") or ""))
        ):
            line_country = ""

        inherited_fields: list[str] = []
        final_card_type = line_card_type or active_scope["card_type"]
        if final_card_type and not line_card_type:
            inherited_fields.append("card_type")
        final_country = line_country or active_scope["country_or_currency"]
        if final_country and not line_country:
            inherited_fields.append("country_or_currency")
        final_form_factor = (
            raw_line_form_factor if raw_line_form_factor and raw_line_form_factor != "不限" else active_scope["form_factor"]
        )
        if final_form_factor and final_form_factor != "不限" and (
            not raw_line_form_factor or raw_line_form_factor == "不限"
        ):
            inherited_fields.append("form_factor")

        if not final_card_type or not final_country or not parsed_amount:
            if line_type == "quote" and (
                explicit_card_type or explicit_country or (explicit_form_factor and explicit_form_factor != "不限")
            ):
                active_scope = {
                    "card_type": explicit_card_type or active_scope["card_type"],
                    "country_or_currency": explicit_country or active_scope["country_or_currency"],
                    "form_factor": (
                        explicit_form_factor
                        if explicit_form_factor and explicit_form_factor != "不限"
                        else active_scope["form_factor"]
                    ),
                    "header_text": source_line,
                    "header_line_index": line_index,
                }
            analyses.append(analysis)
            continue

        candidate = {
            "card_type": final_card_type,
            "country_or_currency": final_country,
            "amount_range": parsed_amount,
            "form_factor": final_form_factor or normalize_quote_form_factor("不限"),
            "price": price,
        }
        if inherited_fields and active_scope["header_text"]:
            candidate["scope_evidence"] = {
                "header_text": active_scope["header_text"],
                "header_line_index": active_scope["header_line_index"],
                "inherited_fields": inherited_fields,
            }
        analysis["candidate"] = candidate
        analyses.append(analysis)

        active_scope = {
            "card_type": final_card_type,
            "country_or_currency": final_country,
            "form_factor": final_form_factor or active_scope["form_factor"],
            "header_text": source_line if not inherited_fields else active_scope["header_text"],
            "header_line_index": line_index if not inherited_fields else active_scope["header_line_index"],
        }

    return analyses


def _fixture_publishable_rows(fixture: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in fixture.get("expected_rows") or []:
        if str(row.get("row_decision") or "") != "publishable":
            continue
        if not row.get("card_type") or not row.get("country_or_currency"):
            continue
        if row.get("price") in (None, ""):
            continue
        rows.append(dict(row))
    return rows


def _fixture_common_row_value(rows: list[dict[str, Any]], key: str) -> str:
    values = {
        str(item.get(key) or "").strip()
        for item in rows
        if str(item.get(key) or "").strip()
    }
    if len(values) != 1:
        return ""
    return next(iter(values))


def _sort_fixture_rows_by_source_order(
    raw_text: str,
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    virtual_lines = _normalized_virtual_lines(raw_text, split_multi_quotes=True)
    indexed_sources = [
        {
            "normalized": normalize_quote_text(str(item.get("source_line") or item.get("line") or "")),
            "match_key": re.sub(r"\s+", "", normalize_quote_text(str(item.get("source_line") or item.get("line") or ""))).lower(),
            "actual": str(item.get("source_line") or item.get("line") or ""),
        }
        for item in virtual_lines
    ]
    used_indexes: set[int] = set()
    ordered: list[tuple[int, int, dict[str, Any]]] = []
    for row_index, row in enumerate(rows):
        row_copy = dict(row)
        target = normalize_quote_text(str(row.get("source_line") or ""))
        target_key = re.sub(r"\s+", "", target).lower()
        matched_index = -1
        if target:
            for candidate_index, candidate in enumerate(indexed_sources):
                if candidate_index in used_indexes:
                    continue
                candidate_key = str(candidate["match_key"])
                if (
                    candidate_key == target_key
                    or candidate_key.startswith(target_key)
                    or target_key.startswith(candidate_key)
                ):
                    matched_index = candidate_index
                    used_indexes.add(candidate_index)
                    row_copy["_matched_source_line"] = str(candidate["actual"])
                    break
        fallback_index = len(indexed_sources) + row_index if matched_index < 0 else matched_index
        row_copy.setdefault("_matched_source_line", target)
        ordered.append((fallback_index, row_index, row_copy))
    ordered.sort(key=lambda item: (item[0], item[1]))
    return [row for _sort_index, _row_index, row in ordered]


def _bootstrap_quote_pattern(source_line: str) -> str:
    normalized = normalize_quote_text(source_line)
    pattern = re.sub(r"(\d+(?:\.\d+)?)(?!.*\d)", "{price}", normalized, count=1)
    if "{price}" not in pattern:
        raise ValueError(
            f"fixture source line does not contain a trailing price token: {source_line}"
        )
    return pattern


def derive_group_parser_sections_from_gold_fixture(
    fixture: dict[str, Any]
) -> list[dict[str, Any]]:
    from .quotes import (
        normalize_quote_amount_range,
        normalize_quote_card_type,
        normalize_quote_country_or_currency,
        normalize_quote_form_factor,
    )

    raw_text = str(fixture.get("raw_text") or "")
    publishable_rows = _sort_fixture_rows_by_source_order(
        raw_text,
        _fixture_publishable_rows(fixture),
    )
    if not publishable_rows:
        raise ValueError(
            f"fixture {fixture.get('fixture_name') or '<unknown>'} has no publishable rows for bootstrap"
        )

    section_defaults: dict[str, str] = {}
    common_card_type = normalize_quote_card_type(
        _fixture_common_row_value(publishable_rows, "card_type")
    )
    common_country = normalize_quote_country_or_currency(
        _fixture_common_row_value(publishable_rows, "country_or_currency")
    )
    common_form_factor = normalize_quote_form_factor(
        _fixture_common_row_value(publishable_rows, "form_factor") or "不限"
    )
    if common_card_type:
        section_defaults["card_type"] = common_card_type
    if common_country:
        section_defaults["country_or_currency"] = common_country
    if common_form_factor and common_form_factor != "不限":
        section_defaults["form_factor"] = common_form_factor

    quote_lines: list[dict[str, Any]] = []
    for row in publishable_rows:
        outputs = {
            "card_type": normalize_quote_card_type(str(row.get("card_type") or "").strip()),
            "country_or_currency": normalize_quote_country_or_currency(
                str(row.get("country_or_currency") or "").strip()
            ),
            "form_factor": normalize_quote_form_factor(str(row.get("form_factor") or "不限")),
        }
        amount_range = normalize_quote_amount_range(str(row.get("amount_range") or "不限"))
        if amount_range != "不限":
            outputs["amount_range"] = amount_range
        quote_lines.append(
            {
                "kind": "quote",
                "pattern": _bootstrap_quote_pattern(
                    str(row.get("_matched_source_line") or row.get("source_line") or "")
                ),
                "outputs": outputs,
            }
        )

    first_section = (fixture.get("expected_sections") or [{}])[0]
    section_label = str(
        first_section.get("label") or fixture.get("fixture_name") or "bootstrap"
    ).strip() or "bootstrap"
    section_evidence = str(first_section.get("evidence") or section_label).strip() or section_label
    return [
        {
            "id": "section-1",
            "enabled": True,
            "priority": 10,
            "label": section_label,
            "evidence": section_evidence,
            "defaults": section_defaults,
            "lines": quote_lines,
        }
    ]


def build_group_parser_template_from_gold_fixture(
    fixture: dict[str, Any]
) -> dict[str, Any]:
    return {
        "version": _GROUP_PARSER_VERSION,
        "defaults": {},
        "sections": derive_group_parser_sections_from_gold_fixture(fixture),
    }


def _join_restriction_lines(lines: list[str]) -> str:
    unique_lines: list[str] = []
    for line in lines:
        normalized = normalize_quote_text(line)
        if normalized and normalized not in unique_lines:
            unique_lines.append(normalized)
    return " | ".join(unique_lines)


def _normalized_indexed_nonempty_lines(text: str, *, split_multi_quotes: bool) -> list[dict[str, Any]]:
    indexed_lines: list[dict[str, Any]] = []
    for raw_index, raw_line in enumerate(text.splitlines()):
        normalized = normalize_quote_text(raw_line)
        if not normalized:
            continue
        if split_multi_quotes:
            for line in split_multi_quote_line(normalized):
                indexed_lines.append({"raw_index": raw_index, "line": line})
            continue
        indexed_lines.append({"raw_index": raw_index, "line": normalized})
    return indexed_lines


def _normalized_nonempty_lines(text: str, *, split_multi_quotes: bool) -> list[str]:
    return [
        str(item["line"])
        for item in _normalized_indexed_nonempty_lines(
            text,
            split_multi_quotes=split_multi_quotes,
        )
    ]


def _strict_section_pattern(
    line: str,
    *,
    price: str,
    amount: str = "",
) -> tuple[str | None, str | None, bool]:
    from .quotes import _extract_price

    fields = {"price": price}
    if str(amount or "").strip():
        fields["amount"] = amount
    annotations = build_annotations_from_fields(line, fields)
    names = {str(item["type"]) for item in annotations}
    if "price" not in names:
        return None, "price_not_found", False
    amount_in_pattern = False
    if str(amount or "").strip() and "amount" not in names:
        _price_value, left_text, _right_text = _extract_price(line)
        if re.search(r"\d", left_text):
            return None, "amount_not_found", False
    elif str(amount or "").strip():
        amount_in_pattern = True
    pattern = generate_strict_pattern_from_annotations(line, annotations)
    variables = re.findall(r"\{(\w+)\}", pattern)
    if any(name not in _STRICT_SECTION_VARIABLES for name in variables):
        return None, "unsupported_variable", False
    return pattern, None, amount_in_pattern


def _find_last_literal_span(line: str, literal: str) -> tuple[int, int] | None:
    matches = list(re.finditer(re.escape(str(literal or "")), str(line or "")))
    if not matches:
        return None
    match = matches[-1]
    return match.start(), match.end()


def _build_amount_label_matcher(label: str) -> re.Pattern[str] | None:
    normalized = normalize_strict_section_amount_label(label)
    if not normalized:
        return None
    parts = re.split(r"([/-])", normalized)
    regex_parts: list[str] = []
    for part in parts:
        if not part:
            continue
        if part == "-":
            regex_parts.append(r"\s*-\s*")
            continue
        if part == "/":
            regex_parts.append(r"\s*/\s*")
            continue
        regex_parts.append(re.escape(part))
    if not regex_parts:
        return None
    return re.compile("".join(regex_parts))


def normalize_strict_section_amount_label(value: str) -> str:
    text = normalize_quote_text(str(value or ""))
    if not text:
        return ""
    text = text.replace("／", "/").replace("－", "-").replace("—", "-").replace("~", "-")
    text = re.sub(r"\s*([/-])\s*", r"\1", text)
    return text.strip()


def _compile_group_parser_quote_pattern(
    line: str,
    *,
    quote: dict[str, Any],
) -> tuple[str | None, str | None]:
    normalized_line = normalize_quote_text(line)
    price_text = str(quote.get("price_text") or quote.get("price") or "").strip()
    price_span = _find_last_literal_span(normalized_line, price_text)
    if price_span is None:
        return None, "price_not_found"

    annotations: list[dict[str, str | int]] = [
        {
            "type": "price",
            "value": price_text,
            "start": price_span[0],
            "end": price_span[1],
        }
    ]

    amount_range = str(quote.get("amount_range") or "").strip()
    if amount_range:
        amount_label = str(quote.get("label") or "").strip() or amount_range
        matcher = _build_amount_label_matcher(amount_label)
        if matcher is None:
            return None, "amount_not_found"
        search_text = normalized_line[: price_span[0]]
        amount_match = matcher.search(search_text)
        if amount_match is None:
            return None, "amount_not_found"
        annotations.append(
            {
                "type": "amount",
                "value": normalized_line[amount_match.start() : amount_match.end()],
                "start": amount_match.start(),
                "end": amount_match.end(),
            }
        )

    annotations.sort(key=lambda item: int(item["start"]))
    pattern = generate_strict_pattern_from_annotations(normalized_line, annotations)
    variables = re.findall(r"\{(\w+)\}", pattern)
    if any(name not in _GROUP_PARSER_VARIABLES for name in variables):
        return None, "unsupported_variable"
    return pattern, None


def derive_strict_section_preview(
    *,
    raw_text: str,
    section_start_line: int,
    section_end_line: int,
    defaults: dict[str, Any],
    rows: list[dict[str, Any]],
    ignored_line_indexes: list[int],
) -> dict[str, Any]:
    raw_lines = raw_text.splitlines()
    total_lines = len(raw_lines)
    errors: list[str] = []
    if total_lines == 0:
        return {
            "preview_rows": [],
            "derived_section": None,
            "derived_patterns": [],
            "unhandled_lines": [],
            "ignored_lines": [],
            "errors": ["empty_raw_text"],
            "can_save": False,
        }
    if section_start_line < 0 or section_end_line < section_start_line or section_end_line >= total_lines:
        return {
            "preview_rows": [],
            "derived_section": None,
            "derived_patterns": [],
            "unhandled_lines": [],
            "ignored_lines": [],
            "errors": ["invalid_section_range"],
            "can_save": False,
        }

    selected_indexes = set(range(section_start_line, section_end_line + 1))
    ignored_set = {int(item) for item in ignored_line_indexes if int(item) in selected_indexes}
    bindings: dict[int, dict[str, Any]] = {}
    preview_rows: list[dict[str, Any]] = []
    for idx, row in enumerate(rows):
        try:
            source_line_index = int(row.get("source_line_index"))
        except (TypeError, ValueError):
            errors.append(f"row_{idx}_missing_source_line")
            continue
        if source_line_index not in selected_indexes:
            errors.append(f"row_{idx}_source_out_of_section")
            continue
        if source_line_index in bindings:
            errors.append(f"duplicate_source_line_{source_line_index}")
            continue
        amount = str(row.get("amount") or "").strip()
        price = str(row.get("price") or "").strip()
        if not amount or not price:
            errors.append(f"row_{idx}_missing_amount_or_price")
            continue
        bindings[source_line_index] = {
            "source_line_index": source_line_index,
            "amount": amount,
            "price": price,
            "country_or_currency": str(row.get("country_or_currency") or "").strip(),
            "form_factor": str(row.get("form_factor") or "").strip(),
        }

    section_lines: list[dict[str, Any]] = []
    derived_patterns: list[dict[str, Any]] = []
    ignored_lines: list[dict[str, Any]] = []
    unhandled_lines: list[dict[str, Any]] = []
    quote_candidates: list[dict[str, Any]] = []
    restriction_candidates: list[dict[str, Any]] = []
    non_quote_literals: list[dict[str, Any]] = []
    default_card_type = str(defaults.get("card_type") or "").strip()
    default_country = str(defaults.get("country_or_currency") or "").strip()
    default_form_factor = str(defaults.get("form_factor") or "").strip()

    for source_line_index in range(section_start_line, section_end_line + 1):
        raw_line = raw_lines[source_line_index]
        normalized_line = normalize_quote_text(raw_line)
        if not normalized_line:
            continue
        line_info = {
            "source_line_index": source_line_index,
            "line": normalized_line,
        }
        if looks_like_quote_line(normalized_line):
            quote_candidates.append(dict(line_info))
        elif is_restriction_candidate(normalized_line):
            restriction_candidates.append(dict(line_info))
        else:
            non_quote_literals.append(dict(line_info))
        binding = bindings.get(source_line_index)
        if binding is not None:
            pattern, error, amount_in_pattern = _strict_section_pattern(
                normalized_line,
                price=binding["price"],
                amount=binding["amount"],
            )
            if error:
                unhandled_lines.append(
                    {
                        "source_line_index": source_line_index,
                        "line": normalized_line,
                        "reason": error,
                    }
                )
                continue
            final_country = binding["country_or_currency"] or default_country
            final_form_factor = binding["form_factor"] or default_form_factor
            if not default_card_type or not final_country or not final_form_factor:
                errors.append(f"row_{source_line_index}_missing_fixed_fields")
            preview_row = {
                "source_line_index": source_line_index,
                "card_type": default_card_type,
                "country_or_currency": final_country,
                "amount": binding["amount"],
                "form_factor": final_form_factor,
                "price": binding["price"],
                "source_line": normalized_line,
            }
            preview_rows.append(preview_row)
            section_line = {
                "kind": "quote",
                "source_line_index": source_line_index,
                "pattern": pattern,
                "outputs": {
                    "card_type": default_card_type,
                    "country_or_currency": final_country,
                    "form_factor": final_form_factor,
                    **(
                        {}
                        if amount_in_pattern
                        else {"amount_range": normalize_strict_section_amount_label(binding["amount"])}
                    ),
                },
            }
            section_lines.append(section_line)
            derived_patterns.append(
                {
                    "source_line_index": source_line_index,
                    "kind": "quote",
                    "pattern": pattern,
                }
            )
            continue
        if source_line_index in ignored_set:
            ignored_lines.append(
                {
                    "source_line_index": source_line_index,
                    "line": normalized_line,
                }
            )
            continue
        if looks_like_quote_line(normalized_line):
            unhandled_lines.append(
                {
                    "source_line_index": source_line_index,
                    "line": normalized_line,
                    "reason": "price_like_line_unhandled",
                }
            )
            continue
        if is_restriction_candidate(normalized_line):
            section_lines.append(
                {
                    "kind": "restriction",
                    "source_line_index": source_line_index,
                    "pattern": normalized_line,
                }
            )
            derived_patterns.append(
                {
                    "source_line_index": source_line_index,
                    "kind": "restriction",
                    "pattern": normalized_line,
                }
            )
            continue
        section_lines.append(
            {
                "kind": "literal",
                "source_line_index": source_line_index,
                "pattern": normalized_line,
            }
        )
        derived_patterns.append(
            {
                "source_line_index": source_line_index,
                "kind": "literal",
                "pattern": normalized_line,
            }
        )

    preview_rows.sort(key=lambda item: int(item["source_line_index"]))
    restriction_text = _join_restriction_lines(
        [str(item["line"]) for item in restriction_candidates if int(item["source_line_index"]) not in ignored_set]
    )
    for row in preview_rows:
        row["restriction_text"] = restriction_text
    if not default_card_type:
        errors.append("missing_default_card_type")
    if not default_form_factor:
        errors.append("missing_default_form_factor")
    if not preview_rows:
        errors.append("no_quote_rows")

    derived_section = {
        "label": str(defaults.get("section_label") or "").strip() or "未命名 Section",
        "priority": int(defaults.get("priority") or 100),
        "defaults": {
            "card_type": default_card_type,
            "country_or_currency": default_country,
            "form_factor": default_form_factor,
        },
        "lines": section_lines,
    }

    return {
        "preview_rows": preview_rows,
        "derived_section": derived_section,
        "derived_patterns": derived_patterns,
        "unhandled_lines": unhandled_lines,
        "ignored_lines": ignored_lines,
        "quote_candidates": quote_candidates,
        "restriction_candidates": restriction_candidates,
        "non_quote_literals": non_quote_literals,
        "errors": errors,
        "can_save": not errors and not unhandled_lines,
    }


_RESULT_TEMPLATE_BLOCK_RE = re.compile(r"^\[(.+)\]$")
_RESULT_TEMPLATE_PRICE_RE = re.compile(
    r"^(?P<label>.+?)[=:](?P<price>\d+(?:\.\d+)?)$"
)
_RESULT_TEMPLATE_AMOUNT_RE = re.compile(r"^\d+(?:\s*[-/]\s*\d+)*$")


def _normalize_result_block_name(name: str) -> str:
    return re.sub(r"\s+", "", str(name or "").strip().lower())


def _result_default_key(name: str) -> str:
    normalized = _normalize_result_block_name(name)
    mapping = {
        "标题": "title",
        "title": "title",
        "形态": "form_factor",
        "formfactor": "form_factor",
        "卡种": "card_type",
        "cardtype": "card_type",
        "国家": "country_or_currency",
        "币种": "country_or_currency",
        "国家/币种": "country_or_currency",
        "countryorcurrency": "country_or_currency",
    }
    return mapping.get(normalized, "")


def _extract_bracket_label(line: str) -> str:
    normalized = normalize_quote_text(line)
    if normalized.startswith("【") and normalized.endswith("】"):
        return normalized[1:-1].strip()
    if normalized.startswith("[") and normalized.endswith("]"):
        return normalized[1:-1].strip()
    return ""


def _result_note_candidate(line: str) -> bool:
    normalized = normalize_quote_text(line)
    if not normalized:
        return False
    if _extract_bracket_label(normalized):
        return False
    if all(ch in _DECORATION_CHARS for ch in normalized):
        return False
    return not looks_like_quote_line(normalized)


def _parse_result_quote_line(line: str) -> dict[str, Any] | None:
    from .quotes import (
        normalize_quote_amount_range,
        normalize_quote_country_or_currency,
    )

    normalized = normalize_quote_text(line)
    match = _RESULT_TEMPLATE_PRICE_RE.match(normalized)
    if match is None:
        return None
    label = str(match.group("label") or "").strip()
    price_text = str(match.group("price") or "").strip()
    if not label or not price_text:
        return None
    amount_range = ""
    country_or_currency = ""
    if _RESULT_TEMPLATE_AMOUNT_RE.fullmatch(label.replace(" ", "")):
        amount_range = normalize_quote_amount_range(label)
    else:
        country_or_currency = normalize_quote_country_or_currency(label)
    return {
        "label": label,
        "country_or_currency": country_or_currency,
        "amount_range": amount_range,
        "price": float(price_text),
        "price_text": price_text,
    }


def parse_result_template_text(result_template_text: str) -> dict[str, Any]:
    from .quotes import normalize_quote_card_type, normalize_quote_form_factor

    draft = {
        "defaults": {
            "title": "",
            "form_factor": "不限",
            "card_type": "",
            "country_or_currency": "",
        },
        "cards": [],
        "notes": [],
    }
    errors: list[str] = []
    warnings: list[str] = []
    current_block: str | None = None
    current_card: dict[str, Any] | None = None
    active_defaults = dict(draft["defaults"])
    pending_defaults = dict(active_defaults)

    for raw_line in str(result_template_text or "").splitlines():
        normalized = normalize_quote_text(raw_line)
        if not normalized:
            continue
        block_match = _RESULT_TEMPLATE_BLOCK_RE.match(normalized)
        if block_match is not None:
            block_name = str(block_match.group(1) or "").strip()
            block_key = _normalize_result_block_name(block_name)
            if block_key in {"默认", "default"}:
                current_block = "defaults"
                current_card = None
                pending_defaults = dict(active_defaults)
                continue
            if block_key in {"说明", "note", "notes"}:
                current_block = "notes"
                current_card = None
                continue
            current_block = "card"
            current_card = {
                "label": block_name,
                "card_type": normalize_quote_card_type(block_name),
                "defaults": dict(pending_defaults),
                "quotes": [],
            }
            active_defaults = dict(current_card["defaults"])
            draft["cards"].append(current_card)
            continue

        if current_block is None:
            errors.append(f"这行不在任何块里，请先写 [默认] 或 [真实卡种]：{normalized}")
            continue
        if current_block == "defaults":
            quote_line = _parse_result_quote_line(normalized)
            if quote_line is not None:
                errors.append(f"[默认] 里只能写固定默认值，不能直接写报价：{normalized}")
                continue
            if "=" in normalized:
                key_text, value = normalized.split("=", 1)
            elif ":" in normalized:
                key_text, value = normalized.split(":", 1)
            else:
                errors.append(f"[默认] 这一行格式不对：{normalized}")
                continue
            field_key = _result_default_key(key_text)
            if not field_key:
                warnings.append(f"[默认] 里这个字段当前不会生效，已忽略：{key_text.strip()}")
                continue
            value = str(value or "").strip()
            if field_key == "form_factor":
                value = normalize_quote_form_factor(value)
            pending_defaults[field_key] = value
            draft["defaults"][field_key] = value
            continue
        if current_block == "notes":
            draft["notes"].append(normalized)
            continue
        if current_card is None:
            errors.append(f"这行缺少卡种块，先写 [真实卡种] 再填报价：{normalized}")
            continue
        parsed_quote = _parse_result_quote_line(normalized)
        if parsed_quote is None:
            errors.append(f"报价格式不对，统一写成 50=5.3 或 USD=5.20：{normalized}")
            continue
        current_card["quotes"].append(parsed_quote)

    if not draft["cards"]:
        errors.append("至少要有一个卡种块，例如 [Apple] 或 [Steam]。")
    for card in draft["cards"]:
        if not card["quotes"]:
            errors.append(f"卡种块里没有任何报价：{card['card_type']}")
    if not draft["defaults"].get("form_factor"):
        draft["defaults"]["form_factor"] = "不限"
    return {
        "draft_structure": draft,
        "errors": errors,
        "warnings": warnings,
    }


def _normalize_result_amount_label(text: str) -> str:
    from .quotes import normalize_quote_amount_range

    cleaned = normalize_quote_text(text)
    if not cleaned:
        return ""
    cleaned = re.sub(r"[（(][^）)]*[）)]\s*$", "", cleaned).strip()
    return normalize_quote_amount_range(cleaned)


def _resolve_result_card_type(card_type: str, *, chat_name: str = "") -> str:
    from .quotes import _infer_card_type, normalize_quote_card_type

    normalized = normalize_quote_card_type(card_type)
    if normalized and normalized.lower() != "unknown":
        return normalized
    chat_card_type = normalize_quote_card_type(_infer_card_type(chat_name or "") or "")
    if chat_card_type and chat_card_type.lower() != "unknown":
        return chat_card_type
    return normalized


def suggest_result_template_text(raw_text: str, *, chat_name: str = "") -> str:
    from .quotes import (
        _extract_price,
        _infer_card_type,
        _infer_country_or_currency,
        normalize_quote_card_type,
        normalize_quote_country_or_currency,
        normalize_quote_form_factor,
    )

    defaults = {
        "country_or_currency": "",
        "form_factor": normalize_quote_form_factor("不限"),
    }
    cards: list[dict[str, Any]] = []
    current_card: dict[str, Any] | None = None
    current_defaults = dict(defaults)

    for item in _normalized_virtual_lines(str(raw_text or ""), split_multi_quotes=True):
        normalized = str(item["line"] or "")
        source_line = str(item.get("source_line") or normalized)
        if not normalized:
            continue
        inferred_card = _infer_card_type(source_line)
        if inferred_card and (
            any(marker in source_line for marker in ("【", "】", "[", "]", "价格表", "报价单", "="))
            or not looks_like_quote_line(source_line)
        ):
            next_card = {
                "card_type": normalize_quote_card_type(inferred_card),
                "defaults": dict(current_defaults),
                "quotes": [],
            }
            cards.append(next_card)
            current_card = next_card
            continue
        inferred_country = normalize_quote_country_or_currency(_infer_country_or_currency(source_line) or "")
        if (
            inferred_country
            and not looks_like_quote_line(source_line)
            and not defaults["country_or_currency"]
            and not inferred_card
        ):
            defaults["country_or_currency"] = inferred_country
            current_defaults["country_or_currency"] = inferred_country
            continue
        detection = auto_detect_line_type(normalized)
        if detection.get("type") == "price":
            fields = dict(detection.get("fields") or {})
            price_text = str(fields.get("price") or "").strip()
            if not price_text:
                continue
            desired_country = normalize_quote_country_or_currency(
                str(fields.get("currency") or fields.get("country") or "")
            )
            desired_form_factor = normalize_quote_form_factor(
                str(fields.get("form_factor") or current_defaults.get("form_factor") or "不限")
            )
            amount_label = str(fields.get("amount") or "").strip()
            label = ""
            if amount_label:
                label = amount_label
            elif desired_country:
                label = desired_country
            else:
                price_value, left_text, _ = _extract_price(normalized)
                if price_value is None:
                    continue
                label = normalize_quote_country_or_currency(left_text) if left_text else ""
            if not label:
                continue
            if current_card is None:
                fallback_card = _resolve_result_card_type(inferred_card or "unknown", chat_name=chat_name)
                current_card = {
                    "card_type": fallback_card,
                    "defaults": dict(current_defaults),
                    "quotes": [],
                }
                cards.append(current_card)
            if amount_label:
                target_defaults = {
                    "country_or_currency": desired_country or str(current_defaults.get("country_or_currency") or ""),
                    "form_factor": desired_form_factor,
                }
                current_card_defaults = {
                    "country_or_currency": str(current_card.get("defaults", {}).get("country_or_currency") or ""),
                    "form_factor": str(current_card.get("defaults", {}).get("form_factor") or ""),
                }
                if (
                    str(current_card.get("card_type") or "") != str(
                        _resolve_result_card_type(inferred_card or str(current_card.get("card_type") or ""), chat_name=chat_name)
                    )
                    or current_card_defaults != target_defaults
                ):
                    fallback_card = _resolve_result_card_type(
                        inferred_card or str(current_card.get("card_type") or "") or "unknown",
                        chat_name=chat_name,
                    )
                    current_defaults = dict(target_defaults)
                    current_card = {
                        "card_type": fallback_card,
                        "defaults": dict(current_defaults),
                        "quotes": [],
                    }
                    cards.append(current_card)
                else:
                    current_defaults = dict(target_defaults)
            current_card["quotes"].append({"label": label, "price_text": price_text})
            continue

    lines: list[str] = []
    for card in cards:
        quotes = list(card.get("quotes") or [])
        if not quotes:
            continue
        card_defaults = dict(card.get("defaults") or {})
        if lines:
            lines.append("")
        lines.append("[默认]")
        if card_defaults.get("country_or_currency"):
            lines.append(f"国家 / 币种={card_defaults['country_or_currency']}")
        lines.append(f"形态={card_defaults.get('form_factor') or defaults['form_factor']}")
        lines.append("")
        lines.append(f"[{card['card_type']}]")
        for quote in quotes:
            lines.append(f"{quote['label']}={quote['price_text']}")
    if not lines:
        lines = ["[默认]", f"形态={defaults['form_factor']}"]
    return "\n".join(lines).strip()


def _line_matches_result_quote(line: str, quote: dict[str, Any]) -> bool:
    from .quotes import _extract_price, _infer_country_or_currency_candidates
    from .quotes import normalize_quote_amount_range, normalize_quote_country_or_currency

    normalized = normalize_quote_text(line)
    detection = auto_detect_line_type(normalized)
    price_value = None
    left_text = ""
    parsed_amount = ""
    parsed_country = ""
    if detection.get("type") == "price":
        fields = dict(detection.get("fields") or {})
        try:
            price_value = float(str(fields.get("price") or "").strip())
        except ValueError:
            price_value = None
        parsed_amount = normalize_quote_amount_range(str(fields.get("amount") or "").strip()) if fields.get("amount") else ""
        parsed_country = normalize_quote_country_or_currency(
            str(fields.get("currency") or fields.get("country") or "").strip()
        )
        left_text = normalize_quote_text(
            " ".join(
                part
                for part in (
                    str(fields.get("country") or fields.get("currency") or "").strip(),
                    str(fields.get("amount") or "").strip(),
                    str(fields.get("form_factor") or "").strip(),
                )
                if part
            )
        )
    if price_value is None:
        price_value, left_text, _ = _extract_price(normalized)
        if price_value is None:
            return False
    if abs(price_value - float(quote.get("price") or 0.0)) > 0.000001:
        return False
    amount_range = str(quote.get("amount_range") or "").strip()
    if amount_range:
        if parsed_amount and parsed_amount != amount_range:
            return False
        if not parsed_amount and _normalize_result_amount_label(left_text) != amount_range:
            return False
        target_country = str(quote.get("country_or_currency") or "").strip()
        if not target_country:
            return True
        if parsed_country:
            return parsed_country == target_country
        candidates = _infer_country_or_currency_candidates(normalized)
        return target_country in candidates
    target_country = str(quote.get("country_or_currency") or "").strip()
    if not target_country:
        return False
    if parsed_country:
        return parsed_country == target_country
    candidates = _infer_country_or_currency_candidates(normalized)
    if target_country in candidates:
        return True
    return target_country.lower() in left_text.lower().replace(" ", "")


def _extract_result_amount_source(line: str) -> str:
    from .quotes import _extract_price

    normalized = normalize_quote_text(line)
    _price_value, left_text, _right_text = _extract_price(normalized)
    return normalize_quote_text(left_text)


def _is_card_header_candidate(source_line: str, target_card_type: str) -> bool:
    from .quotes import _infer_card_type, normalize_quote_card_type

    inferred_card = normalize_quote_card_type(_infer_card_type(source_line) or "")
    if not inferred_card or inferred_card != target_card_type:
        return False
    return any(marker in source_line for marker in ("【", "】", "[", "]", "价格表", "报价单", "=")) or not looks_like_quote_line(source_line)


def _preview_row_signature(row: dict[str, Any]) -> tuple[str, str, str, str, float]:
    from .quotes import (
        normalize_quote_amount_range,
        normalize_quote_card_type,
        normalize_quote_country_or_currency,
        normalize_quote_form_factor,
    )

    return (
        normalize_quote_card_type(str(row.get("card_type") or "").strip()),
        normalize_quote_country_or_currency(str(row.get("country_or_currency") or "").strip()),
        normalize_quote_amount_range(str(row.get("amount") or row.get("amount_range") or "不限")),
        normalize_quote_form_factor(str(row.get("form_factor") or "不限")),
        round(float(row.get("price") or 0.0), 6),
    )


def _parsed_row_signature(row: Any) -> tuple[str, str, str, str, float]:
    from .quotes import (
        normalize_quote_amount_range,
        normalize_quote_card_type,
        normalize_quote_country_or_currency,
        normalize_quote_form_factor,
    )

    return (
        normalize_quote_card_type(str(getattr(row, "card_type", "") or "").strip()),
        normalize_quote_country_or_currency(str(getattr(row, "country_or_currency", "") or "").strip()),
        normalize_quote_amount_range(str(getattr(row, "amount_range", "") or "不限")),
        normalize_quote_form_factor(str(getattr(row, "form_factor", "") or "不限")),
        round(float(getattr(row, "price", 0.0) or 0.0), 6),
    )


def _validate_group_parser_replay(
    *,
    raw_text: str,
    chat_name: str,
    derived_sections: list[dict[str, Any]],
    expected_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    if not derived_sections or not expected_rows:
        return {
            "ok": False,
            "errors": ["当前原文还没有生成可验证的群骨架。"],
            "expected_rows": [],
            "actual_rows": [],
        }

    candidate = TemplateConfig(
        version=_GROUP_PARSER_VERSION,
        sections=derived_sections,
    )
    parsed = parse_message_with_template(
        raw_text,
        candidate,
        chat_name=chat_name,
    )
    expected = sorted(_preview_row_signature(item) for item in expected_rows)
    actual = sorted(_parsed_row_signature(item) for item in parsed.rows)
    errors: list[str] = []
    if parsed.exceptions:
        unmatched_lines: list[str] = []
        for exc in parsed.exceptions:
            for line in str(getattr(exc, "source_line", "") or "").splitlines():
                cleaned = normalize_quote_text(line)
                if cleaned and cleaned not in unmatched_lines:
                    unmatched_lines.append(cleaned)
        for line in unmatched_lines:
            errors.append(f"当前原文严格回放时，仍有报价行没有被骨架吸收：{line}")
    if actual != expected:
        errors.append("当前原文严格回放后，生成结果和右侧标准答案不一致。")
    return {
        "ok": not errors,
        "errors": errors,
        "expected_rows": expected,
        "actual_rows": actual,
    }


def derive_result_template_preview(
    *,
    raw_text: str,
    result_template_text: str,
    chat_name: str = "",
) -> dict[str, Any]:
    from .quotes import _infer_card_type, normalize_quote_card_type, normalize_quote_form_factor

    normalized_lines = _normalized_virtual_lines(str(raw_text or ""), split_multi_quotes=True)
    suggested_text = suggest_result_template_text(raw_text, chat_name=chat_name)
    effective_text = str(result_template_text or "").strip() or suggested_text
    parsed = parse_result_template_text(effective_text)
    draft = dict(parsed.get("draft_structure") or {})
    errors = list(parsed.get("errors") or [])
    warnings = list(parsed.get("warnings") or [])
    preview_rows: list[dict[str, Any]] = []
    derived_sections: list[dict[str, Any]] = []
    note_candidates: list[str] = list(draft.get("notes") or [])
    skeleton_summaries: list[dict[str, Any]] = []

    cards = list(draft.get("cards") or [])
    if not normalized_lines:
        errors.append("原文为空，不能编译群专用解析器。")
    if errors:
        return {
            "result_template_text": effective_text,
            "suggested_result_template_text": suggested_text,
            "draft_structure": draft,
            "preview_rows": preview_rows,
            "derived_sections": derived_sections,
            "notes": note_candidates,
            "errors": errors,
            "warnings": warnings,
            "can_save": False,
            "skeleton_summaries": skeleton_summaries,
            "strict_replay_ok": False,
            "strict_replay_errors": ["原文或模板草稿还不完整，无法做严格回放。"],
        }

    section_starts: list[int] = []
    search_cursor = 0
    single_card = len(cards) == 1
    for card_index, card in enumerate(cards):
        target_card_type = _resolve_result_card_type(
            str(card.get("card_type") or "").strip(),
            chat_name=chat_name,
        )
        card["card_type"] = target_card_type
        first_quote = next(iter(card.get("quotes") or []), None)
        found_index = None
        quote_start = None
        matched_header = False
        if first_quote is not None:
            for pos in range(search_cursor, len(normalized_lines)):
                if _line_matches_result_quote(
                    str(normalized_lines[pos]["line"] or ""),
                    first_quote,
                ):
                    quote_start = pos
                    break
        if quote_start is not None:
            found_index = quote_start
            for pos in range(quote_start, search_cursor - 1, -1):
                source_line = str(normalized_lines[pos].get("source_line") or normalized_lines[pos]["line"] or "")
                if _is_card_header_candidate(source_line, target_card_type):
                    found_index = pos
                    matched_header = True
                    break
        if found_index is None:
            for pos in range(search_cursor, len(normalized_lines)):
                source_line = str(normalized_lines[pos].get("source_line") or normalized_lines[pos]["line"] or "")
                if _is_card_header_candidate(source_line, target_card_type):
                    found_index = pos
                    matched_header = True
                    break
        if quote_start is not None and not matched_header:
            found_index = quote_start
            if _resolve_result_card_type("", chat_name=chat_name) == target_card_type:
                warnings.append(
                    f"原文里没找到 {target_card_type} 标题，已按群名“{chat_name or '当前群'}”回退成当前群专用卡种。"
                )
            else:
                warnings.append(
                    f"原文里没找到 {target_card_type} 标题，已从这一段第一条报价行开始编译骨架。"
                )
        if found_index is None:
            if single_card and card_index == 0:
                found_index = search_cursor
                if _resolve_result_card_type("", chat_name=chat_name) == target_card_type:
                    warnings.append(
                        f"原文里没找到 {target_card_type} 标题，已按群名“{chat_name or '当前群'}”回退成当前群专用卡种。"
                    )
                else:
                    warnings.append(
                        f"原文里没找到 {target_card_type} 标题，已从原文起始位置尝试编译当前群骨架。"
                    )
            else:
                errors.append(f"没在原文里找到卡种标题：{target_card_type}")
                continue
        section_starts.append(found_index)
        search_cursor = found_index + 1

    if errors:
        return {
            "result_template_text": effective_text,
            "suggested_result_template_text": suggested_text,
            "draft_structure": draft,
            "preview_rows": preview_rows,
            "derived_sections": derived_sections,
            "notes": note_candidates,
            "errors": errors,
            "warnings": warnings,
            "can_save": False,
            "skeleton_summaries": skeleton_summaries,
            "strict_replay_ok": False,
            "strict_replay_errors": ["卡种标题或右侧模板还没对齐，无法做严格回放。"],
        }

    from .quotes import normalize_quote_country_or_currency
    used_note_values = {normalize_quote_text(item) for item in note_candidates}
    base_priority = 100
    for card_index, card in enumerate(cards):
        section_start = section_starts[card_index]
        section_end = (
            section_starts[card_index + 1] - 1
            if card_index + 1 < len(section_starts)
            else len(normalized_lines) - 1
        )
        card_defaults = dict(draft.get("defaults") or {})
        card_defaults.update(dict(card.get("defaults") or {}))
        default_form_factor = normalize_quote_form_factor(
            str(card_defaults.get("form_factor") or "不限")
        )
        default_country = normalize_quote_country_or_currency(
            str(card_defaults.get("country_or_currency") or "")
        )
        matched_quote_lines: dict[int, dict[str, Any]] = {}
        for quote in list(card.get("quotes") or []):
            found_pos = None
            for pos in range(section_start, section_end + 1):
                if pos in matched_quote_lines:
                    continue
                if _line_matches_result_quote(str(normalized_lines[pos]["line"] or ""), quote):
                    found_pos = pos
                    break
            if found_pos is None:
                label = str(quote.get("country_or_currency") or quote.get("amount_range") or "")
                errors.append(
                    f"右侧模板里的报价没有在原文找到对应行：{card.get('card_type')} / {label}={quote.get('price_text')}"
                )
                continue
            line = str(normalized_lines[found_pos]["line"] or "")
            source_line = str(normalized_lines[found_pos].get("source_line") or line)
            amount_range = str(quote.get("amount_range") or "").strip()
            pattern, error = _compile_group_parser_quote_pattern(
                line,
                quote=quote,
            )
            if error:
                errors.append(
                    f"这条报价没法编译成稳定骨架：{line}（{error}）"
                )
                continue
            matched_quote_lines[found_pos] = {
                "kind": "quote",
                "pattern": pattern,
                "outputs": {
                    "card_type": str(card.get("card_type") or "").strip(),
                    "country_or_currency": str(quote.get("country_or_currency") or "").strip() or default_country,
                    "form_factor": default_form_factor,
                    "amount_range": amount_range or "不限",
                },
            }
            final_country = str(quote.get("country_or_currency") or "").strip() or default_country
            preview_rows.append(
                {
                    "card_type": str(card.get("card_type") or "").strip(),
                    "country_or_currency": final_country,
                    "amount": amount_range or "不限",
                    "form_factor": default_form_factor,
                    "price": str(quote.get("price_text") or ""),
                    "source_line": source_line,
                }
            )

        section_lines: list[dict[str, Any]] = []
        for pos in range(section_start, section_end + 1):
            line = str(normalized_lines[pos]["line"] or "")
            source_line = str(normalized_lines[pos].get("source_line") or line)
            quote_line = matched_quote_lines.get(pos)
            if quote_line is not None:
                section_lines.append(quote_line)
                continue
            if looks_like_quote_line(line):
                errors.append(f"原文里还有未吸收的报价行：{source_line}")
            if _result_note_candidate(source_line) and source_line not in used_note_values:
                note_candidates.append(source_line)
                used_note_values.add(source_line)
        section_payload = {
            "label": str(card.get("card_type") or "").strip() or f"Section {card_index + 1}",
            "priority": base_priority + (card_index * 10),
            "defaults": {
                "card_type": str(card.get("card_type") or "").strip(),
                "country_or_currency": default_country,
                "form_factor": default_form_factor,
            },
            "lines": section_lines,
        }
        derived_sections.append(section_payload)
        skeleton_summaries.append(
            {
                "label": section_payload["label"],
                "quote_lines": len(section_lines),
                "defaults": dict(section_payload["defaults"]),
            }
        )

    preview_rows.sort(
        key=lambda item: (
            str(item.get("card_type") or ""),
            str(item.get("country_or_currency") or ""),
            str(item.get("amount") or ""),
        )
    )
    replay_validation = _validate_group_parser_replay(
        raw_text=raw_text,
        chat_name=chat_name,
        derived_sections=derived_sections,
        expected_rows=preview_rows,
    )
    if replay_validation["errors"]:
        errors.extend(replay_validation["errors"])
    return {
        "result_template_text": effective_text,
        "suggested_result_template_text": suggested_text,
        "draft_structure": draft,
        "preview_rows": preview_rows,
        "derived_sections": derived_sections,
        "notes": note_candidates,
        "errors": errors,
        "warnings": warnings,
        "can_save": not errors and bool(preview_rows) and bool(derived_sections),
        "skeleton_summaries": skeleton_summaries,
        "strict_replay_ok": replay_validation["ok"],
        "strict_replay_errors": replay_validation["errors"],
    }


def _parse_message_with_strict_sections(
    text: str,
    template: "TemplateConfig",
    *,
    platform: str = "",
    chat_id: str = "",
    chat_name: str = "",
    message_id: str = "",
    source_name: str = "",
    sender_id: str = "",
    source_group_key: str = "",
    message_time: str = "",
) -> "ParsedQuoteDocument":
    from .quotes import (
        ParsedQuoteDocument,
        ParsedQuoteException,
        ParsedQuoteRow,
        normalize_quote_form_factor,
    )

    lines = _normalized_indexed_nonempty_lines(text, split_multi_quotes=False)
    rows: list[ParsedQuoteRow] = []
    exceptions: list[ParsedQuoteException] = []
    unmatched_quote_lines: list[str] = []
    unmatched_restriction_lines: list[str] = []
    sections = sorted(
        [item for item in template.sections if item.get("enabled", True)],
        key=lambda item: (int(item.get("priority") or 100), str(item.get("id") or "")),
    )
    index = 0
    while index < len(lines):
        matched = False
        for section in sections:
            section_lines = [item for item in section.get("lines", []) if str(item.get("pattern") or "").strip()]
            if not section_lines:
                continue
            if index + len(section_lines) > len(lines):
                continue
            candidate_rows: list[ParsedQuoteRow] = []
            candidate_restrictions: list[str] = []
            failed = False
            section_defaults = dict(section.get("defaults") or {})
            for offset, section_line in enumerate(section_lines):
                current_line = str(lines[index + offset]["line"] or "")
                kind = str(section_line.get("kind") or "literal").strip()
                pattern = str(section_line.get("pattern") or "").strip()
                if kind == "literal":
                    if current_line != pattern:
                        failed = True
                        break
                    continue
                if kind == "restriction":
                    if current_line != pattern:
                        failed = True
                        break
                    candidate_restrictions.append(current_line)
                    continue
                if kind != "quote":
                    failed = True
                    break
                variables = re.findall(r"\{(\w+)\}", pattern)
                if any(name not in _STRICT_SECTION_VARIABLES for name in variables):
                    failed = True
                    break
                matched_variables = match_pattern(current_line, pattern)
                if matched_variables is None:
                    failed = True
                    break
                price_str = matched_variables.get("price")
                amount_str = matched_variables.get("amount")
                if not price_str:
                    failed = True
                    break
                try:
                    price = float(price_str)
                except ValueError:
                    failed = True
                    break
                outputs = dict(section_line.get("outputs") or {})
                card_type = str(outputs.get("card_type") or section_defaults.get("card_type") or "").strip()
                country = str(outputs.get("country_or_currency") or section_defaults.get("country_or_currency") or "").strip()
                form_factor = str(outputs.get("form_factor") or section_defaults.get("form_factor") or "").strip()
                amount_range = str(outputs.get("amount_range") or section_defaults.get("amount_range") or "").strip()
                if not card_type or not country or not form_factor:
                    failed = True
                    break
                candidate_rows.append(
                    ParsedQuoteRow(
                        source_group_key=source_group_key,
                        platform=platform,
                        chat_id=chat_id,
                        chat_name=chat_name,
                        message_id=message_id,
                        source_name=source_name,
                        sender_id=sender_id,
                        card_type=card_type,
                        country_or_currency=country,
                        amount_range=normalize_strict_section_amount_label(
                            amount_str or amount_range or "不限"
                        ),
                        multiplier=None,
                        form_factor=normalize_quote_form_factor(form_factor),
                        price=price,
                        quote_status="active",
                        restriction_text="",
                        source_line=current_line,
                        raw_text=text,
                        message_time=message_time,
                        effective_at=message_time,
                        expires_at=None,
                        parser_template="strict-section",
                        parser_version="strict-section-v1",
                        confidence=1.0,
                    )
                )
            if failed:
                continue
            restriction_text = _join_restriction_lines(candidate_restrictions)
            for row in candidate_rows:
                row.restriction_text = restriction_text
            rows.extend(candidate_rows)
            index += len(section_lines)
            matched = True
            break
        if matched:
            continue
        current_line = str(lines[index]["line"] or "")
        if looks_like_quote_line(current_line):
            unmatched_quote_lines.append(current_line)
        elif is_restriction_candidate(current_line):
            unmatched_restriction_lines.append(current_line)
        index += 1

    unmatched_lines = unmatched_quote_lines + unmatched_restriction_lines
    if unmatched_lines:
        exceptions.append(
            ParsedQuoteException(
                source_group_key=source_group_key,
                platform=platform,
                chat_id=chat_id,
                chat_name=chat_name,
                source_name=source_name,
                sender_id=sender_id,
                reason="strict_match_failed",
                source_line="\n".join(unmatched_lines),
                raw_text=text,
                message_time=message_time,
                parser_template="strict-section",
                parser_version="strict-section-v1",
                confidence=0.0,
            )
        )
    parse_status = "parsed" if rows else "empty"
    return ParsedQuoteDocument(
        source_group_key=source_group_key,
        platform=platform,
        chat_id=chat_id,
        chat_name=chat_name,
        message_id=message_id,
        source_name=source_name,
        sender_id=sender_id,
        raw_text=text,
        message_time=message_time,
        parser_template="strict-section",
        parser_version="strict-section-v1",
        confidence=1.0 if rows else 0.0,
        parse_status=parse_status,
        rows=rows,
        exceptions=exceptions,
    )


def _parse_message_with_group_parser(
    text: str,
    template: "TemplateConfig",
    *,
    platform: str = "",
    chat_id: str = "",
    chat_name: str = "",
    message_id: str = "",
    source_name: str = "",
    sender_id: str = "",
    source_group_key: str = "",
    message_time: str = "",
) -> "ParsedQuoteDocument":
    from .quotes import (
        ParsedQuoteDocument,
        ParsedQuoteException,
        ParsedQuoteRow,
        normalize_quote_amount_range,
        normalize_quote_country_or_currency,
        normalize_quote_form_factor,
    )

    lines = _normalized_virtual_lines(text, split_multi_quotes=True)
    rows: list[ParsedQuoteRow] = []
    exceptions: list[ParsedQuoteException] = []
    sections = sorted(
        [item for item in template.sections if item.get("enabled", True)],
        key=lambda item: (int(item.get("priority") or 100), str(item.get("id") or "")),
    )
    used_indexes: set[int] = set()
    section_cursor = 0

    for section in sections:
        quote_lines = [
            item
            for item in section.get("lines", [])
            if str(item.get("kind") or "quote").strip() == "quote"
            and str(item.get("pattern") or "").strip()
        ]
        if not quote_lines:
            continue
        candidate_matches: list[tuple[int, ParsedQuoteRow]] = []
        failed = False
        search_cursor = section_cursor
        section_defaults = dict(section.get("defaults") or {})
        for quote_line in quote_lines:
            found_match: tuple[int, ParsedQuoteRow] | None = None
            pattern = str(quote_line.get("pattern") or "").strip()
            variables = re.findall(r"\{(\w+)\}", pattern)
            if any(name not in _GROUP_PARSER_VARIABLES for name in variables):
                failed = True
                break
            outputs = dict(quote_line.get("outputs") or {})
            expected_amount = normalize_quote_amount_range(
                str(outputs.get("amount_range") or "不限")
            )
            expected_country = normalize_quote_country_or_currency(
                str(outputs.get("country_or_currency") or section_defaults.get("country_or_currency") or "")
            )
            expected_form_factor = normalize_quote_form_factor(
                str(outputs.get("form_factor") or section_defaults.get("form_factor") or "不限")
            )
            expected_card_type = str(
                outputs.get("card_type") or section_defaults.get("card_type") or ""
            ).strip()
            for pos in range(search_cursor, len(lines)):
                if pos in used_indexes or any(existing_pos == pos for existing_pos, _row in candidate_matches):
                    continue
                current_line = str(lines[pos]["line"] or "")
                source_line = str(lines[pos].get("source_line") or current_line)
                matched_variables = match_pattern(current_line, pattern)
                if matched_variables is None:
                    continue
                price_str = str(matched_variables.get("price") or "").strip()
                if not price_str:
                    continue
                try:
                    price = float(price_str)
                except ValueError:
                    continue
                amount_str = str(matched_variables.get("amount") or "").strip()
                normalized_amount = normalize_quote_amount_range(amount_str or expected_amount or "不限")
                if "amount" in variables and expected_amount and expected_amount != "不限":
                    if normalized_amount != expected_amount:
                        continue
                matched_country = str(
                    matched_variables.get("country_or_currency")
                    or matched_variables.get("country")
                    or ""
                ).strip()
                normalized_country = normalize_quote_country_or_currency(
                    matched_country or expected_country
                )
                if matched_country and expected_country and normalized_country != expected_country:
                    continue
                if not expected_card_type or not normalized_country or not expected_form_factor:
                    continue
                found_match = (
                    pos,
                    ParsedQuoteRow(
                        source_group_key=source_group_key,
                        platform=platform,
                        chat_id=chat_id,
                        chat_name=chat_name,
                        message_id=message_id,
                        source_name=source_name,
                        sender_id=sender_id,
                        card_type=expected_card_type,
                        country_or_currency=expected_country or normalized_country,
                        amount_range=normalized_amount,
                        multiplier=None,
                        form_factor=expected_form_factor,
                        price=price,
                        quote_status="active",
                        restriction_text="",
                        source_line=source_line,
                        raw_text=text,
                        message_time=message_time,
                        effective_at=message_time,
                        expires_at=None,
                        parser_template="group-parser",
                        parser_version=_GROUP_PARSER_VERSION,
                        confidence=1.0,
                    ),
                )
                break
            if found_match is None:
                failed = True
                break
            candidate_matches.append(found_match)
            search_cursor = found_match[0] + 1
        if failed:
            continue
        for pos, row in candidate_matches:
            used_indexes.add(pos)
            rows.append(row)
        if candidate_matches:
            section_cursor = max(pos for pos, _row in candidate_matches) + 1

    unmatched_lines = [
        str(item.get("source_line") or item["line"])
        for index, item in enumerate(lines)
        if index not in used_indexes and looks_like_quote_line(str(item["line"] or ""))
    ]
    if unmatched_lines:
        exceptions.append(
            ParsedQuoteException(
                source_group_key=source_group_key,
                platform=platform,
                chat_id=chat_id,
                chat_name=chat_name,
                source_name=source_name,
                sender_id=sender_id,
                reason="strict_match_failed",
                source_line="\n".join(unmatched_lines),
                raw_text=text,
                message_time=message_time,
                parser_template="group-parser",
                parser_version=_GROUP_PARSER_VERSION,
                confidence=0.0,
            )
        )
    parse_status = "parsed" if rows else "empty"
    return ParsedQuoteDocument(
        source_group_key=source_group_key,
        platform=platform,
        chat_id=chat_id,
        chat_name=chat_name,
        message_id=message_id,
        source_name=source_name,
        sender_id=sender_id,
        raw_text=text,
        message_time=message_time,
        parser_template="group-parser",
        parser_version=_GROUP_PARSER_VERSION,
        confidence=1.0 if rows else 0.0,
        parse_status=parse_status,
        rows=rows,
        exceptions=exceptions,
    )


def parse_message_with_template(
    text: str,
    template: "TemplateConfig",
    *,
    platform: str = "",
    chat_id: str = "",
    chat_name: str = "",
    message_id: str = "",
    source_name: str = "",
    sender_id: str = "",
    source_group_key: str = "",
    message_time: str = "",
) -> "ParsedQuoteDocument":
    if template.version == _GROUP_PARSER_VERSION:
        return _parse_message_with_group_parser(
            text,
            template,
            platform=platform,
            chat_id=chat_id,
            chat_name=chat_name,
            message_id=message_id,
            source_name=source_name,
            sender_id=sender_id,
            source_group_key=source_group_key,
            message_time=message_time,
        )
    if template.version == "strict-section-v1":
        return _parse_message_with_strict_sections(
            text,
            template,
            platform=platform,
            chat_id=chat_id,
            chat_name=chat_name,
            message_id=message_id,
            source_name=source_name,
            sender_id=sender_id,
            source_group_key=source_group_key,
            message_time=message_time,
        )

    from .quotes import (
        ParsedQuoteDocument,
        ParsedQuoteRow,
        ParsedQuoteException,
        normalize_quote_amount_range,
        normalize_quote_form_factor,
    )

    lines = _normalized_virtual_lines(text, split_multi_quotes=True)
    rows: list[ParsedQuoteRow] = []
    exceptions: list[ParsedQuoteException] = []
    
    current_card_type = template.defaults.get("card_type") or "unknown"
    current_country = template.defaults.get("country") or ""
    current_form_factor = template.defaults.get("form_factor") or "不限"

    unmatched_lines: list[str] = []

    for item in lines:
        line = str(item["line"] or "")
        source_line = str(item.get("source_line") or line)
        if not line:
            continue

        matched = False
        for rule in template.rules:
            pattern = rule.get("pattern", "")
            rule_type = rule.get("type", "price")

            variables = match_pattern(line, pattern)
            if variables is not None:
                matched = True
                if rule_type == "section":
                    if "card_type" in variables:
                        current_card_type = _clean_card_type(variables["card_type"])
                    if "country" in variables:
                        current_country = variables["country"]
                elif rule_type == "price":
                    price_str = variables.get("price")
                    if price_str is None:
                        continue
                    try:
                        price = float(price_str)
                    except ValueError:
                        continue

                    amount = variables.get("amount", "不限")
                    country = variables.get("country") or current_country
                    form_factor = variables.get("form_factor") or current_form_factor
                    restriction = variables.get("restriction", "")

                    rows.append(ParsedQuoteRow(
                        source_group_key=source_group_key,
                        platform=platform,
                        chat_id=chat_id,
                        chat_name=chat_name,
                        message_id=message_id,
                        source_name=source_name,
                        sender_id=sender_id,
                        card_type=current_card_type,
                        country_or_currency=country,
                        amount_range=normalize_quote_amount_range(amount),
                        multiplier=None,
                        form_factor=normalize_quote_form_factor(form_factor),
                        price=price,
                        quote_status="active",
                        restriction_text=restriction,
                        source_line=source_line,
                        raw_text=text,
                        message_time=message_time,
                        effective_at=message_time,
                        expires_at=None,
                        parser_template="data-engine",
                        parser_version="data-engine-v1",
                        confidence=1.0,
                    ))
                break

        if not matched and looks_like_quote_line(line):
            unmatched_lines.append(source_line)

    # 消息级异常：所有未匹配行合并为一条异常
    if unmatched_lines:
        exceptions.append(ParsedQuoteException(
            source_group_key=source_group_key,
            platform=platform,
            chat_id=chat_id,
            chat_name=chat_name,
            source_name=source_name,
            sender_id=sender_id,
            reason="strict_match_failed",
            source_line="\n".join(unmatched_lines),
            raw_text=text,
            message_time=message_time,
            parser_template="data-engine",
            parser_version="data-engine-v1",
            confidence=0.0
        ))

    parse_status = "parsed" if rows else "empty"
    return ParsedQuoteDocument(
        source_group_key=source_group_key,
        platform=platform,
        chat_id=chat_id,
        chat_name=chat_name,
        message_id=message_id,
        source_name=source_name,
        sender_id=sender_id,
        raw_text=text,
        message_time=message_time,
        parser_template="data-engine",
        parser_version="data-engine-v1",
        confidence=1.0 if rows else 0.0,
        parse_status=parse_status,
        rows=rows,
        exceptions=exceptions,
    )


def generate_strict_pattern_from_annotations(line: str, annotations: list[dict[str, str | int]]) -> str:
    """根据标注的变量位置，将整行替换为带 {变量} 的 strict pattern。"""
    # Sort annotations by start index
    sorted_anns = sorted(annotations, key=lambda x: int(x["start"]))
    
    result = ""
    last_idx = 0
    for ann in sorted_anns:
        start = int(ann["start"])
        end = int(ann["end"])
        ann_type = str(ann["type"])
        
        if start > last_idx:
            result += line[last_idx:start]
            
        result += f"{{{ann_type}}}"
        last_idx = end
        
    if last_idx < len(line):
        result += line[last_idx:]

    return result


def build_annotations_from_fields(
    source_line: str, fields: dict[str, str]
) -> list[dict[str, str | int]]:
    """将 {变量名: 值} 字典转为带 start/end 的 annotations，按位置排序。"""
    annotations: list[dict[str, str | int]] = []
    for field_type, value in fields.items():
        value = value.strip()
        if not value:
            continue
        start = source_line.find(value)
        end = start + len(value) if start != -1 else -1
        if start == -1 and field_type == "amount":
            matcher = _build_amount_label_matcher(value)
            amount_match = matcher.search(source_line) if matcher is not None else None
            if amount_match is not None:
                start = amount_match.start()
                end = amount_match.end()
        if start == -1:
            continue
        annotations.append({
            "type": field_type,
            "value": source_line[start:end] if field_type == "amount" else value,
            "start": start,
            "end": end,
        })
    annotations.sort(key=lambda a: a["start"])
    return annotations


# ---------------------------------------------------------------------------
# Auto-detection: classify lines and suggest template patterns
# ---------------------------------------------------------------------------

# Ordered from most specific to least specific
_AUTO_DETECT_PATTERNS: list[tuple[re.Pattern, str, list[str]]] = [
    # {country} {currency} {amount}={price}
    (re.compile(r'^([A-Za-z\u4e00-\u9fff]+) ([A-Z]{2,4}) ([\d\-/~]+)=([\d.]+)$'),
     "{country} {currency} {amount}={price}",
     ["country", "currency", "amount", "price"]),
    # {country} {amount} {form_factor}={price}({restriction})
    (re.compile(r'^([A-Za-z\u4e00-\u9fff]+) ([\d\-/~]+) ([A-Za-z\u4e00-\u9fff/]+)=([\d.]+)\((.+)\)$'),
     "{country} {amount} {form_factor}={price}({restriction})",
     ["country", "amount", "form_factor", "price", "restriction"]),
    # {country} {amount} {form_factor}={price}
    (re.compile(r'^([A-Za-z\u4e00-\u9fff]+) ([\d\-/~]+) ([A-Za-z\u4e00-\u9fff/]+)=([\d.]+)$'),
     "{country} {amount} {form_factor}={price}",
     ["country", "amount", "form_factor", "price"]),
    # {country} {amount}={price}({restriction})
    (re.compile(r'^([A-Za-z\u4e00-\u9fff]+) ([\d\-/~]+)=([\d.]+)\((.+)\)$'),
     "{country} {amount}={price}({restriction})",
     ["country", "amount", "price", "restriction"]),
    # {country} {amount}={price} {restriction}
    (re.compile(r'^([A-Za-z\u4e00-\u9fff]+) ([\d\-/~]+)=([\d.]+) (.+)$'),
     "{country} {amount}={price} {restriction}",
     ["country", "amount", "price", "restriction"]),
    # {country} {amount}={price}
    (re.compile(r'^([A-Za-z\u4e00-\u9fff]+) ([\d\-/~]+)=([\d.]+)$'),
     "{country} {amount}={price}",
     ["country", "amount", "price"]),
    # {country}:{amount}={price} {restriction}
    (re.compile(r'^([A-Za-z\u4e00-\u9fff]+):([\d\-/~]+)=([\d.]+) (.+)$'),
     "{country}:{amount}={price} {restriction}",
     ["country", "amount", "price", "restriction"]),
    # {country}:{amount}={price}{restriction}
    (re.compile(r'^([A-Za-z\u4e00-\u9fff]+):([\d\-/~]+)=([\d.]+)([A-Za-z\u4e00-\u9fff(（].+)$'),
     "{country}:{amount}={price}{restriction}",
     ["country", "amount", "price", "restriction"]),
    # {country}:{amount}={price}
    (re.compile(r'^([A-Za-z\u4e00-\u9fff]+):([\d\-/~]+)=([\d.]+)$'),
     "{country}:{amount}={price}",
     ["country", "amount", "price"]),
    # {country}={price}({restriction})
    (re.compile(r'^([A-Za-z\u4e00-\u9fff]+)=([\d.]+)\((.+)\)$'),
     "{country}={price}({restriction})",
     ["country", "price", "restriction"]),
    # {country}={price} {restriction}
    (re.compile(r'^([A-Za-z\u4e00-\u9fff]+)=([\d.]+) (.+)$'),
     "{country}={price} {restriction}",
     ["country", "price", "restriction"]),
    # {amount}={price}({restriction})
    (re.compile(r'^([\d\-/~]+)=([\d.]+)\((.+)\)$'),
     "{amount}={price}({restriction})",
     ["amount", "price", "restriction"]),
    # {amount}={price}
    (re.compile(r'^([\d\-/~]+)=([\d.]+)$'),
     "{amount}={price}",
     ["amount", "price"]),
    # {country}{currency}:{price}  (e.g. "美金USD:5.20", "欧元EUR:6.00")
    (re.compile(r'^([a-z\u4e00-\u9fff]+)([A-Z]{2,4}):([\d.]+)$'),
     "{country}{currency}:{price}",
     ["country", "currency", "price"]),
    # {country} {currency}:{price}  (e.g. "美 USD:5.78")
    (re.compile(r'^([A-Za-z\u4e00-\u9fff]+) ([A-Z]{2,4}):([\d.]+)$'),
     "{country} {currency}:{price}",
     ["country", "currency", "price"]),
    # {country}:{price}  (e.g. "澳大利亚:4.07", "新 加 坡:4.32")
    (re.compile(r'^([A-Za-z\u4e00-\u9fff ]+):([\d.]+)$'),
     "{country}:{price}",
     ["country", "price"]),
    # {country}={price}{suffix} (trailing text like 卡图)
    (re.compile(r'^([A-Za-z\u4e00-\u9fff]+)=([\d.]+)([A-Za-z\u4e00-\u9fff]+)$'),
     "{country}={price}{restriction}",
     ["country", "price", "restriction"]),
    # {country}={price}
    (re.compile(r'^([A-Za-z\u4e00-\u9fff]+)=([\d.]+)$'),
     "{country}={price}",
     ["country", "price"]),
    # {country} {price}
    (re.compile(r'^([A-Za-z\u4e00-\u9fff]+) ([\d.]+)$'),
     "{country} {price}",
     ["country", "price"]),
    # {country}{price}
    (re.compile(r'^([A-Za-z\u4e00-\u9fff]+)([\d.]+)$'),
     "{country}{price}",
     ["country", "price"]),
]


def _auto_detect_normalized_line(line: str) -> dict:
    for regex, pattern, field_names in _AUTO_DETECT_PATTERNS:
        m = regex.match(line)
        if m:
            fields = {name: m.group(i + 1) for i, name in enumerate(field_names)}
            return {"type": "price", "pattern": pattern, "fields": fields}
    return {"type": "skip", "pattern": "", "fields": {}}


def auto_detect_line_type(line: str) -> dict:
    """Auto-detect whether a line is a section header, price quote, or noise.

    Returns {"type": "section"|"price"|"skip", "pattern": str, "fields": dict}
    """
    line = normalize_quote_text(line)
    if not line:
        return {"type": "skip", "pattern": "", "fields": {}}

    # Section header: 【...】
    if re.match(r'^【.+】$', line):
        return {"type": "section", "pattern": "【{card_type}】", "fields": {}}

    detected = _auto_detect_normalized_line(line)
    if detected["type"] == "price":
        return detected

    bracket_entries = _extract_bracket_quote_entries(line)
    if len(bracket_entries) == 1:
        return _auto_detect_normalized_line(str(bracket_entries[0]["line"]))
    return {"type": "skip", "pattern": "", "fields": {}}


def suggest_template_rules(text: str) -> list[dict]:
    """Analyze a full message and suggest template rules.

    Returns a list of per-line detections:
      [{"line": str, "type": "section"|"price"|"skip", "pattern": str, "fields": dict}, ...]
    """
    results: list[dict] = []
    for item in _normalized_virtual_lines(text, split_multi_quotes=True):
        line = str(item["line"] or "")
        source_line = str(item.get("source_line") or line)
        detection = auto_detect_line_type(line)
        results.append({"line": source_line, **detection})
    return results


def deduplicate_rules(detections: list[dict]) -> list[dict]:
    """Extract unique template rules from auto-detection results."""
    seen: set[str] = set()
    rules: list[dict] = []
    for d in detections:
        pattern = d.get("pattern", "")
        rule_type = d.get("type", "")
        if not pattern or rule_type == "skip":
            continue
        if pattern not in seen:
            seen.add(pattern)
            rules.append({"pattern": pattern, "type": rule_type})
    return rules
