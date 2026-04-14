# Failure Dictionary / Quote Repair Lexicon

## Why This Exists

当前 repair case / failure log 已经足够支撑本轮主 agent 理解系统，但这还不是生产级知识形态。进入生产值班后，被叫出来处理异常的主 agent 或 subagent 不会天然拥有当前长窗口上下文。如果失败信息仍然只是“这次尝试失败了 + 一段自然语言说明”，系统就会持续依赖上下文记忆和少数熟手。

因此，repair case 日志必须继续进化成项目自己的 **Failure Dictionary / Quote Repair Lexicon**：

- repair case 是病例
- failure dictionary 是医书

目标不是简单归档，而是让新 agent 先查词条，再动手修，最后把本次修复反写成新的词条修订。

## Core Principle

Failure Dictionary 不是聊天记录堆场，而是结构化、可检索、可修订的项目知识资产。

它必须服务于：

- 无上下文主 agent 的快速定位
- subagent 的标准化修补入口
- 高频失败模式的聚类与工业化沉淀
- “禁止修法”与“已验证修法”的长期积累

## Minimum Entry Shape

每个 failure dictionary 词条至少应包含：

- `failure_code`
- `symptom`
- `trigger_pattern`
- `root_cause`
- `preferred_scope`
- `do_first`
- `do_not_do`
- `known_good_fix`
- `replay_fixture_refs`
- `test_refs`
- `related_groups`
- `first_seen_at`
- `last_seen_at`
- `frequency`

## Relationship To Existing Artifacts

- `quote_repair_cases`: 记录单次异常的 canonical case
- `quote_repair_case_attempts`: 记录单次 case 的尝试历史
- `gold fixtures / approved fixtures`: 提供标准答案与 replay 基准
- failure dictionary: 聚合同类 repair case 的标准知识条目

换句话说：

- repair case 回答“这次发生了什么”
- failure dictionary 回答“这类错应该怎么修”

## Rules

- 原始消息全文只保留在 repair case，不在词条里无限复制
- 词条优先记录结构化摘要和可执行修法，不记录长篇自然语言复述
- 三次失败升级后的结论必须能回写到 failure dictionary
- 已知禁用修法必须入词条，例如：
  - 不允许在已有群 profile 下默认扩骨架
  - 不允许把 `横白卡图 / 整卡卡密` 吸成 `country_or_currency`
  - 不允许绕过 validator / publisher
- 新 agent 或 subagent 在新 case 开修前，应先查 failure dictionary

## Expected Roadmap Use

这项能力将并入后续 operator / verification 工作面：

- 让 operator 能从异常直接跳到对应词条
- 让主 agent / subagent 在没有旧会话上下文时也能按词条修补
- 让高频失败模式从“日志膨胀”转成“词条修订”

## Immediate Insight Captured

当前最重要的洞察是：

> repair case 的失败日志不能停留在“当前主 agent 才看得懂的上下文记录”，必须进化成项目自己的新华字典，让新兵蛋子先查词条、再修问题、最后回写修订。

## Implemented Seed Entries

当前代码里已经实现了第一批 handbook seed，后续允许继续修订：

- `validator_mixed_outcome`
- `auto_remediation_skeleton_expansion_blocked`
- `supermarket_country_pollution`
- `strict_match_failed`
- `missing_group_template`

这些词条现在会和 live repair case 一起被聚合：

- builtin 词条负责给出标准修法和禁用修法
- live repair case 负责补 `frequency / related_groups / source_case_refs`
