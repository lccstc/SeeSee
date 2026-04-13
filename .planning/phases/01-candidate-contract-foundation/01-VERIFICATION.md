---
phase: 01-candidate-contract-foundation
verified: 2026-04-13T18:31:25Z
status: passed
score: 11/11 must-haves verified
overrides_applied: 0
---

# Phase 1: Candidate Contract Foundation Verification Report

**Phase Goal:** Formalize a message-to-candidate pipeline where parsers can propose quote rows but cannot directly publish active facts.
**Verified:** 2026-04-13T18:31:25Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Candidate headers persist raw message, explicit sender display evidence, group, and message time without inserting active quote facts. | ✓ VERIFIED | `bookkeeping_core/quote_candidates.py` defines `QuoteCandidateMessage` with `raw_message`, `sender_display`, `message_time`, `source_group_key`; `bookkeeping_core/database.py` `record_quote_candidate_bundle()` inserts only `quote_documents` and `quote_candidate_rows`; `tests.test_postgres_backend` asserts `quote_price_rows` count stays `0`. |
| 2 | Each candidate row stores source-line evidence plus raw field fragments and parser lineage under one quote document. | ✓ VERIFIED | `QuoteCandidateRow` includes `source_line`, `line_confidence`, `field_sources`, `parser_template`, `parser_version`; schema stores `field_sources_json`; runtime tests assert persisted `source_line`, `source_line_index`, and raw `price` fragment. |
| 3 | Runtime startup fails fast if candidate columns or `quote_candidate_rows` are missing from PostgreSQL. | ✓ VERIFIED | `BookkeepingDB._verify_schema()` requires the Phase 1 `quote_documents` columns and `quote_candidate_rows`; `tests.test_postgres_backend.test_bookkeeping_db_fails_fast_when_candidate_schema_is_missing` passed. |
| 4 | Runtime quote capture persists a candidate message and row candidates instead of mutating active quote facts. | ✓ VERIFIED | `bookkeeping_core/runtime.py` wires `process_envelope()` to `quote_capture.capture_from_message()`; `bookkeeping_core/quotes.py` persists via `record_quote_candidate_bundle(candidate=...)`; repo search found no non-test callers of `deactivate_old_quotes_for_group()` or `upsert_quote_price_row_with_history()`. |
| 5 | The shared parse-to-candidate helper is reusable for both runtime and replay, with explicit `run_kind` and replay lineage inputs. | ✓ VERIFIED | `bookkeeping_core/quotes.py` exports `parse_quote_message_to_candidate(..., run_kind, replay_of_quote_document_id, message_id_override)`; `bookkeeping_web/app.py` reuses it with `run_kind="replay"` and replay lineage. |
| 6 | Candidate rows preserve parser lineage, message fingerprint, and per-row evidence during runtime ingestion. | ✓ VERIFIED | Runtime candidate documents persist `parser_kind`, `parser_template`, `parser_version`, `message_fingerprint`, `snapshot_hypothesis`; `tests.test_runtime` asserts those fields plus `field_sources_json`. |
| 7 | Rejected or non-publishable rows still leave evidence in the exception flow without deactivating existing board facts. | ✓ VERIFIED | `QuoteCaptureService.capture_from_message()` still records `quote_parse_exceptions` for parsed failures and non-publishable rows; `tests.test_runtime` asserts a `strict_match_failed` exception while `quote_price_rows` remains empty. |
| 8 | Replay and harvest-save persist a new replay candidate run instead of refreshing the active quote board. | ✓ VERIFIED | `_replay_latest_quote_document_with_current_template()` loads stored raw message, builds a replay candidate, persists it via `record_quote_candidate_bundle()`, and never calls fact-mutation methods; `tests.test_webapp` asserts a new replay `quote_document_id` and empty board. |
| 9 | Replay responses identify the new candidate run and explicitly state that active facts were not mutated. | ✓ VERIFIED | Replay payload returns `quote_document_id`, `rows`, `exceptions`, `remaining_lines`, and `mutated_active_facts: False`; harvest-save tests assert the flag and replay lineage. |
| 10 | Operator-facing harvest/replay copy no longer claims that save or replay published rows to the board. | ✓ VERIFIED | `bookkeeping_web/pages.py` now renders “候选重放” / “未改动报价墙”; `tests.test_webapp` asserts the new copy is present and the old “继续补一段并上墙” / “并已上墙” strings are absent. |
| 11 | Web regressions no longer treat harvest/replay success as evidence that `/api/quotes/board` changed. | ✓ VERIFIED | Rebased web tests assert replay candidate documents and `quote_candidate_rows` counts, then confirm `/api/quotes/board` remains empty when no fact rows were seeded. |

