# Unified Bookkeeping Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Superseded note (2026-03-22):** `/api/sync/events` 已在 P2.7 从当前支持接口面退役。本文中凡是要求继续保留或验证该在线接口的描述，均只作为历史实现背景，不再作为现行执行指令。

**Goal:** 把正式运行时收敛为 `Adapter -> Python Unified Bookkeeping Core -> Unified Ledger DB`，先立统一 runtime 边界，再逐步切换 WeChat 与 WhatsApp。

**Architecture:** 以 Python `bookkeeping_core` 作为唯一业务内核，新增统一入站 `NormalizedMessageEnvelope` 与统一出站 `CoreAction[]`。适配层只做平台字段归一化与动作执行；旧 `/api/sync/events` 已在 P2.7 退役，不再作为当前在线接口。

**Tech Stack:** Python 3 + sqlite/postgres compatibility + WSGI web app + TypeScript/Node + Baileys + wxautox

---

## 0. 计划约束

- 本计划不包含 `git commit`、`git branch`、`git push` 步骤。
- 本计划按小步执行，先逻辑收口，再考虑目录搬迁。
- reminder / timer、`/diy`、复杂绑定统一，不作为本轮主链路阻塞项。

## 1. 文件职责预映射

### Python Core

- Create: `wxbot/bookkeeping-platform/bookkeeping_core/contracts.py`
  - 定义 `NormalizedMessageEnvelope`、`CoreAction`、序列化 helper、action collector
- Create: `wxbot/bookkeeping-platform/bookkeeping_core/runtime.py`
  - 暴露统一 runtime 边界，封装 `process_envelope` 与 `flush_due_actions`
- Modify: `wxbot/bookkeeping-platform/bookkeeping_core/models.py`
  - 移除/兼容旧 `IncomingMessage`，避免继续把 raw 平台结构作为正式合同
- Modify: `wxbot/bookkeeping-platform/bookkeeping_core/service.py`
  - 从“直接发消息”改为“返回动作”
- Modify: `wxbot/bookkeeping-platform/bookkeeping_core/commands.py`
  - 通过 action collector 产生 `send_text` / `send_file`
- Modify: `wxbot/bookkeeping-platform/bookkeeping_web/app.py`
  - 新增统一 runtime 调用入口；P2.7 后不再保留 `/api/sync/events` 在线入口

### WeChat Adapter

- Modify: `wxbot/bookkeeping-platform/wechat_adapter/client.py`
  - 归一化输出 `NormalizedMessageEnvelope`
- Modify: `wxbot/bookkeeping-platform/wechat_adapter/main.py`
  - 改成 “poll -> runtime -> execute actions”

### WhatsApp Adapter

- Create: `wxbot/whatsapp-bookkeeping/src/core-api.ts`
  - 调用 Python runtime API，发送 envelope，接收 actions
- Modify: `wxbot/whatsapp-bookkeeping/src/index.ts`
  - 删除本地 parser/commands/database 主链路，改成薄适配层
- Modify: `wxbot/whatsapp-bookkeeping/src/whatsapp.ts`
  - 增加 `sendFile`
- Modify: `wxbot/whatsapp-bookkeeping/src/config.ts`
  - 增加 Python core runtime 配置

### Tests

- Create: `wxbot/bookkeeping-platform/tests/test_runtime.py`
  - 统一 runtime 合同、跨平台同结果、动作返回测试
- Modify: `wxbot/bookkeeping-platform/tests/test_webapp.py`
  - 新增 runtime API 测试；P2.7 后不再维护 sync/events 在线兼容测试
- Create: `wxbot/whatsapp-bookkeeping/src/core-api.test.ts`
  - 验证 TS adapter 调用 runtime API 与 action 解析

## 2. 任务拆解

### Task 1: 建立 Python 统一 Contract

**Files:**
- Create: `wxbot/bookkeeping-platform/bookkeeping_core/contracts.py`
- Modify: `wxbot/bookkeeping-platform/bookkeeping_core/models.py`
- Test: `wxbot/bookkeeping-platform/tests/test_runtime.py`

- [ ] **Step 1: 写失败测试，定义最小统一合同**

目标：

- `NormalizedMessageEnvelope` 至少包含 `platform/message_id/chat_id/chat_name/is_group/sender_id/sender_name/sender_kind/content_type/text/received_at`
- `CoreAction` 第一版只支持 `send_text`、`send_file`

Run:

```bash
cd "/Users/lcc/SeeSee/wxbot/bookkeeping-platform"
python3 -m unittest tests.test_runtime -v
```

Expected:

- `ModuleNotFoundError` 或合同相关断言失败

- [ ] **Step 2: 实现合同数据结构与序列化 helper**

最小实现要求：

