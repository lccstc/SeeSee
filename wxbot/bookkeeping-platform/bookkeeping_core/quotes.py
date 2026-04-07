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
    parser_template: str | None = None
    stale_after_minutes: int | None = None
    note: str = ""


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
    ("竖卡", "竖卡"),
    ("电子", "电子"),
    ("代码", "代码"),
    ("图密", "图密"),
    ("卡图", "卡图"),
    ("纸质", "纸质"),
    ("photo", "photo"),
    ("图片", "图片"),
]


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
        inquiry_reply = self._capture_inquiry_reply(envelope, text=text)
        if inquiry_reply.get("captured"):
            return inquiry_reply
        if not looks_like_quote_message(text):
            return {"captured": False, "rows": 0, "exceptions": 0}
        message_time = _normalize_message_time(envelope.received_at)

        parsed = parse_quote_document(
            platform=envelope.platform,
            chat_id=envelope.chat_id,
            chat_name=envelope.chat_name,
            message_id=envelope.message_id,
            source_name=envelope.sender_name,
            sender_id=envelope.sender_id,
            source_group_key=f"{envelope.platform}:{envelope.chat_id}",
            raw_text=text,
            message_time=message_time,
            group_profile=self._group_profile_for_envelope(envelope, text),
        )
        if not parsed.rows and not parsed.exceptions:
            return {"captured": False, "rows": 0, "exceptions": 0}

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
        method = getattr(self.db, "get_quote_group_profile", None)
        if callable(method):
            row = method(platform=envelope.platform, chat_id=envelope.chat_id)
            if row:
                return QuoteGroupProfile(
                    key=f"{envelope.platform}:{envelope.chat_id}",
                    default_card_type=str(row.get("default_card_type") or "") or None,
                    parser_template=str(row.get("parser_template") or "") or None,
                    stale_after_minutes=int(row.get("stale_after_minutes") or DEFAULT_STALE_AFTER_MINUTES),
                    note=str(row.get("note") or ""),
                )
        return resolve_quote_group_profile(
            source_group_key=f"{envelope.platform}:{envelope.chat_id}",
            chat_name=envelope.chat_name,
            raw_text=text,
        )

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
            amount_range=str(context["amount_range"]),
            multiplier=str(context["multiplier"]) if context.get("multiplier") else None,
            form_factor=str(context["form_factor"] or "不限"),
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


