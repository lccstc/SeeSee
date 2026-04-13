# Structure

## Repository Layout

Top-level directories of interest:

- `PROJECT/` — product notes, PRD-lite docs, handoff notes
- `graphify-out/` — repo-level graph artifacts
- `wxbot/bookkeeping-platform/` — primary Python application
- `wxbot/whatsapp-bookkeeping/` — WhatsApp TypeScript adapter

## Primary Python App Layout

Root: `wxbot/bookkeeping-platform/`

Key files:

- `reporting_server.py` — threaded WSGI startup entrypoint
- `wsgi.py` — alternate WSGI entrypoint surface
- `requirements-dev.txt` — Python dependency pinning
- `sql/postgres_schema.sql` — database schema
- `README.md` and `README-启动顺序.md` — operational docs

Primary packages:

- `bookkeeping_core/`
  - domain logic, parsing, persistence, reporting
- `bookkeeping_web/`
  - HTTP routing and HTML page generation
- `wechat_adapter/`
  - WeChat thin adapter
- `tests/`
  - `unittest` test suite
- `scripts/`
  - operational helper scripts like `seed_quote_demo.py`
- `docs/`
  - operator-facing usage documents

## `bookkeeping_core/` Breakdown

Core module set:

- `database.py` — persistence primitives and store methods
- `runtime.py` — unified runtime object
- `service.py` — envelope handling and bookkeeping behavior
- `template_engine.py` — strict quote template engine
- `quotes.py` — quote capture and quote-specific helpers
- `analytics.py` / `reporting.py` / `periods.py` / `reconciliation.py` — reporting and finance workflows
- `contracts.py` / `models.py` — shared contracts and data models

## `bookkeeping_web/` Breakdown

- `app.py` — very large routing and request handling file
- `pages.py` — all page markup, inline CSS, inline JS

Practical implication:

- Route changes usually land in `app.py`
- Page/interaction changes usually land in `pages.py`
- Business rules should still be pushed down into `bookkeeping_core/`

## WeChat Adapter Layout

Directory: `wxbot/bookkeeping-platform/wechat_adapter/`

- `main.py` — main loop
- `client.py` — WeChat platform API wrapper
- `core_api.py` — remote core transport
- `config.py` — config model and load/save logic

## WhatsApp Adapter Layout

Directory: `wxbot/whatsapp-bookkeeping/`

- `src/index.ts` — orchestration entrypoint
- `src/core-api.ts` — core transport and action execution helpers
- `src/whatsapp.ts` — Baileys wrapper
- `src/config.ts` — config loading
- `src/*.test.ts` — built-in node test coverage
- `package.json` / `tsconfig.json` — TS project metadata

## Test Layout

Python tests:

- `wxbot/bookkeeping-platform/tests/test_template_engine.py`
- `wxbot/bookkeeping-platform/tests/test_webapp.py`
- `wxbot/bookkeeping-platform/tests/test_runtime.py`
- `wxbot/bookkeeping-platform/tests/test_reporting.py`
- `wxbot/bookkeeping-platform/tests/test_periods.py`
- `wxbot/bookkeeping-platform/tests/test_reconciliation.py`
- `wxbot/bookkeeping-platform/tests/test_ingestion_alignment.py`
- `wxbot/bookkeeping-platform/tests/test_postgres_backend.py`
- `wxbot/bookkeeping-platform/tests/support/postgres_test_case.py`

TypeScript tests:

- `wxbot/whatsapp-bookkeeping/src/core-api.test.ts`
- `wxbot/whatsapp-bookkeeping/src/chat-context.test.ts`
- `wxbot/whatsapp-bookkeeping/src/whatsapp.test.ts`

## Naming / Placement Heuristic

- Domain logic belongs under `bookkeeping_core/`
- HTTP routes and page endpoints belong under `bookkeeping_web/`
- Transport-specific logic belongs in the relevant adapter directory
- Tests generally mirror the subsystem being validated by file name
