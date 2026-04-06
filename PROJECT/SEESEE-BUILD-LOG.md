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

### 当前下一步
做“原始消息 ↔ 交易记录”的关联查询能力，让系统能回答：
- 这句消息有没有生成交易
- 这笔交易来自哪句原始消息

### 新窗口接手说明
如果换新窗口，先读：
1. `PROJECT/SEESEE-PRD-lite.md`
2. `PROJECT/SEESEE-TODO.md`
3. `PROJECT/SEESEE-BUILD-LOG.md`

再继续施工。
