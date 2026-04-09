# 报价模板引擎 — 设计文档

> 日期：2026-04-10
> 状态：待用户确认

## 1. 问题

当前报价墙解析存在 4 个核心问题：

- **限制文字爆表**：section_restrictions 在整条消息中累积，所有行共享同一份大列表，报价墙 UI 无法阅读
- **国家/币种识别错误**：`_infer_country_or_currency` 用通用正则推断，被 default 覆盖，GBP/HKD 误判为 USD
- **异常噪音**：simple_sheet 逐行解析，非报价行全部抛异常，50 条异常大部分是垃圾
- **多格式兼容差**：通用解析器试图覆盖所有格式，实际覆盖不住

**根本矛盾**：我们试图写一个"万能解析器"去理解所有客人的报价格式，但每个客人的格式虽然**多样但固定**。
- 多样：不同客人用不同格式（`卡图：100=5.35` vs `100=5.35` vs `Apple US 100*5.35`）
- 固定：同一个客人的格式几乎不变（最多早晚班管理员不同）

## 2. 设计理念："机场广播" 模式

- **起飞点 / 终点 / 航线** = 固定结构（模板定义）
- **飞行时间 / 日期 / 票价** = 变量（每次消息中提取）

不再造万能解析器。每个群建立一个消息模板，固定文字做字面量锚点，变量部分做插槽提取。

## 3. 架构

```
                   ┌──────────────────────┐
                   │   QuoteCaptureService │
                   │   .capture_from_      │
                   │    message()          │
                   └──────────┬───────────┘
                              │
                    有模板？────┤
                   YES │      NO│
                       ▼        ▼
              ┌──────────┐   跳过（不采集）
              │ Template │
              │ Engine   │
              └────┬─────┘
                   │
          ┌────────┴────────┐
          │                 │
    match_pattern()   match_restriction()
          │                 │
    ┌─────┴─────┐     ┌────┴────┐
    │价格行匹配  │     │限制行匹配│
    │提取变量    │     │消息级累积│
    └─────┬─────┘     └────┬────┘
          │                 │
          └────────┬────────┘
                   │
            ParsedQuoteDocument
            (rows + exceptions)
```

### 组件

| 组件 | 职责 | 接口 |
|------|------|------|
| `TemplateConfig` | 模板定义数据类 | defaults, price_lines, restriction_lines, skip_lines |
| `match_pattern()` | 单行 pattern 匹配 + 变量提取 | `(line, pattern) -> dict\|None` |
| `parse_message_with_template()` | 完整消息解析 | `(text, template_config) -> ParsedQuoteDocument` |
| `auto_generate_template()` | 从真实消息自动生成模板 | `(sample_text) -> TemplateConfig` |
| `QuoteCaptureService` | 采集链路调度 | 有模板走新引擎，无模板跳过 |

## 4. 数据流

### 4.1 模板解析流

```
收到消息
  │
  ├─ 查找群模板 → 无模板则跳过（不采集）
  │
  ├─ 按换行切分为 lines[]
  │
  ├─ 逐行处理：
  │   ├─ 匹配 restriction_lines → 累积到 message_restrictions[]
  │   ├─ 匹配 skip_lines → 跳过（静默，不产生异常）
  │   ├─ 匹配 price_lines → 提取变量 → 生成 ParsedQuoteRow
  │   │   └─ 每个 row 附带 message_restrictions（消息级共享）
  │   └─ 匹配不到 → 静默跳过（不产生异常）
  │
  └─ 输出：ParsedQuoteDocument(rows=[], exceptions=[])
```

### 4.2 模板创建流（半自动）

