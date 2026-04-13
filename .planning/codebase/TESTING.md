# Testing

## Test Frameworks

Two separate test stacks are present:

- Python: `unittest`
- TypeScript: Node built-in test runner via `node --test`

This matches the repo instruction in `AGENTS.md`: Python tests should be run with `python -m unittest`.

## Python Test Layout

Python tests live under `wxbot/bookkeeping-platform/tests/`.

Important suites:

- `test_template_engine.py` — strict template parsing and pattern round-trips
- `test_webapp.py` — WSGI app, page rendering, quote wall UI/API behavior
- `test_runtime.py` — unified runtime behavior
- `test_reporting.py` and `test_analytics.py` — reporting payloads
- `test_periods.py` — settlement periods
- `test_reconciliation.py` — reconciliation workflows
- `test_ingestion_alignment.py` — runtime/storage alignment
- `test_postgres_backend.py` — PostgreSQL-only runtime guarantees
- `test_reporting_server.py` — server startup helpers

## Python Test Patterns

- Database-backed tests inherit from `PostgresTestCase` in `wxbot/bookkeeping-platform/tests/support/postgres_test_case.py`
- Each test schema is isolated by dynamically creating a new PostgreSQL schema
- Schema SQL is re-applied from `wxbot/bookkeeping-platform/sql/postgres_schema.sql`
- Tests commonly instantiate `BookkeepingDB` directly
- Web tests build WSGI environ objects manually using `wsgiref.util.setup_testing_defaults`

This is a practical, low-abstraction integration-style test strategy.

## Example Assertions

Observed strong regression coverage around:

- route authorization and bad payload handling
- quote wall HTML structure and element IDs
- quote exception workflow preview/save/replay flows
- dictionary write protection via `QUOTE_ADMIN_PASSWORD`
- runtime requirement that SQLite is rejected for production paths

## TypeScript Test Layout

Tests live alongside source in `wxbot/whatsapp-bookkeeping/src/`.

- `core-api.test.ts`
- `chat-context.test.ts`
- `whatsapp.test.ts`

Script entry:

- `npm test` runs `node --test src/*.test.ts`

## TypeScript Test Patterns

- Tests monkeypatch `globalThis.fetch` for API client verification
- Runtime import behavior is tested using local module loading
- Package metadata assertions are included, for example ensuring old SQLite dependencies are absent

## Recommended Test Entry Points

From `wxbot/bookkeeping-platform/README.md`:

- `../../.venv/bin/python -m unittest tests.test_postgres_backend -v`
- `../../.venv/bin/python -m unittest tests.test_ingestion_alignment tests.test_periods tests.test_reporting tests.test_analytics tests.test_webapp tests.test_postgres_backend -v`

From `wxbot/whatsapp-bookkeeping/package.json`:

- `npm test`
- `npm run build`

## Coverage Gaps to Keep in Mind

- The WSGI/router layer is heavily centralized in `bookkeeping_web/app.py`, so route additions should come with focused regression tests
- `pages.py` is large and string-driven; UI regressions are guarded mostly through presence/structure assertions, not browser automation
- Adapter integrations are contract-tested, but true end-to-end multi-process integration remains an operational validation step
