# Conventions

## High-Level Style

This repository favors explicit, imperative code over framework abstraction.

- Python code is mostly function-and-class based with direct method calls
- Routing is manual instead of declarative
- Business invariants are enforced with explicit `ValueError` checks
- Runtime behavior is documented heavily in README and operational docs

## Python Conventions

- `from __future__ import annotations` appears broadly and should be preserved
- Type hints are used, but the code does not appear to require mypy or pyright
- Internal helpers are prefixed with `_`, for example `_with_db`, `_resolve_db_target`, `_extract_search_path_schema`
- Errors are usually raised as `ValueError` close to validation boundaries
- DB rows are treated as dict-like payloads instead of ORM objects

Observed file-level convention:

- Domain logic in `bookkeeping_core/`
- Display-only page functions in `bookkeeping_web/pages.py`
- Route wiring in `bookkeeping_web/app.py`

## Route / Request Handling Conventions

- `bookkeeping_web/app.py` dispatches by `path` and `method`
- JSON endpoints typically return through `_respond_json(...)`
- HTML endpoints return through `_respond_html(...)`
- DB-scoped handlers use `_with_db(...)`
- Runtime-scoped handlers use `_with_runtime(...)`
- Protected endpoints reject unauthenticated requests with `401 {"error": "Unauthorized"}`

## Frontend Conventions

- HTML, CSS, and JS are embedded as Python strings in `wxbot/bookkeeping-platform/bookkeeping_web/pages.py`
- Pages use semantic IDs for testability, for example:
  - `quote-filter-form`
  - `quote-board-table`
  - `quote-profile-table`
  - `quote-dictionary-form`
- `fetch(...)` calls target same-origin JSON APIs

## Template / Quote Parsing Conventions

- Quote parsing is strict by design, not permissive by default
- Full-width punctuation normalization is explicit in `template_engine.py`
- Group-specific template config is represented by `TemplateConfig`
- Replayability matters: tests repeatedly assert that generated patterns can match original text again

## TypeScript Conventions

- ES modules only (`"type": "module"`)
- `strict` TypeScript mode enabled in `wxbot/whatsapp-bookkeeping/tsconfig.json`
- Prefer explicit interfaces and utility types:
  - `CoreApiConfigSource`
  - `SelfMessageTracker`
  - `WhatsAppMessage`
- Node built-ins and runtime libs are imported directly; no framework wrapper layer

## Logging Conventions

- Python uses `logging`
- TypeScript adapter uses `pino`
- Errors and transient transport failures are logged rather than swallowed
- Outbound action execution logs IDs/results in the WhatsApp adapter

## Practical Change Rules

- Put bookkeeping, parsing, reconciliation, and quote logic in `wxbot/bookkeeping-platform/bookkeeping_core/`
- Put page/UI-only changes in `wxbot/bookkeeping-platform/bookkeeping_web/pages.py`
- Put request/authorization/wiring changes in `wxbot/bookkeeping-platform/bookkeeping_web/app.py`
- Keep adapter logic thin; do not move business authority into `wechat_adapter/` or `whatsapp-bookkeeping/src/`