```
用户粘贴一条真实消息
  │
  ├─ 系统逐行分析：
  │   ├─ 包含数字+分隔符的行 → 候选价格行
  │   ├─ 以 # 或注： 开头的行 → 候选限制行
  │   ├─ 以 【 或分隔线 开头 → 候选分节行
  │   └─ 其他 → 候选跳过行
  │
  ├─ 价格行自动生成 pattern：
  │   ├─ 数字序列 → {amount} 或 {price}
  │   ├─ 分隔符（:：=）保留为固定锚点
  │   ├─ 最后一个数字 = {price}，前面的 = {amount}
  │   └─ 前缀文本保留为固定锚点
  │
  ├─ 展示生成的模板给用户确认/调整
  │
  └─ 保存到 quote_group_profiles.template_config
```

## 5. 模板 Schema

```json
{
  "version": "tpl-v1",
  "defaults": {
    "card_type": "Apple",
    "country": "USD",
    "form_factor": "横白卡",
    "multiplier": null,
    "stale_after_minutes": 30
  },
  "price_lines": [
    {
      "pattern": "卡图：{amount}={price}",
      "form_factor": "横白卡"
    }
  ],
  "restriction_lines": ["^#", "^注：", "^注意", "^为避免"],
  "section_lines": ["^【", "^———", "^---"],
  "skip_lines": ["^\\s*$", "^[左中右]", "^[😀-🙏]"]
}
```

### 变量插槽

| 插槽 | 匹配内容 | 示例 |
|------|----------|------|
| `{amount}` | 面值/金额区间 | `100`、`100/150`、`200-450` |
| `{price}` | 价格/汇率 | `5.35` |
| `{country}` | 国家/币种覆盖 | `US`、`UK` |
| `{form_factor}` | 形态覆盖 | `代码`、`竖卡` |
| `{multiplier}` | 倍数 | `50倍` |

### 匹配规则

- 固定文字做**字面量匹配**（`卡图：` 必须完全一致）
- 变量插槽做**正则提取**（`{amount}` → `\d+(?:[.\-/ ]\d+)*`）
- 一行消息尝试所有 price_lines，第一个匹配成功即停止

## 6. 与现有系统的关系

| 现有组件 | 变化 |
|----------|------|
| `quote_group_profiles` 表 | `template_config` 字段存 JSON 模板 |
| `QuoteCaptureService` | 有模板走新引擎，无模板跳过 |
| `parse_quote_document` | **删除** — 被模板引擎替代 |
| `_parse_fixed_group_sheet` | **删除** |
| `_parse_sectioned_group_sheet` | **删除** |
| `_parse_price_segments` | **删除** |
| `normalize_*` 工具函数 | **保留** — 外部模块依赖 |
| `ParsedQuoteRow/Document/Exception` | **保留** — 数据结构不变 |
| `tests/test_quote_parser.py` | **重写** — 测新模板引擎 |

旧解析器已被调查确认为自包含（只在 quotes.py 内部调用，无外部依赖），可以安全删除。

## 7. 关键设计决策

### 7.1 为什么不保留 fallback？

- 开发环境，没有生产数据需要兼容
- 旧解析器全是正则驱动，问题多（限制累积、国家误判、异常噪音）
- 保留 fallback 会增加维护负担，且新旧逻辑混杂容易出错
- 无模板的群直接跳过采集，等模板创建后自然开始工作

### 7.2 限制文字为什么是消息级而不是行级？

一条消息中所有 `#` 开头的限制行对所有价格行有效（例如"40分钟赎回"适用于消息中所有报价）。逐行累积导致每个 row 的 restriction_text 包含大量重复和不相关内容。

### 7.3 为什么跳过行不抛异常？

报价消息中包含大量非报价内容（emoji、问候、广告）。如果每个非报价行都抛异常，异常区会变成垃圾场。静默跳过是正确行为——只有确实看起来像报价但解析失败的行才应该进异常。

## 8. 验收标准

- 新群创建模板后，消息解析准确率 > 95%
- 异常区条数减少 80%+（从 50 降到个位数）
- 限制列文字不超过 200 字符
- 模板创建时间 < 2 分钟（粘贴消息 → 自动生成 → 确认保存）
- 现有 5 个群全部迁移到新模板系统
