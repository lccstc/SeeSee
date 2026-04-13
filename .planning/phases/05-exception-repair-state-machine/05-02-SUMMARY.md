---
phase: 05-exception-repair-state-machine
plan: 02
subsystem: database
tags: [postgres, replay, repair-cases, quote-wall, validation]
requires:
  - phase: 02-validation-engine
    provides: validator-owned quote document and validation-run truth for replay comparison
  - phase: 05-exception-repair-state-machine
    provides: canonical `quote_repair_cases` packaging for raw exception events
provides:
  - additive `quote_repair_case_attempts` storage with one immutable baseline attempt per repair case
  - candidate-only baseline replay orchestration with durable before/after comparison summaries
  - replay-to-case suppression that prevents baseline proof runs from forking duplicate canonical repair cases
affects: [05-03, replay, exception-pool, webapp, postgres]
tech-stack:
  added: []
  patterns:
    - repair case -> immutable baseline attempt -> replay quote document and validation lineage
    - candidate-only replay proof with stored comparison classification instead of transient API-only diffs
key-files:
  created: []
  modified:
    - wxbot/bookkeeping-platform/bookkeeping_core/database.py
    - wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py
    - wxbot/bookkeeping-platform/bookkeeping_web/app.py
    - wxbot/bookkeeping-platform/sql/postgres_schema.sql
    - wxbot/bookkeeping-platform/tests/test_postgres_backend.py
    - wxbot/bookkeeping-platform/tests/test_webapp.py
key-decisions:
  - "Stored baseline lineage in dedicated `quote_repair_case_attempts` rows and linked them from `quote_repair_cases.baseline_attempt_id` instead of overloading case blobs."
  - "Reused `_replay_latest_quote_document_with_current_template(..., record_exceptions=False)` for baseline proof so repair replays stay candidate-only and cannot open duplicate canonical repair cases."
  - "Persisted before/after comparison data on attempt rows using candidate/validator metrics and classification (`better`/`same`/`worse`/`blocked`) rather than ephemeral handler output."
patterns-established:
  - "Baseline attempts are immutable attempt number `0` rows keyed by repair case and replay lineage."
  - "Repair baseline comparison reads origin and replay evidence from quote documents, validation runs, and detected-exception counts without touching publisher state."
requirements-completed: [EXCP-02, EXCP-03]
duration: 27min
completed: 2026-04-14
---

# Phase 05 Plan 02: Exception Repair State Machine Summary

**Immutable repair-case baseline replays with durable before/after validator comparisons and no duplicate canonical repair cases**

## Performance

- **Duration:** 27 min
- **Started:** 2026-04-13T23:24:00Z
- **Completed:** 2026-04-13T23:51:24Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- Added additive `quote_repair_case_attempts` storage plus `baseline_attempt_id` linkage so each repair case can persist one immutable baseline proof row.
- Reused the existing candidate-only replay helper to create baseline attempts, persist replay document and validation lineage, and suppress duplicate canonical repair-case creation during proof runs.
- Stored durable before/after comparison summaries on attempt rows, including origin vs replay row counts, message decisions, exception counts, remaining lines, and `better` / `same` / `worse` / `blocked` classification.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add immutable baseline-attempt persistence and lineage** - `cae8bcb` (`feat`)
2. **Task 2: Persist candidate-only baseline replay and before/after comparison output** - `eb75815` (`feat`)

## Files Created/Modified

- `wxbot/bookkeeping-platform/bookkeeping_core/database.py` - Added repair-case attempt persistence helpers, baseline linkage updates, and schema verification for the new lineage table.
- `wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py` - Added baseline replay orchestration, attempt summary construction, and comparison classification logic.
- `wxbot/bookkeeping-platform/bookkeeping_web/app.py` - Extended replay helper output with detected-exception and validator summary metrics while preserving fact-neutral behavior.
- `wxbot/bookkeeping-platform/sql/postgres_schema.sql` - Added additive `quote_repair_case_attempts` DDL plus repair-case baseline FK linkage.
- `wxbot/bookkeeping-platform/tests/test_postgres_backend.py` - Added baseline attempt storage, idempotence, and blocked-outcome regressions.
- `wxbot/bookkeeping-platform/tests/test_webapp.py` - Added `WebRepairCaseTests` covering replay helper reuse, durable comparison summaries, and no-fork baseline replay behavior.

## Decisions Made

- Baseline attempts become the durable proof surface for repair cases and keep replay lineage in PostgreSQL instead of transient handler state.
- Baseline replay always runs with `record_exceptions=False`, which preserves candidate-only proof behavior and guarantees replay does not fork a second canonical repair case for the same origin exception.
- Comparison classification is stored on attempt rows and derived from candidate/validator evidence rather than publish behavior, keeping Phase 05 inside its non-publisher boundary.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- PostgreSQL verification had to run outside the sandbox because sandboxed processes could not connect to `127.0.0.1:5432`.
- The SQL schema file could not use a `DO $$ ... $$` guard because the existing PostgreSQL test loader splits schema statements on semicolons; the baseline FK was flattened into plain DDL for fresh-schema application, while runtime migration guarding remains in `database.py`.
- `graphify` rebuild is still blocked in this environment because the active Python interpreter cannot import `graphify`.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase `05-03` can build append-only attempt history, failure stacking, and escalation state on top of `quote_repair_case_attempts` and `baseline_attempt_id`.
- Repair-case consumers now have a durable, candidate-only proof substrate with stable origin/replay comparison data and no-fork replay semantics.

## Known Stubs

None.

## Self-Check: PASSED

- Found `.planning/phases/05-exception-repair-state-machine/05-02-SUMMARY.md`
- Found commit `cae8bcb`
- Found commit `eb75815`