def parse_quote_document(
    *,
    platform: str,
    chat_id: str,
    chat_name: str,
    message_id: str,
    source_name: str,
    sender_id: str,
    source_group_key: str,
    raw_text: str,
    message_time: str,
    group_profile: QuoteGroupProfile | None = None,
) -> ParsedQuoteDocument:
    lines = [line.strip() for line in raw_text.splitlines()]
    compact_lines = [line for line in lines if line]
    title = compact_lines[0] if compact_lines else ""
    group_profile = group_profile or resolve_quote_group_profile(
        source_group_key=source_group_key,
        chat_name=chat_name,
        raw_text=raw_text,
    )
    template_key = group_profile.parser_template or _infer_template_key(compact_lines)
    default_card_type = (
        _infer_card_type(title)
        or _infer_card_type(raw_text)
        or _infer_card_type(chat_name)
        or group_profile.default_card_type
        or _fallback_card_type(title)
    )

    rows: list[ParsedQuoteRow] = []
    exceptions: list[ParsedQuoteException] = []
    current_card_type = default_card_type
    section_restrictions: list[str] = []
    modifier_anchor_rows: list[ParsedQuoteRow] = []

    for index, line in enumerate(lines, start=1):
        if not line:
            continue
        header_card = _maybe_section_header_card_type(line)
        if header_card:
            current_card_type = header_card
            section_restrictions = []
            modifier_anchor_rows = []
            header_tail = _section_header_tail(line)
            if header_tail and _looks_like_restriction_line(header_tail) and not _contains_price(header_tail):
                if _looks_like_modifier_line(header_tail):
                    derived_rows = _derive_modifier_rows(header_tail, modifier_anchor_rows)
                    if derived_rows:
                        rows.extend(derived_rows)
                    else:
                        exceptions.append(
                            _build_exception(
                                source_group_key=source_group_key,
                                platform=platform,
                                chat_id=chat_id,
                                chat_name=chat_name,
                                source_name=source_name,
                                sender_id=sender_id,
                                reason="modifier_rule",
                                source_line=header_tail,
                                raw_text=raw_text,
                                message_time=message_time,
                                parser_template=template_key,
                                confidence=0.55,
                            )
                        )
                else:
                    section_restrictions.append(header_tail.lstrip("#").strip())
            continue

        if _is_separator_line(line):
            continue

        if _looks_like_modifier_line(line):
            derived_rows = _derive_modifier_rows(line, modifier_anchor_rows)
            if derived_rows:
                rows.extend(derived_rows)
            else:
                exceptions.append(
                    _build_exception(
                        source_group_key=source_group_key,
                        platform=platform,
                        chat_id=chat_id,
                        chat_name=chat_name,
                        source_name=source_name,
                        sender_id=sender_id,
                        reason="modifier_rule",
                        source_line=line,
                        raw_text=raw_text,
                        message_time=message_time,
                        parser_template=template_key,
                        confidence=0.55,
                    )
                )
            continue

        if _looks_like_restriction_line(line) and not _contains_price(line):
            if _looks_like_modifier_line(line):
                derived_rows = _derive_modifier_rows(line, modifier_anchor_rows)
                if derived_rows:
                    rows.extend(derived_rows)
                else:
                    exceptions.append(
                        _build_exception(
                            source_group_key=source_group_key,
                            platform=platform,
                            chat_id=chat_id,
                            chat_name=chat_name,
                            source_name=source_name,
                            sender_id=sender_id,
                            reason="modifier_rule",
                            source_line=line,
                            raw_text=raw_text,
                            message_time=message_time,
                            parser_template=template_key,
                            confidence=0.55,
                        )
                    )
            else:
                section_restrictions.append(line.lstrip("#").strip())
            continue

        if _looks_like_blocked_question(line):
            exceptions.append(
                _build_exception(
                    source_group_key=source_group_key,
                    platform=platform,
                    chat_id=chat_id,
                    chat_name=chat_name,
                    source_name=source_name,
                    sender_id=sender_id,
                    reason="blocked_or_question_line",
                    source_line=line,
                    raw_text=raw_text,
                    message_time=message_time,
                    parser_template=template_key,
                    confidence=0.45,
                )
            )
            continue

        parsed_segments = _parse_price_segments(
            line=line,
            current_card_type=current_card_type,
            source_group_key=source_group_key,
            platform=platform,
            chat_id=chat_id,
            chat_name=chat_name,
            message_id=message_id,
            source_name=source_name,
            sender_id=sender_id,
            raw_text=raw_text,
            message_time=message_time,
            parser_template=template_key,
            section_restrictions=section_restrictions,
        )
        rows.extend(parsed_segments.rows)
        exceptions.extend(parsed_segments.exceptions)
        if parsed_segments.rows:
            modifier_anchor_rows.extend(parsed_segments.rows)
            inferred_card = parsed_segments.rows[0].card_type
            if inferred_card and inferred_card != "unknown":
                current_card_type = inferred_card

    parse_status = "parsed" if rows else "exception"
    if rows and exceptions:
        parse_status = "partial"
    elif not rows and exceptions:
        parse_status = "exception"

    confidence = _document_confidence(rows, exceptions, template_key)
    return ParsedQuoteDocument(
        source_group_key=source_group_key,
        platform=platform,
        chat_id=chat_id,
        chat_name=chat_name,
        message_id=message_id,
        source_name=source_name,
        sender_id=sender_id,
        raw_text=raw_text,
        message_time=message_time,
        parser_template=template_key,
        parser_version=PARSER_VERSION,
        confidence=confidence,
        parse_status=parse_status,
        rows=rows,
        exceptions=exceptions,
    )


@dataclass(slots=True)
class _ParsedSegments:
    rows: list[ParsedQuoteRow]
    exceptions: list[ParsedQuoteException]


