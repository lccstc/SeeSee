# SeeSee 施工日志

## 2026-04-07

### 当前阶段定位
已经进入生产化开发阶段，当前主线不是做花哨功能，而是先补齐：
- 证据链
- 结构化解析
- 回溯能力
- 差额追踪基础

### 今天完成的事情
1. 打通了本地 coding worker：
   - `acp-bridge`
   - `OpenCode CLI`
   - Gemma 4 31B
2. 完成第一轮真实编码任务并验收：
   - 新增 `GET /api/incoming-messages`
   - 支持 `platform/chat_id/message_id/limit/offset`
3. 本地测试时已证明原始消息能够入库并查询到。

### 当前观察
- 原始消息日志现在是“机器看的调试版”，不是给人直接阅读的最终形态。
- 这没关系，现阶段先确保“录像录下来”，后续再做“能看懂、能回溯”。

### 当前结论
- 本地 31B coding worker 够用，但必须切小任务。
- 一个任务一个新 job 的方式更稳。
- 每次完成后，需要我亲自复查再推进下一刀。

### 第二轮已完成
已完成“原始消息 ↔ 交易记录”的只读关联查询能力。

新增能力：
- 可以查看原始消息是否生成了交易
- 可以查看对应的交易 id
- 仍然保持只读，不碰核心记账主链路

本轮验收结果：
- 关联查询相关新增测试已通过
- `tests.test_webapp` 全量已复跑通过

### 第三轮已完成
已完成“结构化解析结果”的最小持久化。

新增能力：
- 为原始消息保存最基础的解析判断结果
- 当前最小分类已覆盖：`command`、`transaction_like`、`normal_chat`
- 可通过只读接口查看最近 parse results

本轮验收结果：
- backend 侧 parse results 相关测试通过
- webapp 侧 parse results 查询测试通过
- runtime 侧新增的解析记录测试通过

### 本轮踩坑
- 本地 31B 在这轮中途一度跑偏到不该修改的目录，已中止并重开。
- 后续给本地 coding worker 下任务时，必须把可改文件范围写死，不能只说“尽量少改”。
- 还发现 OpenClaw 在监听晚到 agent 事件时存在硬崩问题，已做本机热修；hook 抢救方案已放弃，不再作为依赖。

### 第四轮已完成
已完成原始消息、parse results、交易结果的最小联合查看。

新增能力：
- 可通过单个只读接口查看一条消息的联合信息
- 能同时看到原始消息、解析结果、是否关联到交易及交易摘要
- 回溯时不需要再来回查多个接口

本轮验收结果：
- message inspector 相关新增测试通过
- parse results 相关测试复跑通过
- backend 侧 parse result 相关测试复跑通过

### 当前下一步
准备进入“差额追踪”的最小闭环设计，先定义最小问题面和最小验证路径，不急着做复杂页面。

### OpenClaw cron / pairing 排障已完成
本轮先没有继续加 SeeSee 新功能，而是先处理长任务回看链路不稳的问题。

本轮确认结果：
- 网关本身是正常的，`openclaw status` 与 `openclaw gateway status` 都显示服务在线，RPC probe 正常。
- 问题主因不是 gateway 挂掉，也不是 bind / remote 路由配置错误，而是本机设备权限发生了 scope 漂移。
- 具体表现是：当前设备已配对，但只剩 `operator.read`，当执行 `cron` / `nodes status` 这类需要更高权限的动作时，网关触发了 `repair pairing`，并返回 `pairing required`。
- 网关日志已明确记录：`scope-upgrade`，从 `operator.read` 升级到 `operator.admin / operator.write / operator.approvals / operator.pairing / operator.talk.secrets`。

本轮最小修复：
- 直接批准本机最新的 repair pairing 请求：`openclaw devices approve --latest`

修复后验证结果：
- `openclaw nodes status` 恢复正常
- `openclaw cron status` 恢复正常
- `openclaw cron list` 恢复正常
- gateway 日志可见 cron job 已成功创建并进入执行链路

本轮额外发现：
- `sessionTarget: current` 的 cron job，如果在当前对话回合仍占用时强制 `run`，会因为当前 session 正忙而超时。这不属于 cron 崩溃，而是使用方式问题。
- `sessionTarget: isolated` 的 cron job 本身可以进入执行链路，但若用 `delivery.mode=announce`，需要明确可投递目标，否则会因缺少目标而报投递错误。
- 因此后续“长任务低频回看”应优先采用：当前会话绑定的定时唤醒，不要在同一活跃 turn 内强制执行；若走 isolated job，则必须明确 delivery 目标。

bridge 现状补记：
- 127.0.0.1:8765 当前在监听，但它实际是 `reporting_server.py`（总账中心页面），不是 `acp-bridge` 的 `/health` / `/agents` 接口。
- 本机同时存在 `opencode acp` 进程，监听在 127.0.0.1:4096，说明本地 ACP 侧服务本身是活的。
- 说明这次 cron / pairing 故障与 bridge 健康检查不是同一问题面，不能混为一谈。

### 差额追踪最小闭环侦察结论
本轮没有直接动代码，先把“差额追踪”压缩成最小闭环。

