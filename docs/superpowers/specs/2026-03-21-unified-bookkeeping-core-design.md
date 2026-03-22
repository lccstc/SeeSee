# 2026-03-21 统一业务内核收敛设计

## 0. 文档状态

- 状态：`Draft / 基于代码事实重建后确认`
- 当前目标：先把正式运行时收敛成单业务内核，再处理目录搬迁
- 当前不做：P3/P4、页面补数据、UI 优化、复杂异常工作流、复杂身份绑定统一

## 1. 目标与约束

本轮目标不是“两个平台共用一个数据库”，也不是“两个平台说同一种协议”，而是把正式业务判断、正式账本写入、正式跑账统计，收敛到唯一一套 Python 业务内核。

正式目标链路固定为：

```text
WhatsApp Adapter  ─┐
                  ├─> Python Unified Bookkeeping Core ─> Unified Ledger DB
WeChat Adapter    ─┘
```

本轮固定约束：

1. Python `wxbot/bookkeeping-platform/bookkeeping_core` 是唯一正式业务内核。
2. WhatsApp 与 WeChat 都只能保留薄适配层职责。
3. `schema_version=1` 旧事件只保留历史兼容读取、回放、迁移语义；`/api/sync/events` 已从当前 WSGI 支持面退役。
4. 不允许把平台原始 `raw` 结构直接泄漏进 core 业务判断。
5. 不允许把 `if platform == ...` 大量堆进核心业务主路径。
6. 当前优先级是逻辑单内核，不是物理目录搬迁。

## 2. 代码现状确认

### 2.1 当前不是“一个内核两个入口”，而是“两套业务内核”

当前代码事实是：

1. `wxbot/whatsapp-bookkeeping` 自己维护了一套完整的交易解析、命令处理、账本写入、提醒、同步出站逻辑。
2. `wxbot/bookkeeping-platform/bookkeeping_core` 又维护了一套交易解析、命令处理、账本写入、提醒、账期、报表逻辑。
3. 两边不是“一个 core + 一个 adapter”，而是“TS 正式 bot 内核 + Python 正式 core 内核”并存。

这意味着当前系统的真实问题不是入口数，而是业务判断被复制了两次。

### 2.2 TS WhatsApp 侧：平台层与业务内核的实际边界

当前 TS WhatsApp 中，真正属于平台层的部分只有：

- `src/whatsapp.ts`
  - 登录、二维码、连接/重连
  - 监听 `messages.upsert`
  - 发送文本
  - 解析群名称
- `src/config.ts`
  - 运行配置读取
- `src/chat-context.ts`
  - 群名兜底归一化

当前 TS WhatsApp 中，明显属于业务内核的部分包括：

- `src/parser.ts`
  - 交易文本识别
  - 类别规则
  - 汇率计算
  - 确认文案
- `src/commands.ts`
  - `/set /undo /mx /bal /history /js /alljs /settlements /ngn /diy /bind`
  - 权限判断
  - 导出文件
  - 结算与批量结算
  - 同步事件出站
- `src/database.ts`
  - 交易表、群表、白名单、绑定、提醒、结算、同步 outbox
  - 账本事实写入与查询
- `src/index.ts`
  - 消息接入
  - 身份判断
  - 激活群判断
  - 交易识别与解析
  - 交易入库
  - 确认回复
  - NGN 逻辑
  - reminder/timer
  - 同步出站

结论：`index.ts` 不是薄适配层，它混合了消息接入、交易判断、解析、记账、回复、同步出站，仍然是一条完整本地记账链路。

### 2.3 WeChat adapter 与 Python core：已接近理想但仍有深耦合

WeChat 已接近薄适配层的地方：

- `wechat_adapter/client.py` 已经把平台消息归一成接近通用的消息对象。
- `wechat_adapter/main.py` 的主循环基本是：
  - 拉消息
  - 处理少量平台/运维控制命令
  - 交给 `BookkeepingService`
- 交易解析、命令、账本写入、结算、报表都主要在 Python 侧。

WeChat 仍然耦合过深的地方：

