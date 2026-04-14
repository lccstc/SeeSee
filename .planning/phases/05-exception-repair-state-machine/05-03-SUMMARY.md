---
phase: 05-exception-repair-state-machine
plan: 03
subsystem: api
tags: [postgres, repair-cases, webapp, exceptions, quote-wall]
requires:
  - phase: 05-exception-repair-state-machine
    provides: immutable baseline replay attempts and canonical repair-case packaging
  - phase: 02-validation-engine
    provides: validator-owned quote document and row-decision truth
provides:
  - append-only repair attempt recording with lifecycle validation and escalation-ready rollups
  - compact repair summaries on existing quote exception API rows
  - brownfield handler sync between exception resolve/save flows and linked repair cases without new execution controls
affects: [06, exception-pool, replay, webapp, operator-workbench]
tech-stack:
  added: []
  patterns:
    - repair case rollups are recomputed from append-only attempt history instead of overwriting earlier evidence
    - existing exception handlers sync repair-case state opportunistically while remaining read/state-only
key-files:
  created: []
  modified:
    - wxbot/bookkeeping-platform/bookkeeping_core/database.py
    - wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py
    - wxbot/bookkeeping-platform/bookkeeping_web/app.py
    - wxbot/bookkeeping-platform/tests/test_postgres_backend.py
    - wxbot/bookkeeping-platform/tests/test_webapp.py
key-decisions:
  - "Stored attempt_count, failure_log_json, escalation_state, and closure metadata as recomputed rollups on `quote_repair_cases.case_summary_json` while keeping `quote_repair_case_attempts` append-only."
  - "Exposed only compact repair summaries on `/api/quotes/exceptions`, leaving raw snapshots and full attempt payloads out of the list surface."
  - "Synchronized brownfield resolve/save handlers to repair cases opportunistically and no-op when legacy exception rows cannot be packaged because they lack durable quote-document lineage."
patterns-established:
  - "Manual exception reopen now maps repair cases back to `ready_for_attempt` without adding Phase 06 remediation controls."
  - "Replay-backed save handlers append repair attempts only when replay lineage exists, and sanitize missing lineage IDs to preserve brownfield compatibility."
requirements-completed: [EXCP-01, EXCP-02, EXCP-03]
duration: 22min
completed: 2026-04-14
---

# Phase 05 Plan 03: Exception Repair State Machine Summary

**Append-only repair attempts, escalation-ready lifecycle rollups, and read-only repair summaries on existing exception surfaces**

## Performance

- **Duration:** 22 min
- **Started:** 2026-04-13T23:53:00Z
- **Completed:** 2026-04-14T00:14:45Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Added append-only repair attempt recording with legal lifecycle transitions, cumulative failure logs, and escalation-ready case rollups.
- Exposed compact repair-case summaries on `/api/quotes/exceptions` without leaking raw snapshots or adding remediation/publish controls.
- Wired existing exception resolve, harvest-save, and result-save handlers into repair-case state sync while preserving brownfield flows that still have legacy exception rows.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add append-only attempt recording and escalation-ready state transitions** - `dd8dc42` (`feat`)
2. **Task 2: Surface linked repair-case summaries on existing exception APIs only** - `67307a3` (`feat`)

## Files Created/Modified

- `wxbot/bookkeeping-platform/bookkeeping_core/database.py` - Added repair-case attempt listing, case updates, rollup summaries, and compact exception-list repair payloads.
- `wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py` - Added lifecycle transition validation, append-only repair attempt recording, brownfield state-sync helpers, and lineage sanitization.
- `wxbot/bookkeeping-platform/bookkeeping_web/app.py` - Synced existing exception resolve/harvest/result handlers to linked repair-case state without adding new routes or execution controls.
- `wxbot/bookkeeping-platform/tests/test_postgres_backend.py` - Added regressions for append-only attempts, escalation rollups, successful-attempt state, and legal reopen/illegal-transition boundaries.
- `wxbot/bookkeeping-platform/tests/test_webapp.py` - Added repair summary, resolve/reopen, harvest-save, and result-save regressions on existing web surfaces.

## Decisions Made

- Used `case_summary_json` as the repair-case rollup surface so attempt rows remain immutable and later phases can consume one compact summary without reconstructing history ad hoc.
- Kept exception-list exposure compact by surfacing only `repair_case_id`, lifecycle, attempt count, last outcome, escalation state, and baseline attempt ID.
- Treated legacy exception rows without durable quote-document lineage as sync-ineligible rather than failing existing brownfield resolution flows.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Preserved brownfield exception handlers when replay stubs or legacy rows lacked durable lineage**
- **Found during:** Task 2 (existing exception API/handler sync)
- **Issue:** New repair-case sync initially broke old web flows because some exception rows still use `quote_document_id=0`, and some replay test doubles return quote document / validation IDs that are not persisted rows.
- **Fix:** Made repair-case sync no-op when packaging cannot be established from legacy exception evidence, and sanitized replay lineage IDs before writing attempt rows so FK-safe sync remains additive.
- **Files modified:** `wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py`
- **Verification:** `tests.test_webapp` full suite and targeted brownfield save/resolve regressions
- **Committed in:** `67307a3`

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** The auto-fix was necessary to keep existing exception flows working while adding Phase 05 state sync. No publisher, snapshot, or remediation scope was added.

## Issues Encountered

- PostgreSQL-backed tests require escalated execution because sandboxed processes cannot connect to `127.0.0.1:5432`.
- `graphify` rebuild remains blocked in this environment because `python3` cannot import the local `graphify` module.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 06 now has durable repair-case state, append-only attempt history, cumulative failure logs, and escalation-ready summaries to build bounded remediation on top of.
- Existing exception APIs already carry enough compact repair metadata for a later operator workbench without opening a new bypass path today.
- `graphify` metadata was not rebuilt because the current environment is missing the `graphify` Python module.

## Known Stubs

None.

## Self-Check: PASSED

- Found `.planning/phases/05-exception-repair-state-machine/05-03-SUMMARY.md`
- Found commit `dd8dc42`
- Found commit `67307a3`

---
*Phase: 05-exception-repair-state-machine*
*Completed: 2026-04-14*
