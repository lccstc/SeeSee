# Integrations

## Core External Systems

The repository integrates with three operational boundaries: PostgreSQL, WeChat automation, and WhatsApp Web.

## PostgreSQL

- Production/runtime persistence uses PostgreSQL DSNs only.
- Guardrail is explicit in `wxbot/bookkeeping-platform/bookkeeping_core/database.py` via:
  - `is_postgres_dsn()`
  - `require_postgres_dsn()`
- Core and web runtime instantiate `BookkeepingDB` against the DSN in:
  - `wxbot/bookkeeping-platform/reporting_server.py`
  - `wxbot/bookkeeping-platform/bookkeeping_web/app.py`
- Test suites create isolated schemas against a shared PostgreSQL database in `wxbot/bookkeeping-platform/tests/support/postgres_test_case.py`.

## Core HTTP API

The core runtime exposes adapter-facing HTTP endpoints from `wxbot/bookkeeping-platform/bookkeeping_web/app.py`.

- Primary message ingress:
  - `POST /api/core/messages`
- Outbound action polling:
  - `POST /api/core/actions`
- Outbound acknowledgement:
  - `POST /api/core/actions/ack`
- Message inspection / parse introspection:
  - `GET /api/incoming-messages`
  - `GET /api/incoming-messages/with-transactions`
  - `GET /api/parse-results`
  - `GET /api/message-inspector`

Authentication pattern:

- Bearer token checked by `_is_authorized(...)` in `wxbot/bookkeeping-platform/bookkeeping_web/app.py`
- Token source comes from `BOOKKEEPING_CORE_TOKEN` or `--core-token`

## WeChat Adapter Integration

- WeChat adapter runtime lives in `wxbot/bookkeeping-platform/wechat_adapter/`
- Main loop in `wxbot/bookkeeping-platform/wechat_adapter/main.py`
- Remote core client in `wxbot/bookkeeping-platform/wechat_adapter/core_api.py`
- Platform-specific message collection in `wxbot/bookkeeping-platform/wechat_adapter/client.py`

Observed contract:

- Adapter collects platform messages
- Converts them to normalized envelopes
- Sends them to remote core
- Executes returned `send_text` / `send_file` actions
- Polls outbound actions and acknowledges results

## WhatsApp Adapter Integration

- Adapter runtime lives in `wxbot/whatsapp-bookkeeping/src/`
- Main orchestration in `wxbot/whatsapp-bookkeeping/src/index.ts`
- Core API transport in `wxbot/whatsapp-bookkeeping/src/core-api.ts`
- WhatsApp socket wrapper in `wxbot/whatsapp-bookkeeping/src/whatsapp.ts`

External library boundary:

- `@whiskeysockets/baileys` provides WhatsApp Web socket access
- `fetchLatestBaileysVersion()` is called during startup in `wxbot/whatsapp-bookkeeping/src/whatsapp.ts`
- `qrcode-terminal` renders terminal QR codes for login

## Browser / Frontend Integration

The Python web layer serves HTML pages and JSON APIs from the same WSGI app.

- Pages are rendered from:
  - `render_dashboard_page()`
  - `render_workbench_page()`
  - `render_quotes_page()`
  - `render_quote_dictionary_page()`
  - `render_history_page()`
  - `render_reconciliation_page()`
- Inline frontend JS performs `fetch(...)` calls to JSON APIs declared in `wxbot/bookkeeping-platform/bookkeeping_web/pages.py`

## File / Export Integration

- Runtime export directory is derived inside `wxbot/bookkeeping-platform/bookkeeping_web/app.py`
- File send actions are supported end-to-end by both adapters:
  - Python side recognizes `send_file`
  - Node side uses WhatsApp document sending in `wxbot/whatsapp-bookkeeping/src/whatsapp.ts`
  - WeChat side also routes `send_file` in `wxbot/bookkeeping-platform/wechat_adapter/main.py`

## Operational Docs

Useful runbooks and deployment-facing docs:

- `wxbot/bookkeeping-platform/README.md`
- `wxbot/bookkeeping-platform/README-启动顺序.md`
- `wxbot/bookkeeping-platform/docs/最新启动手册-总账-WeChat-WhatsApp.md`
- `wxbot/whatsapp-bookkeeping/README.md`
- `wxbot/whatsapp-bookkeeping/SSH_SCP_MAC_TO_WINDOWS_README.md`
