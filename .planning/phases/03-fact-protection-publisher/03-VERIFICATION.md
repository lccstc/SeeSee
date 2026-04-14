---
phase: 03-fact-protection-publisher
verified: 2026-04-15T03:21:00+07:00
status: verified
score: 3/3 truths verified
overrides_applied: 0
known_non_blocking_issues:
  - "graphify rebuild remains blocked in this environment because the local graphify module is missing."
---

# Phase 03: Fact Protection Publisher Verification Report

**Phase Goal:** Ensure that only a guarded publisher can change active quote facts, and that failures never corrupt existing wall state.  
**Verified:** 2026-04-15T03:21:00+07:00  
**Status:** verified  
**Verdict:** Verified with known non-blocking issues

## Verification Refresh

This report was refreshed after code review surfaced two real Phase 03 custody gaps:

1. The publisher originally trusted caller-supplied `publishable_rows`
2. The architecture guard originally missed raw SQL `quote_price_rows` mutation callsites

Both gaps are now fixed in code and covered by the PostgreSQL/runtime/web rerun documented below.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | No parse, validation, or publish failure clears existing active quote facts | ✓ VERIFIED | [`QuoteFactPublisher.publish_quote_document()`](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_core/quote_publisher.py:92) wraps mutation in one transaction, takes a per-group advisory lock, locks live rows, and returns `failed` on exception without committing partial state; low-level helpers now accept `commit=False` in [`database.py`](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_core/database.py:1672) and [/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_core/database.py:1688]. PostgreSQL tests prove rollback after deactivate failure and partial apply failure in [`test_postgres_backend.py`](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/tests/test_postgres_backend.py:722) and [/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/tests/test_postgres_backend.py:1021). |
| 2 | Messages with zero `publishable_rows` result in no active-fact mutation | ✓ VERIFIED | The guarded publisher reloads validator-owned rows from `quote_document_id + validation_run_id` before any destructive step and exits early when that persisted row set is empty in [`quote_publisher.py`](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_core/quote_publisher.py:108). Runtime still delegates through the publisher in validation-only mode from [`quotes.py`](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_core/quotes.py:1478). Tests prove explicit `no_op` behavior and zero `quote_price_rows` writes in [`test_postgres_backend.py`](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/tests/test_postgres_backend.py:874) and [`test_runtime.py`](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/tests/test_runtime.py:1793). |
| 3 | UI actions, scripts, and agent-driven operations cannot bypass the guarded publish path | ✓ VERIFIED | Runtime is forced through the publisher in [`quotes.py`](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_core/quotes.py:1478). The legacy delete route is narrowed to a 409 proof-only no-op in [`app.py`](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_web/app.py:1756). Replay/result-save flows remain fact-neutral with `mutated_active_facts: False` in [`app.py`](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_web/app.py:1314). `seed_quote_demo.py --clear` is disabled in [`seed_quote_demo.py`](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/scripts/seed_quote_demo.py:169). The AST custody guard now blocks both helper callsites and raw SQL `quote_price_rows` mutation strings outside the allowlist in [`test_runtime.py`](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/tests/test_runtime.py:24). |

