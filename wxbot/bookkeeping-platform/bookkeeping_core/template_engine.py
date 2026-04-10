"""报价模板引擎 — 按群固定模板匹配提取变量。

核心理念："机场广播"模式：
- 固定文字做字面量匹配（锚点）
- {变量} 插槽做正则提取
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

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

    normalized = [normalize_quote_text(line) for line in text.splitlines()]
    # Expand multi-quote lines (e.g. "巴西=1.03 新加坡=4.25" → two lines)
    lines: list[str] = []
    for line in normalized:
        lines.extend(split_multi_quote_line(line))
    rows: list[ParsedQuoteRow] = []
    exceptions: list[ParsedQuoteException] = []
    
    current_card_type = template.defaults.get("card_type") or "unknown"
    current_country = template.defaults.get("country") or ""
    current_form_factor = template.defaults.get("form_factor") or "不限"

    has_digits = re.compile(r"\d")
    unmatched_lines: list[str] = []

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
            unmatched_lines.append(line)

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
        if start == -1:
            continue
        annotations.append({
            "type": field_type,
            "value": value,
            "start": start,
            "end": start + len(value),
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
    # {country} {amount}={price}({restriction})
    (re.compile(r'^([A-Za-z\u4e00-\u9fff]+) ([\d\-/~]+)=([\d.]+)\((.+)\)$'),
     "{country} {amount}={price}({restriction})",
     ["country", "amount", "price", "restriction"]),
    # {country} {amount}={price}
    (re.compile(r'^([A-Za-z\u4e00-\u9fff]+) ([\d\-/~]+)=([\d.]+)$'),
     "{country} {amount}={price}",
     ["country", "amount", "price"]),
    # {country}:{amount}={price} {restriction}
    (re.compile(r'^([A-Za-z\u4e00-\u9fff]+):([\d\-/~]+)=([\d.]+) (.+)$'),
     "{country}:{amount}={price} {restriction}",
     ["country", "amount", "price", "restriction"]),
    # {country}:{amount}={price}
    (re.compile(r'^([A-Za-z\u4e00-\u9fff]+):([\d\-/~]+)=([\d.]+)$'),
     "{country}:{amount}={price}",
     ["country", "amount", "price"]),
    # {country}={price}({restriction})
    (re.compile(r'^([A-Za-z\u4e00-\u9fff]+)=([\d.]+)\((.+)\)$'),
     "{country}={price}({restriction})",
     ["country", "price", "restriction"]),
    # {amount}={price}({restriction})
    (re.compile(r'^([\d\-/~]+)=([\d.]+)\((.+)\)$'),
     "{amount}={price}({restriction})",
     ["amount", "price", "restriction"]),
    # {amount}={price}
    (re.compile(r'^([\d\-/~]+)=([\d.]+)$'),
     "{amount}={price}",
     ["amount", "price"]),
    # {country}={price}{suffix} (trailing text like 卡图)
    (re.compile(r'^([A-Za-z\u4e00-\u9fff]+)=([\d.]+)([A-Za-z\u4e00-\u9fff]+)$'),
     "{country}={price}{restriction}",
     ["country", "price", "restriction"]),
    # {country}={price}
    (re.compile(r'^([A-Za-z\u4e00-\u9fff]+)=([\d.]+)$'),
     "{country}={price}",
     ["country", "price"]),
]


def auto_detect_line_type(line: str) -> dict:
    """Auto-detect whether a line is a section header, price quote, or noise.

    Returns {"type": "section"|"price"|"skip", "pattern": str, "fields": dict}
    """
    line = line.strip()
    if not line:
        return {"type": "skip", "pattern": "", "fields": {}}

    # Section header: 【...】
    if re.match(r'^【.+】$', line):
        return {"type": "section", "pattern": "【{card_type}】", "fields": {}}

    # Try price patterns
    for regex, pattern, field_names in _AUTO_DETECT_PATTERNS:
        m = regex.match(line)
        if m:
            fields = {name: m.group(i + 1) for i, name in enumerate(field_names)}
            return {"type": "price", "pattern": pattern, "fields": fields}

    return {"type": "skip", "pattern": "", "fields": {}}


def suggest_template_rules(text: str) -> list[dict]:
    """Analyze a full message and suggest template rules.

    Returns a list of per-line detections:
      [{"line": str, "type": "section"|"price"|"skip", "pattern": str, "fields": dict}, ...]
    """
    results: list[dict] = []
    for raw_line in text.splitlines():
        line = normalize_quote_text(raw_line)
        if not line:
            continue
        sub_lines = split_multi_quote_line(line)
        for sub in sub_lines:
            detection = auto_detect_line_type(sub)
            results.append({"line": sub, **detection})
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
