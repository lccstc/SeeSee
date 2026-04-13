---
phase: 05-exception-repair-state-machine
plan: 01
subsystem: database
tags: [postgres, repair-cases, runtime, quote-wall, validation]
requires:
  - phase: 02-validation-engine
    provides: validator-owned `quote_validation_runs` and row-decision truth
  - phase: 02.1-real-exception-corpus-candidate-coverage
    provides: runtime quote capture coverage and exception-heavy failure surfaces
provides:
  - additive `quote_repair_cases` persistence for one durable case per raw exception event
  - system-owned repair-case packaging that freezes raw message, source line, group profile, and validator summary evidence
  - runtime wiring that packages parse failures and validator `no_publish` outcomes without mutating active quote facts
affects: [05-02, 05-03, replay, exception-pool, runtime]
tech-stack:
  added: []
  patterns:
    - candidate -> validation -> raw exception -> repair case
    - one repair case per exception row with validator tables kept as canonical truth
key-files:
  created:
    - wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py
  modified:
    - wxbot/bookkeeping-platform/bookkeeping_core/database.py
    - wxbot/bookkeeping-platform/bookkeeping_core/quotes.py
    - wxbot/bookkeeping-platform/sql/postgres_schema.sql
    - wxbot/bookkeeping-platform/tests/test_postgres_backend.py
    - wxbot/bookkeeping-platform/tests/test_runtime.py
key-decisions:
  - "Kept `quote_parse_exceptions` as the raw failure-event table and added dedicated `quote_repair_cases` instead of overloading exception rows with workflow state."
  - "Packaged repair cases by linking origin exception/document/validation rows and freezing only mutable evidence like group-profile snapshots and validator summary JSON."
  - "Runtime creates `validator_no_publish` exception rows only when validation returns `no_publish` and no earlier parse exception already explains the failure."
patterns-established:
  - "Repair packaging is idempotent per `origin_exception_id` and returns the same case on repeated packaging calls."
  - "Runtime failure handling now opens repair cases at the exception-recording boundary rather than inventing a second evidence pipeline."
requirements-completed: [EXCP-01, EXCP-02]
duration: 20min
completed: 2026-04-14
---

# Phase 05 Plan 01: Exception Repair State Machine Summary

**Durable repair-case packaging for quote exceptions with runtime coverage for parse failures and validator `no_publish` outcomes**

## Performance

- **Duration:** 20 min
- **Started:** 2026-04-13T23:06:00Z
- **Completed:** 2026-04-13T23:25:53Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- Added additive `quote_repair_cases` schema plus backend helpers that enforce one repair case per originating exception row.
- Created `bookkeeping_core/repair_cases.py` to package raw exception, quote document, validator summary, and frozen group-profile evidence into a system-owned case.
- Wired runtime quote capture to package parse exceptions immediately and to emit deterministic `validator_no_publish` exception rows when validation fails without an existing raw exception event.

## Task Commits

1. **Task 1: Add repair-case schema and evidence-packaging contract** - `1daa0df` (`feat`)
2. **Task 2: Wire runtime failure surfaces into system-owned repair cases** - `82bbbd5` (`feat`)

## Files Created/Modified

- `wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py` - Repair-case state constants, frozen-snapshot packaging, and idempotent case creation entrypoint.
- `wxbot/bookkeeping-platform/bookkeeping_core/database.py` - Additive repair-case schema init/verification plus lookup and creation helpers.
- `wxbot/bookkeeping-platform/bookkeeping_core/quotes.py` - Runtime repair-case packaging for parse exceptions and validator `no_publish` failures.
- `wxbot/bookkeeping-platform/sql/postgres_schema.sql` - PostgreSQL DDL for `quote_repair_cases`.
- `wxbot/bookkeeping-platform/tests/test_postgres_backend.py` - PostgreSQL repair-case persistence and idempotence regressions.
- `wxbot/bookkeeping-platform/tests/test_runtime.py` - Runtime repair-case coverage for parse failures and validator-driven no-publish outcomes.

## Decisions Made

- Used a dedicated `quote_repair_cases` table instead of extending `quote_parse_exceptions` with lifecycle state, keeping raw exception evidence and repair workflow state separated.
- Stored validator linkage by referencing `quote_validation_runs` while keeping row-level truth in existing validator tables rather than copying row results into repair blobs.
- Limited Task 2 runtime packaging to existing failure surfaces and a deterministic `validator_no_publish` reason code, preserving publisher boundaries and avoiding snapshot/remediation scope creep.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- PostgreSQL-backed tests required execution outside the sandbox because the local sandbox could not connect to `127.0.0.1:5432`.
- `graphify` rebuild remains blocked in this environment because the local `graphify` Python module is not installed.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 05-02 can now attach immutable baseline replay attempts to a canonical repair case instead of reconstructing context from exceptions and validator tables ad hoc.
- Runtime failures now arrive in the exception pool with stable repair-case lineage, but before/after replay attempts and append-only attempt history are still deferred to later Phase 05 plans.

## Known Stubs

None.

## Self-Check: PASSED

- Found `.planning/phases/05-exception-repair-state-machine/05-01-SUMMARY.md`
- Found commit `1daa0df`
- Found commit `82bbbd5`

---
*Phase: 05-exception-repair-state-machine*
*Completed: 2026-04-14*
