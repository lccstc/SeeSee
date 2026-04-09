from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
import re
from typing import Any

from .contracts import NormalizedMessageEnvelope


PARSER_VERSION = "quote-v1"
AUTO_PUBLISH_CONFIDENCE = 0.8
DEFAULT_STALE_AFTER_MINUTES = 120
APPLE_STALE_AFTER_MINUTES = 30

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
    ("steam", "Steam"),
    ("razer gold", "Razer"),
    ("razer", "Razer"),
    ("xbox", "Xbox"),
    ("google play", "Google Play"),
    ("google", "Google Play"),
    ("playstation", "PSN"),
    ("psn", "PSN"),
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
    ("希腊", "EUR"),
    ("葡萄牙", "EUR"),
    ("意大利", "EUR"),
    ("意", "EUR"),
    ("比利时", "EUR"),
    ("比", "EUR"),
    ("爱尔兰", "EUR"),
    ("爱", "EUR"),
    ("奥地利", "EUR"),
    ("奥", "EUR"),
    ("荷兰", "EUR"),
    ("荷", "EUR"),
    ("法国", "EUR"),
    ("法", "EUR"),
    ("芬兰", "EUR"),
    ("芬", "EUR"),
    ("西班牙", "EUR"),
    ("西", "EUR"),
    ("斯洛伐克", "EUR"),
    ("斯洛文尼亚", "EUR"),
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
    ("de", "EUR"),
    ("德国", "EUR"),
    ("jpy", "JPY"),
    ("日元", "JPY"),
    ("cny", "CNY"),
    ("rmb", "RMB"),
    ("人民币", "RMB"),
]

_FORM_FACTORS: list[tuple[str, str]] = [
    ("横白卡", "横白卡"),
    ("横白卡图", "横白卡"),
    ("横白", "横白卡"),
    ("横卡", "横白卡"),
    ("横板", "横白卡"),
    ("竖卡", "竖卡"),
    ("竖板", "竖卡"),
    ("电子", "电子"),
    ("代码", "代码"),
    ("图密", "图密"),
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
    ):
        return "横白卡"
    if any(alias in normalized for alias in ("竖卡", "竖板", "vertical")):
        return "竖卡"

    values: list[str] = []
    if any(alias in normalized for alias in ("代码", "code")):
        values.append("代码")
    if any(alias in normalized for alias in ("电子", "electronic", "electron")):
        values.append("电子")
    if any(alias in normalized for alias in ("卡图", "图片", "photo", "image", "card")):
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