**Score:** 3/3 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `wxbot/bookkeeping-platform/bookkeeping_core/quote_publisher.py` | Single guarded active-fact mutation entrypoint | ✓ VERIFIED | `QuoteFactPublisher` and structured publish results are implemented in [quote_publisher.py](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_core/quote_publisher.py:7). |
| `wxbot/bookkeeping-platform/bookkeeping_core/database.py` | Publisher-safe low-level helpers, lock helpers, no hidden commits on publisher path | ✓ VERIFIED | Per-group advisory lock, active-row row lock, and commit-controlled mutation helpers exist in [database.py](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_core/database.py:1638). |
| `wxbot/bookkeeping-platform/bookkeeping_core/quotes.py` | Runtime delegates publish custody to publisher with persisted validator lineage only | ✓ VERIFIED | Quote capture instantiates the publisher and passes only `quote_document_id + validation_run_id`; the publisher itself reloads validator-owned rows before mutation in [quotes.py](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_core/quotes.py:1478) and [quote_publisher.py](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_core/quote_publisher.py:108). |
| `wxbot/bookkeeping-platform/bookkeeping_web/app.py` | Web surfaces are guarded or fact-neutral | ✓ VERIFIED | Delete is disabled; replay surfaces keep `mutated_active_facts: False` in [app.py](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_web/app.py:1138), [/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_web/app.py:1314), and [/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_web/app.py:1756). |
| `wxbot/bookkeeping-platform/scripts/seed_quote_demo.py` | Seed/demo tooling does not normalize raw active-fact deletion | ✓ VERIFIED | `--clear` now exits with an explicit refusal in [seed_quote_demo.py](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/scripts/seed_quote_demo.py:169). |
| `wxbot/bookkeeping-platform/sql/postgres_schema.sql` | Schema-level live-row integrity backstop | ✓ VERIFIED | Partial unique live-row index exists in [postgres_schema.sql](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/sql/postgres_schema.sql:348). |
| `wxbot/bookkeeping-platform/tests/test_postgres_backend.py` | Rollback, no-op, locking, and index regressions | ✓ VERIFIED | Phase-specific PostgreSQL regressions cover the guarded publisher path in [test_postgres_backend.py](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/tests/test_postgres_backend.py:722). |
| `wxbot/bookkeeping-platform/tests/test_runtime.py` | Runtime custody and structural bypass guard | ✓ VERIFIED | Runtime publisher delegation and the expanded AST/raw-SQL custody guard live in [test_runtime.py](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/tests/test_runtime.py:24) and [/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/tests/test_runtime.py:1553). |
| `wxbot/bookkeeping-platform/tests/test_webapp.py` | Disabled delete route regression | ✓ VERIFIED | Web delete no-op coverage exists in [test_webapp.py](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/tests/test_webapp.py:527). |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| `quotes.py` | `quote_publisher.py` | Runtime publish delegation | ✓ WIRED | Runtime no longer mutates `quote_price_rows` directly; it calls the publisher with `quote_document_id + validation_run_id`, and the publisher resolves validator-owned rows internally in [quotes.py](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_core/quotes.py:1478) and [quote_publisher.py](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_core/quote_publisher.py:108). |
| `quote_publisher.py` | `database.py` | Transaction, lock, deactivate, upsert custody | ✓ WIRED | The publisher owns the outer transaction and uses DB lock/mutation primitives with `commit=False` in [quote_publisher.py](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_core/quote_publisher.py:140). |
| `quote_publisher.py` | `postgres_schema.sql` | Live-row uniqueness backstop | ✓ WIRED | Publisher assumptions are reinforced by `quote_price_rows_one_live_row` in [postgres_schema.sql](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/sql/postgres_schema.sql:348), with enforcement tested in [test_postgres_backend.py](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/tests/test_postgres_backend.py:1134). |
| `bookkeeping_web/app.py` | Guarded publisher custody | Narrowed route/delete + fact-neutral replay | ✓ GUARDED | Phase 03 satisfies web custody by removing the delete side door and keeping replay flows proof-only instead of adding a second publisher in the web layer; see [app.py](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_web/app.py:1314) and [/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_web/app.py:1756). |
| `tests/test_runtime.py` | `tests/test_webapp.py` | Structural and route-level bypass prevention | ✓ WIRED | The architecture guard blocks forbidden helper callsites and raw SQL `quote_price_rows` mutations globally while the web test proves the old delete endpoint no longer mutates active rows. |

### Data-Flow Trace

