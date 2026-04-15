from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
import hashlib
import json
import os
import re
from typing import Any

from .contracts import NormalizedMessageEnvelope
from .quote_candidates import QuoteCandidateMessage, QuoteCandidateRow
from .quote_snapshot import (
    get_effective_snapshot_decision,
    get_guarded_publish_mode,
    infer_snapshot_hypothesis,
)
from .repair_cases import package_quote_repair_case
from .quote_validation import validate_quote_candidate_document


PARSER_VERSION = "quote-v1"
AUTO_PUBLISH_CONFIDENCE = 0.8
DEFAULT_STALE_AFTER_MINUTES = 120
APPLE_STALE_AFTER_MINUTES = 30

QUOTE_WALL_RUNTIME_MODE_ENV = "BOOKKEEPING_QUOTE_WALL_MODE"
QUOTE_WALL_MODE_VALIDATION_ONLY = "validation_only"
QUOTE_WALL_MODE_EXPERIMENTAL_ACTIVE = "experimental_active_wall"
_EXPERIMENTAL_WALL_MODE_ALIASES = {
    QUOTE_WALL_MODE_EXPERIMENTAL_ACTIVE,
    "experimental",
    "experimental_active",
    "experimental_wall",
    "live_experimental_wall",
}

_SECTION_HEADER_RE = re.compile(r"[【\[](?P<label>.+?)[】\]]")
_PRICE_TOKEN_RE = re.compile(r"(￥|¥|RMB|人民币)\s*(?P<price>\d+(?:\.\d+)?)", re.IGNORECASE)
_PRICE_AFTER_SEPARATOR_RE = re.compile(
    r"[:：=]\s*(?P<price>\d+(?:\.\d+)?)(?!.*\d)",
)
_TRAILING_PRICE_RE = re.compile(r"(?P<label>.+?)(?P<price>\d+(?:\.\d+)?)\s*$")
_RANGE_RE = re.compile(
    r"(?P<start>\d+(?:\.\d+)?)\s*(?:[-~－—/／]\s*(?P<end>\d+(?:\.\d+)?))?"
)
_MULTIPLIER_RE = re.compile(r"(?P<value>\d+(?:\.\d+)?)\s*(?:X|x|倍数|倍)")
_QUESTION_KEYWORDS = ("问", "待定", "不拿", "不收", "不加账", "ask", "询价")

_RESTRICTION_KEYWORDS = (
    "尾刀",
    "连卡",
    "批量",
    "大额",
    "收据",
    "使用时间",
    "压1h",
    "不退",
    "不赔",
    "锁卡",
    "勿清",
    "请标记",
    "先问",
)
_MODIFIER_RE = re.compile(r"[-+]\d+(?:\.\d+)?")
_NON_QUOTE_OPERATIONAL_KEYWORDS = (
    "当前账单金额",
    "账单金额",
    "balance",
    "closing balance",
    "current balance",
    "bill amount",
)

_INVALID_TEMPLATE_COUNTRY_TOKENS = (
    "卡图",
    "卡密",
    "白卡",
    "横白",
    "横卡",
    "竖卡",
    "快刷",
    "快加",
    "网单",
)


def _build_snapshot_hypothesis(
    *,
    raw_message: str,
    parser_template: str,
) -> tuple[str, str, dict[str, Any]]:
    hypothesis = infer_snapshot_hypothesis(
        raw_message=raw_message,
        parser_template=parser_template,
    )
    return (
        hypothesis.hypothesis,
        hypothesis.reason,
        dict(hypothesis.evidence),
    )


def get_quote_wall_runtime_mode(config_value: str | None = None) -> str:
    raw_mode = (
        config_value
        if config_value is not None
        else os.environ.get(
            QUOTE_WALL_RUNTIME_MODE_ENV,
            QUOTE_WALL_MODE_VALIDATION_ONLY,
        )
    )
    normalized = str(raw_mode or "").strip().lower()
    if normalized in _EXPERIMENTAL_WALL_MODE_ALIASES:
        return QUOTE_WALL_MODE_EXPERIMENTAL_ACTIVE
    return QUOTE_WALL_MODE_VALIDATION_ONLY


def describe_quote_wall_runtime_mode(config_value: str | None = None) -> dict[str, Any]:
    mode = get_quote_wall_runtime_mode(config_value)
    real_wall_updates_enabled = mode == QUOTE_WALL_MODE_EXPERIMENTAL_ACTIVE
    return {
        "mode": mode,
        "real_wall_updates_enabled": real_wall_updates_enabled,
        "downstream_actions_enabled": False,
        "status_label": (
            "单人运营实验墙"
            if real_wall_updates_enabled
            else "验证证据模式"
        ),
        "summary_text": (
            "当前报价墙会通过 guarded publisher 真实更新，但仍处于实验运行，且下游动作保持关闭。"
            if real_wall_updates_enabled
            else "当前只保留验证证据，不会通过 guarded publisher 真实更新报价墙。"
        ),
    }


@dataclass(frozen=True, slots=True)
class QuoteGroupProfile:
    key: str
    default_card_type: str | None = None
    default_country_or_currency: str | None = None
    default_form_factor: str | None = None
    default_multiplier: str | None = None
    parser_template: str | None = None
    stale_after_minutes: int | None = None
    note: str = ""
    template_config: str = ""
    dictionary_aliases: dict[str, tuple[tuple[str, str], ...]] | None = None


def sanitize_quote_group_template_config(
    *,
    parser_template: str | None,
    template_config_raw: str,
    default_country_or_currency: str | None = None,
    default_form_factor: str | None = None,
) -> str:
    parser_template_text = str(parser_template or "").strip()
    raw = str(template_config_raw or "").strip()
    if not raw or parser_template_text != "supermarket-card":
        return raw
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return raw
    if str(payload.get("version") or "") != "group-parser-v1":
        return raw

    fallback_country = normalize_quote_country_or_currency(
        str(default_country_or_currency or "").strip()
    )
    fallback_form_factor = normalize_quote_form_factor(
        str(default_form_factor or "不限").strip() or "不限"
    )
    sections = list(payload.get("sections") or [])
    changed = False

    for section in sections:
        if not isinstance(section, dict):
            continue
        defaults = dict(section.get("defaults") or {})
        section_label = str(section.get("label") or "").strip()
        original_country = str(defaults.get("country_or_currency") or "").strip()
        inferred_section_form = _sanitize_section_form_factor_hint(
            original_country or section_label,
            fallback=fallback_form_factor,
        )
        if _looks_invalid_template_country_token(original_country):
            if fallback_country and original_country != fallback_country:
                defaults["country_or_currency"] = fallback_country
                changed = True
            elif original_country:
                defaults.pop("country_or_currency", None)
                changed = True
        default_form_factor = normalize_quote_form_factor(
            str(defaults.get("form_factor") or "").strip() or "不限"
        )
        if (
            inferred_section_form != "不限"
            and default_form_factor == "不限"
        ):
            defaults["form_factor"] = inferred_section_form
            changed = True
        if defaults != dict(section.get("defaults") or {}):
            section["defaults"] = defaults

        lines = list(section.get("lines") or [])
        for line in lines:
            if not isinstance(line, dict):
                continue
            outputs = dict(line.get("outputs") or {})
            output_country = str(outputs.get("country_or_currency") or "").strip()
            inferred_output_form = _sanitize_section_form_factor_hint(
                output_country or str(line.get("pattern") or "").strip() or section_label,
                fallback=str(defaults.get("form_factor") or fallback_form_factor),
            )
            if _looks_invalid_template_country_token(output_country):
                replacement_country = str(defaults.get("country_or_currency") or fallback_country or "").strip()
                if replacement_country:
                    outputs["country_or_currency"] = replacement_country
                elif output_country:
                    outputs.pop("country_or_currency", None)
                changed = True
            output_form_factor = normalize_quote_form_factor(
                str(outputs.get("form_factor") or "").strip() or "不限"
            )
            if inferred_output_form != "不限" and output_form_factor == "不限":
                outputs["form_factor"] = inferred_output_form
                changed = True
            if outputs != dict(line.get("outputs") or {}):
                line["outputs"] = outputs
        if lines != list(section.get("lines") or []):
            section["lines"] = lines

    if not changed:
        return raw
    payload["sections"] = sections
    return json.dumps(payload, ensure_ascii=False)


def _looks_invalid_template_country_token(value: str) -> bool:
    normalized = _normalize_key(str(value or ""))
    if not normalized:
        return False
    return any(_normalize_key(token) in normalized for token in _INVALID_TEMPLATE_COUNTRY_TOKENS)


def _sanitize_section_form_factor_hint(value: str, *, fallback: str = "不限") -> str:
    inferred = normalize_quote_form_factor(_infer_form_factor(str(value or "")) or "")
    if inferred and inferred != "不限":
        return inferred
    return normalize_quote_form_factor(fallback or "不限")


_QUOTE_GROUP_PROFILES: tuple[tuple[str, QuoteGroupProfile], ...] = (
    (
        "客人1",
        QuoteGroupProfile(
            key="customer_1_apple",
            default_card_type="Apple",
            parser_template="apple_modifier_sheet",
            stale_after_minutes=APPLE_STALE_AFTER_MINUTES,
            note="US Apple 横白卡基准价，后续 #竖卡/#电子/#代码 为同上下文派生价",
        ),
    ),
)

