# 报价模板引擎实施计划

> **For Hermes:** 按任务顺序执行，每个任务遵循 TDD 循环。

**Goal:** 用模板匹配引擎替代旧正则解析器，实现 per-group 确定性报价提取。

**Architecture:** 每个群一个 JSON 模板（存在 template_config 字段），模板定义价格行 pattern 和限制行规则。解析时字面量匹配固定文字，正则提取变量插槽。

**Tech Stack:** Python, PostgreSQL, Flask (web), unittest/pytest

**Spec:** `docs/superpowers/specs/2026-04-10-quote-template-engine-design.md`

**Design reference (real message formats):**
```
Doc 301: 卡图：100/150=5.35  +  #限制行
Doc 300: 横白卡图：50=5.3  +  横白卡图：100 150 5.37 连卡问  +  #注：...
Doc 299: 500=5.45单张 清晰完整  +  #手持图不要
Doc 296: 10-195=5.25（5倍数）  +  50=5.3  +  100/150=5.43
Doc 286: Apple Sweden 4500*1
```

---

## Phase 1: 模板引擎核心

### Task 1: match_pattern 已完成 ✓

`bookkeeping_core/template_engine.py` 中的 `match_pattern()` 已实现，8 个测试全部通过。

### Task 2: TemplateConfig 数据类 + JSON 序列化

**Objective:** 定义模板数据结构，支持 JSON 序列化/反序列化

**Files:**
- Modify: `bookkeeping_core/template_engine.py`

**Step 1: Write failing test**

```python
# 添加到 tests/test_template_engine.py

class TemplateConfigTests(unittest.TestCase):
    def test_from_json_roundtrip(self) -> None:
        raw = json.dumps({
            "version": "tpl-v1",
            "defaults": {
                "card_type": "Apple",
                "country": "USD",
                "form_factor": "横白卡",
            },
            "price_lines": [
                {"pattern": "卡图：{amount}={price}", "form_factor": "横白卡"},
            ],
            "restriction_lines": ["^#"],
            "skip_lines": ["^\\s*$"],
        })
        tpl = TemplateConfig.from_json(raw)
        self.assertEqual(tpl.version, "tpl-v1")
        self.assertEqual(tpl.defaults["card_type"], "Apple")
        self.assertEqual(len(tpl.price_lines), 1)
        self.assertEqual(tpl.price_lines[0]["pattern"], "卡图：{amount}={price}")
        # roundtrip
        self.assertEqual(TemplateConfig.from_json(tpl.to_json()).defaults, tpl.defaults)

    def test_from_json_empty_string(self) -> None:
        with self.assertRaises(ValueError):
            TemplateConfig.from_json("")

    def test_from_json_invalid(self) -> None:
        with self.assertRaises(ValueError):
            TemplateConfig.from_json("{bad json")
```

**Step 2: Run test to verify failure**
`PYTHONPATH='.' ./.venv/bin/python -m pytest tests/test_template_engine.py::TemplateConfigTests -v`

**Step 3: Write minimal implementation**

```python
# bookkeeping_core/template_engine.py — 添加

from __future__ import annotations
import json
from dataclasses import dataclass, field


@dataclass
class TemplateConfig:
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
```

**Step 4: Run test to verify pass**
`PYTHONPATH='.' ./.venv/bin/python -m pytest tests/test_template_engine.py::TemplateConfigTests -v`

**Step 5: Commit**
```bash
git add bookkeeping_core/template_engine.py tests/test_template_engine.py
git commit -m "feat(template): add TemplateConfig dataclass with JSON serialization"
```

### Task 3: parse_message_with_template — 核心解析函数

**Objective:** 用模板解析完整消息，输出 ParsedQuoteDocument

**Files:**
- Modify: `bookkeeping_core/template_engine.py`
- Modify: `tests/test_template_engine.py`

**Step 1: Write failing test**

