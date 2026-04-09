# Quote Wall Data Engine MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform the quote parsing system from a complex, error-prone regex matching system to a "Data Engine" where a strict, zero-tolerance template engine fails fast, and exceptions are used to auto-generate new strict templates via human annotation.

**Architecture:** 
1. `template_engine.py` is stripped of heuristic logic and uses strict literal+variable matching.
2. Unmatched lines with digits/prices fall into the exceptions pool.
3. The `/api/quotes/exceptions/resolve` endpoint receives user annotations for a failed line, auto-generates a strict `{variable}literal` pattern, and appends it to the group's `template_config` in the DB.

**Tech Stack:** Python, PostgreSQL, Flask (WSGI)

---

### Task 1: Refactor TemplateConfig Schema

**Files:**
- Modify: `bookkeeping_core/template_engine.py`
- Test: `tests/test_template_engine.py`

- [ ] **Step 1: Write the failing test**

```python
def test_template_config_schema_data_engine():
    from bookkeeping_core.template_engine import TemplateConfig
    raw = '''{
        "version": "data-engine-v1",
        "rules": [
            {"pattern": "【{card_type}】", "type": "section"},
            {"pattern": "{country}={price}({restriction})", "type": "price"}
        ]
    }'''
    config = TemplateConfig.from_json(raw)
    assert config.version == "data-engine-v1"
    assert len(config.rules) == 2
    assert config.rules[0]["type"] == "section"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_template_engine.py::test_template_config_schema_data_engine -v`
Expected: FAIL with missing `rules` attribute or similar error.

- [ ] **Step 3: Write minimal implementation**

```python
import json
from dataclasses import dataclass, field

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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_template_engine.py::test_template_config_schema_data_engine -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add bookkeeping_core/template_engine.py tests/test_template_engine.py
git commit -m "feat(template_engine): update TemplateConfig for data-engine-v1 schema"
```

### Task 2: Implement Strict Template Matcher

**Files:**
- Modify: `bookkeeping_core/template_engine.py`
- Modify: `tests/test_template_engine.py`

- [ ] **Step 1: Write the failing test**

```python
def test_strict_match_pattern():
    from bookkeeping_core.template_engine import match_pattern
    
    pattern = "{country}={price}({restriction})"
    # Exact match
    res = match_pattern("加拿大=3.4(代码批量问)", pattern)
    assert res == {"country": "加拿大", "price": "3.4", "restriction": "代码批量问"}
    
    # Failing match due to extra space
    res2 = match_pattern("加拿大 = 3.4(代码批量问)", pattern)
    assert res2 is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_template_engine.py::test_strict_match_pattern -v`
Expected: FAIL because `match_pattern` might allow spaces or fail differently.

- [ ] **Step 3: Write minimal implementation**

```python
import re

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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_template_engine.py::test_strict_match_pattern -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add bookkeeping_core/template_engine.py tests/test_template_engine.py
git commit -m "feat(template_engine): implement strict match_pattern"
```

### Task 3: Rewrite parse_message_with_template

**Files:**
- Modify: `bookkeeping_core/template_engine.py`
- Modify: `tests/test_template_engine.py`

- [ ] **Step 1: Write the failing test**

```python
def test_parse_message_strict():
    from bookkeeping_core.template_engine import TemplateConfig, parse_message_with_template
    
    text = "【XBOX】\n加拿大=3.4(代码批量问)\n10-1000=5.2\n未知格式=1.0"
    config = TemplateConfig(
        version="data-engine-v1",
        rules=[
            {"pattern": "【{card_type}】", "type": "section"},
            {"pattern": "{country}={price}({restriction})", "type": "price"},
            {"pattern": "{amount}={price}", "type": "price"}
        ]
    )
    
    doc = parse_message_with_template(text, config, source_group_key="G1")
    assert len(doc.rows) == 2
    assert doc.rows[0].country_or_currency == "加拿大"
    assert doc.rows[0].price == 3.4
    assert doc.rows[0].card_type == "XBOX"
    
    assert doc.rows[1].amount_range == "10-1000"
    assert doc.rows[1].price == 5.2
    assert doc.rows[1].card_type == "XBOX"
    
    assert len(doc.exceptions) == 1
    assert doc.exceptions[0].source_line == "未知格式=1.0"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_template_engine.py::test_parse_message_strict -v`
Expected: FAIL due to missing logic for the new rules list.