_CARD_TYPE_ALIASES: list[tuple[str, str]] = [
    ("itunes", "Apple"),
    ("i tunes", "Apple"),
    ("apple", "Apple"),
    ("苹果", "Apple"),
    ("steam", "Steam"),
    ("黄金雷蛇", "Razer"),
    ("黄金雷蛇us", "Razer"),
    ("美国雷蛇", "Razer"),
    ("绿蛇", "Razer"),
    ("外卡雷蛇", "Razer"),
    ("razer gold", "Razer"),
    ("razer", "Razer"),
    ("外卡xbox", "Xbox"),
    ("美国xb", "Xbox"),
    ("xb", "Xbox"),
    ("xbox", "Xbox"),
    ("google play", "Google Play"),
    ("google", "Google Play"),
    ("playstation", "PSN"),
    ("psn", "PSN"),
    ("paysafecard", "Paysafe"),
    ("安全支付图密同价", "Paysafe"),
    ("安全支付图密", "Paysafe"),
    ("paysafe", "Paysafe"),
    ("roblox", "Roblox"),
    ("pcs", "PCS"),
    ("transcash", "Transcash"),
    ("eneba", "Eneba"),
    ("game stop", "Game Stop"),
    ("gamestop", "Game Stop"),
    ("sephora", "Sephora"),
    ("footlocker", "Footlocker"),
    ("macy", "Macy's"),
    ("nordstrom", "Nordstrom"),
    ("razer gold 雷蛇", "Razer"),
    ("雷蛇", "Razer"),
    ("蒸汽", "Steam"),
    ("谷歌", "Google Play"),
    ("罗布乐思", "Roblox"),
    ("安全支付", "Paysafe"),
]


_CARD_TYPE_QUERY_ALIASES: dict[str, str] = {
    "it": "Apple",
    "itunes": "Apple",
    "iTunes": "Apple",
}

_COUNTRY_ALIASES: list[tuple[str, str]] = [
    ("eu", "EUR"),
    ("欧盟", "EUR"),
    ("usd", "USD"),
    ("usa", "USD"),
    ("us", "USD"),
    ("美金", "USD"),
    ("美国", "USD"),
    ("eur", "EUR"),
    ("欧元", "EUR"),
    ("gbp", "GBP"),
    ("uk", "GBP"),
    ("英镑", "GBP"),
    ("英国", "GBP"),
    ("hkd", "HKD"),
    ("hk", "HKD"),
    ("香港", "HKD"),
    ("cad", "CAD"),
    ("加元", "CAD"),
    ("加拿大", "CAD"),
    ("aud", "AUD"),
    ("澳元", "AUD"),
    ("澳大利亚", "AUD"),
    ("nzd", "NZD"),
    ("新西兰", "NZD"),
    ("chf", "CHF"),
    ("瑞士", "CHF"),
    ("希腊", "希腊"),
    ("葡萄牙", "葡萄牙"),
    ("意大利", "意大利"),
    ("意", "意大利"),
    ("比利时", "比利时"),
    ("比", "比利时"),
    ("爱尔兰", "爱尔兰"),
    ("爱", "爱尔兰"),
    ("奥地利", "奥地利"),
    ("奥", "奥地利"),
    ("荷兰", "荷兰"),
    ("荷", "荷兰"),
    ("法国", "法国"),
    ("法", "法国"),
    ("芬兰", "芬兰"),
    ("芬", "芬兰"),
    ("西班牙", "西班牙"),
    ("西", "西班牙"),
    ("斯洛伐克", "斯洛伐克"),
    ("斯洛文尼亚", "斯洛文尼亚"),
    ("pln", "PLN"),
    ("波兰", "PLN"),
    ("sgd", "SGD"),
    ("新加坡", "SGD"),
    ("mas", "MYR"),
    ("myr", "MYR"),
    ("马来西亚", "MYR"),
    ("mx", "MXN"),
    ("mexico", "MXN"),
    ("墨西哥", "MXN"),
    ("mex", "MXN"),
    ("bra", "BRL"),
    ("bar", "BRL"),
    ("brl", "BRL"),
    ("巴西", "BRL"),
    ("dkk", "DKK"),
    ("丹麦", "DKK"),
    ("sek", "SEK"),
    ("瑞典", "SEK"),
    ("nok", "NOK"),
    ("挪威", "NOK"),
    ("czk", "CZK"),
    ("捷克", "CZK"),
    ("krw", "KRW"),
    ("韩国", "KRW"),
    ("cop", "COP"),
    ("哥伦比亚", "COP"),
    ("php", "PHP"),
    ("菲律宾", "PHP"),
    ("inr", "INR"),
    ("india", "INR"),
    ("印度", "INR"),
    ("thb", "THB"),
    ("thailand", "THB"),
    ("泰国", "THB"),
    ("idr", "IDR"),
    ("indonesia", "IDR"),
    ("印尼", "IDR"),
    ("印度尼西亚", "IDR"),
    ("try", "TRY"),
    ("turkey", "TRY"),
    ("土耳其", "TRY"),
    ("clp", "CLP"),
    ("chile", "CLP"),
    ("智利", "CLP"),
    ("pkr", "PKR"),
    ("pakistan", "PKR"),
    ("巴基斯坦", "PKR"),
    ("twd", "TWD"),
    ("taiwan", "TWD"),
    ("台湾", "TWD"),
    ("de", "德国"),
    ("德国", "德国"),
    ("jpy", "JPY"),
    ("japan", "JPY"),
    ("日元", "JPY"),
    ("日本", "JPY"),
    ("cny", "CNY"),
    ("rmb", "RMB"),
    ("人民币", "RMB"),
    ("sar", "SAR"),
    ("saudi", "SAR"),
    ("沙特", "SAR"),
    ("沙特阿拉伯", "SAR"),
    ("huf", "HUF"),
    ("hungary", "HUF"),
    ("匈牙利", "HUF"),
    ("zar", "ZAR"),
    ("south africa", "ZAR"),
    ("南非", "ZAR"),
    ("ils", "ILS"),
    ("israel", "ILS"),
    ("以色列", "ILS"),
    ("uyu", "UYU"),
    ("uruguay", "UYU"),
    ("乌拉圭", "UYU"),
    ("bgn", "BGN"),
    ("bulgaria", "BGN"),
    ("保加利亚", "BGN"),
    ("ron", "RON"),
    ("romania", "RON"),
    ("罗马尼亚", "RON"),
    ("pt", "葡萄牙"),
]

_FORM_FACTORS: list[tuple[str, str]] = [
    ("横白卡", "横白卡"),
    ("横白卡图", "横白卡"),
    ("白卡", "横白卡"),
    ("横白", "横白卡"),
    ("横卡", "横白卡"),
    ("横板", "横白卡"),
    ("竖卡", "竖卡"),
    ("竖板", "竖卡"),
    ("电子", "代码"),
    ("电子代码", "代码"),
    ("电子卡图", "代码"),
    ("代码", "代码"),
    ("code", "代码"),
    ("卡密", "代码"),
    ("纯数字", "代码"),
    ("图密", "代码"),
    ("图密同价", "代码"),
    ("卡图", "卡图"),
    ("纸质", "纸质"),
    ("photo", "photo"),
    ("图片", "图片"),
]

_BUILTIN_TEMPLATE_KEYS: set[str] = {
    "apple_modifier_sheet",
    "section_sheet",
    "simple_sheet",
    "group_fixed_sheet",
    "sectioned_group_sheet",
}