- `bookkeeping_core/service.py` 直接持有 `platform_api` 并直接发送消息。
- `bookkeeping_core/commands.py` 直接调用 `platform_api.send_text/send_file`。
- `service.py` 仍读取 `msg.raw["type"]` 做业务过滤，说明 core 仍依赖平台原始字段。
- `wechat_adapter/main.py` 里仍有一批直接操作 DB 的平台控制命令，例如 `/bindid`、监听群增删。

结论：WeChat 方向是对的，但 Python core 还没有形成“只吃标准化入站、只吐标准化动作”的真正 runtime 边界。

### 2.4 `sync_events.py` 为什么只能算已退役的历史兼容导入器

`sync_events.py` 的角色必须明确降级为历史兼容导入器，原因有 5 个：

1. 它只接受 `platform == "whatsapp"` 的旧事件，不是统一入口。
2. 它只支持 `group.set / transaction.created / transaction.deleted / transactions.cleared / settlement.created` 这类旧 schema 事件，不覆盖正式运行时语义。
3. 它不做交易解析、权限判断、身份归一，也不承接命令链路。
4. 它通过 `source_transaction_id -> whatsapp-local-tx-*` 重建 message id，本质是在回放旧本地账本事实，不是 live 决策。
5. 它不会返回待执行动作，因此不可能成为“收消息 -> 决策 -> 回复”的正式主链路。

因此 `sync_events.py` 即使保留，也只能承载历史参考或迁移语义：

- 历史导入参考
- 兼容回放参考
- 迁移补录辅助

`/api/sync/events` 本身不再作为当前支持的在线接口。

## 3. 备选架构方案

### 方案 A：继续保留 TS WhatsApp 正式业务内核，再同步到 Python 总账

链路：

```text
WhatsApp Adapter + TS Core -> 本地 DB -> sync/events -> Python 总账
WeChat Adapter -> Python Core -> Unified DB
```

优点：

- 改动表面上最少
- WhatsApp 现有行为最容易延续

缺点：

- 仍然保留两套解析、命令、账本规则
- 任何新业务都要改 TS 与 Python 两边
- 若继续让 `/api/sync/events` 承担正式链路，将无法真正统一 live runtime
- “共用总账”只是数据汇聚，不是内核统一

结论：拒绝。

### 方案 B：适配层先做交易解析，再把结构化交易交给 Python core

链路：

```text
Adapter(raw -> parsed_tx) -> Python Core(bookkeeping only) -> Unified DB
```

优点：

- 适配层调用简单
- Python core 接口短期上更容易设计

缺点：

- 交易解析仍在多平台重复实现
- 未来新增输入规则时，仍要改每个 adapter
- “平台翻译”与“业务翻译”混在一起，边界不干净
- 不能保证新增命令默认只改 core

结论：拒绝。

### 方案 C：适配层只发送标准化消息事件，Python core 返回动作

链路：

```text
Adapter(raw -> NormalizedMessageEnvelope)
  -> Python Unified Bookkeeping Core
  -> CoreAction[]
  -> Adapter(action executor)
```

优点：

- 交易解析、权限、命令、账本写入只保留一份
- WeChat 与 WhatsApp 共用同一条核心决策链
- 新增业务能力默认只改 Python core
- 平台差异只剩输入归一化和动作执行

缺点：

- 需要显式定义统一 contract
- 需要把 Python core 从“直接发消息”改造成“返回动作”
- WhatsApp 需要从本地 bot 降级为真正薄适配层

结论：推荐并锁定。

## 4. 推荐架构

### 4.1 正式运行时

正式 live path 固定为：

```text
WhatsApp Adapter  ─┐
                  ├─> Unified Bookkeeping Runtime ─> Unified Ledger DB
WeChat Adapter    ─┘
```

其中：

- `Adapter` 只做平台接入与动作执行
- `Unified Bookkeeping Runtime` 只存在于 Python core
- `Unified Ledger DB` 只认 Python core 写入

### 4.2 设计原则

1. 适配层只负责把平台消息翻译成统一入站合同。
2. 业务内核只负责基于统一合同做解析、判断、落库、生成动作。
3. 出站动作必须显式化，不能再由 core 直接调平台 SDK。
4. 平台差异必须停留在适配层，不能继续扩散进 parser / commands / database。

## 5. Adapter 与 Core 的职责边界

