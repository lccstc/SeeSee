# Architecture

## System Shape

The codebase follows a hub-and-spoke design:

- One Python core owns bookkeeping logic and persistence
- Thin chat adapters normalize inbound messages and execute outbound actions
- The web layer shares the same Python core and database

This matches the repo-level architecture guidance in `AGENTS.md`: adapters receive and normalize, the core remains the single business runtime.

## Main Components

### 1. Core Domain Layer

Location: `wxbot/bookkeeping-platform/bookkeeping_core/`

Key modules:

- `runtime.py` defines `UnifiedBookkeepingRuntime`
- `service.py` houses higher-level bookkeeping command processing
- `database.py` owns DB access and persistence helpers
- `quotes.py`, `template_engine.py`, `parser.py`, `ingestion.py` drive quote parsing/capture
- `reporting.py`, `analytics.py`, `periods.py`, `reconciliation.py` serve reporting and operational workflows

This is the real business core. UI and adapters both route into it.

### 2. Web / HTTP Layer

Location: `wxbot/bookkeeping-platform/bookkeeping_web/`

- `app.py` is a large manual router plus request handler layer
- `pages.py` generates the actual HTML/CSS/JS for pages

Pattern:

- HTML pages are returned directly for top-level paths
- JSON endpoints open a DB connection per request through `_with_db(...)`
- Core endpoints use a lazily initialized shared runtime via `_with_runtime(...)`

### 3. Core Server Process

Location: `wxbot/bookkeeping-platform/reporting_server.py`

- Wraps the WSGI app with a threaded server
- Parses startup args and environment
- Enforces PostgreSQL DSN before boot

### 4. WeChat Adapter

Location: `wxbot/bookkeeping-platform/wechat_adapter/`

- `main.py` contains the polling/event loop
- `client.py` encapsulates WeChat platform IO
- `core_api.py` handles remote core HTTP transport
- `config.py` loads/persists adapter configuration

Role: transport only, no business settlement authority.

### 5. WhatsApp Adapter

Location: `wxbot/whatsapp-bookkeeping/src/`

- `index.ts` orchestrates normalization, core calls, outbound polling, and self-message suppression
- `core-api.ts` defines the HTTP contract with core
- `whatsapp.ts` wraps Baileys socket behavior
- `config.ts` loads local config

Role: same as WeChat, a thin edge adapter.

## Data Flow

Inbound path:

1. WeChat or WhatsApp receives a message
2. Adapter converts it into a normalized envelope
3. Adapter sends it to `POST /api/core/messages`
4. `UnifiedBookkeepingRuntime.process_envelope()` records the message and triggers capture / bookkeeping logic
5. Core returns zero or more actions
6. Adapter executes actions and acknowledges outcomes

Outbound path:

1. Core queues or exposes outbound actions
2. Adapter polls `POST /api/core/actions`
3. Adapter executes `send_text` / `send_file`
4. Adapter posts acknowledgement to `POST /api/core/actions/ack`

## Quote Parsing Sub-Architecture

The quote wall subsystem is a first-class internal architecture, not an add-on.

- Strict template matching lives in `wxbot/bookkeeping-platform/bookkeeping_core/template_engine.py`
- Quote capture lives in `wxbot/bookkeeping-platform/bookkeeping_core/quotes.py`
- Exception handling and template management routes live in `wxbot/bookkeeping-platform/bookkeeping_web/app.py`
- Operator-facing quote UI lives in `wxbot/bookkeeping-platform/bookkeeping_web/pages.py`

Architecturally important constraint:

- Group template profiles and exception remediation are part of the design, not fallback hacks
- The engine favors accuracy and replayability over broad heuristic parsing

## Build Order Implications

If extending this system, the natural dependency order is:

1. Schema / persistence capability in `database.py` and SQL schema
2. Core business behavior in `bookkeeping_core/`
3. HTTP surface in `bookkeeping_web/app.py`
4. Operator UI in `pages.py`
5. Adapter behavior in `wechat_adapter/` and `whatsapp-bookkeeping/src/`

The biggest architectural pressure points are `BookkeepingDB`, `TemplateConfig`, `UnifiedBookkeepingRuntime`, and the large route surface in `bookkeeping_web/app.py`.
