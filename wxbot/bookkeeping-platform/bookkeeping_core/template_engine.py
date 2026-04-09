"""报价模板引擎 — 按群固定模板匹配提取变量。

核心理念："机场广播"模式：
- 固定文字做字面量匹配（锚点）
- {变量} 插槽做正则提取
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

import re


@dataclass
class TemplateConfig:
    """群报价模板定义 (Data Engine v1)。"""
    version: str = "data-engine-v1"
    rules: list[dict[str, str]] = field(default_factory=list)
    defaults: dict[str, str | None] = field(default_factory=dict)
    
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
            defaults=data.get("defaults", {})
        )

    def to_json(self) -> str:
        return json.dumps({
            "version": self.version,
            "rules": self.rules,
            "defaults": self.defaults,
        }, ensure_ascii=False)


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
                regex_parts.append(r"([\d]+(?:[.\-/][\d]+)*)")
            else:
                regex_parts.append(r"(.+?)")

    regex = "^" + "".join(regex_parts) + "$"
    m = re.match(regex, line.strip())
    if m is None:
        return None

    return {name: m.group(i + 1).strip() for i, name in enumerate(names)}


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
    from .quotes import (
        PARSER_VERSION,
        ParsedQuoteDocument,
        ParsedQuoteRow,
        ParsedQuoteException,
        normalize_quote_amount_range,
        normalize_quote_form_factor,
        normalize_quote_multiplier,
    )

    lines = [line.strip() for line in text.splitlines()]
    rows: list[ParsedQuoteRow] = []
    exceptions: list[ParsedQuoteException] = []
    
    current_card_type = template.defaults.get("card_type") or "unknown"
    current_country = template.defaults.get("country") or ""
    current_form_factor = template.defaults.get("form_factor") or "不限"

    import re
    has_digits = re.compile(r"\d")
    
    for line in lines:
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
                        current_card_type = variables["card_type"]
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
                        source_line=line,
                        raw_text=text,
                        message_time=message_time,
                        effective_at=message_time,
                        expires_at=None,
                        parser_template="data-engine",
                        parser_version="data-engine-v1",
                        confidence=1.0,
                    ))
                break 

        if not matched and has_digits.search(line):
            exceptions.append(ParsedQuoteException(
                source_group_key=source_group_key,
                platform=platform,
                chat_id=chat_id,
                chat_name=chat_name,
                source_name=source_name,
                sender_id=sender_id,
                reason="strict_match_failed",
                source_line=line,
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


def _matches_any(line: str, patterns: list[str]) -> bool:
    for pat in patterns:
        if re.search(pat, line):
            return True
    return False


# --- 模板自动生成 ---

_PRICE_SEPARATORS = re.compile(r"[:：=]")
_HAS_DIGITS = re.compile(r"\d")
_RESTRICTION_PREFIX = re.compile(r"^#|^注[：:]|^注意|^为避免")
_SECTION_MARKER = re.compile(r"^【|^———|^---|^===|^═══")
_SKIP_MARKER = re.compile(r"^\s*$|^[😀-🙏😀-🚀]|^\[左|^\[右|^\[中")


def auto_generate_template(
    text: str,
    *,
    defaults: dict[str, str | None] | None = None,
) -> TemplateConfig:
    """从一条真实报价消息自动生成 TemplateConfig。

    算法：
    1. 包含数字+分隔符的行 → 候选价格行，生成 pattern
    2. 以 # 或注： 开头的行 → 限制行
    3. 以 【 或分隔线 开头 → 分节行
    4. 其他 → 跳过行
    """
    if not text or not text.strip():
        raise ValueError("empty text")

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    price_patterns: list[dict[str, str | None]] = []
    restriction_pats: list[str] = []
    section_pats: list[str] = []

    for line in lines:
        if _RESTRICTION_PREFIX.search(line):
            restriction_pats.append(r"^#|^注[：:]")
            continue
        if _SECTION_MARKER.search(line):
            section_pats.append(re.escape(line[:3]))
            continue
        if _SKIP_MARKER.search(line):
            continue
        if not _HAS_DIGITS.search(line):
            continue

        # 尝试生成价格行 pattern
        pattern = _generate_price_pattern(line)
        if pattern:
            price_patterns.append({"pattern": pattern, "form_factor": None})

    # 去重
    seen_patterns: set[str] = set()
    unique_price: list[dict[str, str | None]] = []
    for pp in price_patterns:
        p = pp["pattern"]
        if p not in seen_patterns:
            seen_patterns.add(p)
            unique_price.append(pp)

    seen_restrictions: set[str] = set()
    unique_restrictions: list[str] = []
    for r in restriction_pats:
        if r not in seen_restrictions:
            seen_restrictions.add(r)
            unique_restrictions.append(r)

    return TemplateConfig(
        defaults=defaults or {},
        price_lines=unique_price,
        restriction_lines=unique_restrictions,
        section_lines=list(set(section_pats)),
        skip_lines=[r"^\s*$", r"^[😀-🙏]"],
    )


def _generate_price_pattern(line: str) -> str | None:
    """从一行消息中提取 pattern。固定文字做锚点，数字做 {amount}/{price}。"""
    # 找所有数字 token（含小数、区间）
    tokens = list(re.finditer(r"[\d]+(?:[.\-/][\d]+)*", line))
    if not tokens:
        return None

    # 至少需要一个数字
    if len(tokens) < 1:
        return None

    parts: list[str] = []
    prev_end = 0
    for i, token in enumerate(tokens):
        # 固定文字部分
        fixed = line[prev_end:token.start()]
        if fixed:
            parts.append(re.escape(fixed))
        # 变量部分：最后一个数字 = price，其他 = amount
        if i == len(tokens) - 1 and len(tokens) > 1:
            parts.append("{price}")
        elif len(tokens) == 1:
            # 只有一个数字，可能是 amount（后面可能还有价格在别的位置）
            parts.append("{amount}")
        else:
            parts.append("{amount}")
        prev_end = token.end()

    # 尾部固定文字（如果有的话）
    tail = line[prev_end:]
    if tail:
        parts.append(re.escape(tail))

    return "".join(parts)
