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

### 新窗口接手说明
如果换新窗口，先读：
1. `PROJECT/SEESEE-PRD-lite.md`
2. `PROJECT/SEESEE-TODO.md`
3. `PROJECT/SEESEE-BUILD-LOG.md`

再继续施工。
