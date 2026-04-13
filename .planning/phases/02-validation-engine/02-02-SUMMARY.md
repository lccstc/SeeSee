---
phase: 02-validation-engine
plan: 02
subsystem: validation
tags: [postgres, validation, replay, runtime, quote-wall, testing]
requires:
  - phase: 02-validation-engine
    provides: validator contract and dedicated validation persistence tables from 02-01
provides:
  - deterministic schema validation for persisted quote candidate documents
  - automatic validation runs for runtime and replay candidate bundles
  - explicit no-publish verdicts for zero-row candidate documents
affects: [validation-engine, fact-protection-publisher, replay, quote-wall]
tech-stack:
  added: []
  patterns:
    - shared validator entrypoint reused by runtime and replay
    - candidate persistence immediately followed by durable validation persistence
key-files:
  created: [wxbot/bookkeeping-platform/tests/test_quote_validation.py]
  modified:
    - wxbot/bookkeeping-platform/bookkeeping_core/quote_validation.py
    - wxbot/bookkeeping-platform/bookkeeping_core/quotes.py
    - wxbot/bookkeeping-platform/bookkeeping_web/app.py
    - wxbot/bookkeeping-platform/tests/support/postgres_test_case.py
    - wxbot/bookkeeping-platform/tests/test_runtime.py
    - wxbot/bookkeeping-platform/tests/test_webapp.py
key-decisions:
  - "Runtime and replay both call the same validate_quote_candidate_document entrypoint after candidate persistence."
  - "Zero-row candidate documents persist an explicit no_publish validation run instead of relying on absence."
patterns-established:
  - "Validation execution pattern: record quote candidate bundle -> load persisted candidate rows -> validate -> record quote_validation_run"
  - "Zero-row safety pattern: parser-empty candidate documents still receive message-level validator reasons"
requirements-completed: [VALI-01]
duration: 21min
completed: 2026-04-13
---

# Phase 02 Plan 02: Validation Runtime Wiring Summary

**Schema validation now runs automatically after every runtime and replay candidate bundle, and zero-row candidate documents persist explicit no-publish verdicts**

## Performance

- **Duration:** 21 min
- **Started:** 2026-04-13T19:21:10Z
- **Completed:** 2026-04-13T19:42:35Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- Added `validate_quote_candidate_document` to classify persisted candidate rows with stable schema rejection codes and explicit message-level no-publish results.
- Wired runtime quote capture so every stored candidate bundle immediately records a `quote_validation_run`, including zero-row missing-template documents.
- Wired replay harvest save to use the same validator entrypoint and expose `validation_run_id`, with PostgreSQL regressions covering runtime and replay custody.

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement deterministic schema validation for candidate documents and rows** - `0fd125e` (feat)
2. **Task 2: Run validation automatically in runtime and replay paths** - `e13c311` (feat)

## Files Created/Modified

- `wxbot/bookkeeping-platform/bookkeeping_core/quote_validation.py` - Shared schema validator entrypoint, message-level no-publish handling, and row-shape helpers for persisted candidate rows.
- `wxbot/bookkeeping-platform/bookkeeping_core/quotes.py` - Runtime candidate capture now persists validator runs immediately after candidate storage.
- `wxbot/bookkeeping-platform/bookkeeping_web/app.py` - Replay candidate storage now validates through the same entrypoint and returns `validation_run_id`.
- `wxbot/bookkeeping-platform/tests/test_quote_validation.py` - Focused validator logic coverage for schema pass/fail and zero-row documents.
- `wxbot/bookkeeping-platform/tests/test_runtime.py` - PostgreSQL regression coverage for runtime validation runs and zero-row no-publish persistence.
- `wxbot/bookkeeping-platform/tests/test_webapp.py` - Replay regression coverage proving harvest replay creates a validation run without mutating active quote facts.

## Decisions Made

- Reused the same pure validator entrypoint from both runtime and replay so later replay comparisons consume identical validation behavior.
- Kept validation persistence outside candidate rows and quote facts, returning only `validation_run_id` metadata to prove custody.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- The first attempt at the Phase 02 quick suite hit `psycopg.errors.DeadlockDetected` in `PostgresTestCase.tearDown()` because PostgreSQL auto-backup `pg_dump` processes overlapped with per-test schema cleanup. The fix was to disable `BOOKKEEPING_AUTO_BACKUP_ON_CLOSE` inside `tests/support/postgres_test_case.py`, after which the full quick suite passed.
- `graphify` rebuild still fails with `ModuleNotFoundError: No module named 'graphify'`, matching the pre-existing blocker already recorded in `.planning/STATE.md`.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 02-03 can now add business-rule validation on top of a stable schema-validation custody layer that already runs in runtime and replay.
- Phase 03 publisher work can rely on persisted message-level no-publish decisions instead of inferring from missing validation rows.

## Self-Check: PASSED

- Found summary file: `.planning/phases/02-validation-engine/02-02-SUMMARY.md`
- Found task commit: `0fd125e`
- Found task commit: `e13c311`
- Verified `BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_quote_validation tests.test_runtime tests.test_webapp -v` passed (`Ran 108 tests`, `OK`)