```python
# 添加到 tests/test_template_engine.py

class ParseMessageTests(unittest.TestCase):
    def _make_apple_template(self) -> TemplateConfig:
        return TemplateConfig(
            defaults={"card_type": "Apple", "country": "USD", "form_factor": "横白卡"},
            price_lines=[
                {"pattern": "卡图：{amount}={price}", "form_factor": "横白卡"},
                {"pattern": "横白卡图：{amount}={price}", "form_factor": "横白卡"},
                {"pattern": "{amount}={price}", "form_factor": None},
            ],
            restriction_lines=["^#"],
            section_lines=["^———"],
            skip_lines=["^\\s*$"],
        )

    def test_simple_price_line(self) -> None:
        tpl = self._make_apple_template()
        doc = parse_message_with_template("卡图：100=5.35", tpl)
        self.assertEqual(len(doc.rows), 1)
        self.assertEqual(doc.rows[0].card_type, "Apple")
        self.assertEqual(doc.rows[0].country_or_currency, "USD")
        self.assertEqual(doc.rows[0].amount_range, "100")
        self.assertEqual(doc.rows[0].price, 5.35)
        self.assertEqual(doc.rows[0].form_factor, "横白卡")
        self.assertEqual(len(doc.exceptions), 0)

    def test_multiline_with_restrictions(self) -> None:
        tpl = self._make_apple_template()
        text = "卡图：100/150=5.35\n卡图：200-450=5.38\n#250面值不拿\n#尾刀勿动"
        doc = parse_message_with_template(text, tpl)
        self.assertEqual(len(doc.rows), 2)
        self.assertEqual(len(doc.exceptions), 0)
        # 限制文字消息级共享
        self.assertIn("250面值不拿", doc.rows[0].restriction_text)
        self.assertIn("尾刀勿动", doc.rows[0].restriction_text)
        self.assertIn("250面值不拿", doc.rows[1].restriction_text)

    def test_unmatched_lines_are_silent(self) -> None:
        tpl = self._make_apple_template()
        text = "随便说句话\n卡图：100=5.35\n[左哼哼]"
        doc = parse_message_with_template(text, tpl)
        self.assertEqual(len(doc.rows), 1)
        self.assertEqual(len(doc.exceptions), 0)  # 不匹配的行静默跳过

    def test_empty_text(self) -> None:
        tpl = self._make_apple_template()
        doc = parse_message_with_template("", tpl)
        self.assertEqual(len(doc.rows), 0)
        self.assertEqual(len(doc.exceptions), 0)
```

**Step 2: Run test to verify failure**

**Step 3: Write minimal implementation**

```python
# bookkeeping_core/template_engine.py — 添加

import re as _re
from .models import ParsedTransaction  # 只引用 models，不引用旧解析器
from .quotes import (  # 引用数据类和 normalize 工具
    ParsedQuoteRow,
    ParsedQuoteDocument,
    ParsedQuoteException,
    PARSER_VERSION,
    normalize_quote_amount_range,
    normalize_quote_form_factor,
    normalize_quote_multiplier,
)


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
) -> ParsedQuoteDocument:
    lines = [line.strip() for line in text.splitlines()]
    message_restrictions: list[str] = []
    rows: list[ParsedQuoteRow] = []

    for line in lines:
        if not line:
            continue

        # 匹配限制行
        if _matches_any(line, template.restriction_lines):
            restriction = _re.sub(r"^#|^注[：:]", "", line).strip()
            if restriction:
                message_restrictions.append(restriction)
            continue

        # 匹配跳过行
        if _matches_any(line, template.skip_lines):
            continue

        # 匹配价格行
        matched = False
        for price_line in template.price_lines:
            pattern = price_line.get("pattern", "")
            variables = match_pattern(line, pattern)
            if variables is not None:
                amount = variables.get("amount", "不限")
                price_str = variables.get("price")
                if price_str is None:
                    continue
                try:
                    price = float(price_str)
                except ValueError:
                    continue

                card_type = template.defaults.get("card_type", "unknown") or "unknown"
                country = template.defaults.get("country", "") or ""
                form_factor = price_line.get("form_factor") or template.defaults.get("form_factor", "不限") or "不限"
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
                matched = True
                break  # 第一个匹配即停止

        # 匹配不到 → 静默跳过（不抛异常）

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
        exceptions=[],  # 永远为空——不匹配的行静默跳过
    )


def _matches_any(line: str, patterns: list[str]) -> bool:
    for pat in patterns:
        if _re.search(pat, line):
            return True
    return False
```

**Step 4: Run test to verify pass**
`PYTHONPATH='.' ./.venv/bin/python -m pytest tests/test_template_engine.py::ParseMessageTests -v`

**Step 5: Run all tests to check regressions**
`PYTHONPATH='.' ./.venv/bin/python -m pytest tests/test_template_engine.py -v`

**Step 6: Commit**

---

## Phase 2: 删除旧解析器

### Task 4: 删除旧解析函数

**Objective:** 删除 parse_quote_document 及其内部函数

**Files:**
- Modify: `bookkeeping_core/quotes.py` — 删除以下函数:
  - `parse_quote_document` (line ~707)
  - `_parse_sectioned_group_sheet` (line ~945)
  - `_parse_fixed_group_sheet` (line ~1175)
  - `_parse_price_segments` (line ~1371)
  - `_parse_single_segment` (line ~1430)
  - `_infer_template_key` (line ~1852)
  - 以及所有相关的辅助函数（`_split_segments`, `_normalize_segment`, `_looks_like_*`, `_extract_*`, `_infer_*` 等——仅解析相关、无外部引用的）

**保留:** normalize_* 工具函数、数据类（ParsedQuoteRow/Document/Exception）、QuoteCaptureService、PARSER_VERSION、别名列表

**验证:** 删除后运行 `PYTHONPATH='.' ./.venv/bin/python -c "from bookkeeping_core.quotes import QuoteCaptureService, normalize_quote_card_type"` 确认导入不报错

**Step 1: 备份当前 quotes.py** (git stash 或确认在 feature branch 上)

**Step 2: 删除函数** — 逐个删除，每删一个确认导入不报错

