---
phase: 02-validation-engine
plan: 01
subsystem: database
tags: [postgres, validation, quote-wall, evidence, testing]
requires:
  - phase: 01-candidate-contract-foundation
    provides: candidate evidence persisted in quote_documents and quote_candidate_rows
provides:
  - validator contract dataclasses and stable reason-code taxonomy
  - separate quote_validation_runs and quote_validation_row_results persistence
  - postgres regression coverage proving validation stays separate from candidate evidence and quote facts
affects: [validation-engine, fact-protection-publisher, replay, quote-wall]
tech-stack:
  added: []
  patterns:
    - separate validator custody tables from parser evidence tables
    - persist message-level validation runs plus row-level row decisions
key-files:
  created: [wxbot/bookkeeping-platform/bookkeeping_core/quote_validation.py]
  modified:
    - wxbot/bookkeeping-platform/bookkeeping_core/database.py
    - wxbot/bookkeeping-platform/sql/postgres_schema.sql
    - wxbot/bookkeeping-platform/tests/test_postgres_backend.py
key-decisions:
  - "Validator verdicts persist in dedicated run/result tables instead of mutating quote_candidate_rows."
  - "record_quote_validation_run enforces candidate-row lineage before accepting row decisions."
patterns-established:
  - "Validation storage pattern: quote_documents -> quote_candidate_rows -> quote_validation_runs -> quote_validation_row_results"
  - "Schema verification pattern: new postgres tables must be added to BookkeepingDB fail-fast column checks and regression tests"
requirements-completed: [VALI-01, VALI-02]
duration: 14min
completed: 2026-04-13
---

# Phase 02 Plan 01: Validation Boundary Summary

**Validator custody now lives in dedicated PostgreSQL run/result tables with stable reason codes and regression coverage, without mutating candidate evidence or active quote facts**

## Performance

- **Duration:** 14 min
- **Started:** 2026-04-13T19:05:00Z
- **Completed:** 2026-04-13T19:19:01Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Added `QuoteValidationRun` and `QuoteValidationRowResult` contracts plus stable schema/business/message reason-code constants in `quote_validation.py`.
- Added additive PostgreSQL validator tables, indexes, persistence helpers, and fail-fast schema verification in `database.py` and `postgres_schema.sql`.
- Added PostgreSQL regression coverage for mixed validator row decisions, foreign-key custody, structured JSON reasons, and schema-missing startup failure.

## Task Commits

Each task was committed atomically:

1. **Task 1: Define the validator contract and additive DB schema** - `85b189a` (feat)
2. **Task 2: Add DB-backed regression coverage for validator persistence** - `f2018a4` (test)

## Files Created/Modified

- `wxbot/bookkeeping-platform/bookkeeping_core/quote_validation.py` - Validator dataclasses, reason-code taxonomy, and serialization helpers.
- `wxbot/bookkeeping-platform/bookkeeping_core/database.py` - Validation run persistence/query helpers, lineage checks, additive schema DDL, and schema verification coverage.
- `wxbot/bookkeeping-platform/sql/postgres_schema.sql` - Formal PostgreSQL validator tables and indexes.
- `wxbot/bookkeeping-platform/tests/test_postgres_backend.py` - PostgreSQL regression tests for validation persistence and schema fail-fast behavior.

## Decisions Made

- Persisted validator output outside `quote_candidate_rows` so parser evidence remains immutable and replay-safe.
- Enforced candidate-row lineage during validation persistence to prevent row decisions from attaching to the wrong quote document.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Adjusted existing candidate-schema regression for new validator FK dependency**
- **Found during:** Task 2 (Add DB-backed regression coverage for validator persistence)
- **Issue:** The pre-existing `candidate schema missing` test dropped `quote_candidate_rows` directly, which now fails because `quote_validation_row_results` has a foreign key to candidate rows.
- **Fix:** Updated the regression to drop `quote_candidate_rows CASCADE` so it still validates fail-fast startup semantics under the new validator schema.
- **Files modified:** `wxbot/bookkeeping-platform/tests/test_postgres_backend.py`
- **Verification:** `BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_postgres_backend -v`
- **Committed in:** `f2018a4`

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Required to keep the existing schema-mismatch guard compatible with the new validator tables. No scope creep.

## Issues Encountered

- `graphify` rebuild could not run because the active Python environment does not provide the `graphify` module (`ModuleNotFoundError`). This was already noted in `.planning/STATE.md` and does not block the plan deliverable.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 02-02 can now wire runtime and replay candidate bundles to automatic validator execution against a durable storage boundary.
- Publisher work in Phase 03 can consume persisted validator results instead of parser-side `row_publishable` hints.

## Self-Check: PASSED

- Found summary file: `.planning/phases/02-validation-engine/02-01-SUMMARY.md`
- Found task commit: `85b189a`
- Found task commit: `f2018a4`

---
*Phase: 02-validation-engine*
*Completed: 2026-04-13*
