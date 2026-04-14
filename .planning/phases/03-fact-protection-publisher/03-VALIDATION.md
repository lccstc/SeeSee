---
phase: 03
slug: fact-protection-publisher
status: planned
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-15
---

# Phase 03 — Validation Strategy

> Validation contract for guarded active-quote publication work.

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `unittest` |
| **Quick run command** | `cd wxbot/bookkeeping-platform && BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_postgres_backend tests.test_runtime -v` |
| **Full suite command** | `cd wxbot/bookkeeping-platform && BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_postgres_backend tests.test_runtime tests.test_webapp -v` |
| **Estimated runtime** | ~180 seconds |

## Sampling Rate

- After every task commit: run the quick run command
- After every plan wave: run the full suite command
- Before verification: full suite must be green
- Max feedback latency: 180 seconds

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Secure Behavior | Test Type | Automated Command | Status |
|---------|------|------|-------------|-----------------|-----------|-------------------|--------|
| 03-01-01 | 01 | 1 | FACT-01, FACT-03 | only one guarded publisher owns active-fact mutation entrypoints | unit/integration | `tests.test_postgres_backend tests.test_runtime` | ✅ planned |
| 03-01-02 | 01 | 1 | FACT-01 | publish helpers no longer commit independently and can participate in one transaction | unit/integration | `tests.test_postgres_backend tests.test_runtime` | ✅ planned |
| 03-02-01 | 02 | 2 | FACT-01, FACT-02 | zero publishable rows become explicit no-op before any active-row mutation | integration | `tests.test_postgres_backend tests.test_runtime` | ✅ planned |
| 03-02-02 | 02 | 2 | FACT-01 | injected failure during publish leaves prior active rows untouched under one transaction/lock boundary | integration | `tests.test_postgres_backend tests.test_runtime` | ✅ planned |
| 03-03-01 | 03 | 3 | FACT-03 | web routes and scripts cannot delete or mutate active rows outside the publisher | integration | `tests.test_webapp tests.test_postgres_backend` | ✅ planned |
| 03-03-02 | 03 | 3 | FACT-03 | architecture test blocks forbidden low-level mutation callsites outside allowlisted publisher/test setup paths | unit | `tests.test_runtime tests.test_webapp` | ✅ planned |

## Wave 0 Requirements

No separate Wave 0 is required.

Missing regression surfaces should be created inside the first task that needs them:

- publisher atomicity / rollback tests in `tests.test_postgres_backend`
- runtime no-op publish tests in `tests.test_runtime`
- web-route bypass regression and structural callsite guard tests in `tests.test_webapp` or a new focused test module

## Manual-Only Verifications

| Behavior | Why Manual | Test Instructions |
|----------|------------|-------------------|
| Proof wording for replay/apply/delete surfaces still communicates “未改动报价墙” unless a guarded publish explicitly ran | trust wording is business-sensitive | Review one replay/result-save/delete flow and confirm the UI never implies silent publish or silent delete |
| Guarded publisher outcomes remain understandable to operator workflows before Phase 07 workbench arrives | operator trust is not binary | Review one no-op publish and one applied publish result and confirm both explain why facts did or did not change |

## Validation Sign-Off

- [x] Every auto task has an automated verify path
- [x] No more than two tasks between meaningful regressions
- [x] Wave-local feedback stays under 180 seconds
- [x] Manual verification is reserved for wording/trust checks
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** planned