def _parse_price_segments(
    *,
    line: str,
    current_card_type: str,
    source_group_key: str,
    platform: str,
    chat_id: str,
    chat_name: str,
    message_id: str,
    source_name: str,
    sender_id: str,
    raw_text: str,
    message_time: str,
    parser_template: str,
    section_restrictions: list[str],
) -> _ParsedSegments:
    rows: list[ParsedQuoteRow] = []
    exceptions: list[ParsedQuoteException] = []
    segments = _split_segments(line)
    inherited_card_type = current_card_type
    inherited_country = ""
    inherited_amount_range = ""
    inherited_form_factor = ""
    for segment in segments:
        candidate = _parse_single_segment(
            segment=segment,
            inherited_card_type=inherited_card_type,
            inherited_country=inherited_country,
            inherited_amount_range=inherited_amount_range,
            inherited_form_factor=inherited_form_factor,
            source_group_key=source_group_key,
            platform=platform,
            chat_id=chat_id,
            chat_name=chat_name,
            message_id=message_id,
            source_name=source_name,
            sender_id=sender_id,
            raw_text=raw_text,
            message_time=message_time,
            parser_template=parser_template,
            section_restrictions=section_restrictions,
        )
        if candidate.row is not None:
            rows.append(candidate.row)
            inherited_card_type = candidate.row.card_type or inherited_card_type
            inherited_country = candidate.row.country_or_currency or inherited_country
            inherited_amount_range = candidate.row.amount_range or inherited_amount_range
            inherited_form_factor = candidate.row.form_factor or inherited_form_factor
        elif candidate.exception is not None:
            exceptions.append(candidate.exception)
    return _ParsedSegments(rows=rows, exceptions=exceptions)


@dataclass(slots=True)
class _ParsedSegment:
    row: ParsedQuoteRow | None
    exception: ParsedQuoteException | None


