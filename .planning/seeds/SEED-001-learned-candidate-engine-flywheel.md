---
id: SEED-001
status: dormant
planted: 2026-04-15
planted_during: Phase 08 completed
trigger_when: 当 P8 实验墙跑出一段真实观察数据后，如果第三层候选生成的不确定性开始主要表现为“显式字典/profile 维护成本高、自动修补成功率进入边际递减、但系统裁决链已经稳定”，就应该把这个 seed 提出来
scope: Large
---

# SEED-001: 终局演进 — 显式训练 + 可学习候选引擎

## Why This Matters

当前架构已经证明：

- 原始消息 -> candidate -> validator -> publisher 这条确定性治理链是成立的
- repair case、failure dictionary、group profile、replay fixture、known-good fix 都已经开始沉淀成高质量知识资产
- 真正长期昂贵且不稳定的部分，正在集中到第三层候选生成

如果后续继续只靠显式字典、group profile、section 和 deterministic 修补来扩覆盖，理论上在固定客群下可以继续收敛；但随着群级语法书越来越厚、边际格式越来越多、自动修补开始更多暴露“会判断、难压缩”的模糊区间，第三层的维护成本会持续上升。

这个 seed 的价值不是推翻现有五层架构，而是让它继续进化：

- 第三层从“显式规则候选引擎”进化成“可学习候选引擎”
- repair case / failure dictionary / approved fixtures / 人工纠错沉淀成训练资产
- 本地专属小模型接手高频候选清洗劳动
- 云端高智商 agent 只处理真正没见过的新格式和高复杂度破译
- 第五层确定性系统裁决继续保留，不允许模型直接持有事实发布权

换句话说：

**终局不是让模型接管系统，而是让系统用真实错误和修补结果，训练出更强的第三层候选引擎，同时始终把最终裁决权留在确定性代码手里。**

## When to Surface

**Trigger:** 当实验墙观察期跑出真实数据后，如果发现第三层的不确定性已成为主要瓶颈，就进入这个方向。

This seed should be presented during `/gsd-new-milestone` when the milestone scope matches any of these conditions:

- `P8` 已经连续运行一段时间，你已经能看到稳定的实验墙指标，而下一步问题开始集中在“第三层候选生成还不够强”
- 高频群已经被大体收敛，但新增收益主要来自继续补第三层，不再来自修 publisher / snapshot / operator workbench
- repair case / failure dictionary / approved fixtures 已经积累到足够多，开始具备“训练资产”而不是“单次排障记录”的特征
- 你开始明确感受到：继续纯手工补字典和 profile 可以收敛，但维护成本正在上升，且希望引入本地专属小模型接手一部分候选清洗劳动
- 你准备讨论“显式训练 vs 参数训练”的分工，而不是继续只做 v1 骨架或下游业务接管

## Scope Estimate

**Large** — 这是一个完整新 milestone，甚至可能继续拆成多个 milestone。

它至少会涉及：

- 训练资产规范化
- 训练集准入规则
- 第三层离线评测框架
- 本地专属小模型的候选引擎接入
- 云端高智商 fallback 破译链
- 训练飞轮和版本治理
- learned candidate engine 的灰度比较与接管策略

这不是 quick task，也不适合在当前 milestone 尾巴上直接追加。

## Breadcrumbs

Related code and decisions found in the current codebase:

- `.planning/PROJECT.md` — 当前项目方法论、群级 profile 主架构、failure dictionary 和实验墙边界
- `.planning/STATE.md` — 当前 milestone 已完成到 P8，说明下一阶段不再是补基础骨架
- `.planning/ROADMAP.md` — 当前 1-8 phase 已闭环，适合在新 milestone 中承接终局演进
- `PROJECT/可进化确定性治理系统方法论.md` — 当前系统方法论与“不是万能解析器”的正式沉淀
- `PROJECT/抽象语言到工程术语对照表.md` — 当前抽象语言到工程语言的对照
- `wxbot/bookkeeping-platform/sql/postgres_schema.sql` — 已有 `quote_snapshot_decisions`、`quote_repair_cases` 等 durable substrate
- `wxbot/bookkeeping-platform/bookkeeping_core/quotes.py` — 当前第三层候选生成和实验墙运行模式入口
- `wxbot/bookkeeping-platform/bookkeeping_core/quote_publisher.py` — 第五层事实裁决 / 发布铁门
- `wxbot/bookkeeping-platform/scripts/bootstrap_quote_group_profiles.py` — 群级 profile bootstrap，未来可视作显式训练资产生成器之一
- `.planning/phases/02.1-real-exception-corpus-candidate-coverage/` — 真实异常语料、gold fixture、bootstrap coverage 的起点
- `.planning/phases/07-operator-verification-failure-dictionary/` — failure dictionary / repair lexicon 的正式化基础
- `PROJECT/P8单人运营实验墙上线标准.md` — 触发这个 seed 前，先让实验墙跑出真实观察数据

## Notes

- 当前默认判断：**先观察 P8，再决定是否正式进入这个方向。**
- 这个 seed 不代表现在就开工，也不代表“显式训练路线已经不够用”；它只是把终局方向结构化保存下来。
- 一个核心前提已经在当前对话中被确认：即使未来走微调路线，第五层的确定性系统裁决也绝对不能丢。
- 另一个关键前提：训练资产不能直接来自“系统自己猜自己对”，必须优先来自人工确认样本、confirmed repair absorption、approved fixtures 和已验证的 known-good fix。
