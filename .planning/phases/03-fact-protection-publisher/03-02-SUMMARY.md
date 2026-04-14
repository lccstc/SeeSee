---
phase: 03
plan: 02
title: Guarded publisher no-op and atomicity
status: completed
requirements:
  - FACT-01
  - FACT-02
files_changed:
  - wxbot/bookkeeping-platform/bookkeeping_core/quote_publisher.py
  - wxbot/bookkeeping-platform/bookkeeping_core/database.py
  - wxbot/bookkeeping-platform/sql/postgres_schema.sql
  - wxbot/bookkeeping-platform/tests/test_postgres_backend.py
  - wxbot/bookkeeping-platform/tests/test_runtime.py
completed_at: 2026-04-15
---

# Phase 03 Plan 03-02 Summary

The guarded publisher now fails safe before mutation, runs inside one PostgreSQL transaction and lock boundary, and rolls back cleanly when an apply step fails.

## What Changed

- Tightened `QuoteFactPublisher` so unsupported publish modes are explicit `no_op` results rather than partial/fake publishes.
- Added per-group PostgreSQL publish locking and active-row locking helpers in `database.py`, then used them inside the guarded publisher transaction.
- Backed the live-row invariant with the `quote_price_rows_one_live_row` unique index in `postgres_schema.sql`.
- Added PostgreSQL regressions for:
  - zero `publishable_rows` no-op before mutation
  - unsupported publish mode no-op
  - rollback after group deactivate failure
  - rollback after partial row apply failure
  - per-group publish lock serialization
  - live-row unique index enforcement

## Verification

- `python3 -m py_compile wxbot/bookkeeping-platform/bookkeeping_core/quote_publisher.py wxbot/bookkeeping-platform/bookkeeping_core/database.py wxbot/bookkeeping-platform/tests/test_postgres_backend.py wxbot/bookkeeping-platform/tests/test_runtime.py` — passed
- `BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_postgres_backend tests.test_runtime -v` — passed, 85 tests

## Deviations

- This wave still does not introduce `full_snapshot` / `delta_update` semantics; publisher custody remains explicit but mode semantics stay deferred to Phase 04.
- `.planning/STATE.md` was left out of the wave commit because it reflects orchestration state rather than wave-local code changes.
- `graphify` rebuild remains environment-blocked until the local `graphify` module is available.

## Self-Check

- Summary file created at `.planning/phases/03-fact-protection-publisher/03-02-SUMMARY.md`
- All modified code files remain inside the plan write scope