| Artifact | Data Variable | Source | Produces Real Data | Status |
| --- | --- | --- | --- | --- |
| `quote_publisher.py` guarded publish call | `publishable_rows` | `db.list_publishable_quote_candidate_rows(quote_document_id, validation_run_id)` reloaded inside publisher | Yes | ✓ FLOWING |
| `quote_publisher.py` apply path | live `quote_price_rows` mutations | Transaction-scoped deactivate + upsert operations behind advisory/row locks | Yes | ✓ FLOWING |
| `app.py` replay/result-save surfaces | `mutated_active_facts` | Explicit proof-only replay payload | Yes, fact-neutral by design | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| Publisher rollback, no-op, locking, and live-row index | `BOOKKEEPING_TEST_DSN=... ./.venv/bin/python -m unittest tests.test_postgres_backend tests.test_runtime tests.test_webapp.WebAppTests.test_quote_delete_endpoint_is_disabled_and_leaves_active_facts_untouched -v` | Ran 88 tests, `OK` | ✓ PASS |
| Runtime custody, explicit no-op result, and disabled delete route | `BOOKKEEPING_TEST_DSN=... ./.venv/bin/python -m unittest tests.test_postgres_backend tests.test_runtime tests.test_webapp.WebAppTests.test_quote_delete_endpoint_is_disabled_and_leaves_active_facts_untouched -v` | Ran 88 tests, `OK` | ✓ PASS |
| Plan artifact presence | `gsd-tools verify artifacts` on `03-01`, `03-02`, `03-03` plans | 7/7 listed artifacts found and substantive | ✓ PASS |

### Requirements Coverage

| Requirement | Description | Status | Evidence |
| --- | --- | --- | --- |
| `FACT-01` | Failed parse, validation, or publish attempts leave prior active quote facts untouched | ✓ SATISFIED | Guarded transaction/rollback path in [quote_publisher.py](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_core/quote_publisher.py:140), commit-controlled DB helpers in [database.py](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_core/database.py:1672), and rollback regressions in [test_postgres_backend.py](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/tests/test_postgres_backend.py:722) and [/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/tests/test_postgres_backend.py:1021). |
| `FACT-02` | If a message produces no `publishable_rows`, the system performs no publish for that message | ✓ SATISFIED | Explicit `no_publishable_rows` no-op in [quote_publisher.py](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_core/quote_publisher.py:121); validator-owned row sourcing now occurs inside the publisher in [quote_publisher.py](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_core/quote_publisher.py:108); no-op tests in [test_postgres_backend.py](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/tests/test_postgres_backend.py:874) and [test_runtime.py](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/tests/test_runtime.py:1793). |
| `FACT-03` | No route, script, page action, Agent, or SubAgent can bypass validator and publisher safeguards to mutate active quotes directly | ✓ SATISFIED | Delete route disabled in [app.py](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_web/app.py:1756); replay remains fact-neutral in [app.py](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_web/app.py:1314); demo clear path disabled in [seed_quote_demo.py](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/scripts/seed_quote_demo.py:169); architecture guard for helpers and raw SQL lives in [test_runtime.py](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/tests/test_runtime.py:24); route regression in [test_webapp.py](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/tests/test_webapp.py:527). |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| --- | --- | --- | --- | --- |
| — | — | No blocking TODO/placeholder/orphaned-mutation anti-patterns found in Phase 03 implementation surfaces | — | No blocker detected |
| [03-01-SUMMARY.md](/Users/newlcc/SeeSee/repo/.planning/phases/03-fact-protection-publisher/03-01-SUMMARY.md:35) | 35 | One unrelated pre-existing `tests.test_webapp` failure remained during the broader suite run | ℹ️ Info | Non-blocking to Phase 03 because the failing case does not exercise publisher custody |
| [03-03-SUMMARY.md](/Users/newlcc/SeeSee/repo/.planning/phases/03-fact-protection-publisher/03-03-SUMMARY.md:89) | 89 | `graphify` rebuild blocked by missing local module | ℹ️ Info | Non-blocking to FACT-01/02/03 verification |

### Gaps Summary

No blocking implementation gaps remain for Phase 03. The guarded publisher now owns active-fact mutation custody, reloads validator-owned rows at the mutation boundary, empty or disallowed publish attempts are explicit no-ops, publish failures roll back cleanly, and the remaining legacy web/script side doors are either disabled or structurally prevented by helper + raw-SQL custody guards.

The only known non-blocking issue is the local-environment `graphify` rebuild block.

---

_Verified: 2026-04-15T03:21:00+07:00_  
_Verifier: Claude (gsd-verifier)_
