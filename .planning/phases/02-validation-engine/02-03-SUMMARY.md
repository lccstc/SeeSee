---
phase: 02-validation-engine
plan: 03
subsystem: validation
tags: [postgres, validation, publishable-rows, runtime, replay, quote-wall, testing]
requires:
  - phase: 02-validation-engine
    provides: schema-validation runtime/replay wiring from 02-02
provides:
  - business-rule validation that separates publishable, rejected, and held rows
  - validator-owned publishable-row lookup for later publisher work
  - mixed-outcome regressions across unit, runtime, and replay paths
affects: [validation-engine, fact-protection-publisher, replay, quote-wall]
tech-stack:
  added: []
  patterns:
    - validator decisions override parser publishability hints
    - publishable row lookup reads persisted validator outcomes instead of candidate flags
key-files:
  created: []
  modified:
    - wxbot/bookkeeping-platform/bookkeeping_core/quote_validation.py
    - wxbot/bookkeeping-platform/bookkeeping_core/database.py
    - wxbot/bookkeeping-platform/tests/test_quote_validation.py
    - wxbot/bookkeeping-platform/tests/test_runtime.py
    - wxbot/bookkeeping-platform/tests/test_webapp.py
key-decisions:
  - "Rows with incomplete normalization, low confidence, ambiguous restriction parsing, or duplicate SKU collisions drift to held rather than publishable."
  - "publishable_rows are derived from quote_validation_row_results, never from parser-side row_publishable hints."
patterns-established:
  - "Mixed-outcome validation pattern: one message can yield publishable, held, and rejected rows together."
  - "Replay/runtime parity pattern: both flows expose validator-owned publishable rows from persisted validation results."
requirements-completed: [VALI-02, VALI-03]
duration: 10min
completed: 2026-04-14
---

# Phase 02 Plan 03: Business Rule Validation Summary

**Validator decisions now separate publishable, rejected, and held rows conservatively, and later publisher work can query `publishable_rows` directly from persisted validator results**

## Performance

- **Duration:** 10 min
- **Started:** 2026-04-14T02:49:00+07:00
- **Completed:** 2026-04-14T02:59:00+07:00
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Added business-rule validation for low confidence, partial normalization, ambiguous restrictions, inactive quote status, and duplicate normalized SKUs.
- Kept parser-side `row_publishable` advisory only; final row custody now comes from validator decisions.
- Added a DB helper that returns publishable candidate rows from the latest validation run, then covered it in runtime and replay regressions.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add business-rule validation and final decision taxonomy** - `ff90872` (feat)
2. **Task 2: Expose durable `publishable_rows` helpers and integration regressions** - `1f10a4b` (feat)

## Files Created/Modified

- `wxbot/bookkeeping-platform/bookkeeping_core/quote_validation.py` - Business-rule hold/reject logic, mixed-outcome summaries, and validator-owned publishable/rejected/held separation.
- `wxbot/bookkeeping-platform/bookkeeping_core/database.py` - `list_publishable_quote_candidate_rows(...)` helper that reads persisted validation results rather than parser flags.
- `wxbot/bookkeeping-platform/tests/test_quote_validation.py` - Unit coverage for mixed-outcome validation and duplicate-SKU hold behavior.
- `wxbot/bookkeeping-platform/tests/test_runtime.py` - Runtime integration coverage proving mixed outcomes persist and publishable helper lookup ignores parser-side `row_publishable`.
- `wxbot/bookkeeping-platform/tests/test_webapp.py` - Replay integration coverage proving publishable-row lookup follows replay validation results.

## Decisions Made

- Business uncertainty is treated conservatively: rows are held unless the validator can justify publication.
- `publishable_rows` is now a validator concept, not a parser concept, which prevents later publisher work from regressing to parser hints.

## Deviations from Plan

None - plan scope was already partially prepared by the existing validator wiring, and execution completed by hardening business rules plus validator-owned lookup coverage.

## Issues Encountered

- No new blocker was introduced in this wave.
- The previously discovered PostgreSQL test deadlock was already neutralized by disabling auto backup in `PostgresTestCase`, so the final Phase 2 quick suite completed cleanly.

## User Setup Required

None.

## Next Phase Readiness

- Phase 03 can now consume a stable, persisted `publishable_rows` surface instead of re-deriving decisions inline.
- The system now has the validator custody layer needed before guarded publisher work centralizes active-fact mutation.

## Self-Check: PASSED

- Summary file exists at `.planning/phases/02-validation-engine/02-03-SUMMARY.md`
- Verified task commits `ff90872` and `1f10a4b` are present in git history
- Verified `BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_quote_validation tests.test_runtime tests.test_webapp -v` passed (`Ran 112 tests`, `OK`)
