---
phase: 01-candidate-contract-foundation
plan: 01
subsystem: database
tags: [postgres, quote-wall, candidate-contract, unittest]
requires: []
provides:
  - quote candidate dataclasses with explicit sender-display and line-evidence fields
  - dedicated quote_documents plus quote_candidate_rows persistence boundary
  - PostgreSQL schema verification and regression coverage for candidate storage
affects: [runtime, replay, validator, exception-review]
tech-stack:
  added: []
  patterns: [message-header-plus-child-candidate-rows, fail-fast-postgres-schema-verification]
key-files:
  created:
    - wxbot/bookkeeping-platform/bookkeeping_core/quote_candidates.py
  modified:
    - wxbot/bookkeeping-platform/bookkeeping_core/database.py
    - wxbot/bookkeeping-platform/sql/postgres_schema.sql
    - wxbot/bookkeeping-platform/tests/test_postgres_backend.py
key-decisions:
  - "Use quote_documents as the message-level candidate header and quote_candidate_rows as the child evidence table."
  - "Keep candidate persistence separate from quote_price_rows so Phase 1 never implies fact publication."
  - "Fail startup when candidate schema artifacts are missing instead of auto-healing them at runtime."
patterns-established:
  - "Candidate persistence writes one message header plus zero-to-many row candidates."
  - "Candidate JSON evidence is serialized in the DB layer and verified through PostgreSQL-backed tests."
requirements-completed: [EVID-01, CAND-02]
duration: 7min
completed: 2026-04-13
---

# Phase 01 Plan 01: Candidate Contract Foundation Summary

**Candidate message headers now persist parser lineage, snapshot hypotheses, and row-level evidence in PostgreSQL without touching active quote facts**

## Performance

- **Duration:** 7 min
- **Started:** 2026-04-13T17:38:52Z
- **Completed:** 2026-04-13T17:45:53Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Added `QuoteCandidateMessage` and `QuoteCandidateRow` as the Phase 1 contract for message-level and row-level candidate evidence.
- Added `record_quote_candidate_bundle(...)` and `list_quote_candidate_rows(...)` so candidate storage no longer relies on `quote_price_rows`.
- Extended PostgreSQL schema verification and backend tests to prove candidate-only persistence and fail-fast behavior for missing candidate schema.

## Task Commits

Each task was committed atomically:

1. **Task 1: Create the Phase 1 candidate contract module and DB write/read API** - `4f72392` (feat)
2. **Task 2: Apply additive PostgreSQL schema changes and backend regression coverage** - `64f19d8` (feat)

## Files Created/Modified
- `wxbot/bookkeeping-platform/bookkeeping_core/quote_candidates.py` - Candidate dataclasses and sender-display serialization helpers.
- `wxbot/bookkeeping-platform/bookkeeping_core/database.py` - Candidate bundle persistence, candidate row querying, schema verification updates, and startup leak fix on schema failure.
- `wxbot/bookkeeping-platform/sql/postgres_schema.sql` - Candidate metadata columns on `quote_documents` and new `quote_candidate_rows` table.
- `wxbot/bookkeeping-platform/tests/test_postgres_backend.py` - PostgreSQL coverage for candidate persistence and candidate-schema fail-fast behavior.

## Decisions Made
- Reused `quote_documents` as the candidate header instead of inventing a second message table, minimizing brownfield churn while preserving custody.
- Persisted explicit sender-display evidence through the existing `source_name` path in Phase 1, with code comments making the temporary mapping explicit.
- Required missing candidate columns/table to raise a schema mismatch instead of being auto-created during runtime startup.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Closed PostgreSQL connections when schema verification fails**
- **Found during:** Task 2 (Apply additive PostgreSQL schema changes and backend regression coverage)
- **Issue:** `BookkeepingDB(...)` left an open psycopg connection behind when `_verify_schema()` raised, producing a `ResourceWarning` during fail-fast tests.
- **Fix:** Wrapped `_init_schema()` in a `try/except` and closed the raw connection before re-raising.
- **Files modified:** `wxbot/bookkeeping-platform/bookkeeping_core/database.py`
- **Verification:** `BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_postgres_backend -v`
- **Committed in:** `64f19d8`

---

**Total deviations:** 1 auto-fixed (Rule 1: 1)
**Impact on plan:** The fix was directly in the startup path exercised by the new fail-fast schema checks and kept verification clean without widening scope.

## Issues Encountered

- The PostgreSQL backend tests were initially blocked by sandbox network restrictions on `127.0.0.1:5432`; rerunning the exact test command with elevated permissions resolved verification.
- The repo-level `graphify` rebuild command was attempted twice and failed because the current Python environments do not expose a `graphify` module. No graph artifacts were updated in this execution.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Runtime and replay work can now target a stable candidate contract backed by `quote_documents` plus `quote_candidate_rows`.
- PostgreSQL startup now rejects partial candidate schema deployments before any candidate read/write path can proceed.
- `STATE.md` and `ROADMAP.md` were intentionally left untouched in this execution because the orchestrator owns those writes.

## Self-Check: PASSED

- Summary file exists at `.planning/phases/01-candidate-contract-foundation/01-01-SUMMARY.md`.
- Verified task commits `4f72392` and `64f19d8` are present in `git log --oneline --all`.
