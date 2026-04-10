# 异常行标注 UI 实现计划

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** 在报价墙异常区加"标注"按钮，弹窗填写 5 个字段（卡种/国家/面额/形态/价格），提交后自动生成 strict template 并存入群配置，跑通异常→标注→模板→解析的完整闭环。

**Architecture:**
- 前端：pages.py 异常列表加"标注"按钮 + 复用已有 modal 样式的弹窗 + JS 交互逻辑
- 后端：修改 `_handle_quotes_exception_resolve` 的 annotate 分支，接收 fields 而非 annotations，后端自动计算位置
- 新增后端函数：`build_annotations_from_fields(source_line, fields)` 将字段值转为带位置的 annotations

**Tech Stack:** Python, Flask (WSGI), vanilla JS (嵌入 pages.py)

---

### Task 1: 后端 — build_annotations_from_fields 函数

**Objective:** 实现将字段值映射为带 start/end 位置的 annotations 数组的核心逻辑

**Files:**
- Modify: `bookkeeping_core/template_engine.py`
- Test: `tests/test_template_engine.py`

**Step 1: Write failing test**

```python
def test_build_annotations_from_fields(self):
    from bookkeeping_core.template_engine import build_annotations_from_fields
    line = "加拿大=3.4(代码批量问)"
    fields = {"country": "加拿大", "price": "3.4"}
    anns = build_annotations_from_fields(line, fields)
    self.assertEqual(len(anns), 2)
    self.assertEqual(anns[0], {"type": "country", "value": "加拿大", "start": 0, "end": 3})
    self.assertEqual(anns[1], {"type": "price", "value": "3.4", "start": 4, "end": 7})
```

**Step 2: Run test to verify failure**

```bash
cd /Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform && PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_template_engine.TestBuildAnnotations -v
```
Expected: FAIL — function not found

**Step 3: Write minimal implementation**

在 `template_engine.py` 末尾添加：

```python
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
```

**Step 4: Run test to verify pass**

```bash
cd /Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform && PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_template_engine.TestBuildAnnotations -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add bookkeeping_core/template_engine.py tests/test_template_engine.py
git commit -m "feat(template_engine): add build_annotations_from_fields"
```

---

### Task 2: 后端 — 修改 annotate 分支接收 fields

**Objective:** 修改 `_handle_quotes_exception_resolve` 的 annotate 分支，接收 fields 字典而非预计算的 annotations

**Files:**
- Modify: `bookkeeping_web/app.py` (L604-629)

**Step 1: 修改 app.py annotate 分支**

将现有的：
```python
if resolution_status == "annotate":
    annotations = payload.get("annotations", [])
    exc_row = db.get_quote_exception(exception_id=exception_id)
    ...
```

替换为：
```python
if resolution_status == "annotate":
    fields = payload.get("fields", {})
    if not fields:
        return _respond_json(start_response, 400, {"error": "fields is required for annotate"})
    exc_row = db.get_quote_exception(exception_id=exception_id)
    if not exc_row:
        return _respond_json(start_response, 404, {"error": "exception not found"})

    source_line = str(exc_row["source_line"])
    platform = str(exc_row["platform"])
    chat_id = str(exc_row["chat_id"])

    # 构建 annotations
    from bookkeeping_core.template_engine import build_annotations_from_fields, generate_strict_pattern_from_annotations
    annotations = build_annotations_from_fields(source_line, fields)

    # 尾部 (...) 自动追加 restriction
    import re as _re
    restriction_match = _re.search(r'\([^)]*\)\s*$', source_line)
    if restriction_match and "restriction" not in fields:
        ann_start = restriction_match.start()
        annotations.append({
            "type": "restriction",
            "value": source_line[ann_start:],
            "start": ann_start,
            "end": len(source_line),
        })
        annotations.sort(key=lambda a: a["start"])

    pattern = generate_strict_pattern_from_annotations(source_line, annotations)
    new_rule = {"pattern": pattern, "type": "price"}

    db.append_rule_to_group_profile(platform=platform, chat_id=chat_id, new_rule=new_rule)

    updated = db.resolve_quote_exception(
        exception_id=exception_id,
        resolution_status="resolved",
        resolution_note=f"auto-generated strict rule: {pattern}"
    )
    return _respond_json(start_response, 200, {"updated": updated, "new_pattern": pattern})
```

**Step 2: Commit**

```bash
git add bookkeeping_web/app.py
git commit -m "feat(api): annotate endpoint accepts fields dict with auto restriction"
```

---

### Task 3: 后端测试 — 集成测试 annotate 流程

**Objective:** 测试从 fields 提交到 pattern 生成的完整后端链路

**Files:**
- Test: `tests/test_template_engine.py`

**Step 1: Write test**