def _parse_single_segment(
    *,
    segment: str,
    inherited_card_type: str,
    inherited_country: str,
    inherited_amount_range: str,
    inherited_form_factor: str,
    source_group_key: str,
    platform: str,
    chat_id: str,
    chat_name: str,
    message_id: str,
    source_name: str,
    sender_id: str,
    raw_text: str,
    message_time: str,
    parser_template: str,
    section_restrictions: list[str],
) -> _ParsedSegment:
    cleaned = _normalize_segment(segment)
    if not cleaned:
        return _ParsedSegment(row=None, exception=None)

    if _contains_price(cleaned) is False:
        if _looks_like_short_quote(cleaned):
            return _ParsedSegment(
                row=None,
                exception=_build_exception(
                    source_group_key=source_group_key,
                    platform=platform,
                    chat_id=chat_id,
                    chat_name=chat_name,
                    source_name=source_name,
                    sender_id=sender_id,
                    reason="missing_context",
                    source_line=cleaned,
                    raw_text=raw_text,
                    message_time=message_time,
                    parser_template=parser_template,
                    confidence=0.4,
                ),
            )
        return _ParsedSegment(row=None, exception=None)

    price, left_text, right_text = _extract_price(cleaned)
    if price is None:
        return _ParsedSegment(
            row=None,
            exception=_build_exception(
                source_group_key=source_group_key,
                platform=platform,
                chat_id=chat_id,
                chat_name=chat_name,
                source_name=source_name,
                sender_id=sender_id,
                reason="unparsed_price_line",
                source_line=cleaned,
                raw_text=raw_text,
                message_time=message_time,
                parser_template=parser_template,
                confidence=0.35,
            ),
        )

    context_text = " ".join(part for part in (left_text, right_text, cleaned) if part)
    card_type = (
        _infer_card_type(context_text)
        or inherited_card_type
        or _fallback_card_type(context_text)
    )
    country_or_currency = _infer_country_or_currency(context_text) or inherited_country
    form_factor = _infer_form_factor(context_text) or inherited_form_factor or "不限"
    amount_range = _extract_amount_range(context_text) or inherited_amount_range or "不限"
    multiplier = _extract_multiplier(context_text)
    restriction_text = _merge_restrictions(section_restrictions, right_text)
    if _looks_like_modifier_line(cleaned):
        return _ParsedSegment(
            row=None,
            exception=_build_exception(
                source_group_key=source_group_key,
                platform=platform,
                chat_id=chat_id,
                chat_name=chat_name,
                source_name=source_name,
                sender_id=sender_id,
                reason="modifier_rule",
                source_line=cleaned,
                raw_text=raw_text,
                message_time=message_time,
                parser_template=parser_template,
                confidence=0.55,
            ),
        )

    if not card_type or card_type == "unknown" or not country_or_currency:
        return _ParsedSegment(
            row=None,
            exception=_build_exception(
                source_group_key=source_group_key,
                platform=platform,
                chat_id=chat_id,
                chat_name=chat_name,
                source_name=source_name,
                sender_id=sender_id,
                reason="missing_context",
                source_line=cleaned,
                raw_text=raw_text,
                message_time=message_time,
                parser_template=parser_template,
                confidence=0.45,
            ),
        )

    quote_status = "active"
    if _looks_like_blocked_question(cleaned):
        quote_status = "blocked"
    elif _contains_question_keyword(cleaned):
        quote_status = "needs_review"

    confidence = _segment_confidence(
        cleaned=cleaned,
        card_type=card_type,
        country_or_currency=country_or_currency,
        amount_range=amount_range,
        form_factor=form_factor,
        multiplier=multiplier,
        quote_status=quote_status,
    )
    if confidence < AUTO_PUBLISH_CONFIDENCE or quote_status != "active":
        return _ParsedSegment(
            row=ParsedQuoteRow(
                source_group_key=source_group_key,
                platform=platform,
                chat_id=chat_id,
                chat_name=chat_name,
                message_id=message_id,
                source_name=source_name,
                sender_id=sender_id,
                card_type=card_type,
                country_or_currency=country_or_currency,
                amount_range=amount_range,
                multiplier=multiplier,
                form_factor=form_factor,
                price=price,
                quote_status=quote_status,
                restriction_text=restriction_text,
                source_line=cleaned,
                raw_text=raw_text,
                message_time=message_time,
                effective_at=message_time,
                expires_at=None,
                parser_template=parser_template,
                parser_version=PARSER_VERSION,
                confidence=confidence,
            ),
            exception=_build_exception(
                source_group_key=source_group_key,
                platform=platform,
                chat_id=chat_id,
                chat_name=chat_name,
                source_name=source_name,
                sender_id=sender_id,
                reason="low_confidence_or_non_active",
                source_line=cleaned,
                raw_text=raw_text,
                message_time=message_time,
                parser_template=parser_template,
                confidence=confidence,
            ),
        )

    return _ParsedSegment(
        row=ParsedQuoteRow(
            source_group_key=source_group_key,
            platform=platform,
            chat_id=chat_id,
            chat_name=chat_name,
            message_id=message_id,
            source_name=source_name,
            sender_id=sender_id,
            card_type=card_type,
            country_or_currency=country_or_currency,
            amount_range=amount_range,
            multiplier=multiplier,
            form_factor=form_factor,
            price=price,
            quote_status=quote_status,
            restriction_text=restriction_text,
            source_line=cleaned,
            raw_text=raw_text,
            message_time=message_time,
            effective_at=message_time,
            expires_at=None,
            parser_template=parser_template,
            parser_version=PARSER_VERSION,
            confidence=confidence,
        ),
        exception=None,
    )


def _derive_modifier_rows(
    modifier_line: str,
    anchor_rows: list[ParsedQuoteRow],
) -> list[ParsedQuoteRow]:
    target_form_factor = _infer_form_factor(modifier_line)
    delta = _extract_modifier_delta(modifier_line)
    if not target_form_factor or delta is None or not anchor_rows:
        return []

    derived: list[ParsedQuoteRow] = []
    modifier_note = modifier_line.lstrip("#").strip()
    for row in anchor_rows:
        if row.form_factor == target_form_factor:
            continue
        price = round(row.price + delta, 6)
        if price <= 0:
            continue
        restriction_text = _merge_restrictions(
            [row.restriction_text],
            modifier_note,
        )
        derived.append(
            replace(
                row,
                form_factor=target_form_factor,
                price=price,
                restriction_text=restriction_text,
                source_line=f"{row.source_line} | {modifier_line}",
                confidence=min(row.confidence, 0.9),
            )
        )
    return derived