**Score:** 11/11 truths verified

### Deferred Items

These are intentionally outside Phase 1 scope, not Phase 1 failures.

| # | Item | Addressed In | Evidence |
| --- | --- | --- | --- |
| 1 | Fixed schema/business validation and explicit `publishable_rows` separation | Phase 2 | ROADMAP Phase 2 goal: “Build explicit schema and business validators that separate `publishable_rows` from invalid or held rows.” |
| 2 | Guarded publisher as the only active-fact mutation path | Phase 3 | ROADMAP Phase 3 goal: “Ensure that only a guarded publisher can change active quote facts.” |
| 3 | Real `full_snapshot` / `delta_update` semantics beyond unresolved default | Phase 4 | ROADMAP Phase 4 goal: “Make `full_snapshot` and `delta_update` explicit message semantics with safe defaults.” |
| 4 | Replay comparison outputs and richer operator inspection workbench | Phases 5 and 7 | ROADMAP Phases 5 and 7 cover replay comparisons and message-level verification surfaces. |

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `wxbot/bookkeeping-platform/bookkeeping_core/quote_candidates.py` | Candidate contract dataclasses | ✓ VERIFIED | Defines `QuoteCandidateMessage` / `QuoteCandidateRow`, including `sender_display`, `confidence`, `message_fingerprint`, `run_kind`, `replay_of_quote_document_id`. |
| `wxbot/bookkeeping-platform/sql/postgres_schema.sql` | Additive candidate schema | ✓ VERIFIED | Adds Phase 1 columns to `quote_documents` and creates `quote_candidate_rows` with FK to `quote_documents`. |
| `wxbot/bookkeeping-platform/bookkeeping_core/database.py` | Candidate persistence boundary | ✓ VERIFIED | `record_quote_candidate_bundle()`, `list_quote_candidate_rows()`, schema verification, and board read model remain separate. |
| `wxbot/bookkeeping-platform/tests/test_postgres_backend.py` | DB regressions | ✓ VERIFIED | Covers candidate persistence, fail-fast schema checks, confidence persistence, and candidate FK integrity. |
| `wxbot/bookkeeping-platform/bookkeeping_core/quotes.py` | Runtime parse-to-candidate boundary | ✓ VERIFIED | Shared parse helper, candidate-only runtime capture, exception evidence preservation, no parser-direct fact writes. |
| `wxbot/bookkeeping-platform/tests/test_runtime.py` | Runtime regressions | ✓ VERIFIED | Asserts runtime candidate headers/rows, fingerprints, parser lineage, exception evidence, and zero `quote_price_rows` writes. |
| `wxbot/bookkeeping-platform/bookkeeping_web/app.py` | Replay candidate-only flow | ✓ VERIFIED | Replay persists candidate bundles, returns `mutated_active_facts: False`, and keeps board read model separate. |
| `wxbot/bookkeeping-platform/bookkeeping_web/pages.py` | Candidate-first operator copy | ✓ VERIFIED | Harvest/replay copy states candidate replay and explicit board non-mutation. |
| `wxbot/bookkeeping-platform/tests/test_webapp.py` | Replay/harvest web regressions | ✓ VERIFIED | Verifies replay lineage, unchanged board, and the replay-failure exception loop fix from `ed333b2`. |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| `bookkeeping_core/runtime.py` | `bookkeeping_core/quotes.py` | `self.quote_capture.capture_from_message(...)` | ✓ WIRED | `process_envelope()` always sends accepted inbound messages through quote capture before business actions. |
| `bookkeeping_core/quotes.py` | `bookkeeping_core/database.py` | `record_quote_candidate_bundle(candidate=...)` | ✓ WIRED | Runtime capture and inquiry-reply candidate paths persist candidate bundles through the DB boundary. |
| `bookkeeping_core/quotes.py` | `bookkeeping_core/database.py` | `record_quote_exception_unless_suppressed(...)` | ✓ WIRED | Parse failures and non-publishable rows still enter the exception store. |
| `bookkeeping_web/app.py` | `bookkeeping_core/quotes.py` | `parse_quote_message_to_candidate(..., run_kind=\"replay\", replay_of_quote_document_id=...)` | ✓ WIRED | Replay consumes the same helper contract as runtime rather than forking a new parser path. |
| `bookkeeping_web/app.py` | `bookkeeping_core/database.py` | `record_quote_candidate_bundle(candidate=...)` | ✓ WIRED | Replay writes a new replay candidate document instead of touching active fact rows. |
| `bookkeeping_web/app.py` | `bookkeeping_core/database.py` | `list_quote_board()` | ✓ WIRED | `/api/quotes/board` still reads the fact table read model, not candidate rows. |
| `bookkeeping_web/pages.py` | `bookkeeping_web/app.py` | `replay` payload fields including `mutated_active_facts` | ✓ WIRED | UI text and summary rendering consume replay metadata and state board non-mutation explicitly. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| --- | --- | --- | --- | --- |
| `bookkeeping_core/quotes.py` | `candidate.rows` / candidate header metadata | Template-engine parse output or missing-template fallback from raw message | Yes — runtime tests assert persisted candidate rows, fingerprints, parser lineage, and exception evidence | ✓ FLOWING |
| `bookkeeping_core/database.py` | `quote_documents` + `quote_candidate_rows` inserts | `candidate.to_document_payload()` / `candidate.to_row_payloads()` | Yes — backend tests assert stored raw message, sender evidence, confidence, JSON evidence, and FK integrity | ✓ FLOWING |
| `bookkeeping_web/app.py` | Replay candidate bundle | Stored `quote_documents.raw_text` + current `quote_group_profile` + shared parse helper | Yes — web tests assert new replay document ID, replay lineage, candidate row counts, and unchanged board | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| Candidate persistence contract works against PostgreSQL | `BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_postgres_backend -v` | Ran 8 tests, `OK` | ✓ PASS |
| Runtime ingestion uses candidate-only persistence | `BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_runtime -v` | Ran 40 tests, `OK` | ✓ PASS |
| Replay/harvest-save create replay candidates without board mutation | `BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_webapp -v` | Ran 65 tests, `OK` | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| `EVID-01` | `01-01`, `01-03` | User can trace every candidate or published quote row back to exact raw message, source line, sender, group, and message time | ✓ SATISFIED | Candidate headers persist raw message/group/time/sender evidence; candidate rows persist source-line evidence; replay lineage is stored and tested. |
| `CAND-01` | `01-02`, `01-03` | System creates quote candidates without directly mutating active quote facts | ✓ SATISFIED | Runtime and replay both persist candidate bundles; board stays on `quote_price_rows`; tests assert `quote_price_rows` remains empty in Phase 1 flows. |
| `CAND-02` | `01-01`, `01-02`, `01-03` | Each candidate preserves parser/template/rule lineage and message-type hypothesis for later debugging | ✓ SATISFIED | Candidate documents store `parser_kind`, `parser_template`, `parser_version`, `message_fingerprint`, `snapshot_hypothesis`, `snapshot_hypothesis_reason`, `run_kind`, and replay lineage. |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| --- | --- | --- | --- | --- |
| `wxbot/bookkeeping-platform/bookkeeping_core/database.py` | `deactivate_old_quotes_for_group()` / `upsert_quote_price_row_with_history()` definitions | Legacy fact-mutation APIs still exist in the DB layer | ℹ️ Info | Not called by runtime/replay anymore, so Phase 1 goal still holds; complete bypass removal is intentionally deferred to Phase 3. |
| `wxbot/bookkeeping-platform/bookkeeping_core/quote_candidates.py` | `resolve_candidate_sender_display()` | Sender display still piggybacks on brownfield `source_name` storage path | ℹ️ Info | Traceability is explicit enough for Phase 1, but a dedicated sender-display column may still be worthwhile if future phases need both concepts separately. |

## Residual Risks / Notes

- The strongest Phase 1 claim is verified for runtime and replay: parser output no longer writes quote facts directly in production code paths. The legacy fact-write helpers still exist as library methods, so the final system-wide bypass lock remains Phase 3 work.
- `snapshot_hypothesis` is intentionally stored as unresolved/default-safe metadata only. Phase 1 lays the contract; it does not implement real snapshot semantics yet.
- `graphify` rebuild was attempted previously but failed because the current environment lacks the `graphify` module. That is an environment/tooling issue, not evidence of a product gap in Phase 1.

## Gaps Summary

No blocking gaps were found against the Phase 1 goal or its roadmap contract. Phase 1 achieved the intended outcome: runtime and replay now persist candidate evidence through a two-layer message/header plus row-candidate contract, parser output no longer mutates quote facts directly in those paths, and the groundwork is in place for later validator, publisher, snapshot, and operator phases.

---

_Verified: 2026-04-13T18:31:25Z_
_Verifier: Claude (gsd-verifier)_
