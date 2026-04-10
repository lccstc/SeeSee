# 异常区改造设计

## 问题
当前异常区逐行存储和展示未匹配行，同一条消息产生 16-19 条碎片异常。违背"数据飞轮"初衷——运营人员应该看到完整消息原文，一次性创建模板或忽略。

## 设计目标
- 异常区按**消息**分组，每条消息一个卡片
- 卡片显示完整原文，可折叠
- 操作（标注模板/忽略）是消息级，不是行级
- 标注时在完整原文上下文中逐行标注字段

## 改动范围

### 1. Template Engine 层（核心改动）

**文件**: `bookkeeping_core/template_engine.py`

当前逻辑（第168-183行）：
```python
if not matched and has_digits.search(line):
    exceptions.append(ParsedQuoteException(...source_line=line...))
```

改为：收集未匹配行，函数末尾合并为一条消息级异常。

新逻辑：
- 收集所有 unmatched_lines（含数字的未匹配行）
- 函数末尾，如果有 unmatched_lines，生成一条 ParsedQuoteException：
  - `source_line` = 所有未匹配行用 `\n` 拼接
  - `raw_text` = 完整消息原文（不变）
  - `reason` = `strict_match_failed`
- 如果没有未匹配行，不产生异常

同时：如果**整条消息**一条行都没匹配成功（rows 为空），也产生一条消息级异常。这和上面的逻辑一致——只是 rows 为空时 unmatched_lines 就是全部含数字的行。

**特殊情况**：模板匹配了部分行（比如影子段匹配了，雷蛇段没匹配）。此时：
- matched rows 正常上墙
- unmatched lines 合并为一条异常
- 异常的 `source_line` 只包含未匹配的行
- `raw_text` 仍然保留完整原文供参考

### 2. 数据库层（无需改动）

表结构不变。`source_line` 从"一行文本"变为"多行文本用换行拼接"。`raw_text` 不变。字段类型都是 TEXT，兼容。

### 3. API 层（无需改动）

`/api/quotes/exceptions` 返回格式不变，只是 `source_line` 字段内容变长了。

### 4. UI 层（重点改动）

**文件**: `bookkeeping_web/pages.py`

#### 异常区列表改造

当前：表格，每行一个异常，显示 `source_line`（单行）
改为：卡片列表，每个异常一张卡片

卡片内容：
- 标题行：群名 | 发送者 | 时间
- 原文区域：完整 `raw_text`，默认折叠，点击展开
- 未匹配行：`source_line`（多行），用高亮背景显示（这些是模板没覆盖到的）
- 操作按钮：[标注模板] [附加限制] [忽略]

#### 标注流程改造

当前：点击"标注"→ 弹窗显示单行 `source_line` → 填写 5 个字段 → 提交
改为：点击"标注模板"→ 弹窗显示完整 `raw_text`，每行可点击 → 
  - 点击某一行 → 弹出标注表单（卡种/国家/面额/形态/价格）
  - 标注完一行后，该行高亮标记为"已标注"
  - 可连续标注多行
  - 最后点"生成模板"→ 自动为该群创建模板规则

标注表单复用现有的 `generate_strict_pattern_from_annotations` + `build_annotations_from_fields` 逻辑。

### 5. 标注Web UI 复用

现有标注界面（在异常行上标注字段位置）已有基础组件。需要：
- 将弹窗从"显示单行"改为"显示完整原文 + 可点击选择行"
- 添加多行标注状态管理（已标注/未标注）
- 添加"生成模板"按钮，汇总所有标注生成群模板

## 数据流

```
WhatsApp消息
  → template_engine.parse_message_with_template()
  → 部分行匹配 → rows: [matched rows]
  → 部分行不匹配 → collect unmatched_lines
  → 返回 ParsedQuoteDocument:
      rows = [matched rows]  # 上墙
      exceptions = [1条消息级异常]  # 异常区
        source_line = "行A\n行B\n行C"  # 未匹配行
        raw_text = "完整原文"  # 含已匹配和未匹配
  → quotes.py 存储
  → API 返回
  → UI 展示为卡片
  → 用户标注 → 生成模板规则
  → 下次同类消息自动匹配 → 数据飞轮
```

## 测试计划

1. 单元测试：template_engine 返回的消息级异常包含正确的 source_line（多行拼接）
2. 单元测试：部分匹配场景（有的行匹配，有的不匹配），异常只包含未匹配行
3. 单元测试：完全匹配的消息不产生异常
4. Web 测试：异常区卡片显示完整原文
5. Web 测试：标注流程可连续标注多行并生成模板
6. 集成测试：标注生成的模板能正确解析同类消息