- [ ] **Step 3: Write minimal implementation**

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_template_engine.py::test_parse_message_strict -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add bookkeeping_core/template_engine.py
git commit -m "feat(template_engine): rewrite parse_message_with_template for strict rules"
```

### Task 4: Implement Auto-Generation Logic

**Files:**
- Modify: `bookkeeping_core/template_engine.py`
- Test: `tests/test_template_engine.py`

- [ ] **Step 1: Write the failing test**

```python
def test_generate_strict_pattern():
    from bookkeeping_core.template_engine import generate_strict_pattern_from_annotations
    
    line = "加拿大=3.4(代码批量问)"
    annotations = [
        {"type": "country", "value": "加拿大", "start": 0, "end": 3},
        {"type": "price", "value": "3.4", "start": 4, "end": 7},
        {"type": "restriction", "value": "代码批量问", "start": 8, "end": 13}
    ]
    pattern = generate_strict_pattern_from_annotations(line, annotations)
    assert pattern == "{country}={price}({restriction})"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_template_engine.py::test_generate_strict_pattern -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_template_engine.py::test_generate_strict_pattern -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add bookkeeping_core/template_engine.py tests/test_template_engine.py
git commit -m "feat(template_engine): implement generate_strict_pattern_from_annotations"
```

### Task 5: Database method to append rule

**Files:**
- Modify: `bookkeeping_core/database.py`

- [ ] **Step 1: Write the minimal implementation**

```python
    def append_rule_to_group_profile(self, *, platform: str, chat_id: str, new_rule: dict) -> bool:
        row = self.get_quote_group_profile(platform=platform, chat_id=chat_id)
        if not row:
            return False
        
        import json
        from .template_engine import TemplateConfig
        
        raw_config = str(row.get("template_config") or "")
        try:
            config = TemplateConfig.from_json(raw_config) if raw_config.strip() else TemplateConfig()
        except ValueError:
            config = TemplateConfig()
            
        config.rules.append(new_rule)
        
        self.conn.execute(
            """
            UPDATE quote_group_profiles 
            SET template_config = ?, updated_at = CURRENT_TIMESTAMP
            WHERE platform = ? AND chat_id = ?
            """,
            (config.to_json(), platform, chat_id)
        )
        self.conn.commit()
        return True
```

- [ ] **Step 2: Commit**

```bash
git add bookkeeping_core/database.py
git commit -m "feat(database): add append_rule_to_group_profile method"
```

### Task 6: API Endpoint for Annotation Resolution

**Files:**
- Modify: `bookkeeping_web/app.py`

- [ ] **Step 1: Write the implementation in `_handle_quotes_exception_resolve`**

```python
# Replace _handle_quotes_exception_resolve in bookkeeping_web/app.py:
def _handle_quotes_exception_resolve(db: BookkeepingDB, start_response, environ):
    import json
    from bookkeeping_core.template_engine import generate_strict_pattern_from_annotations
    try:
        payload = _read_json_body(environ)
        exception_id = int(payload["exception_id"])
        
        # New resolution mode: "annotate"
        resolution_status = str(payload.get("resolution_status") or "ignored").strip()
        if resolution_status == "annotate":
            annotations = payload.get("annotations", [])
            exc_row = db.get_quote_exception(exception_id=exception_id)
            if not exc_row:
                return _respond_json(start_response, 404, {"error": "exception not found"})
                
            source_line = str(exc_row["source_line"])
            platform = str(exc_row["platform"])
            chat_id = str(exc_row["chat_id"])
            
            # Generate new strict pattern
            pattern = generate_strict_pattern_from_annotations(source_line, annotations)
            new_rule = {"pattern": pattern, "type": "price"}
            
            # Append rule to DB
            db.append_rule_to_group_profile(platform=platform, chat_id=chat_id, new_rule=new_rule)
            
            # Mark exception as resolved
            updated = db.resolve_quote_exception(
                exception_id=exception_id,
                resolution_status="resolved",
                resolution_note=f"auto-generated strict rule: {pattern}"
            )
            return _respond_json(start_response, 200, {"updated": updated, "new_pattern": pattern})
            
        if resolution_status == "attached":
            result = db.attach_quote_exception_to_restrictions(
                exception_id=exception_id,
            )
            return _respond_json(start_response, 200, result)
        if resolution_status not in {"ignored", "resolved", "open"}:
            raise ValueError("resolution_status must be ignored, resolved, attached, annotate, or open")
        updated = db.resolve_quote_exception(
            exception_id=exception_id,
            resolution_status=resolution_status,
            resolution_note=str(payload.get("resolution_note") or ""),
        )
    except (KeyError, TypeError, ValueError) as exc:
        return _respond_json(start_response, 400, {"error": f"Bad payload: {exc}"})
    return _respond_json(start_response, 200, {"updated": updated})
```

- [ ] **Step 2: Commit**

```bash
git add bookkeeping_web/app.py
git commit -m "feat(api): handle annotate resolution mode to auto-generate strict templates"
```