当前已具备的底座：
- `incoming_messages`：原始消息证据
- `message_parse_results`：最小解析结果
- `transactions`：最终入账结果
- `message-inspector`：单条消息的联合查看
- `reconciliation ledger`：已有交易级 `issue_flags`（如待对账、汇率公式异常、缺失汇率）

当前真正缺的不是又一套新账，而是：
- 当 reconciliation 里出现异常交易时，不能直接一跳看到“这笔账是从哪条消息来的、当时怎么解析的、最后记成了什么、哪里开始不对”。

因此当前决定的最小闭环是：
1. 先不做复杂页面
2. 先不做自动裁决
3. 先新增一个只读的 `difference trace` / `差额追踪` 接口
4. 入口先以 `transaction_id` 为主，因为 reconciliation 当前天然就是按交易行工作

这条只读 trace 最小应返回：
- transaction 摘要
- 对应原始 message
- 对应 parse result
- 当前 reconciliation issue flags
- 如果交易被人工改过，带出最近一次 edit 信息
- 一组最小 trace 状态：`captured -> parsed -> posted -> edited? -> flagged?`

第一阶段只覆盖这类问题：
- 有 `transaction_id` 的异常交易
- 能通过 `platform + chat_id + message_id` 回到源消息的交易
- 典型场景包括：记错汇率、记错金额、人工改坏、该对账未对账

第一阶段暂不覆盖：
- 没有 message_id 的历史脏数据
- 多条消息共同形成一笔业务的复杂链路
- 账期级汇总差额的自动归因
- 大页面和复杂可视化

建议的下一刀实现顺序：
1. 先做只读 `difference trace` 接口
2. 复用现有 `message-inspector` 与 reconciliation 数据，不重复造表
3. 再给 reconciliation 行补一个 trace 入口

### 第五轮已完成
已完成只读 `difference trace` 接口，作为差额追踪的第一条最小闭环。

新增能力：
- 新增 `GET /api/difference-trace?transaction_id=...`
- 可从 `transaction_id` 直接查看交易摘要、原始消息、parse result、当前 issue flags、最近一次 edit 信息
- 会返回最小状态链：`captured / parsed / posted / edited / flagged`
- transaction 即使缺少 `message_id`，仍可返回 transaction 本体与 trace 状态，不会整条失败

本轮实际实现方式：
- 没有新建表
- 复用了现有 `transactions`、`incoming_messages`、`message_parse_results`、`transaction_edit_logs`
- issue flags 口径与 reconciliation 保持一致

本轮验收结果：
- 使用项目自己的测试方式补跑了 difference trace 相关 5 个新增测试
- 需要带 `BOOKKEEPING_TEST_DSN` 环境变量，指向本机 PostgreSQL 测试连接
- 5 个新增测试已通过
- 对应功能提交已存在：`7639a9d feat: add difference trace api`

本轮额外流程修正：
- 31B worker 的状态回看 cron 不能再用持续循环 job 盯一个旧 session
- 正确规范应是：发出 worker 任务后，只创建一个一次性 cron，约 1 分钟后唤醒当前会话查看状态；如果 worker session 变更，旧 cron 必须立刻移除或改绑

### 第六轮已完成
已把 `difference trace` 接到 reconciliation 实际页面路径里，先落最小只读详情，不再要求人工来回切接口。

新增能力：
- reconciliation 逐笔台账里的交易行现在有 `追踪` 入口
- 点击后会在同页下方加载只读 `差额追踪` 面板
- 面板可直接查看：交易摘要、原始消息、parse result、最近修改痕迹、trace 状态链
- 为页面使用补了一个同口径只读入口：`GET /api/reconciliation/difference-trace?transaction_id=...`

本轮实现取舍：
- 没有新做复杂页面路由
- 没有新建表
- 没有改 reconciliation 核心计算口径
- 只是把现有 `difference trace` 能力接进真实对账路径，降低排查切换成本

本轮验收结果：
- 页面结构测试通过，确认 trace 面板和入口已挂到 reconciliation 页面
- difference trace 核心接口相关测试复跑通过
- 页面实际使用的 `reconciliation/difference-trace` 入口测试通过
- 本轮实际补跑 4 个测试，命令为：
  - `.venv/bin/python -m unittest tests.test_webapp.WebAppTests.test_reconciliation_page_contains_filter_and_adjustment_controls tests.test_webapp.WebAppTests.test_difference_trace_returns_full_trace_with_all_fields tests.test_webapp.WebAppTests.test_difference_trace_returns_transaction_without_message_parse tests.test_webapp.WebAppTests.test_reconciliation_difference_trace_alias_returns_trace_without_auth`

当前主线变化：
- 差额追踪已经不再只是 API，已经进入 reconciliation 的真实操作路径
- 对账时看到异常交易，可以直接同页追到消息、解析和人工修改痕迹

### 新窗口接手说明
如果换新窗口，先读：
1. `PROJECT/SEESEE-PRD-lite.md`
2. `PROJECT/SEESEE-TODO.md`
3. `PROJECT/SEESEE-BUILD-LOG.md`

再继续施工。
