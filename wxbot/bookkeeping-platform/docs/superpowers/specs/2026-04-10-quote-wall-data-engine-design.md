# SeeSee 报价墙 MVP - 数据飞轮解析架构设计 (Data Engine Design)

## 1. 核心理念 (The First Principle)

放弃构建“万能解析器”或“高容错模板引擎”的幻想。人类的自然语言输入熵是无限的。
采用**“死板引擎 + 异常驱动进化 (Exception-Driven Evolution)”**架构：
1. **极简引擎**：解析器没有任何容错能力。模板长什么样，消息必须长什么样（差一个空格直接报错）。
2. **异常是养料**：解析失败的报价行直接掉入“异常区”。
3. **人工闭环 (Human-in-the-loop)**：业务员在异常区标注数据（“这里是价格，这里是国家”），系统自动将人工标注转化为该群的一条“绝对正确且死板”的新模板。
4. **数据飞轮**：随着日常运营，系统针对每个群的微小格式变体自动积累大量精确规则，解析率逼近 100%，而无需研发修改代码。

## 2. 架构组件

### 2.1 Strict Template Matcher (极简严格匹配器)
替换原有的复杂正则逻辑。
- 只有精确的字符串比对和基础的类型提取（如 `{price}` 必须是浮点数）。
- **无上下文推断**：不再尝试跨行推断（除了明确的 Section Header），如果一行不能独立解析且没有明确的 Section 继承，直接失败。
- **Fail Fast**：一旦不匹配当前群的现有严格模板集合，立即作为异常抛出。

### 2.2 Exception Repository (异常池)
- 保存所有匹配失败的候选报价行（排除掉纯文本聊天/表情后，带有数字和常见货币符号的行）。
- 记录来源群 (group_key)、原始文本、时间。

### 2.3 Automatic Template Generator (自动模板生成器)
核心魔法所在，依托于 `/api/quotes/exceptions/resolve` 接口。
- **输入**：业务员在 UI 上对某行异常文本的标注。例如：文本 `加拿大=3.4(代码批量问)`，标注 `加拿大`={country}, `3.4`={price}, `(代码批量问)`={restriction}。
- **处理**：系统将非标注部分视为**严格的字面量锚点**（如 `=`）。
- **输出**：生成一条新的 strict template pattern：`{country}={price}{restriction}`，并自动追加到该群的 `template_config` 中。

## 3. 数据结构设计

### 3.1 模板存储 (QuoteGroupProfile.template_config)
以 JSON 格式存储于数据库，结构扁平化，去中心化。
```json
{
  "version": "data-engine-v1",
  "rules": [
    {
      "pattern": "【{card_type}】",
      "type": "section"
    },
    {
      "pattern": "{country} {currency} {amount}={price}",
      "type": "price"
    },
    {
      "pattern": "{country}={price}({restriction})",
      "type": "price"
    }
  ]
}
```

### 3.2 异常解析接口 API
`POST /api/quotes/exceptions/resolve`
```json
// Request Payload (业务员在 UI 上的标注结果)
{
  "exception_id": 12345,
  "source_group_key": "C-531-万诺",
  "raw_text": "加拿大=3.4(代码批量问)",
  "annotations": [
    {"type": "country", "value": "加拿大", "start": 0, "end": 3},
    {"type": "price", "value": "3.4", "start": 4, "end": 7},
    {"type": "restriction", "value": "(代码批量问)", "start": 7, "end": 14}
  ]
}
```

## 4. 业务工作流 (MVP 实施路径)

1. **初始化**：为 2-3 个核心测试群（如 C-531, C-512）手动配置 3-5 条最基础的严格规则。
2. **上线运行**：系统开始抓取。大量变体格式（多空格、少符号）会解析失败，落入异常区。
3. **闭环训练**：运营人员每天花几分钟在异常区通过 UI 纠正（MVP 阶段可通过 API 脚本模拟 UI 操作注入标注）。
4. **飞轮效应**：规则库自动扩充，该群的解析成功率迅速攀升。

## 5. 验收标准
1. `template_engine.py` 代码大幅简化，移除所有模糊匹配和猜测逻辑。
2. 能够接受人工标注的 JSON Payload，并准确生成针对该原始文本的 strict pattern，保存至群配置。
3. 新生成的 pattern 能够成功解析同群相同格式的后续报价。