**Step 3: Commit**
```bash
git add bookkeeping_core/quotes.py
git commit -m "refactor: remove old regex-based quote parser (replaced by template engine)"
```

### Task 5: 重写 tests/test_quote_parser.py

**Objective:** 旧测试依赖已删除的 parse_quote_document，重写为测新模板引擎

**Files:**
- Modify: `tests/test_quote_parser.py` — 完全重写

**测试用例从旧版迁移并适配：**
- `test_complete_single_quote_parses_card_country_amount_and_price` → 用模板测 Apple MXN
- `test_section_quote_parses_condition_rows` → 用模板测 Xbox 分节格式
- `test_same_line_country_price_pairs_are_split` → 用模板测 Steam 多币种
- `test_modifier_lines_create_derived_form_factor_prices` → 用模板测修改器行

**Step 1: 重写测试文件**

**Step 2: Run test to verify pass**
`PYTHONPATH='.' ./.venv/bin/python -m pytest tests/test_quote_parser.py -v`

**Step 3: Commit**

---

## Phase 3: 集成到采集链路

### Task 6: 修改 QuoteCaptureService 使用模板引擎

**Objective:** capture_from_message 改为从 template_config 加载模板，调用新引擎

**Files:**
- Modify: `bookkeeping_core/quotes.py` — 修改 `QuoteCaptureService.capture_from_message`
- Modify: `bookkeeping_core/template_engine.py` — 导出 parse_message_with_template

**改动点（quotes.py ~line 490）:**
```python
# 旧代码:
parsed = parse_quote_document(...)

# 新代码:
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
    ...
)
```

**Step 1: Write failing test** — 修改 test_quotes.py 中 QuoteCaptureService 的测试

**Step 2: 实现改动**

**Step 3: 全量测试**
`PYTHONPATH='.' ./.venv/bin/python -m pytest tests/ -q`

**Step 4: Commit**

---

## Phase 4: 模板创建工具

### Task 7: auto_generate_template — 从真实消息自动生成模板

**Objective:** 输入一条真实报价消息，自动分析行结构并生成 TemplateConfig

**Files:**
- Modify: `bookkeeping_core/template_engine.py`
- Modify: `tests/test_template_engine.py`

**算法：**
1. 按行切分
2. 包含数字+分隔符（=：:）的行 → 候选价格行
3. 以 # 或注： 开头的行 → 候选限制行
4. 以 【 或分隔线 开头 → 候选分节行
5. 其他 → 候选跳过行
6. 价格行生成 pattern：数字 → {amount}/{price}，固定文字保留

**Step 1: Write failing test**

```python
class AutoGenerateTests(unittest.TestCase):
    def test_generates_from_real_message(self) -> None:
        text = "卡图：100/150=5.35\n卡图：200-450=5.38\n#250面值不拿"
        tpl = auto_generate_template(text, defaults={"card_type": "Apple", "country": "USD"})
        self.assertTrue(len(tpl.price_lines) >= 2)
        self.assertTrue(len(tpl.restriction_lines) >= 1)
        # 生成的模板应该能解析同一条消息
        doc = parse_message_with_template(text, tpl)
        self.assertEqual(len(doc.rows), 2)
```

**Step 2-4: TDD 循环**

**Step 5: Commit**

---

## Phase 5: REST API

### Task 8: 模板管理 API 端点

**Objective:** 提供 REST API 创建/查询/测试模板

**Files:**
- Modify: `bookkeeping_web/app.py` — 添加路由
- Modify: `bookkeeping_core/database.py` — 确认 template_config 读写方法存在

**端点：**
- `POST /api/quote-templates/generate` — 从样本消息生成模板
- `PUT /api/quote-templates/{group_key}` — 保存模板到群配置
- `GET /api/quote-templates/{group_key}` — 获取群的当前模板
- `POST /api/quote-templates/validate` — 用样本消息验证模板

**Step 1-4: TDD 循环（每个端点一个 TDD 循环）**

**Step 5: Commit**

---

## Phase 6: 数据清理 + 模板初始化

### Task 9: 清理历史数据 + 为现有群创建初始模板

**Objective:** 清理旧异常数据，用真实消息为 5 个群生成初始模板

**Steps:**
1. 清理 `quote_parse_exceptions` 中因旧逻辑产生的垃圾异常
2. 清理 `quote_price_rows` 中过长的 `restriction_text`（截断到 200 字符）
3. 为 4 个已有 group_profile 的群创建初始模板
4. 测试完整采集链路

**Step 5: Commit**

---

## 执行状态

| Task | 状态 |
|------|------|
| T1: match_pattern | ✓ 已完成 |
| T2: TemplateConfig | 待执行 |
| T3: parse_message_with_template | 待执行 |
| T4: 删除旧解析器 | 待执行 |
| T5: 重写 test_quote_parser | 待执行 |
| T6: 集成到 QuoteCaptureService | 待执行 |
| T7: auto_generate_template | 待执行 |
| T8: REST API | 待执行 |
| T9: 数据清理 + 模板初始化 | 待执行 |
