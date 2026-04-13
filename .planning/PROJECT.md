# SeeSee 报价墙硬验证系统

## What This Is

这是 SeeSee 现有总账系统里的报价墙解析与发布链路升级项目，目标不是做一个“更会猜”的模型解析器，而是把供应商群报价解析做成一条受系统硬约束保护的正式发布管道。系统可以探索候选解析策略，但最终只有通过 schema 校验、业务规则校验、事实保护和发布条件的结果，才允许影响报价墙事实。

第一阶段服务于你本人做准确度验证、异常整理、回放验证和规则沉淀，不直接接管现有生产报价流程。只有当这条链路在真实样本上证明可以稳定做到“宁可漏，不可错”时，后续功能才有资格建立在它上面。

## Core Value

把供应商群原始消息转成“可追溯、可验证、不可误发布”的报价事实，宁可不上墙，也绝不把错价、错面额、错国家/币种上墙。

## Requirements

### Validated

- ✓ 原始聊天消息可以入库并回查 — existing
- ✓ Web 端已经有报价墙、异常池、模板维护和字典管理页面 — existing
- ✓ 系统已经存在按群模板解析、strict-section / group-parser 两条报价解析链路 — existing
- ✓ 解析失败样本已经能进入异常池并保留原始文本、异常原因、来源群和时间 — existing
- ✓ 当前系统已经能把部分解析成功结果展示为 active 报价墙事实 — existing

### Active

- [ ] 原始群消息是供应商报价解析的唯一事实输入，任何发布判断都必须可追溯回原始消息
- [ ] 解析器和模型只能产出候选结果，不能直接发布到报价墙事实
- [ ] 候选结果必须经过固定 schema 校验、业务规则校验和事实保护校验，只有 `publishable_rows` 才允许进入发布链路
- [ ] 当候选结果不满足发布条件时，系统必须拒绝发布，默认保守，准确性优先于覆盖率，宁可漏，不可错
- [ ] 候选失败、校验失败、发布失败时，不得污染旧事实，不得清空旧 active，不得因为本次消息失败而删除历史有效报价
- [ ] 系统必须明确区分 `full_snapshot` 与 `delta_update`，默认按 `delta_update` 处理，只有在明确确认 `full_snapshot` 时才允许根据“本次未出现的 SKU”去失活旧 SKU
- [ ] 如果一轮候选结果里没有 `publishable_rows`，本轮必须视为“不发布”，不得因为存在候选对象就默认落地部分不合法内容
- [ ] 所有解析失败、分类不明、校验失败、发布被拒绝的样本都必须进入异常池，并能 replay、追踪、人工整理和回放验证
- [ ] 异常池里的高频重复错误必须优先沉淀为模板、脚本、skill、单测或显式规则，不允许长期依赖 prompt 修补
- [ ] 主 Agent、SubAgent、脚本和页面操作都不得绕过 validator 直接发布，发布规则和事实保护规则必须落实在系统代码和校验层，不能寄托在提示词里
- [ ] v1 必须先验证“输入 -> 候选 -> 校验 -> 异常沉淀 -> replay”是否形成闭环，并支持人工比对真实样本准确度

### Out of Scope

- 让大模型直接决定最终上墙结果 — 违背系统裁决权与事实保护原则
- 为了架构洁癖进行大规模重构 — 当前阶段以最小必要改动达成目标，不为重构而重构
- 改动财务、结算、总账业务逻辑 — 这次工作聚焦报价墙解析与发布链路
- v1 直接接管现有生产报价发布 — 先验证准确度和闭环，默认不替代生产流程
- 依赖人工逐条审核所有消息才能工作 — 人工用于确认边界和调试，不应成为长期主链路

## Context

SeeSee 最初更像一个记账机器人和财务辅助页面，但你已经明确判断：如果供应商群报价解析做不到接近 100% 的确定性准确，后续很多自动化能力都没有可靠基础。当前最重要的不是扩张功能，而是把“解析准确度”变成系统、代码、工具层面都无法绕开的硬约束。

