---
phase: 08
slug: experimental-active-wall-gate
status: planned
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-15
---

# Phase 08 — Validation Strategy

> Validation contract for the experimental active wall gate.

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `unittest` |
| **Quick run command** | `cd wxbot/bookkeeping-platform && BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_postgres_backend tests.test_runtime tests.test_webapp -v` |
| **Estimated runtime** | ~240 seconds |

## Sampling Rate

- After every task commit: run targeted tests for the touched layer
- After every wave: run the quick run command
- Before verification: full PostgreSQL-backed quick run must be green

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Secure Behavior | Test Type | Automated Command | Status |
|---------|------|------|-------------|-----------------|-----------|-------------------|--------|
| 08-01-01 | 01 | 1 | GOV-01 | experimental mode enables real wall mutation only through guarded publisher custody | integration | `tests.test_postgres_backend tests.test_runtime` | ✅ planned |
| 08-01-02 | 01 | 1 | GOV-01 | downstream actions remain disabled while experimental wall mode is on | integration | `tests.test_runtime tests.test_webapp` | ✅ planned |
| 08-02-01 | 02 | 2 | GOV-01 | `/quotes` exposes operator-visible experimental mode status and wall health metrics | integration | `tests.test_webapp` | ✅ planned |
| 08-02-02 | 02 | 2 | GOV-01 | observation surface explains real wall updates, untouched rows, mixed outcomes, and escalations without overstating authority | integration/manual | `tests.test_webapp` | ✅ planned |
| 08-03-01 | 03 | 3 | GOV-01 | promotion criteria are durable, visible, and tied to measurable wall-health indicators | integration | `tests.test_postgres_backend tests.test_webapp` | ✅ planned |
| 08-03-02 | 03 | 3 | GOV-01 | experimental mode still does not imply downstream automation or formal production handoff | integration/manual | `tests.test_runtime tests.test_webapp` | ✅ planned |

## Manual-Only Verifications

| Behavior | Why Manual | Test Instructions |
|----------|------------|-------------------|
| Operator can tell at a glance that the wall is real-but-experimental | this is partly wording and operator trust judgment | Open `/quotes` and verify the wall clearly identifies itself as experimental, real-updating, and downstream-off |
| Promotion criteria feel actionable instead of ceremonial | business readability matters | Read the promotion panel / document and confirm it tells you what to watch daily before any formal handoff |

## Validation Sign-Off

- [x] Every auto task has an automated verify path
- [x] No more than two tasks between meaningful regressions
- [x] Manual verification is reserved for operator trust and promotion-readiness checks
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** planned