### 5.1 第一版 Adapter 保留职责

- 登录、连接、重连
- 拉取消息
- 发送文本
- 发送文件
- 平台字段最小归一化
- 少量纯平台控制逻辑
  - 例如监听群增删
  - 例如连接状态维护

### 5.2 第一版 Core 吸收职责

- 交易解析
- 权限与身份归一
- `/set`
- `/undo`
- `/mx`
- `/bal`
- `/history`
- `/js`
- `/alljs`
- `/settlements`
- `/ngn`
- 正式账本写入
- 结算与对账事实
- 账期关闭
- 快照与统计
- 导出文件生成

### 5.3 当前阶段明确后移

- reminder / timer
- `/diy`
- WhatsApp `/bind` 与 WeChat `/bindid` 统一形态
- 更复杂异常工作流
- 更细身份绑定
- UI / P3 / P4

后移不代表删除，而是明确不作为本轮统一 runtime 的阻塞项。

## 6. 为什么 Python core 可以作为唯一正式业务内核

Python core 已经具备成为唯一内核的条件：

1. 数据模型更完整  
   已有 `platform / group_key / chat_id / chat_name / sender_name / message_id / identity_bindings / admins / accounting_periods / snapshots / reporting` 等统一字段与读模型。

2. 业务覆盖面更宽  
   不仅有交易、命令、结算，还有账期关闭、快照、分析、Web 读取接口。

3. 统一账本事实已经围绕它搭建  
   `bookkeeping_web`、`periods.py`、`reporting.py`、测试体系都依赖 Python DB 模型。

4. WeChat 已经部分接入  
   说明 Python core 已经不是纯“总账导入器”，而是正在承担 live 业务逻辑。

5. 把它收敛成标准 runtime，比继续养第二套 TS 正式内核更便宜、更稳。

## 7. 统一 Contract

## 7.1 入站：`NormalizedMessageEnvelope`

第一版采用最小稳定字段集：

- `platform`
- `message_id`
- `chat_id`
- `chat_name`
- `is_group`
- `sender_id`
- `sender_name`
- `sender_kind`
- `content_type`
- `text`
- `received_at`（可选）

字段说明：

1. `platform`
   - 仅用于构造统一 `group_key`、身份作用域和日志归属
   - 不允许在核心命令分支中大量出现平台判断

2. `message_id`
   - 用于幂等去重
   - 必须由 adapter 提供稳定值

3. `chat_id` / `chat_name`
   - `chat_id` 是事实主键
   - `chat_name` 只用于显示与导出

4. `sender_id` / `sender_name`
   - `sender_id` 参与权限、身份归一与审计
   - `sender_name` 只作为显示辅助

5. `sender_kind`
   - 推荐值：`user | self | system | unknown`
   - 用来替代 core 对 WeChat `raw.type` 之类平台字段的直接依赖

6. `content_type`
   - 第一版只正式支持 `text`
   - 预留未来图片/文件/系统消息扩展

7. `text`
   - 统一后的文本内容
   - 所有命令与交易解析都只看这个字段

8. `received_at`
   - 仅用于日志与未来审计，不参与第一版业务判断

刻意不进入 contract 的内容：

- 平台原始 `raw`
- 平台 SDK message 对象
- WhatsApp / WeChat 特有元数据

理由很简单：这些字段属于适配层，不属于统一业务输入。

## 7.2 出站：`CoreAction[]`

第一版只支持两个动作：

### `send_text`

字段：

- `action_type = "send_text"`
- `chat_id`
- `text`

### `send_file`

字段：

- `action_type = "send_file"`
- `chat_id`
- `file_path`
- `caption`（可选）

设计原则：

1. action 必须是 adapter 可直接执行的命令，不返回平台 SDK 对象。
2. action 必须只依赖 adapter 已掌握的信息，不要求 core 持有连接状态。
3. 第一版不做“编辑消息”“撤回消息”“按钮回调”等复杂交互。

## 8. “翻译问题”仍然存在，但只剩平台翻译

统一内核之后，翻译问题不会消失，但会被压缩到正确的位置：

仍然存在的翻译：

