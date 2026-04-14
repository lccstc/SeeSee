---
phase: 07-operator-verification-failure-dictionary
plan: 03
subsystem: database
tags: [quotes, failure-dictionary, repair-lexicon, repair-cases]
requires:
  - phase: 07-operator-verification-failure-dictionary
    provides: operator verification workbench and message-level evidence payload
  - phase: 05-exception-repair-state-machine
    provides: durable repair cases and attempt history
  - phase: 06-constrained-auto-remediation-loop
    provides: bounded remediation logs and failure reasons
provides:
  - structured failure dictionary storage
  - search/read API for the operator workbench
  - linkage from live cases to handbook entries
affects: [repair-cases, operators, future-agents, exception-pool]
tech-stack:
  added:
    - quote_failure_dictionary_entries
  patterns:
    - failure dictionary stores structured guidance, not raw message blobs
    - live repair history aggregates into handbook entries with frequency and case references
key-files:
  created: []
  modified:
    - wxbot/bookkeeping-platform/bookkeeping_core/database.py
    - wxbot/bookkeeping-platform/bookkeeping_web/app.py
    - wxbot/bookkeeping-platform/bookkeeping_web/pages.py
    - wxbot/bookkeeping-platform/tests/test_postgres_backend.py
    - wxbot/bookkeeping-platform/tests/test_webapp.py
    - .planning/research/FAILURE-DICTIONARY.md
requirements-completed: [INDU-03]
completed: 2026-04-15
---

# Phase 07 Plan 03: Failure Dictionary / Repair Lexicon Summary

**把 repair-case 历史从“只有当前长上下文看得懂的日志”升级成可检索、可复用、可回写的修复词典**

## Accomplishments

- 增加 `quote_failure_dictionary_entries` 作为结构化词典表，保存 `failure_code / symptom / root_cause / preferred_scope / forbidden fixes / fixtures / tests / case refs`。
- 让词典在读取时自动同步：
  - 先写入 builtin handbook seeds
  - 再从真实 `quote_repair_cases` / `quote_repair_case_attempts` 聚合频次、相关群和 case 引用
- 把相关词条接进 message evidence payload，并提供 `/api/quotes/failure-dictionary` 搜索 API。
- 在 quotes workbench 里新增 `修复词典` 面板和 case 内的 `相关修复词条` 区域，让 operator 和新 agent 不靠长会话记忆也能先查词条再修。

## Files Modified

- `wxbot/bookkeeping-platform/bookkeeping_core/database.py` - 新增 failure dictionary schema、upsert、聚合同步和搜索方法，并把相关词条挂入 evidence payload。
- `wxbot/bookkeeping-platform/bookkeeping_web/app.py` - 新增只读词典 API。
- `wxbot/bookkeeping-platform/bookkeeping_web/pages.py` - 新增 quotes 页修复词典搜索面板和 evidence modal 的相关词条区块。
- `wxbot/bookkeeping-platform/tests/test_postgres_backend.py` - 覆盖 repair history -> searchable entry 聚合回归。
- `wxbot/bookkeeping-platform/tests/test_webapp.py` - 覆盖 failure dictionary endpoint、evidence 关联词条、quotes 页 render。
- `.planning/research/FAILURE-DICTIONARY.md` - 记录当前已实现的 handbook 形态与原则。

## Verification

- `python3 -m py_compile ...` 通过
- `BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_postgres_backend -v`
  - `Ran 38 tests`
  - `OK`
- `BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_webapp -v`
  - `Ran 82 tests`
  - `OK`

## Notes

- 词典不会复制 repair case 原文全文；原文继续留在 repair case，词典只保存结构化指导。
- 当前内置词条种子覆盖了 `validator_mixed_outcome`、骨架扩张护栏、supermarket 语义污染、`strict_match_failed`、`missing_group_template` 等稳定模式。
