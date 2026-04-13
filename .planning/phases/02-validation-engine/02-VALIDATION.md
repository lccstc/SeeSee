---
phase: 02
slug: validation-engine
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-04-14
---

# Phase 02 — Validation Strategy

> Validation contract for Phase 02 planning and execution.

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `unittest` |
| **Database** | PostgreSQL via `BOOKKEEPING_TEST_DSN` |
| **Quick run command** | `cd /Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform && BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_postgres_backend tests.test_quote_validation tests.test_runtime tests.test_webapp -v` |
| **Full suite command** | `cd /Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform && BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest -v` |
| **Estimated runtime** | ~180 seconds |

## Sampling Rate

- After every task commit: run the targeted module(s) touched by the change
- After every plan wave: run the quick Phase 02 suite
- Before phase verification: Phase 02 quick suite must be green on PostgreSQL
- Max feedback latency: 180 seconds

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Secure Behavior | Test Type | Automated Command | Status |
|---------|------|------|-------------|-----------------|-----------|-------------------|--------|
| 02-01-01 | 01 | 1 | VALI-01 | Validation run + row decision persistence is durable and separate from candidate evidence | integration | `cd /Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform && BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_postgres_backend -v` | ⬜ pending |
| 02-02-01 | 02 | 2 | VALI-01 | Runtime and replay automatically create validation results after candidate persistence | integration | `cd /Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform && BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_quote_validation tests.test_runtime tests.test_webapp -v` | ⬜ pending |
| 02-03-01 | 03 | 3 | VALI-02, VALI-03 | Mixed row decisions and `publishable_rows` separation are explicit, structured, and queryable | integration | `cd /Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform && BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_quote_validation tests.test_runtime tests.test_webapp -v` | ⬜ pending |

## Wave 0 Requirements

- [ ] create `wxbot/bookkeeping-platform/tests/test_quote_validation.py`
- [ ] extend `tests/test_postgres_backend.py` for validation-run persistence and FK coverage
- [ ] extend `tests/test_runtime.py` so runtime candidate capture also proves validation execution
- [ ] extend `tests/test_webapp.py` so replay candidate runs also prove validation execution
- [ ] PostgreSQL test DB reachable at `127.0.0.1:5432`

If PostgreSQL is unavailable, execution must mark verification blocked rather than silently skipping it.

## Manual-Only Verifications

Manual inspection is optional. Phase 02 acceptance should stay automated because validator custody is too easy to regress invisibly.

## Validation Sign-Off

- [x] each plan has an automated verification target
- [x] validation relies on PostgreSQL, not SQLite shortcuts
- [x] mixed-outcome behavior is explicitly covered
- [x] no watch-mode or non-deterministic test loop is required
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-04-14

