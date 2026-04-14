---
phase: 04
plan: 02
title: Snapshot-aware guarded publisher semantics
status: completed
requirements:
  - SNAP-02
  - SNAP-03
  - FACT-01
files_changed:
  - wxbot/bookkeeping-platform/bookkeeping_core/quote_publisher.py
  - wxbot/bookkeeping-platform/bookkeeping_core/database.py
  - wxbot/bookkeeping-platform/bookkeeping_core/quotes.py
  - wxbot/bookkeeping-platform/tests/test_postgres_backend.py
  - wxbot/bookkeeping-platform/tests/test_runtime.py
completed_at: 2026-04-15
---

# Phase 04 Plan 04-02 Summary

Wave 2 wired snapshot decisions into the guarded publisher so unresolved messages behave as delta-safe updates and only confirmed full snapshots may inactivate unseen prior SKUs.

## What Changed

- Extended [`QuoteFactPublisher`](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_core/quote_publisher.py) with explicit publish modes:
  - `validation_only`
  - `delta_safe_upsert_only`
  - `confirmed_full_snapshot_apply`
- Made the publisher derive effective publish semantics from persisted snapshot decisions instead of trusting caller intent.
- Added [`deactivate_quote_rows_absent_from_snapshot(...)`](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_core/database.py) so confirmed full snapshots only inactivate active rows absent from the current publishable set.
- Kept runtime validation-first in [`quotes.py`](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_core/quotes.py) while surfacing:
  - `proposed_publish_mode`
  - `resolved_snapshot_decision`
  - `snapshot_decision_source`
- Added PostgreSQL/runtime regressions proving:
  - unresolved defaults to delta-safe no-destructive behavior
  - confirmed full snapshots may inactivate unseen rows
  - runtime still does not auto-apply snapshot-aware publish authority

## Verification

- `python3 -m py_compile bookkeeping_core/quote_publisher.py bookkeeping_core/database.py bookkeeping_core/quotes.py tests/test_postgres_backend.py tests/test_runtime.py` — passed
- `BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_postgres_backend tests.test_runtime -v` — passed as part of the final 171-test PostgreSQL regression suite

## Deviations

- Runtime still invokes the guarded publisher in `validation_only` mode; Phase 04 only exposed semantics, it did not hand v1 automatic publish authority.
- No new bypass route was added for snapshot-aware publication; Phase 03 custody remained intact.
- Graph rebuild command still failed in this environment because the `graphify` module is not installed locally.

## Self-Check

- Summary file created at `.planning/phases/04-snapshot-delta-semantics/04-02-SUMMARY.md`
- Default unresolved behavior is now provably delta-safe and fact-neutral
