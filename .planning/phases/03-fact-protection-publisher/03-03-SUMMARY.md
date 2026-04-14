---
phase: 03-fact-protection-publisher
plan: 03
subsystem: api
tags: [quotes, publisher-custody, web, scripts, testing]
requires:
  - phase: 03-01
    provides: guarded quote publisher and validator-owned publishable rows
  - phase: 03-02
    provides: no-op/rollback semantics and per-group publish locking
provides:
  - web delete route no longer mutates active quote facts
  - demo seed script no longer models raw active-fact deletion as acceptable
  - structural tests block forbidden low-level quote-fact mutation callsites outside a narrow allowlist
affects: [phase-04-snapshot-semantics, phase-07-operator-verification, quote-wall-safety]
tech-stack:
  added: []
  patterns: [disable-unsafe-surface, ast-architecture-guard, proof-only-route-wording]
key-files:
  created: []
  modified:
    - wxbot/bookkeeping-platform/bookkeeping_web/app.py
    - wxbot/bookkeeping-platform/scripts/seed_quote_demo.py
    - wxbot/bookkeeping-platform/tests/test_postgres_backend.py
    - wxbot/bookkeeping-platform/tests/test_runtime.py
    - wxbot/bookkeeping-platform/tests/test_webapp.py
key-decisions:
  - "Legacy /api/quotes/delete was narrowed to an explicit no-op because Phase 03 cannot safely express raw delete through publisher semantics."
  - "Demo seeding no longer offers --clear because scripts must not normalize direct active-fact deletion."
  - "Publisher custody is enforced with an AST architecture test over the bookkeeping-platform tree, not just route-level assertions."
patterns-established:
  - "Unsafe legacy fact-mutation surfaces are disabled rather than preserved behind ad hoc SQL."
  - "Low-level quote fact helpers remain callable only from the guarded publisher or tightly-scoped test setup."
requirements-completed: [FACT-03]
duration: 1h
completed: 2026-04-15
---

# Phase 03 Plan 03 Summary

**Web/script quote-fact side doors are now disabled or guarded, with structural tests preventing new direct active-row mutation callsites**

## Performance

- **Duration:** ~1h
- **Started:** 2026-04-14T19:00:00Z
- **Completed:** 2026-04-14T20:03:26Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Disabled `/api/quotes/delete` as a raw delete path and made its response explicitly proof-only: `未改动报价墙`.
- Removed `seed_quote_demo.py --clear` as an accepted operational path for deleting active quote facts.
- Added architecture coverage that scans repo callsites and fails if low-level quote-fact mutation helpers appear outside the guarded publisher or narrow test setup files.

## Files Created/Modified

- `wxbot/bookkeeping-platform/bookkeeping_web/app.py` - disables the legacy quote delete route and returns explicit no-op wording.
- `wxbot/bookkeeping-platform/scripts/seed_quote_demo.py` - rejects `--clear` before any DB connection or raw fact deletion.
- `wxbot/bookkeeping-platform/tests/test_postgres_backend.py` - proves the demo seed script no longer treats raw deletes as valid.
- `wxbot/bookkeeping-platform/tests/test_runtime.py` - adds the AST-based publisher-custody architecture regression.
- `wxbot/bookkeeping-platform/tests/test_webapp.py` - verifies `/api/quotes/delete` leaves active rows untouched and communicates that clearly.

## Decisions Made

- Disabled the delete route instead of inventing Phase 04 snapshot semantics or a one-off retract mode in the web layer.
- Kept replay/result-save/harvest-save surfaces fact-neutral; this plan does not widen publisher authority beyond the existing guarded core entrypoint.
- Scoped the structural allowlist to `quote_publisher.py` plus test files that seed explicit fixtures, so future bypasses fail loudly.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Architecture test now reads Python files with `utf-8-sig`**
- **Found during:** Task 2
- **Issue:** Repo files with BOM markers caused `ast.parse(...)` to fail before the custody scan could evaluate callsites.
- **Fix:** Switched the architecture test reader to `utf-8-sig`.
- **Files modified:** `wxbot/bookkeeping-platform/tests/test_runtime.py`
- **Verification:** `tests.test_runtime.QuoteFactCustodyArchitectureTests` passed.

---

**Total deviations:** 1 auto-fixed (Rule 3)
**Impact on plan:** No scope creep. The fix was necessary to make the structural guard stable on this repo.

## Issues Encountered

- Full PostgreSQL-backed verification still has one pre-existing out-of-scope failure: `tests.test_webapp.WebAppTests.test_ignored_quote_exception_suppresses_same_content_but_not_other_groups`.
- `graphify` rebuild could not run because the active environment does not have the `graphify` module installed.
- `.planning/STATE.md` and roadmap/session bookkeeping were not updated because this execution was explicitly limited to the user-owned write scope.
- The plan was committed as a single atomic code change instead of per-task commits because the execution request explicitly required one focused atomic commit.

## User Setup Required

None.

## Next Phase Readiness

- Phase 04 can now assume that web routes and scripts do not have a raw delete side door around guarded publisher custody.
- If a future operator flow needs retract/replace behavior, it must be expressed through publisher-owned semantics rather than direct SQL or helper calls.

## Self-Check: PASSED

- Summary file created at `.planning/phases/03-fact-protection-publisher/03-03-SUMMARY.md`
- All code changes stayed inside the granted write scope
- New custody regressions passed; the only failing automated test remained the previously documented webapp failure

---
*Phase: 03-fact-protection-publisher*
*Completed: 2026-04-15*
