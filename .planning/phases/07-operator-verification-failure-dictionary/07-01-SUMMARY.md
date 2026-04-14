---
phase: 07
plan: 01
title: Message-level verification evidence payloads
status: completed
requirements:
  - OPS-01
  - EVID-02
files_changed:
  - wxbot/bookkeeping-platform/bookkeeping_core/database.py
  - wxbot/bookkeeping-platform/bookkeeping_web/app.py
  - wxbot/bookkeeping-platform/tests/test_postgres_backend.py
  - wxbot/bookkeeping-platform/tests/test_webapp.py
completed_at: 2026-04-15
---

# Phase 07 Plan 07-01 Summary

Wave 1 created the message-level verification evidence substrate that Phase 07 needs.

## What Changed

- Added `BookkeepingDB.get_quote_document_verification_evidence(...)` in [database.py](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_core/database.py), which aggregates one `quote_document_id` into a coherent payload:
  - message metadata
  - candidate rows
  - latest validation run and grouped row decisions
  - snapshot decision lineage
  - linked exception / repair metadata
  - publish reasoning, including `untouched_active_rows` and `would_inactivate_active_rows`
- Added `list_active_quote_rows_for_group(...)` and document-linked exception lookup so the evidence payload can explain current-wall impact instead of just parser or validator state.
- Added read-only `/api/quotes/evidence` in [app.py](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_web/app.py). It accepts either `quote_document_id` or `exception_id` and returns one proof-oriented evidence object.
- Tightened publish reasoning wording so the API explicitly says the evidence view itself `未改动报价墙`.
- Hardened JSON serialization in [database.py](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/bookkeeping_core/database.py) so PostgreSQL `Decimal` values from validation / evidence paths are JSON-safe.

## Verification

- `python3 -m py_compile bookkeeping_core/database.py bookkeeping_web/app.py tests/test_postgres_backend.py tests/test_webapp.py` — passed
- `BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_postgres_backend.PostgresBackendTests.test_quote_document_verification_evidence_explains_delta_untouched_rows tests.test_postgres_backend.PostgresBackendTests.test_quote_document_verification_evidence_explains_confirmed_full_snapshot_inactivation tests.test_webapp.WebRepairCaseTests.test_quote_evidence_endpoint_returns_read_only_message_level_payload tests.test_webapp.WebRepairCaseTests.test_quote_evidence_endpoint_accepts_exception_id_indirection -v` — passed, 4 tests

## Deviations

- Kept the payload read-only; no new publish, resolve, or fact-mutation endpoint was introduced.
- Did not build the operator-facing page UI yet. That remains Wave 2.
- Repair linkage is still case-oriented and additive; no new publish-attempt event table was introduced in this wave.

## Self-Check

- Summary file created at `.planning/phases/07-operator-verification-failure-dictionary/07-01-SUMMARY.md`
- One message can now be explained end-to-end through a durable, read-only evidence object
