---
phase: 05-exception-repair-state-machine
verified: 2026-04-14T00:29:28Z
status: human_needed
score: 3/3 must-haves verified
overrides_applied: 0
human_verification:
  - test: "Inspect one real corpus-backed repair case package"
    expected: "Raw message, source line, frozen group-profile snapshot, validator summary, and baseline attempt all match the originating exception message"
    why_human: "Business correctness of packaged evidence on a live exception still needs operator judgment"
  - test: "Review before/after replay wording on an actual exception flow"
    expected: "The UI/API language describes candidate and validator deltas only, without implying publish authority or active-quote mutation"
    why_human: "Operator-facing wording quality and trust signaling cannot be fully verified programmatically"
---

# Phase 05: Exception Repair State Machine Verification Report

**Phase Goal:** Turn every failure into a durable repair case with explicit state, replay baseline, and cumulative remediation history.
**Verified:** 2026-04-14T00:29:28Z
**Status:** human_needed
**Re-verification:** No - initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Failed, partial, and rejected parse attempts always enter the exception pool as structured repair cases | ✓ VERIFIED | Runtime packages parse failures and validator `no_publish` failures into `quote_repair_cases` via [`quotes.py`](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_core/quotes.py:1312) and [`repair_cases.py`](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py:70); runtime tests prove `strict_match_failed`, `missing_group_template`, and `validator_no_publish` create linked repair cases in [`test_runtime.py`](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/tests/test_runtime.py:1792) and [/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/tests/test_runtime.py:1962](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/tests/test_runtime.py:1962). |
| 2 | Each repair case carries replay-critical context, including current group profile/template version, candidate/validator result, unmatched evidence, and prior attempts | ✓ VERIFIED | `quote_repair_cases` stores raw/source/profile/validator snapshots and `quote_repair_case_attempts` stores replay lineage plus summaries in [`database.py`](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_core/database.py:2156) and [/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_core/database.py:2232](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_core/database.py:2232); packaging and rollups are built in [`repair_cases.py`](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py:70) and [/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py:418](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py:418); DB tests verify frozen snapshots, baseline linkage, append-only history, and escalation rollups in [`test_postgres_backend.py`](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/tests/test_postgres_backend.py:736), [/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/tests/test_postgres_backend.py:890](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/tests/test_postgres_backend.py:890), and [/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/tests/test_postgres_backend.py:1518](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/tests/test_postgres_backend.py:1518). |
| 3 | Before/after replay comparisons show whether a proposed fix actually improved the owning group's grammar safely | ✓ VERIFIED | Baseline replay uses `_replay_latest_quote_document_with_current_template(..., record_exceptions=False)` in [`repair_cases.py`](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py:531), stores comparison summaries with `better/same/worse/blocked` classifications in [`repair_cases.py`](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py:443), and the replay helper remains candidate-only with `mutated_active_facts: False` in [`app.py`](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_web/app.py:1031); web tests verify no duplicate canonical case creation, persisted comparison output, and zero `quote_price_rows` writes in [`test_webapp.py`](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/tests/test_webapp.py:4382), [/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/tests/test_webapp.py:4529](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/tests/test_webapp.py:4529), and [/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/tests/test_webapp.py:4616](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/tests/test_webapp.py:4616). |

