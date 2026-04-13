---
phase: 02-validation-engine
verified: 2026-04-14T03:05:00+07:00
status: passed
score: 8/8 must-haves verified
overrides_applied: 0
---

# Phase 2: Validation Engine Verification Report

**Phase Goal:** Build explicit schema and business validators that separate `publishable_rows` from invalid or held rows.
**Verified:** 2026-04-14T03:05:00+07:00
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Every candidate row is evaluated against a fixed quote schema before publication | ✓ VERIFIED | `validate_quote_candidate_document(...)` runs `_schema_rejection_reasons(...)` before any business decision and rejects rows missing required normalized fields, valid amount ranges, or positive numeric prices in `wxbot/bookkeeping-platform/bookkeeping_core/quote_validation.py:183-245` and `:308-354`. Unit coverage: `tests/test_quote_validation.py:24-64`. |
| 2 | Business-rule failures are recorded with structured rejection or hold reasons | ✓ VERIFIED | Stable business reason codes are defined in `quote_validation.py:19-25`, normalized via `build_validation_reason(...)` / `normalize_reason_payloads(...)` at `:57-89`, and applied in `_business_rejection_reasons(...)` / `_business_hold_reasons(...)` at `:357-424`. Mixed outcome tests assert persisted structured payloads in `tests/test_quote_validation.py:103-237` and `tests/test_postgres_backend.py:445-586`. |
| 3 | A message can produce publishable, rejected, and held rows in the same evaluation without ambiguity | ✓ VERIFIED | `separate_publishable_rows(...)` splits final decisions in `quote_validation.py:165-180`; validator final decisions are assigned per row in `:213-245`. Mixed-outcome unit coverage at `tests/test_quote_validation.py:103-237`; runtime persistence coverage at `tests/test_runtime.py:1307-1480`. |
| 4 | Validation results persist separately from candidate evidence and active quote facts | ✓ VERIFIED | Validator state is stored in dedicated tables `quote_validation_runs` and `quote_validation_row_results` in `sql/postgres_schema.sql:283-352`, while candidate rows stay in `quote_candidate_rows` and active facts remain `quote_price_rows`. Persistence path in `database.py:1478-1560` never writes `quote_price_rows`. Tests assert `quote_price_rows` remains empty in `tests/test_postgres_backend.py:630-633`, `tests/test_runtime.py:1474-1479`, and `tests/test_webapp.py:1130-1133,1343-1348`. |
| 5 | Each validation run keeps a durable message-level result plus row-level decisions tied back to candidate rows | ✓ VERIFIED | `QuoteValidationRun` and `QuoteValidationRowResult` contracts are defined in `quote_validation.py:92-163`. `record_quote_validation_run(...)` enforces same-document lineage and row ordinal matching before inserting header + row results in `database.py:1478-1560`. Query helpers exist at `database.py:1562-1587`. |
| 6 | Runtime and replay automatically create validation runs after candidate persistence, including explicit zero-row no-publish results | ✓ VERIFIED | Runtime `_record_candidate_with_validation(...)` records candidate bundle, reloads persisted candidate rows, validates, and persists run in `quotes.py:1274-1289`. Replay does the same in `bookkeeping_web/app.py:1118-1127`. Zero-row no-publish is emitted in `quote_validation.py:249-305` and covered in `tests/test_quote_validation.py:296-341` plus runtime integration at `tests/test_runtime.py:1481-1550`. |
| 7 | Business-rule outcomes are durable and authoritative, separate from parser-side hints | ✓ VERIFIED | Validator only counts parser `row_publishable` as advisory in summary via `_row_publishable_hint(...)` and `parser_advisory_counts` in `quote_validation.py:195-205,267-276,465-467`. Durable lookup for publishable rows reads `quote_validation_row_results.final_decision = 'publishable'`, not parser flags, in `database.py:1589-1624`. Runtime and replay tests confirm publishable rows can come from `row_publishable = False` candidates in `tests/test_runtime.py:1460-1472` and `tests/test_webapp.py:1335-1341`. |
| 8 | Later publisher work has a validator-owned `publishable_rows` surface and does not need to re-derive it ad hoc | ✓ VERIFIED | `list_publishable_quote_candidate_rows(...)` joins persisted validator results back to candidate rows and defaults to the latest validation run in `database.py:1589-1624`. Runtime and replay regressions prove this helper returns only validator-approved rows in `tests/test_runtime.py:1465-1472` and `tests/test_webapp.py:1115-1128,1335-1341`. |

