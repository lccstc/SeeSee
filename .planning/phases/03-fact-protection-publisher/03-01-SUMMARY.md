---
phase: 03
plan: 01
title: Guarded quote publisher custody
status: completed
requirements:
  - FACT-01
  - FACT-03
files_changed:
  - wxbot/bookkeeping-platform/bookkeeping_core/quote_publisher.py
  - wxbot/bookkeeping-platform/bookkeeping_core/database.py
  - wxbot/bookkeeping-platform/bookkeeping_core/quotes.py
  - wxbot/bookkeeping-platform/tests/test_postgres_backend.py
  - wxbot/bookkeeping-platform/tests/test_runtime.py
completed_at: 2026-04-15
---

# Phase 03 Plan 03-01 Summary

One guarded `QuoteFactPublisher` now owns the intended active-quote mutation API, while runtime quote capture calls that publisher with validator-owned `publishable_rows` in explicit `validation_only` mode.

## What Changed

- Added `bookkeeping_core/quote_publisher.py` with `QuoteFactPublisher` and structured `QuoteFactPublishResult`.
- Wired `QuoteCaptureService` to call the publisher after candidate + validator persistence, using `list_publishable_quote_candidate_rows(...)` instead of parser-side publish hints.
- Narrowed quote mutation helpers in `database.py` so publisher call sites can opt out of hidden `commit()` behavior and run inside one outer transaction.
- Added PostgreSQL regressions proving helper rollback participation and publisher rollback on failure.
- Added runtime regression proving quote capture delegates to the publisher and passes validator-owned publishable rows.

## Verification

- `python3 -m py_compile bookkeeping_core/quote_publisher.py bookkeeping_core/database.py bookkeeping_core/quotes.py tests/test_postgres_backend.py tests/test_runtime.py` — passed
- `BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_postgres_backend -v` — passed, 24 tests
- `BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_runtime -v` — passed, 54 tests
- `BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_webapp -v` — failed, 1 pre-existing out-of-scope failure in `tests.test_webapp.WebAppTests.test_ignored_quote_exception_suppresses_same_content_but_not_other_groups`

## Deviations

- Kept runtime in explicit `validation_only` publisher mode. This preserves Phase 03 scope and avoids silently introducing Phase 04 snapshot semantics.
- Did not update `.planning/STATE.md` or `.planning/ROADMAP.md` because this execution was limited to the user-owned write scope.
- Graph rebuild command failed because the active environment does not have the `graphify` module installed.

## Self-Check

- Summary file created at `.planning/phases/03-fact-protection-publisher/03-01-SUMMARY.md`
- All modified code files are inside the granted write scope