class QuoteCaptureService:
    def __init__(self, db) -> None:
        self.db = db

    def capture_from_message(
        self,
        envelope: NormalizedMessageEnvelope,
        *,
        raw_text: str | None = None,
    ) -> dict[str, Any]:
        text = str(raw_text if raw_text is not None else envelope.text or "").strip()
        if not text or not envelope.is_group or envelope.content_type != "text":
            return {"captured": False, "rows": 0, "exceptions": 0}
        # 采集供应商组（2/3/4）和客人组（5/6/7/8）的报价
        group_key = f"{envelope.platform}:{envelope.chat_id}"
        group_num = self.db.get_group_num(group_key)
        if group_num is None or group_num not in (2, 3, 4, 5, 6, 7, 8):
            return {"captured": False, "rows": 0, "exceptions": 0}
        group_profile = self._group_profile_for_envelope(envelope, text)
        inquiry_reply = self._capture_inquiry_reply(envelope, text=text)
        if inquiry_reply.get("captured"):
            return inquiry_reply
        message_time = _normalize_message_time(envelope.received_at)

        # 模板引擎解析
        from .template_engine import TemplateConfig, parse_message_with_template

        template_config_raw = str(getattr(group_profile, "template_config", "") or "").strip()
        if not template_config_raw:
            return {"captured": False, "rows": 0, "exceptions": 0}
        try:
            tpl = TemplateConfig.from_json(template_config_raw)
        except ValueError:
            return {"captured": False, "rows": 0, "exceptions": 0}

        parsed = parse_message_with_template(
            text=text,
            template=tpl,
            platform=envelope.platform,
            chat_id=envelope.chat_id,
            chat_name=envelope.chat_name,
            message_id=envelope.message_id,
            source_name=envelope.sender_name,
            sender_id=envelope.sender_id,
            source_group_key=f"{envelope.platform}:{envelope.chat_id}",
            message_time=message_time,
        )
        if not parsed.rows and not parsed.exceptions:
            return {"captured": False, "rows": 0, "exceptions": 0}

        # 同一群发新消息时，旧报价标记为不活跃
        source_group_key = f"{envelope.platform}:{envelope.chat_id}"
        deactivate_method = getattr(self.db, "deactivate_old_quotes_for_group", None)
        if callable(deactivate_method):
            deactivate_method(source_group_key=source_group_key)

        document_id = self.db.record_quote_document(
            platform=parsed.platform,
            source_group_key=parsed.source_group_key,
            chat_id=parsed.chat_id,
            chat_name=parsed.chat_name,
            message_id=parsed.message_id,
            source_name=parsed.source_name,
            sender_id=parsed.sender_id,
            raw_text=parsed.raw_text,
            message_time=parsed.message_time,
            parser_template=parsed.parser_template,
            parser_version=parsed.parser_version,
            confidence=parsed.confidence,
            parse_status=parsed.parse_status,
        )
        for item in parsed.exceptions:
            self.db.record_quote_exception(
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
            )
        published_rows = 0
        for item in parsed.rows:
            if item.quote_status != "active" or item.confidence < AUTO_PUBLISH_CONFIDENCE:
                self.db.record_quote_exception(
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
                )
                continue
            self.db.upsert_quote_price_row_with_history(
                quote_document_id=document_id,
                message_id=item.message_id,
                platform=item.platform,
                source_group_key=item.source_group_key,
                chat_id=item.chat_id,
                chat_name=item.chat_name,
                source_name=item.source_name,
                sender_id=item.sender_id,
                card_type=item.card_type,
                country_or_currency=item.country_or_currency,
                amount_range=item.amount_range,
                multiplier=item.multiplier,
                form_factor=item.form_factor,
                price=item.price,
                quote_status=item.quote_status,
                restriction_text=item.restriction_text,
                source_line=item.source_line,
                raw_text=item.raw_text,
                message_time=item.message_time,
                effective_at=item.effective_at,
                expires_at=item.expires_at,
                parser_template=item.parser_template,
                parser_version=item.parser_version,
                confidence=item.confidence,
            )
            published_rows += 1
        return {
            "captured": True,
            "document_id": document_id,
            "rows": published_rows,
            "exceptions": len(parsed.exceptions),
            "template": parsed.parser_template,
            "parse_status": parsed.parse_status,
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
        # 先通过 chat_id 查找
        method = getattr(self.db, "get_quote_group_profile", None)
        if callable(method):
            row = method(platform=envelope.platform, chat_id=envelope.chat_id)
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
                    template_config=str(row.get("template_config") or ""),
                    dictionary_aliases=dictionary_aliases,
                )
        # 如果通过 chat_id 找不到，再通过 chat_name 查找
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
                    template_config=str(row.get("template_config") or ""),
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
        document_id = self.db.record_quote_document(
            platform=envelope.platform,
            source_group_key=str(context["source_group_key"]),
            chat_id=envelope.chat_id,
            chat_name=envelope.chat_name,
            message_id=envelope.message_id,
            source_name=envelope.sender_name,
            sender_id=envelope.sender_id,
            raw_text=raw_text,
            message_time=message_time,
            parser_template="inquiry_context_reply",
            parser_version=PARSER_VERSION,
            confidence=0.98,
            parse_status="parsed",
        )
        self.db.upsert_quote_price_row_with_history(
            quote_document_id=document_id,
            message_id=envelope.message_id,
            platform=envelope.platform,
            source_group_key=str(context["source_group_key"]),
            chat_id=envelope.chat_id,
            chat_name=envelope.chat_name,
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
        resolve_method = getattr(self.db, "resolve_quote_inquiry_context", None)
        if callable(resolve_method):
            resolve_method(
                inquiry_id=int(context["id"]),
                resolved_message_id=envelope.message_id,
            )
        return {
            "captured": True,
            "document_id": document_id,
            "rows": 1,
            "exceptions": 0,
            "template": "inquiry_context_reply",
            "parse_status": "parsed",
        }


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
    for alias, canonical in (dictionary_aliases or {}).get("country_currency", ()):
        if _normalize_key(alias) and _normalize_key(alias) in normalized and canonical not in values:
            values.append(canonical)
    if values:
        return values
    for alias, canonical in _COUNTRY_ALIASES:
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


def looks_like_quote_message(text: str) -> bool:
    normalized = str(text or "")
    if not normalized.strip():
        return False
    if any(marker in normalized for marker in ("【", "】", "★★", "———", "===", "价格表", "报价单", "行情")):
        return True
    if any(keyword in normalized for keyword in ("问价", "收卡", "收价", "出价")):
        return True
    lines = [line.strip() for line in normalized.splitlines() if line.strip()]
    if len(lines) >= 2 and any(_contains_price(line) for line in lines):
        return any(
            _infer_card_type(line) is not None or _infer_country_or_currency(line) is not None
            for line in lines
        )
    if _infer_card_type(normalized) is not None:
        return True
    if _infer_country_or_currency(normalized) is not None and (
        _contains_price(normalized)
        or any(token in normalized for token in ("=", "：", ":", "【", "】", "￥", "¥", "₦"))
    ):
        return True
    return False


def _normalize_message_time(value: str | None) -> str:
    text = str(value or "").strip()
    if text:
        return text
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def _normalize_key(text: str) -> str:
    return re.sub(r"[\s\W_]+", "", str(text or "").lower())