```python
def test_annotate_end_to_end(self):
    """模拟完整标注流程：fields → annotations → pattern → 能匹配原始行"""
    from bookkeeping_core.template_engine import (
        build_annotations_from_fields,
        generate_strict_pattern_from_annotations,
        match_pattern,
    )
    line = "加拿大=3.4(代码批量问)"
    fields = {"country": "加拿大", "price": "3.4"}

    annotations = build_annotations_from_fields(line, fields)
    pattern = generate_strict_pattern_from_annotations(line, annotations)

    # 尾部 restriction 自动追加
    import re as _re
    restriction_match = _re.search(r'\([^)]*\)\s*$', line)
    if restriction_match and "restriction" not in fields:
        ann_start = restriction_match.start()
        annotations.append({
            "type": "restriction",
            "value": line[ann_start:],
            "start": ann_start,
            "end": len(line),
        })
        annotations.sort(key=lambda a: a["start"])
        pattern = generate_strict_pattern_from_annotations(line, annotations)

    self.assertIn("{restriction}", pattern)
    result = match_pattern(line, pattern)
    self.assertIsNotNone(result)
    self.assertEqual(result["country"], "加拿大")
    self.assertEqual(result["price"], "3.4")
```

**Step 2: Run test**

```bash
cd /Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform && PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_template_engine.TestBuildAnnotations.test_annotate_end_to_end -v
```
Expected: PASS

**Step 3: Commit**

```bash
git add tests/test_template_engine.py
git commit -m "test: add end-to-end annotate flow test"
```

---

### Task 4: 前端 — 异常列表加"标注"按钮

**Objective:** 在每行异常的操作列中加一个"标注"按钮

**Files:**
- Modify: `bookkeeping_web/pages.py` — `quoteExceptionActions()` 函数 (L1101-1116)

**Step 1: 修改 quoteExceptionActions**

在 `actions.push(...)` 区域，"一键建模板"按钮之后加：

```javascript
actions.push(`<button type="button" data-quote-exception-annotate="${row.id}">标注</button>`);
```

**Step 2: Commit**

```bash
git add bookkeeping_web/pages.py
git commit -m "feat(web): add annotate button to exception rows"
```

---

### Task 5: 前端 — 标注弹窗 HTML

**Objective:** 在 pages.py 模板中添加标注弹窗的 HTML 结构

**Files:**
- Modify: `bookkeeping_web/pages.py` — 在 `quote-ranking-modal` 之后添加 modal HTML

**Step 1: 添加弹窗 HTML**

在 `quote-ranking-modal` div 之后（约 L963）、script 标签之前添加：

```html
<div class="quote-modal-backdrop" id="quote-annotate-modal" aria-hidden="true">
  <div class="quote-modal" role="dialog" aria-modal="true">
    <div class="quote-modal-header">
      <div><h2>标注异常行</h2></div>
      <button class="quote-modal-close" type="button" id="quote-annotate-close">关闭</button>
    </div>
    <div style="padding: 12px 0;">
      <div class="muted" style="margin-bottom:8px;">原文</div>
      <div id="quote-annotate-source" style="background:#f5f5f5;padding:8px;border-radius:4px;font-family:monospace;word-break:break-all;"></div>
      <form id="quote-annotate-form" style="margin-top:12px;display:flex;flex-direction:column;gap:8px;">
        <input type="hidden" name="exception_id" value="">
        <label>卡种 <input type="text" name="card_type" placeholder="如：XBOX、FT"></label>
        <label>国家 <input type="text" name="country" placeholder="如：加拿大、美国"></label>
        <label>面额 <input type="text" name="amount" placeholder="如：10-1000"></label>
        <label>形态 <input type="text" name="form_factor" placeholder="如：实卡、代码"></label>
        <label>价格 <input type="text" name="price" placeholder="如：3.4"></label>
      </form>
      <div class="muted" style="margin-top:8px;">预览 pattern</div>
      <div id="quote-annotate-preview" style="font-family:monospace;color:#0a0;"></div>
    </div>
    <div style="display:flex;gap:8px;justify-content:flex-end;">
      <button type="button" id="quote-annotate-cancel">取消</button>
      <button type="button" id="quote-annotate-submit" style="font-weight:bold;">确认并保存</button>
    </div>
  </div>
</div>
```

**Step 2: Commit**

```bash
git add bookkeeping_web/pages.py
git commit -m "feat(web): add annotate modal HTML"
```

---

### Task 6: 前端 — 标注弹窗 JS 逻辑

**Objective:** 实现弹窗打开、pattern 预览、提交的完整 JS 交互

**Files:**
- Modify: `bookkeeping_web/pages.py` — script 部分，在 `bindQuoteExceptionButtons()` 函数末尾或之后添加

**Step 1: 在 bindQuoteExceptionButtons() 中绑定标注按钮**

在 `bindQuoteExceptionButtons()` 函数末尾（L1455 附近）添加：

