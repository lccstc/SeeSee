---
phase: 07-operator-verification-failure-dictionary
plan: 02
subsystem: webapp
tags: [quotes, operator-workbench, proof-only, evidence]
requires:
  - phase: 07-operator-verification-failure-dictionary
    provides: message-level evidence payload from 07-01
provides:
  - quotes-page verification workbench for one message
  - proof-only wording for candidate / validation / snapshot / repair / publish reasoning
  - read-only visibility into untouched rows and would-inactivate rows
affects: [operator-debugging, quotes-page, exception-pool]
tech-stack:
  added: []
  patterns:
    - verification UI is read-only and must never imply publish authority
    - operators inspect grouped row outcomes instead of raw JSON blobs
key-files:
  created: []
  modified:
    - wxbot/bookkeeping-platform/bookkeeping_web/pages.py
    - wxbot/bookkeeping-platform/bookkeeping_web/app.py
    - wxbot/bookkeeping-platform/tests/test_webapp.py
requirements-completed: [EVID-02, OPS-01]
completed: 2026-04-15
---

# Phase 07 Plan 02: Operator Verification Workbench Summary

**把 message-level evidence 变成 quotes 页里的可读验证工作台，并且保持 proof-only 语义**

## Accomplishments

- 在 quotes 页新增 `验证工作台`，可查看单条消息的消息元数据、异常原因、snapshot 决策、publish reasoning、repair 状态。
- 候选 / 校验结果按 `publishable`、`held`、`rejected` 分组展示，不再要求运营读原始 JSON。
- 把 `untouched_active_rows` 与 `would_inactivate_active_rows` 直接展示出来，让运营能看懂“为什么这条消息没改墙”。
- 所有 operator wording 都明确保留在 `仅展示证据，未改动报价墙` 这一条线内。

## Files Modified

- `wxbot/bookkeeping-platform/bookkeeping_web/pages.py` - 新增验证工作台 modal、验证详情入口、proof-only 渲染与修复词条承接位。
- `wxbot/bookkeeping-platform/bookkeeping_web/app.py` - 暴露 message-level evidence API 的只读入口。
- `wxbot/bookkeeping-platform/tests/test_webapp.py` - 锁住 quotes 页 render、验证工作台文案、evidence endpoint 的回归。

## Verification

- `python3 -m py_compile ...` 通过
- `BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_webapp -v`
  - `Ran 82 tests`
  - `OK`

## Notes

- 这块工作台只解释 candidate / validation / snapshot / repair / publish reasoning，不新增任何发布权。
- 词条搜索和 repair lexicon 入口在下一 wave 与 failure dictionary 一起补齐。