**Score:** 8/8 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `wxbot/bookkeeping-platform/bookkeeping_core/quote_validation.py` | Validator contract, schema/business decision engine, mixed-outcome separation | ✓ VERIFIED | Exists, substantive, and wired from runtime + replay. Key definitions at `:10-25`, `:92-305`, `:308-424`. |
| `wxbot/bookkeeping-platform/bookkeeping_core/database.py` | Validation persistence/query helpers and publishable lookup | ✓ VERIFIED | Exists, substantive, and wired. Persistence/query helpers at `:1478-1624`; schema verification includes validator tables at `:3939-3965`. |
| `wxbot/bookkeeping-platform/sql/postgres_schema.sql` | Additive validator persistence schema | ✓ VERIFIED | Dedicated run/result tables and indexes present at `:283-352`. |
| `wxbot/bookkeeping-platform/bookkeeping_core/quotes.py` | Runtime auto-validation after candidate persistence | ✓ VERIFIED | `_record_candidate_with_validation(...)` is called by runtime quote capture flows and persists `validation_run_id` at `:1257-1289`. |
| `wxbot/bookkeeping-platform/bookkeeping_web/app.py` | Replay auto-validation after candidate persistence | ✓ VERIFIED | Replay path records candidate bundle, validates, persists `validation_run_id`, and returns `mutated_active_facts: False` at `:1118-1194`. |
| `wxbot/bookkeeping-platform/tests/test_quote_validation.py` | Focused validator logic coverage | ✓ VERIFIED | Covers schema rejection, mixed publishable/rejected/held outcomes, duplicate SKU hold, and zero-row no-publish at `:24-341`. |
| `wxbot/bookkeeping-platform/tests/test_postgres_backend.py` | DB-backed validation persistence coverage | ✓ VERIFIED | Covers persisted run header, row-result lineage, structured reason JSON, FK integrity, and no `quote_price_rows` mutation at `:445-633`. |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| `bookkeeping_core/quotes.py` | `bookkeeping_core/quote_validation.py` | `_record_candidate_with_validation(...)` calls `validate_quote_candidate_document(...)` after `record_quote_candidate_bundle(...)` | ✓ WIRED | `quotes.py:1274-1289` |
| `bookkeeping_web/app.py` | `bookkeeping_core/quote_validation.py` | Replay helper calls `validate_quote_candidate_document(...)` after replay candidate persistence | ✓ WIRED | `app.py:1118-1127` |
| `bookkeeping_core/quote_validation.py` | `bookkeeping_core/database.py` | `QuoteValidationRun` / `QuoteValidationRowResult` serialized through `record_quote_validation_run(...)` | ✓ WIRED | Contracts at `quote_validation.py:92-163`; persistence at `database.py:1478-1560` |
| `bookkeeping_core/database.py` | later publisher consumption surface | `list_publishable_quote_candidate_rows(...)` joins validator row decisions back to candidate rows | ✓ WIRED | `database.py:1589-1624`; integration proven by `tests/test_runtime.py:1465-1472` and `tests/test_webapp.py:1115-1128` |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| --- | --- | --- | --- | --- |
| `bookkeeping_core/quotes.py::_record_candidate_with_validation` | `candidate_rows` | `self.db.list_quote_candidate_rows(quote_document_id=document_id)` immediately after `record_quote_candidate_bundle(...)` | Yes — rows are loaded from persisted `quote_candidate_rows` before validation | ✓ FLOWING |
| `bookkeeping_web/app.py::_replay_latest_quote_document_with_current_template` | `candidate_rows` | `db.list_quote_candidate_rows(quote_document_id=replay_document_id)` immediately after replay candidate persistence | Yes — replay document rows are reloaded from DB and then validated | ✓ FLOWING |
| `bookkeeping_core/database.py::list_publishable_quote_candidate_rows` | publishable candidate row result set | `quote_validation_row_results` joined to `quote_candidate_rows`, filtered by `final_decision = 'publishable'` | Yes — direct SQL join against persisted validator outputs in `database.py:1603-1624` | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| Validator logic, runtime wiring, replay wiring, and publishable lookup stay green together | `cd /Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform && BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_quote_validation tests.test_runtime tests.test_webapp -v` | `Ran 112 tests in 166.807s`, `OK` | ✓ PASS |
| Validation persistence schema and row-result durability are PostgreSQL-backed | `cd /Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform && BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_postgres_backend -v` | `Ran 10 tests in 25.935s`, `OK` | ✓ PASS |
| Phase 02 execution commits exist in git history | `git rev-list --all --abbrev-commit --abbrev=7 | rg "^(85b189a|f2018a4|fe5cbe1|e9c31ab|0fd125e|e13c311|fbef94b|2112c87|1b6c840|ff90872|1f10a4b|e2a2b1d)$"` | All listed hashes found | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| `VALI-01` | `02-01`, `02-02` | System validates every candidate row against a fixed quote schema before publish evaluation | ✓ SATISFIED | Schema checks in `quote_validation.py:308-354`; runtime/replay auto-validation wiring in `quotes.py:1274-1289` and `app.py:1118-1127`; green suites above |
| `VALI-02` | `02-01`, `02-03` | System applies explicit business-rule validation and records structured rejection reasons for invalid candidates | ✓ SATISFIED | Business rejection/hold logic in `quote_validation.py:357-424`; structured persistence in `database.py:1533-1558`; persisted JSON coverage in `tests/test_postgres_backend.py:553-586` |
| `VALI-03` | `02-03` | System computes `publishable_rows` separately from rejected rows and held rows | ✓ SATISFIED | `separate_publishable_rows(...)` in `quote_validation.py:165-180`; persisted lookup helper in `database.py:1589-1624`; mixed-outcome tests in `tests/test_quote_validation.py:103-237`, `tests/test_runtime.py:1446-1472`, and `tests/test_webapp.py:1330-1341` |

### Anti-Patterns Found

No blocker anti-patterns found in the phase files. Grep hits were limited to benign initial empty collections and test fixtures, not user-visible stubs or unwired placeholders.

### Calibration Notes

- Partial-but-non-blocking: validator-owned row decisions are fully structured, but `summary["candidate_rejection_reasons"]` still preserves upstream parser evidence in its legacy shape from `quote_validation.py:281-285`. This does not weaken validator custody, but upstream parser evidence is not yet normalized to validator reason codes.
- Test caveat: `tests/test_quote_validation.py:66-101` proves a fully valid row becomes publishable, but it is not an isolated schema-only test because it also depends on business-pass inputs. Mixed and failing business cases are covered elsewhere, so this is a coverage-shape note, not a gap.
- Uncovered error path: there is no direct regression for `record_quote_validation_run(...)` rejecting wrong-document candidate row IDs, duplicate candidate row IDs, or row-ordinal mismatches, even though the guards exist in `database.py:1495-1508`.

---

_Verified: 2026-04-14T03:05:00+07:00_
_Verifier: Claude (gsd-verifier)_
