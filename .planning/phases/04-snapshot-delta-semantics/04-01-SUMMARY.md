---
phase: 04
plan: 01
title: Durable snapshot decision surface
status: completed
requirements:
  - SNAP-01
  - OPS-02
files_changed:
  - wxbot/bookkeeping-platform/bookkeeping_core/quote_snapshot.py
  - wxbot/bookkeeping-platform/bookkeeping_core/quote_candidates.py
  - wxbot/bookkeeping-platform/bookkeeping_core/quotes.py
  - wxbot/bookkeeping-platform/bookkeeping_core/database.py
  - wxbot/bookkeeping-platform/sql/postgres_schema.sql
  - wxbot/bookkeeping-platform/tests/test_postgres_backend.py
  - wxbot/bookkeeping-platform/tests/test_quote_validation.py
  - wxbot/bookkeeping-platform/tests/test_quote_exception_corpus.py
completed_at: 2026-04-15
---

# Phase 04 Plan 04-01 Summary

Wave 1 introduced a durable, message-level snapshot decision model so `full_snapshot` / `delta_update` semantics are no longer implied parser hints.

## What Changed

- Added [`bookkeeping_core/quote_snapshot.py`](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_core/quote_snapshot.py) with deterministic hypothesis helpers, effective-decision resolution, and guarded publish-mode mapping.
- Extended [`QuoteCandidateMessage`](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_core/quote_candidates.py) to preserve snapshot evidence alongside the existing message-level candidate contract.
- Taught runtime quote capture in [`quotes.py`](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_core/quotes.py) to record evidence-backed system hypotheses instead of hard-coding every message to `unresolved`.
- Added additive PostgreSQL persistence in [`quote_snapshot_decisions`](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/sql/postgres_schema.sql) and corresponding DB helpers in [`database.py`](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_core/database.py).
- Added deterministic classification regressions and corpus-backed snapshot judgments in [`tests.test_quote_validation`](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/tests/test_quote_validation.py) and [`tests.test_quote_exception_corpus`](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/tests/test_quote_exception_corpus.py).

## Verification

- `python3 -m py_compile bookkeeping_core/quote_snapshot.py bookkeeping_core/quote_candidates.py bookkeeping_core/quotes.py bookkeeping_core/database.py tests/test_postgres_backend.py tests/test_quote_validation.py tests/test_quote_exception_corpus.py` — passed
- `PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_quote_validation tests.test_quote_exception_corpus -v` — passed, 16 tests
- `BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_postgres_backend -v` — passed as part of the final 171-test PostgreSQL regression suite

## Deviations

- Kept message-level classification conservative: ambiguous messages remain `unresolved` instead of being promoted into destructive semantics.
- Did not connect operator confirmation or active-fact mutation in Wave 1; those stayed scoped to later waves.
- Graph rebuild command still failed in this environment because the `graphify` module is not installed locally.

## Self-Check

- Summary file created at `.planning/phases/04-snapshot-delta-semantics/04-01-SUMMARY.md`
- Durable snapshot lineage now exists separately from parser-side publish hints