def _extract_modifier_delta(text: str) -> float | None:
    match = _MODIFIER_RE.search(text)
    if match is None:
        return None
    return float(match.group(0))


def _extract_standalone_reply_price(text: str) -> float | None:
    cleaned = _normalize_segment(text)
    lines = [_normalize_segment(line) for line in cleaned.splitlines() if _normalize_segment(line)]
    candidates = lines or [cleaned]
    if len(candidates) > 2:
        return None
    for candidate in reversed(candidates):
        if re.fullmatch(r"\d+(?:\.\d+)?", candidate):
            return float(candidate)
        price, left_text, right_text = _extract_price(candidate)
        if price is not None and not _infer_card_type(left_text) and not _infer_country_or_currency(left_text):
            return price
    return None


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


def _infer_template_key(lines: list[str]) -> str:
    joined = "\n".join(lines)
    if any(marker in joined for marker in ("【", "】", "★★", "———", "===", "===")):
        return "section_sheet"
    if any(token in joined for token in ("￥", "₦", "RMB", "人民币")):
        return "tabular_sheet"
    return "simple_sheet"


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


def _maybe_section_header_card_type(line: str) -> str | None:
    if not any(marker in line for marker in ("【", "】", "★★", "———", "===")):
        return None
    candidate = _SECTION_HEADER_RE.search(line)
    if candidate is not None:
        value = candidate.group("label")
    else:
        value = line
    card_type = _infer_card_type(value) or _normalize_card_type_label(value)
    if card_type and card_type not in {"unknown", "报价单"}:
        return card_type
    return None


def _section_header_tail(line: str) -> str:
    tail = _SECTION_HEADER_RE.sub(" ", line)
    tail = re.sub(r"[★=—\-_]+", " ", tail)
    return re.sub(r"\s+", " ", tail).strip()


def _infer_card_type(text: str) -> str | None:
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


def _infer_country_or_currency(text: str) -> str | None:
    normalized = _normalize_key(text)
    if not normalized:
        return None
    for alias, canonical in _COUNTRY_ALIASES:
        if _normalize_key(alias) in normalized:
            return canonical
    return None


def _infer_form_factor(text: str) -> str | None:
    normalized = _normalize_key(text)
    if not normalized:
        return None
    values: list[str] = []
    for alias, canonical in _FORM_FACTORS:
        if _normalize_key(alias) in normalized:
            if canonical not in values:
                values.append(canonical)
    if not values:
        return None
    return "/".join(values)


def _extract_amount_range(text: str) -> str | None:
    for pattern in (
        re.compile(r"[【\[]\s*(?P<value>\d+(?:\s*[-~－—/／]\s*\d+)?)\s*[】\]]"),
        re.compile(r"(?P<value>\d+(?:\s*[-~－—]\s*\d+)+)"),
        re.compile(r"(?P<value>\d+\s*/\s*\d+)"),
    ):
        match = pattern.search(text)
        if match is not None:
            value = re.sub(r"\s+", "", match.group("value"))
            value = value.replace("~", "-").replace("－", "-").replace("—", "-").replace("／", "/").replace("/", "-")
            return value
    numeric_tokens = re.findall(r"\d+(?:\.\d+)?", text)
    if len(numeric_tokens) >= 2:
        return numeric_tokens[0]
    return None


def _extract_multiplier(text: str) -> str | None:
    match = _MULTIPLIER_RE.search(text)
    if match is None:
        return None
    value = match.group("value")
    if value.endswith(".0"):
        value = value[:-2]
    return f"{value}X"


def _merge_restrictions(section_restrictions: list[str], right_text: str) -> str:
    items = [item.strip() for item in section_restrictions if item.strip()]
    if right_text.strip():
        items.append(right_text.strip())
    deduped: list[str] = []
    for item in items:
        if item not in deduped:
            deduped.append(item)
    return " | ".join(deduped)