**Score:** 3/3 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py` | State machine, packaging, baseline replay, attempt history, state sync | ✓ VERIFIED | Substantive implementation at lines 8-546; wired from runtime and web handlers. |
| `wxbot/bookkeeping-platform/bookkeeping_core/database.py` | Durable repair-case persistence and summary queries | ✓ VERIFIED | Dedicated case/attempt tables and helpers at lines 2156-2475, 3259-3352, and 4043-4163. |
| `wxbot/bookkeeping-platform/bookkeeping_core/quotes.py` | Runtime failure packaging after candidate/validation persistence | ✓ VERIFIED | Failure capture calls repair packaging at lines 1312-1387. |
| `wxbot/bookkeeping-platform/bookkeeping_web/app.py` | Candidate-only replay reuse plus exception-surface state sync | ✓ VERIFIED | Replay helper at lines 1031-1224 and handler sync at lines 623-761, 1357-1405, and 2294-2310. |
| `wxbot/bookkeeping-platform/sql/postgres_schema.sql` | Additive schema for repair cases and attempts | ✓ VERIFIED | Artifact checker passed; runtime schema verification also passed through `BookkeepingDB` startup and full PostgreSQL suite. |
| `wxbot/bookkeeping-platform/tests/test_postgres_backend.py` | Persistence, baseline, append-only, escalation regressions | ✓ VERIFIED | `RepairCaseTests` passed 9/9. |
| `wxbot/bookkeeping-platform/tests/test_runtime.py` | Runtime exception -> repair-case regressions | ✓ VERIFIED | `RuntimeRepairCaseTests` passed 4/4. |
| `wxbot/bookkeeping-platform/tests/test_webapp.py` | Replay baseline, exception API summary, handler sync regressions | ✓ VERIFIED | Full module passed 73/73, including `WebRepairCaseTests`. |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| `quotes.py` | `repair_cases.py` | Runtime exception packaging | ✓ WIRED | `_record_exception_with_repair_case()` calls `package_quote_repair_case()` in [`quotes.py`](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_core/quotes.py:1312). |
| `repair_cases.py` | `quote_parse_exceptions` / `quote_documents` / `quote_validation_runs` / `quote_group_profiles` | Origin links + frozen snapshots | ✓ WIRED | `package_quote_repair_case()` reads origin exception/document/run/profile and persists snapshots in [`repair_cases.py`](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py:70). |
| `quote_repair_case_attempts` | `quote_documents` / `quote_validation_runs` | Baseline and repair replay lineage | ✓ WIRED | Foreign keys and helper writes are defined in [`database.py`](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_core/database.py:2232) and [/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_core/database.py:4079](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_core/database.py:4079). |
| `repair_cases.py` | `app.py` | Shared replay helper | ✓ WIRED | `_run_repair_case_baseline_replay()` imports `_replay_latest_quote_document_with_current_template()` with `record_exceptions=False` in [`repair_cases.py`](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py:531). |
| `database.py` | `/api/quotes/exceptions` | Compact repair summary payload | ✓ WIRED | `list_quote_exceptions()` injects `repair_case` summary fields and `_handle_quotes_exceptions()` returns them in [`database.py`](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_core/database.py:3259) and [`app.py`](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_web/app.py:623). |
| Exception resolve/harvest/result handlers | Repair-case lifecycle | `_sync_quote_exception_repair_case_state()` | ✓ WIRED | Sync happens on resolve, harvest-save replay, and result-save in [`app.py`](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_web/app.py:714), [/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_web/app.py:1386](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_web/app.py:1386), and [/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_web/app.py:1500](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_web/app.py:1500). |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| --- | --- | --- | --- | --- |
| `repair_cases.py` baseline/attempt summaries | `comparison`, `origin_metrics`, `attempt_metrics` | Origin case IDs + replay `quote_document_id`/`validation_run_id` -> DB row queries | Yes | ✓ FLOWING |
| `database.py` exception list summary | `repair_case`, `attempt_count`, `baseline_attempt_id`, `escalation_state` | `quote_repair_cases` + `quote_repair_case_attempts` rollup via `get_quote_repair_case_summary()` | Yes | ✓ FLOWING |
| `app.py` replay proof path | `replay_result` | Candidate replay -> validation run -> returned proof payload | Yes | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| Repair-case persistence and state transitions | `BOOKKEEPING_TEST_DSN=... ./.venv/bin/python -m unittest tests.test_postgres_backend.RepairCaseTests -v` | Ran 9 tests, `OK` | ✓ PASS |
| Runtime failure -> repair-case packaging | `BOOKKEEPING_TEST_DSN=... ./.venv/bin/python -m unittest tests.test_runtime.RuntimeRepairCaseTests -v` | Ran 4 tests, `OK` | ✓ PASS |
| Replay baseline and exception API sync | `BOOKKEEPING_TEST_DSN=... ./.venv/bin/python -m unittest tests.test_webapp -v` | Ran 73 tests, `OK` | ✓ PASS |
| Full PostgreSQL validation gate | `BOOKKEEPING_TEST_DSN=... ./.venv/bin/python -m unittest tests.test_quote_validation tests.test_postgres_backend tests.test_runtime tests.test_webapp -v` | Ran 142 tests in 59.886s, `OK` | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| `EXCP-01` | 05-01, 05-03 | Every failed/partial/rejected/unclassifiable parse attempt becomes a durable repair case | ✓ SATISFIED | Runtime repair-case packaging in [`quotes.py`](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_core/quotes.py:1312) and runtime tests in [`test_runtime.py`](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/tests/test_runtime.py:1792). |
| `EXCP-02` | 05-01, 05-02, 05-03 | Repair case carries raw message, profile/template version, candidate/validator result, unmatched evidence, and replay baseline | ✓ SATISFIED | Dedicated case/attempt persistence in [`database.py`](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_core/database.py:2156) and [/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_core/database.py:2232), plus DB tests in [`test_postgres_backend.py`](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/tests/test_postgres_backend.py:736) and [/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/tests/test_postgres_backend.py:1019](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/tests/test_postgres_backend.py:1019). |
| `EXCP-03` | 05-02, 05-03 | Stored raw message can be replayed through current parser/validator chain and compared before/after | ✓ SATISFIED | Candidate-only replay helper in [`app.py`](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_web/app.py:1031), baseline replay orchestration in [`repair_cases.py`](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py:136), and web tests in [`test_webapp.py`](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/tests/test_webapp.py:4382) and [/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/tests/test_webapp.py:4529](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/tests/test_webapp.py:4529). |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| --- | --- | --- | --- | --- |
| — | — | No TODO/FIXME/placeholder stubs found in Phase 05 implementation surfaces | — | No blocker anti-patterns detected |
| `bookkeeping_web/app.py` | 1659 | Legacy `quote_price_rows` delete path exists outside repair-case flow | ℹ️ Info | Not introduced by Phase 05; repair-case tests still prove replay/repair paths do not mutate active quote facts |
| `graphify` | — | Local module missing for graph rebuild in this environment | ℹ️ Info | Non-blocking for Phase 05 outcome verification |

### Human Verification Required

### 1. Real Repair Package Audit

**Test:** Open one real top-volume exception from the live corpus, inspect its `quote_repair_cases` row and linked baseline attempt.
**Expected:** Raw message, source line, current group profile snapshot, validator summary, and baseline replay lineage all match the originating failure.
**Why human:** Automated tests use fixtures and synthetic cases; only the operator can confirm business fidelity on a live sample.

### 2. Replay Language Audit

**Test:** Trigger an actual before/after replay flow from the exception UI/API and read the returned wording.
**Expected:** The response communicates candidate/validator proof only, and does not imply publish success or active-quote mutation.
**Why human:** This is a trust/UX judgment, not a binary code-path check.

### Boundary Check

- No publisher change found in repair-case code paths: replay helper always returns `mutated_active_facts: False` in [`app.py`](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_web/app.py:1207), runtime tests assert zero `quote_price_rows` writes in [`test_runtime.py`](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/tests/test_runtime.py:1957), and web replay tests assert zero replay-side `quote_price_rows` in [`test_webapp.py`](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/tests/test_webapp.py:4520).
- No snapshot execution semantics added: repair-case code stores comparison/state only and does not branch on `full_snapshot`/`delta_update` execution or inactivate unseen SKUs.
- No auto-remediation loop added: `sync_quote_exception_repair_case()` and `record_quote_repair_attempt()` update state/history only in [`repair_cases.py`](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py:243) and [/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py:350); they do not schedule retries, propose fixes, or mutate group grammar automatically.

### Gaps Summary

No blocking implementation gaps were found. Phase 05 meets its roadmap success criteria and `EXCP-01` through `EXCP-03` under automated verification. Status remains `human_needed` because the phase's own validation contract still includes two operator-only checks on live repair-package fidelity and replay wording.

---

_Verified: 2026-04-14T00:29:28Z_  
_Verifier: Claude (gsd-verifier)_
