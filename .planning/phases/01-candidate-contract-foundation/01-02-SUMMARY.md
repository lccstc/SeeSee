---
phase: 01-candidate-contract-foundation
plan: 02
subsystem: runtime
tags: [postgres, quote-wall, candidate-contract, runtime, unittest]
requires:
  - phase: 01-01
    provides: "QuoteCandidateMessage/QuoteCandidateRow persistence via quote_documents and quote_candidate_rows."
provides:
  - runtime quote capture persists candidate headers and candidate rows instead of mutating quote_price_rows
  - shared parse_quote_message_to_candidate helper with replay-safe run metadata inputs
  - PostgreSQL-backed runtime regressions for candidate-only ingestion and missing-template capture
affects: [runtime, replay, validator, exception-review]
tech-stack:
  added: []
  patterns: [shared parse-to-candidate helper, runtime candidate-only ingestion, exception evidence preservation]
key-files:
  created: []
  modified:
    - wxbot/bookkeeping-platform/bookkeeping_core/quotes.py
    - wxbot/bookkeeping-platform/tests/test_runtime.py
key-decisions:
  - "Runtime quote capture now writes only candidate bundles plus exception evidence; quote_price_rows remains a later-phase fact table."
  - "The shared parse helper carries run_kind, replay_of_quote_document_id, and message_id_override so replay can reuse the same contract without shape drift."
  - "Row evidence stores line-level provenance and raw fragments, while publishability remains parser prevalidation only."
patterns-established:
  - "Runtime ingestion follows raw message -> candidate header/rows -> exception evidence, with no deactivate/upsert side effects in quotes.py."
  - "Runtime PostgreSQL tests verify candidate metadata and prove active quote facts stay untouched."
requirements-completed: [CAND-01, CAND-02]
duration: 16min
completed: 2026-04-14
---

# Phase 01 Plan 02: Runtime Candidate Boundary Summary

**Runtime quote capture now persists replay-ready candidate bundles with parser lineage, message fingerprints, and row evidence while leaving active quote facts untouched**

## Performance

- **Duration:** 16 min
- **Started:** 2026-04-13T17:42:30Z
- **Completed:** 2026-04-13T17:58:48Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Replaced runtime quote capture’s direct fact writes with candidate bundle persistence through `record_quote_candidate_bundle(candidate=...)`.
- Added `parse_quote_message_to_candidate(...)` plus row-mapping helpers that preserve `run_kind`, replay lineage, parser metadata, message fingerprints, and row evidence.
- Rebased runtime integration tests around candidate-only ingestion, including missing-template headers and proof that `quote_price_rows` stays empty.

## Task Commits

Each task was committed atomically:

1. **Task 1: Refactor quote capture to build and persist runtime candidates only** - `1313b96` (feat)
2. **Task 2: Rebaseline runtime tests around candidate-only ingestion** - `a4304de` (test)

## Files Created/Modified
- `wxbot/bookkeeping-platform/bookkeeping_core/quotes.py` - Shared parse-to-candidate helpers, candidate-only runtime capture, inquiry-reply candidate persistence, and preserved exception recording.
- `wxbot/bookkeeping-platform/tests/test_runtime.py` - PostgreSQL-backed runtime assertions for candidate headers, candidate rows, missing-template evidence, and zero `quote_price_rows` mutation.

## Decisions Made
- Reused `QuoteCaptureService.capture_from_message(...)` as the custody boundary, but changed its persistence target from active facts to candidate bundles so runtime behavior stays in core code.
- Used `parser_kind` to reflect the concrete parser path (`group-parser`, `strict-section`, or `inquiry_context_reply`) while keeping `snapshot_hypothesis` unresolved in Phase 1.
- Kept low-confidence and non-active rows in candidate storage and continued mirroring them into `quote_parse_exceptions` instead of dropping that evidence.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- The required PostgreSQL-backed `tests.test_runtime` command could not connect to `127.0.0.1:5432` inside the sandbox; rerunning the same command with elevated permissions verified the work successfully.
- The repo-level `graphify` rebuild command failed with `ModuleNotFoundError: No module named 'graphify'`, so graph artifacts were not refreshed in this execution.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Replay work can call the same `parse_quote_message_to_candidate(...)` contract with explicit `run_kind` and replay lineage fields.
- Runtime capture now leaves a stable candidate/evidence trail for validator and exception-review phases without touching active board facts.
- `STATE.md` and `ROADMAP.md` were intentionally left untouched in this execution because the orchestrator owns those writes.

## Self-Check: PASSED

- Summary file exists at `.planning/phases/01-candidate-contract-foundation/01-02-SUMMARY.md`.
- Verified task commits `1313b96` and `a4304de` are present in `git log --oneline --all`.

---
*Phase: 01-candidate-contract-foundation*
*Completed: 2026-04-14*
