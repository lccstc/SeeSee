---
phase: 01-candidate-contract-foundation
plan: 03
subsystem: ui
tags: [postgres, quote-wall, replay, candidate-contract, unittest]
requires:
  - phase: 01-01
    provides: "quote_documents plus quote_candidate_rows candidate persistence boundary"
  - phase: 01-02
    provides: "parse_quote_message_to_candidate(...) runtime/replay contract"
provides:
  - replay and harvest-save now persist replay candidate runs without mutating active quote facts
  - harvest/replay payloads expose replay lineage and explicit mutated_active_facts=false metadata
  - operator-facing harvest copy and web regressions now prove candidate evidence instead of board refresh
affects: [replay, exception-review, validator, quote-board]
tech-stack:
  added: []
  patterns: [candidate-only replay persistence, candidate-first harvest messaging, replay lineage assertions]
key-files:
  created: []
  modified:
    - wxbot/bookkeeping-platform/bookkeeping_web/app.py
    - wxbot/bookkeeping-platform/bookkeeping_web/pages.py
    - wxbot/bookkeeping-platform/tests/test_webapp.py
key-decisions:
  - "Replay keeps a distinct replay message_id while preserving replay_of_quote_document_id so quote_documents can store repeat replays without colliding with the original message header."
  - "Harvest-save continues to gate replay on latest-for-group and resolved status, but replay success now means candidate evidence exists and not that quote_price_rows changed."
patterns-established:
  - "Replay follows raw quote document -> replay candidate bundle -> optional replay exceptions, with mutated_active_facts always false."
  - "Web regressions assert quote_documents.run_kind/replay_of_quote_document_id and quote_candidate_rows counts instead of /api/quotes/board growth."
requirements-completed: [EVID-01, CAND-01, CAND-02]
duration: 26min
completed: 2026-04-14
---

# Phase 01 Plan 03: Candidate Replay Boundary Summary

**Replay and harvest-save now generate replay candidate evidence with lineage metadata while leaving quote_price_rows and the active board untouched**

## Performance

- **Duration:** 26 min
- **Started:** 2026-04-13T17:43:00Z
- **Completed:** 2026-04-13T18:09:19Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Replaced replay-path fact mutation in `app.py` with candidate bundle persistence using `run_kind="replay"` and `replay_of_quote_document_id`.
- Updated harvest UI status, summaries, and success alerts so operators now see candidate replay / no-board-mutation wording.
- Rebased PostgreSQL-backed web regressions to assert replay document lineage, candidate row counts, and unchanged `/api/quotes/board` output.

## Task Commits

Each task was committed atomically:

1. **Task 1: Convert replay and harvest-save to persist replay candidate runs only** - `6a38987` (feat)
2. **Task 2: Rebaseline UI copy and web regressions from board refresh to replay-candidate evidence** - `5cd1892` (test)

## Files Created/Modified
- `wxbot/bookkeeping-platform/bookkeeping_web/app.py` - replay helper now persists replay candidates, returns lineage metadata, and never deactivates/upserts active facts.
- `wxbot/bookkeeping-platform/bookkeeping_web/pages.py` - harvest modal copy, status text, and success alerts now describe candidate replay and explicit board non-mutation.
- `wxbot/bookkeeping-platform/tests/test_webapp.py` - rebased harvest/replay assertions, added replay document helpers, and aligned lingering web expectations with Phase 1 candidate-only behavior.

## Decisions Made
- Preserved the existing latest-message and resolved-only harvest replay gate so this plan changed custody semantics without widening replay authority.
- Returned `mutated_active_facts: False` in both replay and non-replay harvest payloads so the web layer can stop inferring publish semantics from absence of fields.
- Kept replay evidence inside existing `quote_documents` / `quote_candidate_rows` storage rather than introducing a new inspection surface in Phase 1.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Replay candidate persistence initially collided with the original quote document unique key**
- **Found during:** Task 1 (Convert replay and harvest-save to persist replay candidate runs only)
- **Issue:** Reusing the original `message_id` caused `quote_documents_platform_chat_id_message_id_key` violations when replay tried to persist a second header for the same source message.
- **Fix:** Generated a distinct replay `message_id_override` while still recording `replay_of_quote_document_id` on the new candidate document.
- **Files modified:** `wxbot/bookkeeping-platform/bookkeeping_web/app.py`
- **Verification:** `BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_webapp -v`
- **Committed in:** `6a38987`

**2. [Rule 3 - Blocking] Rebased two lingering web regressions that still assumed pre-Phase-1 board mutation semantics**
- **Found during:** Task 2 (Rebaseline UI copy and web regressions from board refresh to replay-candidate evidence)
- **Issue:** `tests.test_webapp` still contained one dictionary-page title assertion and one runtime quote-board assertion that no longer matched the current brownfield UI/runtime behavior, blocking the required module-level verification command.
- **Fix:** Updated those expectations to match the current dictionary page title and runtime candidate-only capture contract.
- **Files modified:** `wxbot/bookkeeping-platform/tests/test_webapp.py`
- **Verification:** `BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_webapp -v`
- **Committed in:** `5cd1892`

---

**Total deviations:** 2 auto-fixed (Rule 1: 1, Rule 3: 1)
**Impact on plan:** Both fixes were required to complete the candidate-only replay boundary and get the mandated PostgreSQL-backed web suite green. No architecture widened beyond Phase 1 scope.

## Issues Encountered

- Sandbox networking blocked PostgreSQL access to `127.0.0.1:5432`; rerunning the required `tests.test_webapp` command with elevation verified the plan successfully.
- The required repo-level `graphify` rebuild command failed with `ModuleNotFoundError: No module named 'graphify'`, so graph artifacts were not refreshed in this execution.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Replay, harvest-save, and runtime web coverage now share the same candidate-only custody boundary and replay lineage vocabulary.
- Later validator/publisher phases can consume replay evidence from `quote_documents` plus `quote_candidate_rows` without inferring anything from active board mutation.
- `STATE.md` and `ROADMAP.md` were intentionally left untouched in this execution because the orchestrator owns those writes.

## Self-Check: PASSED

- Summary file exists at `.planning/phases/01-candidate-contract-foundation/01-03-SUMMARY.md`.
- Verified task commits `6a38987` and `5cd1892` are present in `git log --oneline --all`.

---
*Phase: 01-candidate-contract-foundation*
*Completed: 2026-04-14*
