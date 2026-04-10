# 异常行标注 UI 设计

## 目标

在报价墙异常区给每条异常行加"标注"按钮，弹窗填写字段值，提交后自动生成 strict template 并存入该群配置。跑通"异常→标注→模板→解析"的完整闭环。

## 交互流程

```
异常列表 → [标注]按钮 → 弹窗（只读原文+5个输入框）→ 用户填写 → 实时预览pattern → 提交 → 存库 → 列表刷新
```

## 弹窗 UI

```
┌─────────────────────────────────────┐
│  标注异常行                           │
├─────────────────────────────────────┤
│  原文：加拿大=3.4(代码批量问)           │
│                                     │
│  卡种    [          ]               │
│  国家    [          ]               │
│  面额    [          ]               │
│  形态    [          ]               │
│  价格    [          ]               │
│                                     │
│  预览: {country}={price}{restriction} │
│                                     │
│        [取消]  [确认并保存]            │
└─────────────────────────────────────┘
```

- 原文只读展示
- 5 个字段中文标签，空值不参与 pattern
- 前端实时预览生成的 pattern
- 尾部 `(...)` 自动追加为 `{restriction}`，用户不需要填

## 字段映射

| 中文标签 | 内部参数名 | 说明 |
|---------|-----------|------|
| 卡种 | card_type | 通常在 section 行 `【XBOX】` 中继承 |
| 国家 | country | 加拿大、美国、英国等 |
| 面额 | amount | 10-1000、50-500 等数字区间 |
| 形态 | form_factor | 实卡/代码，默认"不限" |
| 价格 | price | 3.4、5.2 等浮点数 |

## 提交逻辑

### 前端

1. 用户填写字段值（空字段留空）
2. 实时预览：非空字段按原文中出现顺序拼成 pattern，字段用 `{name}` 替换，字段间原文作为字面量
3. 点击"确认并保存" → POST `/api/quotes/exceptions/resolve`

### 后端提交流程

1. 接收 `{ exception_id, resolution_status: "annotate", fields: {card_type, country, amount, form_factor, price} }`
2. 从数据库取 exception 的 source_line
3. 过滤掉空值字段
4. 在 source_line 中查找每个值的位置（`str.find`）
5. 按位置排序，构造 annotations 数组
6. 如果 source_line 尾部有 `(...)` 且用户没填 restriction，自动追加 `{restriction}` 到 pattern
7. 调用 `generate_strict_pattern_from_annotations` 生成 pattern
8. `append_rule_to_group_profile` 存入群配置
9. `resolve_quote_exception` 标记已解决
10. 返回 `{ updated, new_pattern }`

### restriction 自动处理

- 检测 source_line 是否以 `(...)` 结尾
- 如果是，在 pattern 中对应位置替换为 `{restriction}`
- 用户不需要填 restriction 字段
- 没有 `(...)` 尾部则正常处理，不追加

## API 变更

### 修改已有端点

`POST /api/quotes/exceptions/resolve`

新增 `resolution_status: "annotate"` 的处理逻辑，payload 格式：

```json
{
  "exception_id": 12345,
  "resolution_status": "annotate",
  "fields": {
    "country": "加拿大",
    "price": "3.4"
  }
}
```

`fields` 中只传非空字段。后端根据 values 在 source_line 中定位，不需要前端传 start/end。

## 前端改动

在 `bookkeeping_web/pages.py` 的异常区部分：

1. 异常表格每行增加"标注"按钮
2. 新增弹窗 HTML（modal）
3. 新增 JS 逻辑：
   - 打开弹窗时填充 source_line
   - 输入框变化时实时计算 pattern 预览
   - 提交时 POST resolve API
   - 成功后刷新异常列表

预估改动量：~120 行 HTML+JS（嵌入 pages.py 现有模板中）

## 验收标准

1. 异常列表有"标注"按钮，点击弹出弹窗
2. 弹窗显示只读原文 + 5 个中文标签输入框
3. 输入值后实时预览 pattern
4. 提交后群配置中新增对应 rule
5. 后续相同格式的报价行不再落入异常区