- WhatsApp 原始消息 -> `NormalizedMessageEnvelope`
- WeChat 原始消息 -> `NormalizedMessageEnvelope`
- `CoreAction` -> WhatsApp SDK 调用
- `CoreAction` -> WeChat SDK 调用

不应再存在的翻译：

- WhatsApp 自己再解析一套交易规则
- WeChat 自己再实现一套命令逻辑
- 两边各自维护一套账本写入语义

也就是说，未来还会有“平台翻译”，但不再有“业务重复”。

## 9. 未来新增功能的默认修改位置

### 9.1 默认只改 Core 的场景

- 新增或调整交易解析规则
- 新增或调整命令
- 权限规则变化
- 结算逻辑变化
- 账期与快照逻辑变化
- 分析统计口径变化
- 导出格式变化

### 9.2 仍需改 Adapter 的场景

- 新平台接入
- 登录/连接/重连机制变化
- 平台原始消息字段变化
- 新的消息发送能力
- 平台文件发送差异
- 纯平台运维命令

原则：只要是“业务定义”变化，就默认只改 Python core。

## 10. 迁移分阶段方案

### 阶段 1：抽出 Python Unified Runtime 边界

目标：

- 明确 `NormalizedMessageEnvelope -> CoreAction[]` 入口/出口
- Core 不再直接持有真实平台 API

产物：

- 统一 contract
- action collector / runtime 边界
- Core 侧测试

### 阶段 2：WeChat 全量切到新边界

目标：

- WeChat adapter 只做归一化与动作执行
- Core 不再读取 WeChat raw 字段做业务判断

### 阶段 3：暴露统一 runtime 调用面给非 Python adapter

目标：

- 为 WhatsApp 提供正式调用入口
- 不是旧 `/api/sync/events`，而是新的 runtime 入口

### 阶段 4：WhatsApp 从本地记账 bot 降级为薄适配层

目标：

- `index.ts` 只剩连接、收消息、归一化、调用 Python core、执行动作
- `parser / commands / database / sync` 不再承担正式业务链路

### 阶段 5：旧 `sync/events` 从在线接口面退场

目标：

- 主代码路径不再暴露 `/api/sync/events`
- 文档与测试不再把它当成当前支持接口
- 如保留 `sync_events.py`，也只能作为历史兼容参考

### 阶段 6：最后再做目录搬迁

目标：

- 在业务主链路稳定后，完成物理目录收口
- 避免一边搬目录一边改主链路造成混乱

## 11. 目录目标结构

本轮只锁定目标结构，不做大爆炸搬家。

最终目标结构：

- `wxbot/bookkeeping-platform/bookkeeping_core`
- `wxbot/bookkeeping-platform/adapters/wechat`
- `wxbot/bookkeeping-platform/adapters/whatsapp`
- `wxbot/bookkeeping-platform/bookkeeping_web`
- `wxbot/bookkeeping-platform/tests`

当前阶段允许：

- `wxbot/whatsapp-bookkeeping` 暂时继续存在

但语义必须变成：

- “迁移中的 WhatsApp 适配层工作区”

不能再被当作正式业务内核继续长功能。

## 12. 验收标准

满足以下条件，才算这轮“统一业务内核收敛”真正成立：

1. 同一条交易文本，从 WhatsApp 和 WeChat 进入后，核心落库事实一致。
2. `/set /undo /mx /bal /history /js /alljs /settlements /ngn` 走同一段 Python 业务逻辑。
3. WhatsApp 不再保留正式业务写入链路。
4. `/api/sync/events` 不再属于当前支持接口面，主代码路径不再依赖它。
5. 账期关闭、快照、报表只依赖统一账本事实源。

## 13. 本轮结论

这轮收敛的关键不是“把文件挪到同一目录”，而是先把正式业务判断收口到一个 runtime。

因此本轮推荐动作顺序必须是：

1. 先立 Python unified runtime 边界
2. 再把 WeChat 完全接到新边界
3. 再把 WhatsApp 从本地记账 bot 降成薄适配层
4. 再把旧 sync/events 明确降级
5. 最后才做目录迁移

只有按这个顺序，系统才会从“两个平台 + 两套逻辑 + 一个总账”真正收敛成“两个入口 + 一个内核 + 一个账本”。