def _build_exception(
    *,
    source_group_key: str,
    platform: str,
    chat_id: str,
    chat_name: str,
    source_name: str,
    sender_id: str,
    reason: str,
    source_line: str,
    raw_text: str,
    message_time: str,
    parser_template: str,
    confidence: float,
) -> ParsedQuoteException:
    return ParsedQuoteException(
        source_group_key=source_group_key,
        platform=platform,
        chat_id=chat_id,
        chat_name=chat_name,
        source_name=source_name,
        sender_id=sender_id,
        reason=reason,
        source_line=source_line,
        raw_text=raw_text,
        message_time=message_time,
        parser_template=parser_template,
        parser_version=PARSER_VERSION,
        confidence=confidence,
    )


def _document_confidence(
    rows: list[ParsedQuoteRow],
    exceptions: list[ParsedQuoteException],
    parser_template: str,
) -> float:
    if not rows and not exceptions:
        return 0.0
    row_score = sum(row.confidence for row in rows)
    exc_penalty = sum(0.05 if item.reason != "modifier_rule" else 0.08 for item in exceptions)
    base = row_score / max(len(rows), 1) if rows else 0.55
    if parser_template == "section_sheet":
        base += 0.05
    return max(0.0, min(0.99, base - exc_penalty))


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


def _segment_confidence(
    *,
    cleaned: str,
    card_type: str,
    country_or_currency: str,
    amount_range: str,
    form_factor: str,
    multiplier: str | None,
    quote_status: str,
) -> float:
    confidence = 0.78
    if card_type != "unknown":
        confidence += 0.08
    if country_or_currency:
        confidence += 0.07
    if amount_range and amount_range != "不限":
        confidence += 0.08
    if form_factor and form_factor != "不限":
        confidence += 0.04
    if multiplier:
        confidence += 0.03
    if "【" in cleaned or "】" in cleaned or "★★" in cleaned:
        confidence += 0.02
    if quote_status != "active":
        confidence -= 0.2
    return max(0.0, min(0.99, confidence))


def _looks_like_short_quote(text: str) -> bool:
    normalized = _normalize_key(text)
    if not normalized:
        return False
    if re.fullmatch(r"\d+(?:\.\d+)?", normalized):
        return True
    if len(normalized) <= 12 and any(char.isdigit() for char in normalized):
        return True
    return bool(
        re.search(r"^[a-zA-Z\u4e00-\u9fff]{2,6}\d{1,4}$", normalized)
        or re.search(r"\d{1,4}[a-zA-Z\u4e00-\u9fff]{1,8}$", normalized)
    )


def _looks_like_modifier_line(text: str) -> bool:
    return text.lstrip().startswith("#") and bool(_MODIFIER_RE.search(text))


def _looks_like_restriction_line(text: str) -> bool:
    normalized = text.lstrip("#").strip()
    if not normalized:
        return False
    if _contains_price(normalized):
        return False
    return any(keyword in normalized for keyword in _RESTRICTION_KEYWORDS) or text.startswith("#")


def _looks_like_blocked_question(text: str) -> bool:
    normalized = str(text or "")
    if _contains_price(normalized):
        return False
    return any(keyword in normalized for keyword in _QUESTION_KEYWORDS)


def _contains_question_keyword(text: str) -> bool:
    return any(keyword in text for keyword in _QUESTION_KEYWORDS)


def _line_has_price_and_question(text: str) -> bool:
    return _contains_price(text) and _contains_question_keyword(text)


def _is_separator_line(text: str) -> bool:
    stripped = text.strip()
    return bool(stripped) and len(set(stripped)) == 1 and stripped[0] in {"-", "=", "═", "─", "—"}


def _normalize_segment(text: str) -> str:
    cleaned = str(text or "").strip()
    cleaned = cleaned.strip("，,;；")
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def _normalize_key(text: str) -> str:
    return re.sub(r"[\s\W_]+", "", str(text or "").lower())
