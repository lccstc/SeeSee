---
phase: 08-experimental-active-wall-gate
plan: 03
subsystem: governance
tags: [quotes, promotion-boundary, downstream-off, experimental-wall]
requires:
  - phase: 08-experimental-active-wall-gate
    provides: experimental wall overview metrics
provides:
  - durable promotion criteria from experimental wall to formal authority
  - operator-visible downstream-off boundary
  - business-language operating standard for P8
affects: [project-governance, quotes-page, operator-expectations]
tech-stack:
  added: []
  patterns:
    - promotion must be tied to observed wall behavior, not vague confidence
    - UI and docs must tell the same story about experimental scope
key-files:
  modified:
    - .planning/PROJECT.md
    - .planning/ROADMAP.md
    - PROJECT/P8单人运营实验墙上线标准.md
    - wxbot/bookkeeping-platform/bookkeeping_core/database.py
    - wxbot/bookkeeping-platform/bookkeeping_web/app.py
    - wxbot/bookkeeping-platform/bookkeeping_web/pages.py
    - wxbot/bookkeeping-platform/tests/test_webapp.py
requirements-completed: [GOV-01]
completed: 2026-04-15
---

# Phase 08 Plan 03: Promotion Boundary Summary

**把“实验墙能做什么、不能做什么、什么时候才有资格升格”写进系统和文档，而不是留在聊天上下文里**

## Accomplishments

- 在 `PROJECT/P8单人运营实验墙上线标准.md` 中补全了从实验墙升格到正式生产标准的业务门槛：
  - 连续观察期
  - 异常池增长控制
  - mixed outcome 负担
  - repair 升级压力
  - 关键群稳定度
  - 误清/误上墙事故为零
  - 下游动作继续单独评估
- `.planning/PROJECT.md` 和 `.planning/ROADMAP.md` 现在也明确写进：实验墙允许真实更新，但不自动授予正式生产 authority 或下游动作。
- `/quotes` 顶部新增 `升格边界` 面板，operator 打开页面就能看到：
  - 当前仍是实验墙
  - 下游动作继续关闭
  - 升格条件是基于真实观察指标，而不是“感觉差不多”

## Files Modified

- `.planning/PROJECT.md` - 补充实验墙的治理决策。
- `.planning/ROADMAP.md` - 把 Phase 08 的升格门槛改成可观察的墙行为。
- `PROJECT/P8单人运营实验墙上线标准.md` - 补齐业务语言版 go/no-go 标准。
- `wxbot/bookkeeping-platform/bookkeeping_core/database.py` - 新增 promotion gate 聚合。
- `wxbot/bookkeeping-platform/bookkeeping_web/app.py` - 追加 promotion gate payload。
- `wxbot/bookkeeping-platform/bookkeeping_web/pages.py` - 新增 operator-facing 升格边界面板。
- `wxbot/bookkeeping-platform/tests/test_webapp.py` - 锁住升格边界面板在 `/quotes` 中可见。

## Verification

- `BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_webapp -v`
  - included in full Phase 08 regression
  - `OK`

## Notes

- 这一步不是宣告“可以正式生产”，而是把“不可以自动漂移成正式生产”这件事写死。
- 实验墙升格以后，也不代表通知、记账、结算、外发这些下游动作会自动一起开启。