- `NormalizedMessageEnvelope.from_dict(...)`
- `core_action_to_dict(...)`
- `CoreActionCollector.send_text(...)`
- `CoreActionCollector.send_file(...)`

- [ ] **Step 3: 重新运行测试，确认合同层变绿**

Run:

```bash
cd "/Users/lcc/SeeSee/wxbot/bookkeeping-platform"
python3 -m unittest tests.test_runtime -v
```

Expected:

- 合同相关测试通过

### Task 2: 抽出 Python Unified Runtime 边界

**Files:**
- Create: `wxbot/bookkeeping-platform/bookkeeping_core/runtime.py`
- Modify: `wxbot/bookkeeping-platform/bookkeeping_core/service.py`
- Modify: `wxbot/bookkeeping-platform/bookkeeping_core/commands.py`
- Test: `wxbot/bookkeeping-platform/tests/test_runtime.py`

- [ ] **Step 1: 写失败测试，证明 core 现在必须返回动作**

覆盖点：

- `/set` 返回 `send_text`
- 交易消息返回确认 `send_text`
- `/export` 返回 `send_file`
- 同一条交易文本从 `wechat` 与 `whatsapp` 进入，核心记账字段一致

Run:

```bash
cd "/Users/lcc/SeeSee/wxbot/bookkeeping-platform"
python3 -m unittest tests.test_runtime -v
```

Expected:

- `BookkeepingService` 仍试图直接调用 `platform_api`
- 或返回值不符合 `CoreAction[]`

- [ ] **Step 2: 用 action collector 替代 core 直接发消息**

实现要求：

- `BookkeepingService` 不再依赖真实平台 SDK
- `CommandHandler` 不再直接持有真实 adapter API
- `service.py` 不再读取平台 `raw` 做业务判断
- 业务判断统一基于 `NormalizedMessageEnvelope`

- [ ] **Step 3: 运行测试确认 runtime 入口稳定**

Run:

```bash
cd "/Users/lcc/SeeSee/wxbot/bookkeeping-platform"
python3 -m unittest tests.test_runtime -v
```

Expected:

- runtime 测试通过

### Task 3: 让 WeChat 完全切到新边界

**Files:**
- Modify: `wxbot/bookkeeping-platform/wechat_adapter/client.py`
- Modify: `wxbot/bookkeeping-platform/wechat_adapter/main.py`
- Test: `wxbot/bookkeeping-platform/tests/test_runtime.py`

- [ ] **Step 1: 写失败测试，锁定 WeChat 只做 envelope 归一化**

覆盖点：

- WeChat 归一化输出不再依赖 core 读取 `raw.type`
- `main.py` 只执行 `runtime.process_envelope(...)` 和 action executor

Run:

```bash
cd "/Users/lcc/SeeSee/wxbot/bookkeeping-platform"
python3 -m unittest tests.test_runtime -v
```

Expected:

- sender kind / content type 断言失败
- 或 adapter 仍依赖旧 service API

- [ ] **Step 2: 实现 WeChat action executor**

实现要求：

- `send_text` -> `platform_api.send_text`
- `send_file` -> `platform_api.send_file`
- 主循环不再把真实 `platform_api` 注入 core

- [ ] **Step 3: 运行现有 Web 与 runtime 测试**

Run:

```bash
cd "/Users/lcc/SeeSee/wxbot/bookkeeping-platform"
python3 -m unittest tests.test_runtime tests.test_webapp -v
```

Expected:

- 相关测试通过

### Task 4: 暴露统一 runtime API，供非 Python adapter 调用

**Files:**
- Modify: `wxbot/bookkeeping-platform/bookkeeping_web/app.py`
- Modify: `wxbot/bookkeeping-platform/tests/test_webapp.py`

- [ ] **Step 1: 写失败测试，新增 runtime API**

建议接口：

- `POST /api/core/messages`

返回：

```json
{
  "actions": [
    { "action_type": "send_text", "chat_id": "xxx", "text": "..." }
  ]
}
```

Run:

```bash
cd "/Users/lcc/SeeSee/wxbot/bookkeeping-platform"
python3 -m unittest tests.test_webapp -v
```

Expected:

- `404`

- [ ] **Step 2: 实现 runtime API**

实现要求：

- 使用同一个 Python unified runtime
- 做基本 Bearer 校验
- 不复用 `/api/sync/events`
- 返回 `CoreAction[]`

- [ ] **Step 3: 保留 sync/events 历史兼容测试**

要求：

- `/api/sync/events` 原有兼容测试继续通过
- runtime API 与 sync/events 语义明确分离

Run:

```bash
cd "/Users/lcc/SeeSee/wxbot/bookkeeping-platform"
python3 -m unittest tests.test_webapp -v
```

Expected:

- runtime API 与 sync/events 测试同时通过

### Task 5: 让 WhatsApp 从本地记账 bot 降级为薄适配层

