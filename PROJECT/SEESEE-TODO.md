# SeeSee TODO

> 规则：完成一项，验收一项，再打勾。

## 当前阶段：证据链 -> 结构化解析 -> 回溯

- [x] 原始消息入库
- [x] 原始消息查询接口 `GET /api/incoming-messages`
- [x] 原始消息与交易记录的关联查询
- [x] 能判断一条原始消息是否生成交易
- [x] 结构化解析结果持久化
- [x] 普通聊天 / 命令 / 交易型消息的初步分类
- [x] 差额追踪的最小闭环设计
- [x] 回溯页面的最小草图

## 本地 coding worker 工作流
- [x] `acp-bridge -> opencode -> Gemma 4 31B` 打通
- [x] 第一轮真实编码任务完成并验收
- [x] 第二轮真实编码任务完成并验收
- [x] 第三轮真实编码任务完成并验收
- [ ] 明确哪些任务适合本地 31B，哪些不适合

## 运行协作链路
- [x] 查明 cron / pairing / gateway 不稳定的最小根因
- [x] 修复本机设备 scope 漂移导致的 repair pairing
- [x] 确认 gateway 正常、`cron status/list` 恢复可用
- [ ] 把“长任务低频回看”的 cron 标准用法整理成固定操作约束

## 当前下一刀
- [x] 为 parse results 增加原始消息 / 交易结果联合查看能力
- [x] 设计差额追踪的最小闭环
- [x] 新增只读差额追踪接口（transaction -> message / parse / tx / issue flags）
- [x] 给 reconciliation 行补一个 trace 入口，先跳只读详情，不做复杂页面
- [x] 把 difference trace 接到实际对账操作路径里，减少人工来回切接口