```javascript
  document.querySelectorAll('[data-quote-exception-annotate]').forEach((button) => {
    button.addEventListener('click', () => {
      const row = allQuoteExceptions.find((item) => String(item.id) === String(button.dataset.quoteExceptionAnnotate));
      if (row) openAnnotateModal(row);
    });
  });
```

**Step 2: 添加弹窗交互函数**

在 `bindQuoteExceptionButtons()` 之后添加：

```javascript
function openAnnotateModal(row) {
  const modal = document.querySelector('#quote-annotate-modal');
  const form = document.querySelector('#quote-annotate-form');
  form.reset();
  form.exception_id.value = row.id;
  document.querySelector('#quote-annotate-source').textContent = row.source_line || '';
  updateAnnotatePreview();
  modal.setAttribute('aria-hidden', 'false');
}

function closeAnnotateModal() {
  document.querySelector('#quote-annotate-modal').setAttribute('aria-hidden', 'true');
}

function updateAnnotatePreview() {
  const form = document.querySelector('#quote-annotate-form');
  const source = document.querySelector('#quote-annotate-source').textContent;
  const fields = {
    card_type: form.card_type.value.trim(),
    country: form.country.value.trim(),
    amount: form.amount.value.trim(),
    form_factor: form.form_factor.value.trim(),
    price: form.price.value.trim(),
  };
  const parts = [];
  const items = Object.entries(fields).filter(([, v]) => v);
  items.sort((a, b) => {
    const ia = source.indexOf(a[1]);
    const ib = source.indexOf(b[1]);
    if (ia === -1 || ib === -1) return 0;
    return ia - ib;
  });
  let lastEnd = 0;
  for (const [name, value] of items) {
    const idx = source.indexOf(value, lastEnd);
    if (idx === -1) continue;
    if (idx > lastEnd) {
      parts.push(source.slice(lastEnd, idx));
    }
    parts.push('{' + name + '}');
    lastEnd = idx + value.length;
  }
  if (lastEnd < source.length) {
    const tail = source.slice(lastEnd);
    if (/\([^)]*\)\s*$/.test(tail)) {
      parts.push('{restriction}');
    } else {
      parts.push(tail);
    }
  }
  document.querySelector('#quote-annotate-preview').textContent = parts.join('') || '（填写字段后预览）';
}

document.querySelector('#quote-annotate-close').addEventListener('click', closeAnnotateModal);
document.querySelector('#quote-annotate-cancel').addEventListener('click', closeAnnotateModal);
document.querySelector('#quote-annotate-form').addEventListener('input', updateAnnotatePreview);

document.querySelector('#quote-annotate-submit').addEventListener('click', async () => {
  const form = document.querySelector('#quote-annotate-form');
  const fields = {};
  if (form.card_type.value.trim()) fields.card_type = form.card_type.value.trim();
  if (form.country.value.trim()) fields.country = form.country.value.trim();
  if (form.amount.value.trim()) fields.amount = form.amount.value.trim();
  if (form.form_factor.value.trim()) fields.form_factor = form.form_factor.value.trim();
  if (form.price.value.trim()) fields.price = form.price.value.trim();
  if (Object.keys(fields).length === 0) {
    alert('至少填写一个字段');
    return;
  }
  const response = await fetch('/api/quotes/exceptions/resolve', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      exception_id: Number(form.exception_id.value),
      resolution_status: 'annotate',
      fields: fields,
    }),
  });
  const payload = await response.json();
  if (payload.error) {
    alert(`标注失败：${payload.error}`);
    return;
  }
  closeAnnotateModal();
  await loadQuotesData();
});
```

**Step 3: Run existing tests to verify no regression**

```bash
cd /Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform && PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_template_engine -v
```
Expected: All PASS

**Step 4: Commit**

```bash
git add bookkeeping_web/pages.py
git commit -m "feat(web): add annotate modal JS — open, preview, submit"
```

---

### Task 7: 端到端验证

**Objective:** 手动启动服务，验证完整标注流程

**Step 1: 启动服务**

```bash
cd /Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform
BOOKKEEPING_CORE_TOKEN='test-token-123456' \
BOOKKEEPING_DB_DSN='postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping' \
BOOKKEEPING_MASTER_USERS='+84389225210' \
QUOTE_ADMIN_PASSWORD='119110' \
PYTHONPATH='.' ./.venv/bin/python reporting_server.py --host 127.0.0.1 --port 8765
```

**Step 2: 打开浏览器访问异常区**

访问 `http://127.0.0.1:8765/`，滚动到异常区，确认每行有"标注"按钮。

**Step 3: 测试标注流程**

1. 点击某行"标注"按钮 → 弹窗打开，显示原文
2. 填写 1-2 个字段 → 预览实时更新
3. 点击"确认并保存" → 弹窗关闭，列表刷新
4. 验证：该异常行状态变为"已处理"
5. 验证：该群的 template_config 中新增了对应 rule

**Step 4: Commit（如有修复）**

```bash
git add -A
git commit -m "fix: end-to-end annotation flow adjustments"
```