def list_builtin_quote_dictionary_aliases(
    category: str | None = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    requested = str(category or "").strip()
    selected = {
        "country_currency",
        "card_type",
        "form_factor",
    }
    if requested:
        if requested not in selected:
            return []
        selected = {requested}

    def _append(cat: str, alias: str, canonical: str) -> None:
        if cat not in selected:
            return
        normalized_alias = str(alias or "").strip()
        normalized_canonical = str(canonical or "").strip()
        if not normalized_alias or not normalized_canonical:
            return
        rows.append(
            {
                "category": cat,
                "alias": normalized_alias,
                "canonical_value": normalized_canonical,
                "canonical_input": normalized_canonical,
                "scope_platform": "",
                "scope_chat_id": "",
                "note": "builtin",
                "enabled": 1,
                "source": "builtin",
                "editable": False,
            }
        )

    for alias, canonical in _COUNTRY_ALIASES:
        _append("country_currency", alias, normalize_quote_country_or_currency(canonical))
    for alias, canonical in _CARD_TYPE_ALIASES:
        _append("card_type", alias, normalize_quote_card_type(canonical))
    for alias, canonical in _CARD_TYPE_QUERY_ALIASES.items():
        _append("card_type", alias, normalize_quote_card_type(canonical))
    for alias, canonical in _FORM_FACTORS:
        _append("form_factor", alias, normalize_quote_form_factor(canonical))

    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        key = f'{row["category"]}:{_normalize_key(str(row["alias"]))}'
        if key in seen:
            continue
        seen.add(key)
        row["id"] = f'builtin:{row["category"]}:{len(deduped) + 1}'
        deduped.append(row)
    return deduped


def normalize_quote_card_type(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    alias = _CARD_TYPE_QUERY_ALIASES.get(text) or _CARD_TYPE_QUERY_ALIASES.get(text.lower())
    if alias:
        return alias
    return _infer_card_type(text) or text


def normalize_quote_country_or_currency(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    return _infer_country_or_currency(text) or text.upper()


def normalize_quote_form_factor(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return "不限"
    if text == "不限":
        return text
    normalized = _normalize_key(text)
    code_like = any(
        alias in normalized
        for alias in (
            "代码",
            "code",
            "纯数字",
            "卡密",
            "图密",
            "图密同价",
            "电子",
            "electronic",
            "electron",
        )
    )
    if any(
        alias in normalized
        for alias in (
            "横白卡",
            "横白",
            "横卡",
            "横板",
            "horizontal",
            "卡图",
            "图片",
            "photo",
            "image",
            "card",
        )
    ) and not code_like:
        return "横白卡"
    if any(alias in normalized for alias in ("竖卡", "竖板", "vertical")):
        return "竖卡"

    values: list[str] = []
    if code_like:
        values.append("代码")
    if any(alias in normalized for alias in ("卡图", "图片", "photo", "image", "card")) and not code_like:
        values.append("横白卡")
    if any(alias in normalized for alias in ("纸质", "paper")):
        values.append("纸质")
    if values:
        deduped: list[str] = []
        for item in values:
            if item not in deduped:
                deduped.append(item)
        return "/".join(deduped)
    return text


def normalize_quote_amount_range(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return "不限"
    if text == "不限":
        return text
    text = text.replace("／", "/").replace("－", "-").replace("—", "-").replace("~", "-")
    spaced_range = re.fullmatch(r"(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)", text)
    if spaced_range:
        start = float(spaced_range.group(1))
        end = float(spaced_range.group(2))
        if end < start:
            start, end = end, start
        start_text = f"{start:g}"
        end_text = f"{end:g}"
        return start_text if start_text == end_text else f"{start_text}-{end_text}"
    text = re.sub(r"\s+", "", text)
    if "/" in text:
        parts = [item for item in text.split("/") if item]
        text = "-".join(parts)
    numeric_tokens = re.findall(r"\d+(?:\.\d+)?", text)
    if not numeric_tokens:
        return text or "不限"
    if len(numeric_tokens) == 1:
        return f"{float(numeric_tokens[0]):g}"
    bounds = sorted(float(token) for token in numeric_tokens)
    start_text = f"{bounds[0]:g}"
    end_text = f"{bounds[-1]:g}"
    return start_text if start_text == end_text else f"{start_text}-{end_text}"


def normalize_quote_multiplier(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    matched = re.fullmatch(r"(\d+(?:\.\d+)?)\s*(?:X|x|倍数|倍)", text)
    if matched:
        number = matched.group(1)
        if number.endswith(".0"):
            number = number[:-2]
        return f"{number}X"
    return ""


def quote_dictionary_aliases_from_rows(
    rows: list[dict[str, Any]] | tuple[dict[str, Any], ...],
) -> dict[str, tuple[tuple[str, str], ...]]:
    grouped: dict[str, list[tuple[str, str]]] = {}
    seen: dict[str, set[str]] = {}
    for row in rows or []:
        category = str(row.get("category") or "").strip()
        alias = str(row.get("alias") or "").strip()
        canonical = str(row.get("canonical_value") or "").strip()
        if not category or not alias or not canonical:
            continue
        alias_key = _normalize_key(alias)
        if alias_key in seen.setdefault(category, set()):
            continue
        seen[category].add(alias_key)
        grouped.setdefault(category, []).append((alias, canonical))
    return {
        category: tuple(
            sorted(values, key=lambda item: len(_normalize_key(item[0])), reverse=True)
        )
        for category, values in grouped.items()
    }


@dataclass(slots=True)
class ParsedQuoteRow:
    source_group_key: str
    platform: str
    chat_id: str
    chat_name: str
    message_id: str
    source_name: str
    sender_id: str
    card_type: str
    country_or_currency: str
    amount_range: str
    multiplier: str | None
    form_factor: str
    price: float
    quote_status: str
    restriction_text: str
    source_line: str
    raw_text: str
    message_time: str
    effective_at: str
    expires_at: str | None
    parser_template: str
    parser_version: str
    confidence: float
    scope_header_text: str = ""
    scope_header_line_index: int | None = None
    inherited_fields: tuple[str, ...] = ()


@dataclass(slots=True)
class ParsedQuoteException:
    source_group_key: str
    platform: str
    chat_id: str
    chat_name: str
    source_name: str
    sender_id: str
    reason: str
    source_line: str
    raw_text: str
    message_time: str
    parser_template: str
    parser_version: str
    confidence: float


@dataclass(slots=True)
class ParsedQuoteDocument:
    source_group_key: str
    platform: str
    chat_id: str
    chat_name: str
    message_id: str
    source_name: str
    sender_id: str
    raw_text: str
    message_time: str
    parser_template: str
    parser_version: str
    confidence: float
    parse_status: str
    rows: list[ParsedQuoteRow]
    exceptions: list[ParsedQuoteException]


def _quote_message_fingerprint(
    *,
    platform: str,
    chat_id: str,
    message_id: str,
    sender_id: str,
    raw_text: str,
) -> str:
    payload = "\n".join(
        (
            str(platform or ""),
            str(chat_id or ""),
            str(message_id or ""),
            str(sender_id or ""),
            str(raw_text or ""),
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _quote_row_publishable(row: ParsedQuoteRow) -> bool:
    return row.quote_status == "active" and row.confidence >= AUTO_PUBLISH_CONFIDENCE


def _quote_row_rejection_reasons(row: ParsedQuoteRow) -> list[dict[str, Any]]:
    reasons: list[dict[str, Any]] = []
    if row.quote_status != "active":
        reasons.append(
            {
                "reason": "quote_status_not_active",
                "quote_status": row.quote_status,
            }
        )
    if row.confidence < AUTO_PUBLISH_CONFIDENCE:
        reasons.append(
            {
                "reason": "confidence_below_auto_publish",
                "confidence": row.confidence,
                "required_confidence": AUTO_PUBLISH_CONFIDENCE,
            }
        )
    return reasons


def _quote_source_line_index(*, raw_text: str, source_line: str) -> int | None:
    normalized_source_line = str(source_line or "").strip()
    if not normalized_source_line:
        return None
    for index, line in enumerate(str(raw_text or "").splitlines()):
        if line.strip() == normalized_source_line:
            return index
    return None


def _extract_raw_fragment(*, source_line: str, candidates: tuple[str, ...]) -> str:
    haystack = str(source_line or "")
    for candidate in candidates:
        text = str(candidate or "").strip()
        if not text:
            continue
        match = re.search(re.escape(text), haystack, re.IGNORECASE)
        if match is not None:
            return match.group(0)
    return ""


def _extract_price_fragment(*, source_line: str, price: float | None) -> str:
    if price is None:
        return ""
    for match in re.finditer(r"\d+(?:\.\d+)?", str(source_line or "")):
        try:
            if float(match.group(0)) == float(price):
                return match.group(0)
        except ValueError:
            continue
    return ""


def _quote_row_field_sources(row: ParsedQuoteRow) -> dict[str, Any]:
    source_line_index = _quote_source_line_index(
        raw_text=row.raw_text,
        source_line=row.source_line,
    )
    field_sources: dict[str, Any] = {
        "line_evidence": {
            "source_line": row.source_line,
            "source_line_index": source_line_index,
        }
    }

    fragments = {
        "card_type": _extract_raw_fragment(
            source_line=row.source_line,
            candidates=(row.card_type,),
        ),
        "country_or_currency": _extract_raw_fragment(
            source_line=row.source_line,
            candidates=(row.country_or_currency,),
        ),
        "amount_range": _extract_raw_fragment(
            source_line=row.source_line,
            candidates=(
                row.amount_range,
                str(row.amount_range or "").replace("-", "/"),
                str(row.amount_range or "").replace("-", " "),
            ),
        ),
        "multiplier": _extract_raw_fragment(
            source_line=row.source_line,
            candidates=(row.multiplier or "",),
        ),
        "form_factor": _extract_raw_fragment(
            source_line=row.source_line,
            candidates=(row.form_factor,),
        ),
        "price": _extract_raw_fragment(
            source_line=_extract_price_fragment(
                source_line=row.source_line,
                price=row.price,
            )
            or row.source_line,
            candidates=(
                _extract_price_fragment(
                    source_line=row.source_line,
                    price=row.price,
                ),
            ),
        ),
        "restriction_text": _extract_raw_fragment(
            source_line=row.source_line,
            candidates=(row.restriction_text,),
        ),
    }
    for field_name, raw_fragment in fragments.items():
        if raw_fragment:
            field_sources[field_name] = {"raw_fragment": raw_fragment}
    if row.inherited_fields and row.scope_header_text:
        field_sources["scope_evidence"] = {
            "header_text": row.scope_header_text,
            "header_line_index": row.scope_header_line_index,
            "inherited_fields": list(row.inherited_fields),
        }
    return field_sources


def _quote_row_normalized_sku_key(row: ParsedQuoteRow) -> str:
    return "|".join(
        (
            normalize_quote_card_type(row.card_type),
            normalize_quote_country_or_currency(row.country_or_currency),
            normalize_quote_amount_range(row.amount_range or "不限"),
            normalize_quote_multiplier(row.multiplier or ""),
            normalize_quote_form_factor(row.form_factor or "不限"),
        )
    )


def _parsed_quote_row_to_candidate_row(
    row: ParsedQuoteRow,
    *,
    row_ordinal: int,
) -> QuoteCandidateRow:
    normalized_card_type = normalize_quote_card_type(row.card_type)
    normalized_country_or_currency = normalize_quote_country_or_currency(
        row.country_or_currency
    )
    normalized_amount_range = normalize_quote_amount_range(row.amount_range or "不限")
    normalized_multiplier = normalize_quote_multiplier(row.multiplier or "")
    normalized_form_factor = normalize_quote_form_factor(row.form_factor or "不限")
    normalization_status = "normalized"
    if not normalized_card_type or not normalized_country_or_currency:
        normalization_status = "partial"

    return QuoteCandidateRow(
        row_ordinal=row_ordinal,
        source_line=row.source_line,
        source_line_index=_quote_source_line_index(
            raw_text=row.raw_text,
            source_line=row.source_line,
        ),
        line_confidence=row.confidence,
        normalized_sku_key=_quote_row_normalized_sku_key(row),
        normalization_status=normalization_status,
        row_publishable=_quote_row_publishable(row),
        publishability_basis="parser_prevalidation",
        restriction_parse_status="parsed" if row.restriction_text else "empty",
        card_type=normalized_card_type or row.card_type,
        country_or_currency=normalized_country_or_currency or row.country_or_currency,
        amount_range=normalized_amount_range,
        multiplier=normalized_multiplier or None,
        form_factor=normalized_form_factor,
        price=row.price,
        quote_status=row.quote_status,
        restriction_text=row.restriction_text,
        field_sources=_quote_row_field_sources(row),
        rejection_reasons=_quote_row_rejection_reasons(row),
        parser_template=row.parser_template,
        parser_version=row.parser_version,
    )


def _parsed_quote_exception_to_rejection_reason(
    item: ParsedQuoteException,
) -> dict[str, Any]:
    return {
        "reason": item.reason,
        "source_line": item.source_line,
        "parser_template": item.parser_template,
        "parser_version": item.parser_version,
        "confidence": item.confidence,
    }


def _missing_template_candidate(
    *,
    envelope: NormalizedMessageEnvelope,
    raw_text: str,
    group_profile: QuoteGroupProfile,
    message_time: str,
    run_kind: str,
    replay_of_quote_document_id: int | None,
    message_id_override: str | None,
) -> QuoteCandidateMessage:
    parser_template = str(getattr(group_profile, "parser_template", "") or "group-parser")
    message_id = str(message_id_override or envelope.message_id)
    first_line = raw_text.splitlines()[0].strip() if raw_text.splitlines() else raw_text
    (
        snapshot_hypothesis,
        snapshot_hypothesis_reason,
        snapshot_hypothesis_evidence,
    ) = _build_snapshot_hypothesis(
        raw_message=raw_text,
        parser_template=parser_template,
    )
    return QuoteCandidateMessage(
        platform=envelope.platform,
        source_group_key=f"{envelope.platform}:{envelope.chat_id}",
        chat_id=envelope.chat_id,
        chat_name=envelope.chat_name,
        message_id=message_id,
        source_name=envelope.sender_name,
        sender_id=envelope.sender_id,
        sender_display=envelope.sender_name,
        raw_message=raw_text,
        message_time=message_time,
        parser_kind=parser_template,
        parser_template=parser_template,
        parser_version=PARSER_VERSION,
        confidence=0.0,
        parse_status="empty",
        message_fingerprint=_quote_message_fingerprint(
            platform=envelope.platform,
            chat_id=envelope.chat_id,
            message_id=message_id,
            sender_id=envelope.sender_id,
            raw_text=raw_text,
        ),
        snapshot_hypothesis=snapshot_hypothesis,
        snapshot_hypothesis_reason=snapshot_hypothesis_reason,
        snapshot_hypothesis_evidence=snapshot_hypothesis_evidence,
        rejection_reasons=[
            {
                "reason": "missing_group_template",
                "source_line": first_line,
                "parser_template": parser_template,
                "parser_version": PARSER_VERSION,
            }
        ],
        run_kind=run_kind,
        replay_of_quote_document_id=replay_of_quote_document_id,
        rows=[],
    )


def _parsed_quote_document_to_candidate(
    parsed: ParsedQuoteDocument,
    *,
    run_kind: str,
    replay_of_quote_document_id: int | None,
    message_id_override: str | None,
) -> QuoteCandidateMessage:
    message_id = str(message_id_override or parsed.message_id)
    (
        snapshot_hypothesis,
        snapshot_hypothesis_reason,
        snapshot_hypothesis_evidence,
    ) = _build_snapshot_hypothesis(
        raw_message=parsed.raw_text,
        parser_template=parsed.parser_template,
    )
    return QuoteCandidateMessage(
        platform=parsed.platform,
        source_group_key=parsed.source_group_key,
        chat_id=parsed.chat_id,
        chat_name=parsed.chat_name,
        message_id=message_id,
        source_name=parsed.source_name,
        sender_id=parsed.sender_id,
        sender_display=parsed.source_name,
        raw_message=parsed.raw_text,
        message_time=parsed.message_time,
        parser_kind=parsed.parser_template,
        parser_template=parsed.parser_template,
        parser_version=parsed.parser_version,
        confidence=parsed.confidence,
        parse_status=parsed.parse_status,
        message_fingerprint=_quote_message_fingerprint(
            platform=parsed.platform,
            chat_id=parsed.chat_id,
            message_id=message_id,
            sender_id=parsed.sender_id,
            raw_text=parsed.raw_text,
        ),
        snapshot_hypothesis=snapshot_hypothesis,
        snapshot_hypothesis_reason=snapshot_hypothesis_reason,
        snapshot_hypothesis_evidence=snapshot_hypothesis_evidence,
        rejection_reasons=[
            _parsed_quote_exception_to_rejection_reason(item)
            for item in parsed.exceptions
        ],
        run_kind=run_kind,
        replay_of_quote_document_id=replay_of_quote_document_id,
        rows=[
            _parsed_quote_row_to_candidate_row(item, row_ordinal=index)
            for index, item in enumerate(parsed.rows, start=1)
        ],
    )


def _parse_quote_message_to_candidate_details(
    *,
    envelope: NormalizedMessageEnvelope,
    raw_text: str,
    group_profile: QuoteGroupProfile,
    message_time: str,
    template: Any | None = None,
    run_kind: str = "runtime",
    replay_of_quote_document_id: int | None = None,
    message_id_override: str | None = None,
) -> tuple[QuoteCandidateMessage, list[ParsedQuoteException], list[ParsedQuoteRow]]:
    from .template_engine import TemplateConfig, parse_message_with_template

    template_config_raw = str(getattr(group_profile, "template_config", "") or "").strip()
    if not template_config_raw:
        return (
            _missing_template_candidate(
                envelope=envelope,
                raw_text=raw_text,
                group_profile=group_profile,
                message_time=message_time,
                run_kind=run_kind,
                replay_of_quote_document_id=replay_of_quote_document_id,
                message_id_override=message_id_override,
            ),
            [],
            [],
        )

    tpl = template if template is not None else TemplateConfig.from_json(template_config_raw)
    parsed = parse_message_with_template(
        text=raw_text,
        template=tpl,
        platform=envelope.platform,
        chat_id=envelope.chat_id,
        chat_name=envelope.chat_name,
        message_id=str(message_id_override or envelope.message_id),
        source_name=envelope.sender_name,
        sender_id=envelope.sender_id,
        source_group_key=f"{envelope.platform}:{envelope.chat_id}",
        message_time=message_time,
    )
    return (
        _parsed_quote_document_to_candidate(
            parsed,
            run_kind=run_kind,
            replay_of_quote_document_id=replay_of_quote_document_id,
            message_id_override=message_id_override,
        ),
        list(parsed.exceptions),
        [item for item in parsed.rows if not _quote_row_publishable(item)],
    )


def parse_quote_message_to_candidate(
    *,
    envelope: NormalizedMessageEnvelope,
    raw_text: str,
    group_profile: QuoteGroupProfile,
    message_time: str,
    run_kind: str = "runtime",
    replay_of_quote_document_id: int | None = None,
    message_id_override: str | None = None,
) -> QuoteCandidateMessage:
    candidate, _parsed_exceptions, _non_publishable_rows = (
        _parse_quote_message_to_candidate_details(
            envelope=envelope,
            raw_text=raw_text,
            group_profile=group_profile,
            message_time=message_time,
            run_kind=run_kind,
            replay_of_quote_document_id=replay_of_quote_document_id,
            message_id_override=message_id_override,
        )
    )
    return candidate


def _build_inquiry_reply_candidate(
    *,
    envelope: NormalizedMessageEnvelope,
    raw_text: str,
    message_time: str,
    context: dict[str, Any],
) -> QuoteCandidateMessage:
    price = _extract_standalone_reply_price(raw_text)
    if price is None:
        raise ValueError("inquiry reply candidate requires a parsable price")
    (
        snapshot_hypothesis,
        snapshot_hypothesis_reason,
        snapshot_hypothesis_evidence,
    ) = _build_snapshot_hypothesis(
        raw_message=raw_text,
        parser_template="inquiry_context_reply",
    )
    parsed_row = ParsedQuoteRow(
        source_group_key=str(context["source_group_key"]),
        platform=envelope.platform,
        chat_id=envelope.chat_id,
        chat_name=envelope.chat_name,
        message_id=envelope.message_id,
        source_name=envelope.sender_name,
        sender_id=envelope.sender_id,
        card_type=str(context["card_type"]),
        country_or_currency=str(context["country_or_currency"]),
        amount_range=normalize_quote_amount_range(str(context["amount_range"])),
        multiplier=str(context["multiplier"]) if context.get("multiplier") else None,
        form_factor=normalize_quote_form_factor(str(context["form_factor"] or "不限")),
        price=price,
        quote_status="active",
        restriction_text="询价上下文回复",
        source_line=raw_text,
        raw_text=raw_text,
        message_time=message_time,
        effective_at=message_time,
        expires_at=None,
        parser_template="inquiry_context_reply",
        parser_version=PARSER_VERSION,
        confidence=0.98,
    )
    return QuoteCandidateMessage(
        platform=envelope.platform,
        source_group_key=str(context["source_group_key"]),
        chat_id=envelope.chat_id,
        chat_name=envelope.chat_name,
        message_id=envelope.message_id,
        source_name=envelope.sender_name,
        sender_id=envelope.sender_id,
        sender_display=envelope.sender_name,
        raw_message=raw_text,
        message_time=message_time,
        parser_kind="inquiry_context_reply",
        parser_template="inquiry_context_reply",
        parser_version=PARSER_VERSION,
        confidence=parsed_row.confidence,
        parse_status="parsed",
        message_fingerprint=_quote_message_fingerprint(
            platform=envelope.platform,
            chat_id=envelope.chat_id,
            message_id=envelope.message_id,
            sender_id=envelope.sender_id,
            raw_text=raw_text,
        ),
        snapshot_hypothesis=snapshot_hypothesis,
        snapshot_hypothesis_reason=snapshot_hypothesis_reason,
        snapshot_hypothesis_evidence=snapshot_hypothesis_evidence,
        rejection_reasons=[],
        run_kind="runtime",
        replay_of_quote_document_id=None,
        rows=[_parsed_quote_row_to_candidate_row(parsed_row, row_ordinal=1)],
    )


class QuoteCaptureService:
    def __init__(self, db, *, wall_runtime_mode: str | None = None) -> None:
        self.db = db
        self.wall_runtime_mode = get_quote_wall_runtime_mode(wall_runtime_mode)
        from .quote_publisher import QuoteFactPublisher

        self.publisher = QuoteFactPublisher(db)

    def capture_from_message(
        self,
        envelope: NormalizedMessageEnvelope,
        *,
        raw_text: str | None = None,
    ) -> dict[str, Any]:
        text = str(raw_text if raw_text is not None else envelope.text or "").strip()
        if not text or not envelope.is_group or envelope.content_type != "text":
            return {"captured": False, "rows": 0, "exceptions": 0}
        # 只采集客人组（5/6/7/8）的报价异常与候选
        group_key = f"{envelope.platform}:{envelope.chat_id}"
        group_num = self.db.get_group_num(group_key)
        if group_num is None or group_num not in (5, 6, 7, 8):
            return {"captured": False, "rows": 0, "exceptions": 0}
        group_profile = self._group_profile_for_envelope(envelope, text)
        inquiry_reply = self._capture_inquiry_reply(envelope, text=text)
        if inquiry_reply.get("captured"):
            return inquiry_reply
        message_time = _normalize_message_time(envelope.received_at)

        template_config_raw = str(getattr(group_profile, "template_config", "") or "").strip()
        if not template_config_raw:
            if not looks_like_quote_message(
                text,
                dictionary_aliases=group_profile.dictionary_aliases,
            ):
                return {"captured": False, "rows": 0, "exceptions": 0}
            if self.db.is_quote_exception_suppressed(
                source_group_key=f"{envelope.platform}:{envelope.chat_id}",
                reason="missing_group_template",
                source_line=text.splitlines()[0].strip() if text.splitlines() else text,
                raw_text=text,
            ):
                return {"captured": False, "rows": 0, "exceptions": 0}
            candidate = parse_quote_message_to_candidate(
                envelope=envelope,
                raw_text=text,
                group_profile=group_profile,
                message_time=message_time,
            )
            document_id, validation_run_id = self._record_candidate_with_validation(
                candidate
            )
            publish_result = self._publish_validation_owned_rows(
                candidate=candidate,
                document_id=document_id,
                validation_run_id=validation_run_id,
            )
            recorded_exception_id = self._record_exception_with_repair_case(
                quote_document_id=document_id,
                platform=envelope.platform,
                source_group_key=f"{envelope.platform}:{envelope.chat_id}",
                chat_id=envelope.chat_id,
                chat_name=envelope.chat_name,
                source_name=envelope.sender_name,
                sender_id=envelope.sender_id,
                reason="missing_group_template",
                source_line=text.splitlines()[0].strip() if text.splitlines() else text,
                raw_text=text,
                message_time=message_time,
                parser_template=str(getattr(group_profile, "parser_template", "") or "group-parser"),
                parser_version=PARSER_VERSION,
                confidence=0.0,
            )
            if not recorded_exception_id:
                return {"captured": False, "rows": 0, "exceptions": 0}
            return {
                "captured": True,
                "document_id": document_id,
                "validation_run_id": validation_run_id,
                "publish_result": publish_result,
                "rows": len(candidate.rows),
                "exceptions": 1,
                "template": candidate.parser_template,
                "parse_status": candidate.parse_status,
            }
        try:
            from .template_engine import TemplateConfig

            tpl = TemplateConfig.from_json(template_config_raw)
        except ValueError:
            return {"captured": False, "rows": 0, "exceptions": 0}
        if not should_attempt_template_quote_capture(
            text,
            template=tpl,
            dictionary_aliases=group_profile.dictionary_aliases,
        ):
            return {"captured": False, "rows": 0, "exceptions": 0}
        candidate, parsed_exceptions, non_publishable_rows = (
            _parse_quote_message_to_candidate_details(
                envelope=envelope,
                raw_text=text,
                group_profile=group_profile,
                message_time=message_time,
                template=tpl,
            )
        )
        if not candidate.rows and not parsed_exceptions:
            return {"captured": False, "rows": 0, "exceptions": 0}
        recordable_parsed_exceptions = [
            item
            for item in parsed_exceptions
            if not self.db.is_quote_exception_suppressed(
                source_group_key=item.source_group_key,
                reason=item.reason,
                source_line=item.source_line,
                raw_text=item.raw_text,
            )
        ]
        recordable_row_exceptions = [
            item
            for item in non_publishable_rows
            if not self.db.is_quote_exception_suppressed(
                source_group_key=item.source_group_key,
                reason="low_confidence_or_non_active",
                source_line=item.source_line,
                raw_text=item.raw_text,
            )
        ]
        if not candidate.rows and not recordable_parsed_exceptions and not recordable_row_exceptions:
            return {"captured": False, "rows": 0, "exceptions": 0}

        document_id, validation_run_id = self._record_candidate_with_validation(candidate)
        publish_result = self._publish_validation_owned_rows(
            candidate=candidate,
            document_id=document_id,
            validation_run_id=validation_run_id,
        )
        recorded_exceptions = 0
        for item in recordable_parsed_exceptions:
            if self._record_exception_with_repair_case(
                quote_document_id=document_id,
                platform=item.platform,
                source_group_key=item.source_group_key,
                chat_id=item.chat_id,
                chat_name=item.chat_name,
                source_name=item.source_name,
                sender_id=item.sender_id,
                reason=item.reason,
                source_line=item.source_line,
                raw_text=item.raw_text,
                message_time=item.message_time,
                parser_template=item.parser_template,
                parser_version=item.parser_version,
                confidence=item.confidence,
            ):
                recorded_exceptions += 1
        for item in recordable_row_exceptions:
            if self._record_exception_with_repair_case(
                quote_document_id=document_id,
                platform=item.platform,
                source_group_key=item.source_group_key,
                chat_id=item.chat_id,
                chat_name=item.chat_name,
                source_name=item.source_name,
                sender_id=item.sender_id,
                reason="low_confidence_or_non_active",
                source_line=item.source_line,
                raw_text=item.raw_text,
                message_time=item.message_time,
                parser_template=item.parser_template,
                parser_version=item.parser_version,
                confidence=item.confidence,
            ):
                recorded_exceptions += 1
        if recorded_exceptions == 0:
            validator_exception_id = self._record_validator_outcome_repair_case(
                candidate=candidate,
                document_id=document_id,
                validation_run_id=validation_run_id,
                envelope=envelope,
                raw_text=text,
                message_time=message_time,
            )
            if validator_exception_id:
                recorded_exceptions += 1
        return {
            "captured": True,
            "document_id": document_id,
            "validation_run_id": validation_run_id,
            "publish_result": publish_result,
            "rows": len(candidate.rows),
            "exceptions": recorded_exceptions,
            "template": candidate.parser_template,
            "parse_status": candidate.parse_status,
        }

    def _group_profile_for_envelope(
        self,
        envelope: NormalizedMessageEnvelope,
        text: str,
    ) -> QuoteGroupProfile:
        dictionary_aliases: dict[str, tuple[tuple[str, str], ...]] | None = None
        alias_method = getattr(self.db, "list_quote_dictionary_aliases_for_scope", None)
        if callable(alias_method):
            dictionary_aliases = quote_dictionary_aliases_from_rows(
                alias_method(platform=envelope.platform, chat_id=envelope.chat_id)
            )
        # 优先使用当前 chat_id 对应且 chat_name 一致的记录，避免同名历史群把新骨架抢走。
        method = getattr(self.db, "get_quote_group_profile", None)
        if callable(method):
            row = method(platform=envelope.platform, chat_id=envelope.chat_id)
            if row and str(row.get("chat_name") or "") == envelope.chat_name:
                return QuoteGroupProfile(
                    key=f"{envelope.platform}:{envelope.chat_id}",
                    default_card_type=str(row.get("default_card_type") or "") or None,
                    default_country_or_currency=str(row.get("default_country_or_currency") or "")
                    or None,
                    default_form_factor=str(row.get("default_form_factor") or "") or None,
                    default_multiplier=str(row.get("default_multiplier") or "") or None,
                    parser_template=str(row.get("parser_template") or "") or None,
                    stale_after_minutes=int(row.get("stale_after_minutes") or DEFAULT_STALE_AFTER_MINUTES),
                    note=str(row.get("note") or ""),
                    template_config=sanitize_quote_group_template_config(
                        parser_template=str(row.get("parser_template") or "") or None,
                        template_config_raw=str(row.get("template_config") or ""),
                        default_country_or_currency=str(row.get("default_country_or_currency") or "") or None,
                        default_form_factor=str(row.get("default_form_factor") or "") or None,
                    ),
                    dictionary_aliases=dictionary_aliases,
                )
        # 当前 chat_id 没有同名记录时，再回退到按 chat_name 取最新 profile。
        method_by_name = getattr(self.db, "get_quote_group_profile_by_name", None)
        if callable(method_by_name):
            row = method_by_name(platform=envelope.platform, chat_name=envelope.chat_name)
            if row:
                return QuoteGroupProfile(
                    key=f"{envelope.platform}:{envelope.chat_id}",
                    default_card_type=str(row.get("default_card_type") or "") or None,
                    default_country_or_currency=str(row.get("default_country_or_currency") or "")
                    or None,
                    default_form_factor=str(row.get("default_form_factor") or "") or None,
                    default_multiplier=str(row.get("default_multiplier") or "") or None,
                    parser_template=str(row.get("parser_template") or "") or None,
                    stale_after_minutes=int(row.get("stale_after_minutes") or DEFAULT_STALE_AFTER_MINUTES),
                    note=str(row.get("note") or ""),
                    template_config=sanitize_quote_group_template_config(
                        parser_template=str(row.get("parser_template") or "") or None,
                        template_config_raw=str(row.get("template_config") or ""),
                        default_country_or_currency=str(row.get("default_country_or_currency") or "") or None,
                        default_form_factor=str(row.get("default_form_factor") or "") or None,
                    ),
                    dictionary_aliases=dictionary_aliases,
                )
        profile = resolve_quote_group_profile(
            source_group_key=f"{envelope.platform}:{envelope.chat_id}",
            chat_name=envelope.chat_name,
            raw_text=text,
        )
        return replace(profile, dictionary_aliases=dictionary_aliases)

    def _capture_inquiry_reply(
        self,
        envelope: NormalizedMessageEnvelope,
        *,
        text: str,
    ) -> dict[str, Any]:
        method = getattr(self.db, "find_open_quote_inquiry_context", None)
        if not callable(method):
            return {"captured": False, "rows": 0, "exceptions": 0}
        context = method(platform=envelope.platform, chat_id=envelope.chat_id)
        if not context:
            return {"captured": False, "rows": 0, "exceptions": 0}
        price = _extract_standalone_reply_price(text)
        if price is None:
            return {"captured": False, "rows": 0, "exceptions": 0}

        message_time = _normalize_message_time(envelope.received_at)
        raw_text = text
        candidate = _build_inquiry_reply_candidate(
            envelope=envelope,
            raw_text=raw_text,
            message_time=message_time,
            context=context,
        )
        document_id, validation_run_id = self._record_candidate_with_validation(candidate)
        publish_result = self._publish_validation_owned_rows(
            candidate=candidate,
            document_id=document_id,
            validation_run_id=validation_run_id,
        )
        resolve_method = getattr(self.db, "resolve_quote_inquiry_context", None)
        if callable(resolve_method):
            resolve_method(
                inquiry_id=int(context["id"]),
                resolved_message_id=envelope.message_id,
            )
        return {
            "captured": True,
            "document_id": document_id,
            "validation_run_id": validation_run_id,
            "publish_result": publish_result,
            "rows": len(candidate.rows),
            "exceptions": 0,
            "template": candidate.parser_template,
            "parse_status": candidate.parse_status,
        }

    def _record_candidate_with_validation(
        self, candidate: QuoteCandidateMessage
    ) -> tuple[int, int]:
        document_id = self.db.record_quote_candidate_bundle(candidate=candidate)
        validation_run = validate_quote_candidate_document(
            quote_document_id=document_id,
            run_kind=candidate.run_kind,
            candidate_document=candidate,
            candidate_rows=self.db.list_quote_candidate_rows(
                quote_document_id=document_id
            ),
        )
        validation_run_id = self.db.record_quote_validation_run(
            validation_run=validation_run
        )
        return document_id, validation_run_id

    def _publish_validation_owned_rows(
        self,
        *,
        candidate: QuoteCandidateMessage,
        document_id: int,
        validation_run_id: int,
    ) -> dict[str, Any]:
        snapshot_decision = self.db.get_quote_snapshot_decision(
            quote_document_id=document_id
        ) or {}
        proposed_publish_mode = get_guarded_publish_mode(snapshot_decision)
        runtime_wall = describe_quote_wall_runtime_mode(self.wall_runtime_mode)
        runtime_publish_mode = self.publisher.VALIDATION_ONLY_MODE
        if runtime_wall["real_wall_updates_enabled"]:
            runtime_publish_mode = proposed_publish_mode
        publish_result = self.publisher.publish_quote_document(
            quote_document_id=document_id,
            validation_run_id=validation_run_id,
            source_group_key=candidate.source_group_key,
            platform=candidate.platform,
            chat_id=candidate.chat_id,
            chat_name=candidate.chat_name,
            message_id=candidate.message_id,
            source_name=candidate.source_name,
            sender_id=candidate.sender_id,
            raw_text=candidate.raw_message,
            message_time=candidate.message_time,
            parser_template=candidate.parser_template,
            parser_version=candidate.parser_version,
            publish_mode=runtime_publish_mode,
        )
        return {
            "status": publish_result.status,
            "quote_document_id": publish_result.quote_document_id,
            "validation_run_id": publish_result.validation_run_id,
            "source_group_key": publish_result.source_group_key,
            "publish_mode": publish_result.publish_mode,
            "proposed_publish_mode": proposed_publish_mode,
            "attempted_row_count": publish_result.attempted_row_count,
            "applied_row_count": publish_result.applied_row_count,
            "reason": publish_result.reason,
            "experimental_wall": runtime_wall,
            "snapshot_hypothesis": str(
                snapshot_decision.get("system_hypothesis")
                or candidate.snapshot_hypothesis
                or "unresolved"
            ),
            "resolved_snapshot_decision": get_effective_snapshot_decision(
                snapshot_decision
            ),
            "snapshot_decision_source": str(
                snapshot_decision.get("decision_source") or "system"
            ),
        }

    def _record_exception_with_repair_case(
        self,
        *,
        quote_document_id: int,
        platform: str,
        source_group_key: str,
        chat_id: str,
        chat_name: str,
        source_name: str,
        sender_id: str,
        reason: str,
        source_line: str,
        raw_text: str,
        message_time: str,
        parser_template: str,
        parser_version: str,
        confidence: float,
    ) -> int:
        exception_id = self.db.record_quote_exception_unless_suppressed(
            quote_document_id=quote_document_id,
            platform=platform,
            source_group_key=source_group_key,
            chat_id=chat_id,
            chat_name=chat_name,
            source_name=source_name,
            sender_id=sender_id,
            reason=reason,
            source_line=source_line,
            raw_text=raw_text,
            message_time=message_time,
            parser_template=parser_template,
            parser_version=parser_version,
            confidence=confidence,
        )
        if exception_id:
            repair_case = package_quote_repair_case(db=self.db, exception_id=exception_id)
            try:
                from bookkeeping_core.remediation import bootstrap_quote_repair_workflow

                bootstrap_quote_repair_workflow(
                    db=self.db,
                    repair_case_id=int(repair_case["id"]),
                )
            except ValueError:
                pass
        return int(exception_id or 0)

    def _record_validator_outcome_repair_case(
        self,
        *,
        candidate: QuoteCandidateMessage,
        document_id: int,
        validation_run_id: int,
        envelope: NormalizedMessageEnvelope,
        raw_text: str,
        message_time: str,
    ) -> int:
        validation_run = self.db.get_latest_quote_validation_run(
            quote_document_id=document_id
        )
        if validation_run is None:
            return 0
        if int(validation_run["id"]) != int(validation_run_id):
            return 0
        message_decision = str(validation_run["message_decision"] or "")
        if message_decision not in {"no_publish", "mixed_outcome"}:
            return 0
        reason = (
            "validator_mixed_outcome"
            if message_decision == "mixed_outcome"
            else "validator_no_publish"
        )
        return self._record_exception_with_repair_case(
            quote_document_id=document_id,
            platform=envelope.platform,
            source_group_key=f"{envelope.platform}:{envelope.chat_id}",
            chat_id=envelope.chat_id,
            chat_name=envelope.chat_name,
            source_name=envelope.sender_name,
            sender_id=envelope.sender_id,
            reason=reason,
            source_line=self._validator_failure_source_line(
                candidate=candidate,
                document_id=document_id,
                validation_run_id=validation_run_id,
                message_decision=message_decision,
                raw_text=raw_text,
            ),
            raw_text=raw_text,
            message_time=message_time,
            parser_template=str(candidate.parser_template or ""),
            parser_version=str(candidate.parser_version or ""),
            confidence=float(candidate.confidence or 0.0),
        )

    def _validator_failure_source_line(
        self,
        *,
        candidate: QuoteCandidateMessage,
        document_id: int,
        validation_run_id: int,
        message_decision: str,
        raw_text: str,
    ) -> str:
        if str(message_decision or "") == "mixed_outcome":
            candidate_rows = {
                int(row["id"]): row
                for row in self.db.list_quote_candidate_rows(
                    quote_document_id=document_id
                )
            }
            failing_lines: list[str] = []
            for row in self.db.list_quote_validation_row_results(
                validation_run_id=validation_run_id
            ):
                if str(row.get("final_decision") or "") == "publishable":
                    continue
                candidate_row = candidate_rows.get(int(row["quote_candidate_row_id"]))
                if candidate_row is None:
                    continue
                source_line = str(candidate_row.get("source_line") or "").strip()
                if source_line and source_line not in failing_lines:
                    failing_lines.append(source_line)
                if len(failing_lines) >= 3:
                    break
            if failing_lines:
                return "\n".join(failing_lines)
        for row in candidate.rows:
            source_line = str(getattr(row, "source_line", "") or "").strip()
            if source_line:
                return source_line
        for line in str(raw_text or "").splitlines():
            cleaned = line.strip()
            if cleaned:
                return cleaned
        return str(raw_text or "").strip()


def _extract_standalone_reply_price(text: str) -> float | None:
    """从简短回复中提取价格数字（用于询价上下文回复）。"""
    cleaned = re.sub(r"\s+", " ", text.strip())
    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
    candidates = lines or [cleaned]
    if len(candidates) > 2:
        return None
    for candidate in reversed(candidates):
        if re.fullmatch(r"\d+(?:\.\d+)?", candidate):
            return float(candidate)
        # 尝试从 "xxx=5.35" 或 "5.35 xxx" 中提取价格
        match = re.search(r"[:：=]\s*(\d+(?:\.\d+)?)\s*$", candidate)
        if match:
            return float(match.group(1))
        match = re.search(r"(\d+(?:\.\d+)?)\s*$", candidate)
        if match:
            left = candidate[:match.start()].strip()
            # 左边如果有卡种或国家信息，不作为独立价格
            if not _infer_card_type(left) and not _infer_country_or_currency(left):
                return float(match.group(1))
    return None


def _extract_fixed_sheet_amount_price(line: str) -> tuple[str | None, float | None, str]:
    normalized_line = str(line or "").strip()
    working = normalized_line
    if "：" in working:
        working = working.split("：", 1)[1].strip()
    elif ":" in working:
        working = working.split(":", 1)[1].strip()
    # Remove explicit multiplier markers first, so lines like
    # "100-500 100倍数 5.47" won't parse the multiplier number as price.
    working_without_multiplier = re.sub(
        r"\d+(?:\.\d+)?\s*(?:X|x|倍数|倍)",
        " ",
        working,
    )

    for pattern in (
        re.compile(
            r"(?P<amount>\d+(?:\s*[/-]\s*\d+)*)\s*[:：=]\s*(?P<price>\d+(?:\.\d+)?)\s*(?P<tail>.*)$"
        ),
        re.compile(
            r"(?P<amount>\d+(?:\s*[/-]\s*\d+)*(?:\s+\d+)?)\s+(?P<price>\d+(?:\.\d+)?)\s*(?P<tail>.*)$"
        ),
    ):
        match = pattern.search(working_without_multiplier)
        if match is None:
            continue
        amount_value = _normalize_fixed_sheet_amount(str(match.group("amount") or ""))
        right_text = str(match.group("tail") or "").strip()
        return amount_value or "不限", float(match.group("price")), right_text
    return None, None, ""


def _normalize_fixed_sheet_amount(raw_amount: str) -> str:
    text = re.sub(r"\s+", " ", str(raw_amount or "").strip())
    text = text.replace("／", "/").replace("－", "-").replace("—", "-")
    spaced_range = re.fullmatch(r"(\d+)\s+(\d+)", text)
    if spaced_range:
        return normalize_quote_amount_range(f"{spaced_range.group(1)}-{spaced_range.group(2)}")
    if "/" in text:
        parts = [item.strip() for item in text.split("/") if item.strip()]
        return normalize_quote_amount_range("-".join(parts))
    return normalize_quote_amount_range(text.replace(" ", ""))


def _looks_like_fixed_sheet_footer(text: str) -> bool:
    normalized = _normalize_key(text)
    if not normalized:
        return True
    return normalized in {"tw;a", "tw;a;", "a", "tw"} or normalized.startswith("tw;a")


def _looks_like_fixed_sheet_header(text: str) -> bool:
    normalized = _normalize_key(text)
    if not normalized:
        return True
    if any(marker in text for marker in ("【", "】", "价格表", "报价单", "行情")):
        return True
    return bool(_infer_card_type(text) or _infer_country_or_currency(text))


def _split_segments(line: str) -> list[str]:
    chunks: list[str] = []
    for part in re.split(r"[；;]", line):
        part = part.strip()
        if not part:
            continue
        if "（" in part or "(" in part:
            pieces = re.split(r"[（(]", part)
            for piece_index, piece in enumerate(pieces):
                piece = piece.strip("）) 、,，")
                if not piece:
                    continue
                if piece_index > 0 and not _contains_price(piece) and chunks:
                    chunks[-1] = f"{chunks[-1]} {piece}".strip()
                    continue
                chunks.extend(_split_repeated_price_pairs(piece))
        else:
            chunks.extend(_split_repeated_price_pairs(part))
    return chunks


def _split_repeated_price_pairs(text: str) -> list[str]:
    cleaned = str(text or "").strip()
    if not cleaned:
        return []
    split_pattern = _country_pair_split_pattern()
    pieces = [piece.strip() for piece in split_pattern.split(cleaned) if piece.strip()]
    return pieces or [cleaned]


def _country_pair_split_pattern() -> re.Pattern[str]:
    aliases = sorted(
        {alias for alias, _canonical in _COUNTRY_ALIASES},
        key=len,
        reverse=True,
    )
    alias_pattern = "|".join(_spaced_alias_pattern(alias) for alias in aliases)
    return re.compile(
        rf"(?<=\d)\s{{2,}}(?=(?:{alias_pattern})\s*(?:美元|欧元|英镑|澳元|加元|新币)?\s*[:：=])",
        re.IGNORECASE,
    )


def _spaced_alias_pattern(alias: str) -> str:
    escaped_parts = [re.escape(char) for char in alias if char.strip()]
    if not escaped_parts:
        return re.escape(alias)
    if all("\u4e00" <= char <= "\u9fff" for char in alias):
        return r"\s*".join(escaped_parts)
    return re.escape(alias)


def _extract_price(segment: str) -> tuple[float | None, str, str]:
    stripped = segment.strip()
    if re.fullmatch(r"\d+(?:\.\d+)?", stripped):
        return float(stripped), "", ""

    price_match = _PRICE_TOKEN_RE.search(segment)
    if price_match is not None:
        price = float(price_match.group("price"))
        left = segment[: price_match.start()].strip()
        right = segment[price_match.end() :].strip("）) ")
        return price, left, right

    separator_matches = list(re.finditer(r"[:：=]\s*(?P<price>\d+(?:\.\d+)?)", segment))
    if separator_matches:
        separator_match = separator_matches[-1]
        price = float(separator_match.group("price"))
        left = segment[: separator_match.start()].strip(" ：:=()（）")
        right = segment[separator_match.end() :].strip("）) ")
        return price, left, right

    separator_match = None
    for pattern in (
        re.compile(r"[:：=]\s*(?P<price>\d+(?:\.\d+)?)(?!.*\d)"),
        re.compile(r"(?P<left>.+?)(?P<price>\d+(?:\.\d+)?)\s*$"),
    ):
        separator_match = pattern.search(segment)
        if separator_match is not None:
            break
    if separator_match is None:
        return None, "", ""
    price = float(separator_match.group("price"))
    if "left" in separator_match.groupdict():
        left = separator_match.group("left").strip()
        right = ""
    else:
        split_at = segment.rfind(separator_match.group("price"))
        left = segment[:split_at].strip(" ：:=()（）")
        right = segment[split_at + len(separator_match.group("price")) :].strip("）) ")
    return price, left, right


def _contains_price(segment: str) -> bool:
    return bool(
        _PRICE_TOKEN_RE.search(segment)
        or re.search(r"[:：=]\s*\d+(?:\.\d+)?", segment)
        or re.search(r"\b\d+(?:\.\d+)?\s*$", segment)
    )


def resolve_quote_group_profile(
    *,
    source_group_key: str,
    chat_name: str,
    raw_text: str = "",
) -> QuoteGroupProfile:
    lookup_text = "\n".join((source_group_key, chat_name, raw_text))
    for marker, profile in _QUOTE_GROUP_PROFILES:
        if marker and marker in lookup_text:
            return profile
    card_type = _infer_card_type(chat_name)
    if card_type == "Apple":
        return QuoteGroupProfile(
            key="apple_default",
            default_card_type="Apple",
            parser_template=None,
            stale_after_minutes=APPLE_STALE_AFTER_MINUTES,
            note="Apple 默认 30 分钟超时",
        )
    return QuoteGroupProfile(key="default", stale_after_minutes=DEFAULT_STALE_AFTER_MINUTES)


def _infer_dictionary_alias(
    text: str,
    category: str,
    dictionary_aliases: dict[str, tuple[tuple[str, str], ...]] | None = None,
) -> str | None:
    normalized = _normalize_key(text)
    if not normalized:
        return None
    for alias, canonical in (dictionary_aliases or {}).get(category, ()):
        if _normalize_key(alias) and _normalize_key(alias) in normalized:
            return canonical
    return None


def _infer_card_type(
    text: str,
    dictionary_aliases: dict[str, tuple[tuple[str, str], ...]] | None = None,
) -> str | None:
    dictionary_value = _infer_dictionary_alias(text, "card_type", dictionary_aliases)
    if dictionary_value:
        return dictionary_value
    normalized = _normalize_key(text)
    if not normalized:
        return None
    for alias, canonical in _CARD_TYPE_ALIASES:
        if _normalize_key(alias) in normalized:
            return canonical
    return None


def _fallback_card_type(text: str) -> str:
    return "unknown"


def _normalize_card_type_label(text: str) -> str:
    cleaned = re.sub(r"[\[\]【】★=—\-_#]+", " ", str(text or ""))
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if not cleaned:
        return ""
    cleaned = cleaned.replace("的实际报价单", "")
    cleaned = cleaned.replace("价格表", "")
    cleaned = cleaned.replace("报价单", "")
    return cleaned.strip()


def _infer_country_or_currency(
    text: str,
    dictionary_aliases: dict[str, tuple[tuple[str, str], ...]] | None = None,
) -> str | None:
    candidates = _infer_country_or_currency_candidates(text, dictionary_aliases)
    return candidates[0] if candidates else None


def _infer_country_or_currency_candidates(
    text: str,
    dictionary_aliases: dict[str, tuple[tuple[str, str], ...]] | None = None,
) -> list[str]:
    normalized = _normalize_key(text)
    if not normalized:
        return []
    values: list[str] = []
    dictionary_country_aliases = sorted(
        (dictionary_aliases or {}).get("country_currency", ()),
        key=lambda item: len(_normalize_key(item[0])),
        reverse=True,
    )
    for alias, canonical in dictionary_country_aliases:
        if _normalize_key(alias) and _normalize_key(alias) in normalized and canonical not in values:
            values.append(canonical)
    if values:
        return values
    for alias, canonical in sorted(
        _COUNTRY_ALIASES,
        key=lambda item: len(_normalize_key(item[0])),
        reverse=True,
    ):
        if _normalize_key(alias) in normalized and canonical not in values:
            values.append(canonical)
    return values


def _infer_form_factor(
    text: str,
    dictionary_aliases: dict[str, tuple[tuple[str, str], ...]] | None = None,
) -> str | None:
    normalized = _normalize_key(text)
    if not normalized:
        return None
    values: list[str] = []
    dictionary_value = _infer_dictionary_alias(text, "form_factor", dictionary_aliases)
    if dictionary_value:
        values.append(dictionary_value)
    for alias, canonical in _FORM_FACTORS:
        if _normalize_key(alias) in normalized:
            if canonical not in values:
                values.append(canonical)
    if not values:
        return None
    return "/".join(values)


def _normalized_quote_message_lines(text: str) -> list[str]:
    return [line.strip() for line in str(text or "").splitlines() if line.strip()]


def _is_non_quote_operational_message(text: str) -> bool:
    normalized = str(text or "").strip()
    if not normalized:
        return False
    lowered = normalized.lower()
    return any(keyword in normalized or keyword in lowered for keyword in _NON_QUOTE_OPERATIONAL_KEYWORDS)


def _count_structured_quote_lines(
    text: str,
    *,
    dictionary_aliases: dict[str, tuple[tuple[str, str], ...]] | None = None,
) -> int:
    from .template_engine import looks_like_quote_line

    count = 0
    for line in _normalized_quote_message_lines(text):
        if not looks_like_quote_line(line):
            continue
        if _infer_card_type(line, dictionary_aliases) or _infer_country_or_currency(
            line, dictionary_aliases
        ):
            count += 1
            continue
        if re.search(r"(?:^|[:：])\s*\d+(?:\.\d+)?(?:[-/]\d+(?:\.\d+)?)+\s*[:：=]\s*\d+(?:\.\d+)?$", line):
            count += 1
    return count


def _has_quote_context_signal(
    text: str,
    *,
    dictionary_aliases: dict[str, tuple[tuple[str, str], ...]] | None = None,
) -> bool:
    normalized = str(text or "").strip()
    if not normalized:
        return False
    return bool(
        _infer_card_type(normalized, dictionary_aliases)
        or _infer_country_or_currency(normalized, dictionary_aliases)
        or any(marker in normalized for marker in ("【", "】", "价格表", "报价单", "行情", "卡图", "代码", "电子"))
    )


def _template_has_quote_prematch(
    text: str,
    *,
    template: "TemplateConfig",
) -> bool:
    from .template_engine import match_pattern, normalize_quote_text

    lines = [
        normalize_quote_text(line)
        for line in str(text or "").splitlines()
        if normalize_quote_text(line)
    ]
    if template.version in {"group-parser-v1", "strict-section-v1"}:
        for section in template.sections:
            for section_line in section.get("lines", []):
                pattern = str(section_line.get("pattern") or "").strip()
                if not pattern:
                    continue
                kind = str(section_line.get("kind") or "quote").strip()
                for line in lines:
                    if kind in {"literal", "restriction"}:
                        if line == pattern:
                            return True
                    elif kind == "quote" and match_pattern(line, pattern) is not None:
                        return True
        return False
    for rule in template.rules:
        pattern = str(rule.get("pattern") or "").strip()
        if not pattern:
            continue
        for line in lines:
            if match_pattern(line, pattern) is not None:
                return True
    return False


def looks_like_quote_message(
    text: str,
    *,
    dictionary_aliases: dict[str, tuple[tuple[str, str], ...]] | None = None,
) -> bool:
    normalized = str(text or "")
    if not normalized.strip() or _is_non_quote_operational_message(normalized):
        return False
    lines = _normalized_quote_message_lines(normalized)
    quote_line_count = _count_structured_quote_lines(
        normalized,
        dictionary_aliases=dictionary_aliases,
    )
    if quote_line_count >= 2:
        return True
    if quote_line_count >= 1 and _has_quote_context_signal(
        normalized,
        dictionary_aliases=dictionary_aliases,
    ):
        return True
    if any(keyword in normalized for keyword in ("问价", "收卡", "收价", "出价")) and quote_line_count >= 1:
        return True
    return len(lines) >= 3 and quote_line_count >= 1 and _has_quote_context_signal(
        normalized,
        dictionary_aliases=dictionary_aliases,
    )


def should_attempt_template_quote_capture(
    text: str,
    *,
    template: "TemplateConfig",
    dictionary_aliases: dict[str, tuple[tuple[str, str], ...]] | None = None,
) -> bool:
    normalized = str(text or "").strip()
    if not normalized or _is_non_quote_operational_message(normalized):
        return False
    quote_line_count = _count_structured_quote_lines(
        normalized,
        dictionary_aliases=dictionary_aliases,
    )
    if quote_line_count >= 2:
        return True
    if _template_has_quote_prematch(normalized, template=template):
        return True
    return quote_line_count >= 1 and _has_quote_context_signal(
        normalized,
        dictionary_aliases=dictionary_aliases,
    )


def _normalize_message_time(value: str | None) -> str:
    text = str(value or "").strip()
    if text:
        return text
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def _normalize_key(text: str) -> str:
    return re.sub(r"[\s\W_]+", "", str(text or "").lower())
