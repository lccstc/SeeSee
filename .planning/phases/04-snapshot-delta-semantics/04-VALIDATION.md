---
phase: 04
slug: snapshot-delta-semantics
status: planned
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-15
---

# Phase 04 — Validation Strategy

> Validation contract for snapshot/delta semantics on top of the guarded publisher.

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `unittest` |
| **Quick run command** | `cd wxbot/bookkeeping-platform && BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_postgres_backend tests.test_runtime tests.test_quote_validation -v` |
| **Full suite command** | `cd wxbot/bookkeeping-platform && BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_postgres_backend tests.test_runtime tests.test_webapp tests.test_quote_validation tests.test_quote_exception_corpus -v` |
| **Estimated runtime** | ~240 seconds |

## Sampling Rate

- After every task commit: run the quick run command
- After every wave: run the full suite command
- Before verification: full suite must be green
- Max feedback latency: 240 seconds

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Secure Behavior | Test Type | Automated Command | Status |
|---------|------|------|-------------|-----------------|-----------|-------------------|--------|
| 04-01-01 | 01 | 1 | SNAP-01 | system and operator snapshot decisions persist with durable lineage and unresolved remains explicit | unit/integration | `tests.test_postgres_backend tests.test_runtime tests.test_quote_validation` | ✅ planned |
| 04-01-02 | 01 | 1 | SNAP-01 | corpus-backed message-level hypothesis logic is deterministic and auditable | unit | `tests.test_quote_exception_corpus tests.test_quote_validation` | ✅ planned |
| 04-02-01 | 02 | 2 | SNAP-02 | unresolved and delta messages never inactivate unseen active rows | integration | `tests.test_postgres_backend tests.test_runtime` | ✅ planned |
| 04-02-02 | 02 | 2 | SNAP-03 | only confirmed full snapshots may inactivate unseen prior SKUs | integration | `tests.test_postgres_backend tests.test_runtime` | ✅ planned |
| 04-03-01 | 03 | 3 | OPS-02 | operator can confirm/override snapshot semantics without mutating active facts as a side effect | integration | `tests.test_webapp tests.test_postgres_backend` | ✅ planned |
| 04-03-02 | 03 | 3 | SNAP-01, SNAP-02, SNAP-03 | replay/proof surfaces show snapshot decision evidence clearly and do not imply silent publish | integration/manual | `tests.test_webapp tests.test_runtime` | ✅ planned |

## Wave 0 Requirements

No separate Wave 0 is required.

Missing regression surfaces should be created inside the first task that needs them:

- snapshot decision persistence regressions in `tests.test_postgres_backend`
- runtime snapshot-aware publish semantics in `tests.test_runtime`
- minimal operator confirmation regressions in `tests.test_webapp`

## Manual-Only Verifications

| Behavior | Why Manual | Test Instructions |
|----------|------------|-------------------|
| One confirmed `full_snapshot` sample and one unresolved sample feel correct to the operator | business trust depends on semantics, not just code branches | In the dev UI, inspect a full-board sample and a delta sample, confirm the wording and current decision match business intuition |
| Confirmation flow does not read like “already上墙” | trust wording matters before Phase 07 workbench | Confirm the page says the decision was recorded, and that active-fact mutation only happens if a guarded publish is separately triggered |

## Validation Sign-Off

- [x] Every auto task has an automated verify path
- [x] No more than two tasks between meaningful regressions
- [x] Wave-local feedback stays under 240 seconds
- [x] Manual verification is reserved for wording/trust checks
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** planned