**Files:**
- Create: `wxbot/whatsapp-bookkeeping/src/core-api.ts`
- Create: `wxbot/whatsapp-bookkeeping/src/core-api.test.ts`
- Modify: `wxbot/whatsapp-bookkeeping/src/index.ts`
- Modify: `wxbot/whatsapp-bookkeeping/src/whatsapp.ts`
- Modify: `wxbot/whatsapp-bookkeeping/src/config.ts`

- [ ] **Step 1: 写失败测试，锁定 WhatsApp adapter 只发送 envelope、执行 actions**

覆盖点：

- `core-api.ts` 请求体是 `NormalizedMessageEnvelope`
- adapter 执行 `send_text` / `send_file`
- `index.ts` 不再 import `parser.ts`、`commands.ts`、`database.ts` 作为主链路

Run:

```bash
cd "/Users/lcc/SeeSee/wxbot/whatsapp-bookkeeping"
npm test -- --test-name-pattern="core api|thin adapter"
```

Expected:

- 请求或动作断言失败

- [ ] **Step 2: 实现 Python core client**

实现要求：

- `sendEnvelope(envelope)` 调用 Python runtime API
- 超时、鉴权、错误响应有最小处理
- 配置新增 `coreApi.endpoint/token/requestTimeoutMs`

- [ ] **Step 3: 改写 index.ts 为薄适配层**

实现要求：

- 保留：连接、收消息、最小归一化、执行动作
- 移除正式链路中的：本地 parser / commands / database / sync outbox
- 不再本地写账本

- [ ] **Step 4: 为 `send_file` 增加 WhatsApp 执行能力**

实现要求：

- `whatsapp.ts` 增加发文件方法
- 只服务于 `CoreAction.send_file`

- [ ] **Step 5: 跑 TS 测试与构建**

Run:

```bash
cd "/Users/lcc/SeeSee/wxbot/whatsapp-bookkeeping"
npm test
npm run build
```

Expected:

- 测试通过
- TypeScript 构建通过

### Task 6: 历史背景记录：sync/events 曾是兼容入口（现已在 P2.7 退役）

**Files:**
- Modify: `wxbot/bookkeeping-platform/README.md`
- Modify: `wxbot/bookkeeping-platform/bookkeeping_core/sync_events.py`（仅在需要更清晰注释或校验时）
- Modify: `wxbot/bookkeeping-platform/tests/test_webapp.py`

- [ ] **Step 1: 写失败测试或文档断言，明确 runtime 与兼容导入分离**

覆盖点：

- runtime 走 `/api/core/messages`
- 本任务中的 `/api/sync/events` 描述仅代表当时背景，不再作为现行要求

- [ ] **Step 2: 更新 README 与必要注释**

要求：

- 明确 WhatsApp 本地内核已降级
- 结合 P2.7 说明 `/api/sync/events` 已从支持接口面退役

- [ ] **Step 3: 全量 Python 回归**

Run:

```bash
cd "/Users/lcc/SeeSee/wxbot/bookkeeping-platform"
python3 -m unittest -v tests.test_runtime tests.test_webapp tests.test_periods tests.test_reporting tests.test_analytics tests.test_postgres_backend
```

Expected:

- Python 侧回归通过

### Task 7: 最后再考虑目录搬迁

**Files:**
- 暂不改物理目录

- [ ] **Step 1: 冻结目录搬迁**

要求：

- 当前阶段不做大规模搬家
- 所有 import / 脚本 / 配置先以逻辑收口为主

- [ ] **Step 2: 搬迁前置检查清单**

检查项：

- WeChat 已切到 unified runtime
- WhatsApp 已不再本地写账
- `/api/sync/events` 已降级
- tests 全绿

- [ ] **Step 3: 再单独立目录搬迁计划**

目标：

- 后续单独处理 `adapters/wechat`、`adapters/whatsapp` 物理收口

## 3. 阶段验收点

### Phase A: Python runtime 立住

- `NormalizedMessageEnvelope -> CoreAction[]` 已成立
- core 不再持有真实平台 API
- 同文本跨平台落库字段一致

### Phase B: WeChat 接到新边界

- WeChat adapter 只做归一化 + 动作执行
- core 不再读取 WeChat raw 平台字段

### Phase C: WhatsApp 降级为薄适配层

- WhatsApp 不再本地写账
- TS `parser / commands / database / sync` 不再是正式链路
- 交易与命令正式走 Python core

### Phase D: 旧 sync/events 降级

- 该接口已在 P2.7 退役
- 正式 live path 不再依赖它

## 4. 建议执行顺序

严格顺序：

1. Task 1
2. Task 2
3. Task 3
4. Task 4
5. Task 5
6. Task 6
7. Task 7

不允许跳到目录搬迁，也不允许先改 WhatsApp 再补 Python runtime。
