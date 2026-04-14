---
phase: 08-experimental-active-wall-gate
plan: 02
subsystem: webapp
tags: [quotes, observation-cockpit, metrics, watchlist]
requires:
  - phase: 08-experimental-active-wall-gate
    provides: experimental wall execution mode
provides:
  - experimental wall observation cockpit on /quotes
  - today-level wall health metrics
  - high-risk group watchlist
affects: [quotes-page, operator-observation, repair-prioritization]
tech-stack:
  added: []
  patterns:
    - wall-level metrics belong on the main quote page, not only inside message drilldowns
    - watchlist remains factual and links back into risk/evidence tools without widening authority
key-files:
  modified:
    - wxbot/bookkeeping-platform/bookkeeping_core/database.py
    - wxbot/bookkeeping-platform/bookkeeping_web/app.py
    - wxbot/bookkeeping-platform/bookkeeping_web/pages.py
    - wxbot/bookkeeping-platform/tests/test_postgres_backend.py
    - wxbot/bookkeeping-platform/tests/test_webapp.py
requirements-completed: []
completed: 2026-04-15
---

# Phase 08 Plan 02: Experimental Wall Observation Cockpit Summary

**把 `/quotes` 补成真正的实验墙观察台，让 operator 一眼判断今天墙稳不稳、先盯哪个群**

## Accomplishments

- 在数据库层新增实验墙总览聚合，按群统计：
  - 今日上墙消息/行数
  - 今日新增异常
  - 今日 mixed outcome
  - 今日修补成功/升级
  - 今日整版快照风险
- `/api/quotes/board` 现在会附带：
  - `experimental_wall_overview`
  - `experimental_wall_gate`
- `/quotes` 顶部新增实验墙横幅、6 个今日指标卡片和高风险群 watchlist，不用先钻异常卡才能判断今天的墙是否健康。
- watchlist 卡片会把你带回风险池和修复词典，帮助你快速进入已有的异常/修补工具链，而不是再加新的 mutation 入口。

## Files Modified

- `wxbot/bookkeeping-platform/bookkeeping_core/database.py` - 新增实验墙 overview 聚合和升格 gate 聚合。
- `wxbot/bookkeeping-platform/bookkeeping_web/app.py` - 把 overview/gate payload 接到 board API。
- `wxbot/bookkeeping-platform/bookkeeping_web/pages.py` - 新增实验墙 banner、metrics、watchlist、升格边界面板和渲染逻辑。
- `wxbot/bookkeeping-platform/tests/test_postgres_backend.py` - 锁住 experimental overview 的数据库级合同。
- `wxbot/bookkeeping-platform/tests/test_webapp.py` - 锁住 `/quotes` 页面和 board payload 中新增的实验墙观察台结构。

## Verification

- `python3 -m py_compile wxbot/bookkeeping-platform/bookkeeping_core/database.py wxbot/bookkeeping-platform/bookkeeping_web/app.py wxbot/bookkeeping-platform/bookkeeping_web/pages.py wxbot/bookkeeping-platform/tests/test_postgres_backend.py wxbot/bookkeeping-platform/tests/test_webapp.py`
  - Passed
- `BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_postgres_backend.PostgresBackendTests.test_get_quote_experimental_wall_overview_aggregates_operational_metrics tests.test_webapp.WebAppTests.test_quotes_page_renders_board_and_exception_sections tests.test_webapp.WebAppTests.test_experimental_wall_mode_updates_board_through_core_without_downstream_actions -v`
  - `Ran 3 tests`
  - `OK`

## Notes

- 这块观察台是 operator cockpit，不是新的发布控制台。
- 指标故意偏保守，重点是让你先看“墙今天稳不稳、风险在哪、先修哪个群”。