现有 brownfield 基础已经提供了一部分重要能力：原始消息入库、报价墙展示、异常池、群模板、字典、strict-section 和 group-parser 两种解析路径，以及 active 报价事实展示。这说明本项目不是从零新建，而是在现有总账与报价墙体系上加一层正式的候选生成、硬验证、事实保护和异常沉淀链路。

真实生产异常池样本显示，当前高频失败主要集中在两类：`missing_group_template` 与 `strict_match_failed`。同时，真实消息里大量混杂了班次开工文案、局部更新、卡种板块、限制说明和报价行，这进一步证明“让模型直接决定上墙结果”风险过高。模型最多只能帮助发现局部候选策略，系统必须掌握最终裁决权。

供应商群消息具有明确业务语义：他们会在开工或交接班时发送一份接近全量的 `full_snapshot`，工作过程中再发送若干局部调整的 `delta_update`。但不同群和不同人格式并不统一，因此在 v1 中，消息类型判定先以系统候选 + 人工确认调试为主，只有在规则足够明确后才逐步自动化。

v1 的主要使用者是你自己。你会用这套链路来看准确度、处理异常、验证 replay、观察 full/delta 识别是否可靠，并决定哪些失败模式值得工业化沉淀。只要这条链路还没有证明自己足够硬，就不会接管生产发布权。

## Constraints

- **Accuracy**: 宁可漏，不可错 — 候选不满足发布条件时必须拒绝发布
- **Fact Protection**: 失败不得污染旧事实 — 失败不能清空、覆盖或失活旧 active
- **Business Semantics**: `full_snapshot` 与 `delta_update` 必须显式区分 — 默认 `delta_update`，不得默认全量覆盖
- **Authority**: 系统掌握最终裁决权 — 模型和 Agent 只能给候选，不能拥有发布权
- **Scope**: 不动财务和结算主逻辑 — 工作聚焦报价墙解析、验证、异常沉淀与发布链路
- **Architecture**: 优先沿用现有 brownfield 架构 — 如现有结构足以达成目标，则以当前架构为主
- **Schema**: PostgreSQL schema 可做最小必要补充 — 仅为支撑报价墙发布链路，不为重构而扩表
- **Validation Mode**: v1 主要用于人工验证与并行观察 — 默认不接管线上生产发布
- **Evidence**: 原始群消息是唯一信息源 — 所有候选、发布、异常、replay 都必须可追溯

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| 报价墙采用“候选生成 + 硬验证 + 事实保护 + 异常沉淀 + 回放进化”架构 | 解析准确度是后续自动化的心脏，不能让模型直接决定上墙 | — Pending |
| 模型只能作为候选来源，不能成为规则来源或发布裁决来源 | 业务规则、发布规则、事实保护规则必须显式写在系统里 | — Pending |
| 默认按 `delta_update` 处理消息 | 供应商群格式不稳定，误把局部更新当全量快照会直接误杀旧事实 | — Pending |
| 只有明确确认 `full_snapshot` 时，才允许基于缺席 SKU 失活旧事实 | 防止一次不完整消息清空整组 active 报价 | — Pending |
| 没有 `publishable_rows` 就视为本轮不发布 | “有候选”不等于“能发布”，不允许部分非法内容穿透 | — Pending |
| 失败样本必须进入异常池，并沉淀为 replay、skill、脚本、单测 | 高频重复错误应工业化消灭，而不是长期靠 prompt 修补 | — Pending |
| v1 先做验证闭环，不直接替代生产报价流程 | 当前首要目标是验证准确度和发布安全性，而不是抢跑上线 | — Pending |
| 以现有架构为主，必要时做最小 schema 补充 | 当前是开发机，可谨慎试验，但不能把时间浪费在大重构上 | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? -> Move to Out of Scope with reason
2. Requirements validated? -> Move to Validated with phase reference
3. New requirements emerged? -> Add to Active
4. Decisions to log? -> Add to Key Decisions
5. "What This Is" still accurate? -> Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check -> still the right priority?
3. Audit Out of Scope -> reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-13 after initialization*
