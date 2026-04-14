---
phase: 08-experimental-active-wall-gate
plan: 01
subsystem: runtime
tags: [quotes, experimental-wall, guarded-publisher, downstream-off]
requires:
  - phase: 03-fact-protection-publisher
    provides: guarded publisher custody
  - phase: 04-snapshot-delta-semantics
    provides: delta/full publish semantics
provides:
  - explicit experimental active wall runtime mode
  - real wall mutation through guarded publisher only
  - downstream-off execution boundary
affects: [quote-wall, runtime, publisher-custody]
tech-stack:
  added: []
  patterns:
    - real wall mutation remains validator-owned and publisher-owned
    - experimental mode never emits downstream actions
key-files:
  modified:
    - wxbot/bookkeeping-platform/bookkeeping_core/quotes.py
    - wxbot/bookkeeping-platform/bookkeeping_web/app.py
    - wxbot/bookkeeping-platform/tests/test_runtime.py
    - wxbot/bookkeeping-platform/tests/test_webapp.py
requirements-completed: []
completed: 2026-04-15
---

# Phase 08 Plan 01: Experimental Wall Runtime Mode Summary

**让实验墙开始真实更新，但仍然只允许经过 guarded publisher，并继续关闭下游动作**

## Accomplishments

- 在 runtime 中新增显式 `BOOKKEEPING_QUOTE_WALL_MODE`，把 `validation_only` 与 `experimental_active_wall` 区分开。
- `QuoteCaptureService` 在实验墙模式下会真实调用 guarded publisher，仍然只消费 validator 持有的 `publishable_rows`。
- 实验墙模式不再是假跑，但也没有新增任何事实写入旁路。
- `/api/quotes/board`、`/api/quotes/exceptions`、`/api/quotes/evidence` 现在都会回显实验墙模式状态，方便 operator 判断当前运行边界。
- runtime 保持下游动作关闭；即使实验墙真实更新，`actions` 仍为空。

## Files Modified

- `wxbot/bookkeeping-platform/bookkeeping_core/quotes.py` - 新增实验墙 runtime mode、mode 描述和 guarded publisher 调用开关。
- `wxbot/bookkeeping-platform/bookkeeping_web/app.py` - 对 quotes 相关接口追加实验墙 mode payload。
- `wxbot/bookkeeping-platform/tests/test_runtime.py` - 锁住实验墙真实上墙和 downstream-off 行为。
- `wxbot/bookkeeping-platform/tests/test_webapp.py` - 锁住通过 core 接口更新实验墙但不产生下游动作的 web 回归。

## Verification

- `BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_postgres_backend tests.test_runtime tests.test_webapp -v`
  - `Ran 180 tests`
  - `OK`

## Notes

- 实验墙模式不是正式生产 authority，只是让你本人运营的这面墙开始真实更新。
- guarded publisher custody、snapshot-safe defaults、no-op on zero publishable rows 都保持不变。
