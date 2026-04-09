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


def parse_message_with_template(text: str, template) -> None:
    """占位 — T1.4 实现"""
    raise NotImplementedError
