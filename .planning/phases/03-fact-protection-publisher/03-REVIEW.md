---
phase: 03-fact-protection-publisher
reviewed: 2026-04-15T00:00:00Z
depth: standard
files_reviewed: 8
files_reviewed_list:
  - wxbot/bookkeeping-platform/bookkeeping_core/quote_publisher.py
  - wxbot/bookkeeping-platform/bookkeeping_core/database.py
  - wxbot/bookkeeping-platform/bookkeeping_core/quotes.py
  - wxbot/bookkeeping-platform/bookkeeping_web/app.py
  - wxbot/bookkeeping-platform/scripts/seed_quote_demo.py
  - wxbot/bookkeeping-platform/tests/test_postgres_backend.py
  - wxbot/bookkeeping-platform/tests/test_runtime.py
  - wxbot/bookkeeping-platform/tests/test_webapp.py
findings:
  critical: 0
  warning: 2
  info: 0
  total: 2
status: resolved_after_fix
---

# Phase 03: Code Review Report

**Reviewed:** 2026-04-15T00:00:00Z
**Depth:** standard
**Files Reviewed:** 8
**Status:** resolved_after_fix

## Summary

Phase 03 substantially improves atomicity and removes the obvious web/script delete bypasses. The targeted Phase 03 regression tests pass against PostgreSQL. The remaining concerns are both about whether the new publisher boundary is actually enforceable over time: the publisher still trusts caller-supplied rows, and the new architecture guard test does not cover raw SQL bypasses.

## Warnings

### WR-01: The guarded publisher still allows validator bypass via caller-supplied rows

**File:** `wxbot/bookkeeping-platform/bookkeeping_core/quote_publisher.py:92`
**Issue:** `QuoteFactPublisher.publish_quote_document()` accepts arbitrary `publishable_rows` from the caller and applies them directly. It never reloads or verifies those rows against `quote_document_id` / `validation_run_id`, so any future route/script/agent that can call the publisher can still skip validator custody by fabricating row dicts. The Phase 03 tests also encode this contract by calling the publisher with hand-built row payloads instead of persisted validator output.
**Fix:** Make the publisher fetch publishable rows itself from `validation_run_id` + `quote_document_id`, or require row IDs and verify lineage before mutating facts. Add a regression that a fabricated row payload is rejected and leaves `quote_price_rows` untouched.

### WR-02: The structural bypass test would miss a raw SQL regression like the one Phase 03 just removed

**File:** `wxbot/bookkeeping-platform/tests/test_runtime.py:24`
**Issue:** `QuoteFactCustodyArchitectureTests` only flags AST calls to `deactivate_old_quotes_for_group()` and `upsert_quote_price_row_with_history()`. It does not detect direct `conn.execute("DELETE/INSERT/UPDATE ... quote_price_rows")` callsites, so a future raw SQL bypass in web/routes/scripts could reappear without failing the test. That is the exact class of bypass removed from `bookkeeping_web/app.py`.
**Fix:** Extend the guard to also scan `execute()` / `executemany()` string literals for mutating `quote_price_rows` statements outside an allowlist. Add a regression fixture or explicit assertion covering the raw-SQL delete pattern.

## Resolution

- **WR-01 resolved:** `QuoteFactPublisher.publish_quote_document()` now reloads validator-owned rows from `quote_document_id + validation_run_id` inside the publisher instead of trusting caller-supplied payloads.
- **WR-02 resolved:** `QuoteFactCustodyArchitectureTests` now blocks raw SQL `DELETE/INSERT/UPDATE quote_price_rows` string literals outside the allowlist, not just helper callsites.
- **Resolution verified:** `BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_postgres_backend tests.test_runtime tests.test_webapp.WebAppTests.test_quote_delete_endpoint_is_disabled_and_leaves_active_facts_untouched -v` — passed, 88 tests.

---

_Reviewed: 2026-04-15T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
