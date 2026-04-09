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
    """群报价模板定义。"""

    version: str = "tpl-v1"
    defaults: dict[str, str | None] = field(default_factory=dict)
    price_lines: list[dict[str, str | None]] = field(default_factory=list)
    restriction_lines: list[str] = field(default_factory=list)
    section_lines: list[str] = field(default_factory=list)
    skip_lines: list[str] = field(default_factory=list)

    @classmethod
    def from_json(cls, raw: str) -> TemplateConfig:
        if not raw or not raw.strip():
            raise ValueError("empty template config")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON: {exc}") from exc
        return cls(
            version=data.get("version", "tpl-v1"),
            defaults=data.get("defaults", {}),
            price_lines=data.get("price_lines", []),
            restriction_lines=data.get("restriction_lines", []),
            section_lines=data.get("section_lines", []),
            skip_lines=data.get("skip_lines", []),
        )

    def to_json(self) -> str:
        return json.dumps({
            "version": self.version,
            "defaults": self.defaults,
            "price_lines": self.price_lines,
            "restriction_lines": self.restriction_lines,
            "section_lines": self.section_lines,
            "skip_lines": self.skip_lines,
        }, ensure_ascii=False)


def match_pattern(line: str, pattern: str) -> dict[str, str] | None:
    """将 pattern 中的 {name} 插槽替换为正则，匹配 line 并提取变量。

    固定文字做字面量匹配，{name} 匹配数字/区间/浮点数。
    返回提取的变量字典，不匹配则返回 None。
    """
    # 把 pattern 转成正则：固定文字转义，{name} 变捕获组
    parts = re.split(r"\{(\w+)\}", pattern)
    if not parts:
        return None

    regex_parts: list[str] = []
    names: list[str] = []
    for i, part in enumerate(parts):
        if i % 2 == 0:
            # 固定文字 — 转义正则特殊字符
            regex_parts.append(re.escape(part))
        else:
            # 变量插槽 — 匹配数字（含小数、区间、斜杠、空格分隔）
            names.append(part)
            regex_parts.append(r"([\d]+(?:[.\-/ ][\d]+)*)")

    regex = "^" + "".join(regex_parts)
    m = re.match(regex, line.strip())
    if m is None:
        return None

    return {name: m.group(i + 1).strip() for i, name in enumerate(names)}


def parse_message_with_template(
    text: str,
    template: TemplateConfig,
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
    """用模板解析完整消息，输出 ParsedQuoteDocument。"""
    from .quotes import (
        PARSER_VERSION,
        ParsedQuoteDocument,
        ParsedQuoteRow,
        normalize_quote_amount_range,
        normalize_quote_form_factor,
        normalize_quote_multiplier,
    )

    lines = [line.strip() for line in text.splitlines()]

    # 第一遍：收集所有限制行（消息级，不分先后）
    message_restrictions: list[str] = []
    for line in lines:
        if not line:
            continue
        if _matches_any(line, template.restriction_lines):
            restriction = re.sub(r"^#|^注[：:]", "", line).strip()
            if restriction:
                message_restrictions.append(restriction)

    # 第二遍：匹配价格行
    rows: list[ParsedQuoteRow] = []
    for line in lines:
        if not line:
            continue

        # 限制行已在第一遍收集，跳过
        if _matches_any(line, template.restriction_lines):
            continue

        # 匹配跳过行
        if _matches_any(line, template.skip_lines):
            continue

        # 匹配价格行
        for price_line in template.price_lines:
            pattern = price_line.get("pattern", "")
            variables = match_pattern(line, pattern)
            if variables is None:
                continue

            price_str = variables.get("price")
            if price_str is None:
                continue
            try:
                price = float(price_str)
            except ValueError:
                continue

            amount = variables.get("amount", "不限")
            card_type = template.defaults.get("card_type") or "unknown"
            country = template.defaults.get("country") or ""
            form_factor = (
                price_line.get("form_factor")
                or template.defaults.get("form_factor")
                or "不限"
            )
            multiplier = variables.get("multiplier") or template.defaults.get("multiplier")

            rows.append(ParsedQuoteRow(
                source_group_key=source_group_key,
                platform=platform,
                chat_id=chat_id,
                chat_name=chat_name,
                message_id=message_id,
                source_name=source_name,
                sender_id=sender_id,
                card_type=card_type,
                country_or_currency=country,
                amount_range=normalize_quote_amount_range(amount),
                multiplier=normalize_quote_multiplier(multiplier or "") or None,
                form_factor=normalize_quote_form_factor(form_factor),
                price=price,
                quote_status="active",
                restriction_text=" | ".join(message_restrictions) if message_restrictions else "",
                source_line=line,
                raw_text=text,
                message_time=message_time,
                effective_at=message_time,
                expires_at=None,
                parser_template="template_engine",
                parser_version=PARSER_VERSION,
                confidence=0.95,
            ))
            break  # 第一个匹配即停止

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
        parser_template="template_engine",
        parser_version=PARSER_VERSION,
        confidence=0.95 if rows else 0.0,
        parse_status=parse_status,
        rows=rows,
        exceptions=[],
    )


def _matches_any(line: str, patterns: list[str]) -> bool:
    for pat in patterns:
        if re.search(pat, line):
            return True
    return False
