# SeeSee 项目上下文

## 项目性质

礼品卡中介报价撮合与总账系统，涉及钱、报价、消息、机器人和数据库。
**不是学习 demo，是真实运营系统。**

当前这轮项目的中心不是“做一个更聪明的解析器”，而是把供应商群报价解析做成一条受系统硬约束保护的正式发布管道。

## 当前项目目标

**SeeSee 报价墙硬验证系统**

这是 SeeSee 现有总账系统里的报价墙解析与发布链路升级项目，目标不是做一个“更会猜”的模型解析器，而是把供应商群报价解析做成一条受系统硬约束保护的正式发布管道。系统可以探索候选解析策略，但最终只有通过 schema 校验、业务规则校验、事实保护和发布条件的结果，才允许影响报价墙事实。

第一阶段服务于人工验证准确度、异常整理、回放验证和规则沉淀，不直接接管现有生产报价流程。只有当这条链路在真实样本上证明可以稳定做到“宁可漏，不可错”时，后续功能才有资格建立在它上面。

**Core Value:** 把供应商群原始消息转成“可追溯、可验证、不可误发布”的报价事实，宁可不上墙，也绝不把错价、错面额、错国家/币种上墙。

## 架构

- 双监听 + Core 核心驱动：WeChat 适配层 + WhatsApp 适配层 + 统一 Core runtime
- Core 是唯一业务核心：`POST /api/core/messages` 是正式消息入口
- 监听器只做：接收消息 -> 归一化 -> 送入 Core -> 执行 Core 返回的动作
- 当前最重要子系统：报价墙（稳定采集、稳定解析、稳定展示、稳定追溯）
- 现有 brownfield 基础已经存在：原始消息入库、报价墙、异常池、群模板、报价字典、strict-section / group-parser 解析链路

## 报价墙硬原则

- 原始群消息是唯一信息源
- 解析器和模型只能产出候选，不能直接发布
- 系统必须通过 schema 校验、业务规则校验、事实保护层来决定能不能发布
- 只有 `publishable_rows` 才允许进入发布链路
- 默认保守：宁可不上墙，不可误上墙；准确性优先于覆盖率
- 当候选结果不满足发布条件时，必须 reject，不允许猜测性上墙
- 任意失败都只能导致“不更新”，不得污染、清空或误失活旧 active
- 候选失败、校验失败、发布失败时，不得因为本次消息未解析成功就删除历史有效报价
- 系统必须明确区分 `full_snapshot` 和 `delta_update`
- 默认按 `delta_update` 处理，不得默认做全量覆盖或全量清理
- 只有明确确认 `full_snapshot` 时，才允许根据“本次未出现的 SKU”去失活旧 SKU
- 主 Agent / SubAgent / 脚本 / 页面操作不得绕过 validator 直接发布
- 业务规则、发布规则、事实保护规则必须落实在系统代码与校验层，不能寄托于提示词自觉遵守
- 所有失败样本必须进入异常池
- 异常池必须支持 replay、skill、脚本、单测沉淀
- 高频重复错误应优先工业化处理，而不是长期依赖 prompt 修复

## 当前阶段边界

- v1 主要服务于人工验证准确度与链路闭环，不直接接管生产报价流程
- v1 的首要目标是验证：输入、候选、校验、异常沉淀、replay 是否闭环
- v1 可以并行观察、回放验证、人工比对，但不默认接管生产发布权
- 财务和结算主逻辑不动
- 若现有数据结构不足以支撑报价墙发布链路，可做**最小必要** PostgreSQL schema 补充
- schema 补充只服务于报价墙发布链路验证，不为重构而重构
- 当前优先沿用现有 brownfield 架构，除非调查后确认现有结构无法达成目标

## 代码与落点约定

- 业务逻辑放 `wxbot/bookkeeping-platform/bookkeeping_core/`
- 页面层只做展示，页面在 `wxbot/bookkeeping-platform/bookkeeping_web/pages.py`
- 路由在 `wxbot/bookkeeping-platform/bookkeeping_web/app.py`
- 解析、校验、发布、异常沉淀这类核心规则必须放系统代码，不放在 prompt 里
- 保持适配层薄：不要把业务裁决权塞进 `wechat_adapter/` 或 `whatsapp-bookkeeping/src/`
- PostgreSQL 是正式事实源；SQLite 不是正式运行时事实源
- 测试用 `unittest`：`python -m unittest`
- 先说影响范围和风险，再动手

## 工作流

### 1. price bug

适用范围：

- 模板保存、模板命中、严格回放、异常池、价格上墙、漏解析、错解析、命中不完整、群模板维护
- 只要任务和价格墙解析链路有关，除非只是改字符、标题、样式这类小活，默认优先走 `price bug`

执行原则：

- 主 agent 负责调度和验收，不把半成品甩出来
- 默认先查证现有链路：消息输入 -> 候选生成 -> 校验 -> 发布 -> 异常池 -> replay
- 任何改动前先说明风险，尤其是是否会影响 active、异常池、模板保存、严格回放
- 每次处理 price bug，顺手补单测、脚本、skill 或文档沉淀，避免同类问题重复靠 prompt 修

硬规则：

- 默认不推翻“一群一模板链路”，除非查证后确认它无法支撑目标
- 保存后的严格回放不通过，视为严重问题
- 目标不是“尽量解析”，而是“正确上墙”

### 2. live bug

适用范围：

- UI 排版、小交互、小文案、小逻辑
- 不涉及价格解析底层、不涉及回放正确性、不涉及模板发布语义

执行原则：

- 本地小改 -> 最小验证 -> 再考虑同步与提交
- 生产页面是第一真相，但不要在未验证情况下碰高风险链路
- 解析链路问题不要误归类为 live bug

## GSD 工作方式

在这个仓库里，进入实质性编辑前，优先走 GSD 工作流，保持 `.planning/` 与实现同步。

优先入口：

- `/gsd-quick`：小修、小文档、小范围代码调整
- `/gsd-debug`：问题定位、回放、异常调查
- `/gsd-execute-phase`：执行已规划 phase

初始化后的规划文档在 `.planning/`，开始工作前优先读：

1. `.planning/PROJECT.md`
2. `.planning/STATE.md`
3. `.planning/ROADMAP.md`
4. `.planning/REQUIREMENTS.md`
5. `.planning/research/SUMMARY.md`

当前 roadmap 聚焦：

- 候选生成
- 硬验证
- 事实保护
- `full_snapshot` / `delta_update`
- 异常沉淀
- replay
- 工业化修复
- shadow validation gate

不要在脱离 GSD 语境的情况下直接对 repo 做大改，除非用户明确要求绕过。

## 技术栈速记

- Python 3 + 标准库 WSGI：`wxbot/bookkeeping-platform/reporting_server.py`
- PostgreSQL：由 `require_postgres_dsn()` 强制约束
- Web UI：Python 生成 HTML 字符串 + 内联 JavaScript，位于 `bookkeeping_web/pages.py`
- WeChat 适配器：`wxbot/bookkeeping-platform/wechat_adapter/`
- WhatsApp 适配器：`wxbot/whatsapp-bookkeeping/src/`

## 禁止事项

- 不把未来自动化描述成已实现能力
- 不把 AI 当主解析链路或最终发布裁决者
- 不在报价解析、高风险区域做未经验证的大改
- 不忽视异常区、模板、字典的运营优先级
- 不默认把局部更新当 `full_snapshot`
- 不因为一次失败消息去清空旧 active
- 不让任何工具、脚本、Agent 绕开 validator / publisher 直接发布

## 最短启动路径

```bash
# Core
cd /Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform
BOOKKEEPING_CORE_TOKEN='test-token-123456' \
BOOKKEEPING_DB_DSN='postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping' \
BOOKKEEPING_MASTER_USERS='+84389225210' \
QUOTE_ADMIN_PASSWORD='119110' \
PYTHONPATH='/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform' \
./.venv/bin/python reporting_server.py --host 127.0.0.1 --port 8765

# WeChat 监听器
cd /Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform && python -m wechat_adapter.main

# WhatsApp 监听器
cd /Users/newlcc/SeeSee/repo/wxbot/whatsapp-bookkeeping && npm start
```

## graphify

This project has a graphify knowledge graph at `graphify-out/`.

Rules:

- Before answering architecture or codebase questions, read `graphify-out/GRAPH_REPORT.md` for god nodes and community structure
- If `graphify-out/wiki/index.md` exists, navigate it instead of reading raw files
- After modifying code files in this session, run `python3 -c "from graphify.watch import _rebuild_code; from pathlib import Path; _rebuild_code(Path('.'))"` to keep the graph current
