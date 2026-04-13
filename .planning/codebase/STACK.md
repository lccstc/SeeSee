# Stack

## Overview

This repository is a brownfield, multi-runtime system centered on a Python bookkeeping core and two chat adapters.

- Primary backend/runtime: Python 3 with standard-library WSGI entrypoints in `wxbot/bookkeeping-platform/reporting_server.py`
- Primary data store: PostgreSQL only in production/runtime, enforced by `require_postgres_dsn()` in `wxbot/bookkeeping-platform/bookkeeping_core/database.py`
- Web UI: server-rendered HTML strings plus inline JavaScript in `wxbot/bookkeeping-platform/bookkeeping_web/pages.py`
- WeChat adapter: Python thin adapter in `wxbot/bookkeeping-platform/wechat_adapter/`
- WhatsApp adapter: TypeScript/Node thin adapter in `wxbot/whatsapp-bookkeeping/src/`

## Python Runtime

- Dependency management is intentionally minimal. The tracked Python dependency file is `wxbot/bookkeeping-platform/requirements-dev.txt`.
- Current explicit dependency:
  - `psycopg[binary]>=3.3,<4` in `wxbot/bookkeeping-platform/requirements-dev.txt`
- Standard-library modules are used heavily instead of framework dependencies:
  - `argparse`, `wsgiref`, `socketserver`, `json`, `logging`, `threading`, `urllib`
- The app is not using Flask/Django/FastAPI. Routing is manual inside `wxbot/bookkeeping-platform/bookkeeping_web/app.py`.

## Node / TypeScript Runtime

- Package manifest: `wxbot/whatsapp-bookkeeping/package.json`
- TypeScript config: `wxbot/whatsapp-bookkeeping/tsconfig.json`
- Output target:
  - `ES2022`
  - module `ESNext`
  - strict mode enabled
  - compiled output in `dist/`
- Runtime/developer dependencies:
  - `@whiskeysockets/baileys` for WhatsApp connectivity
  - `pino` for logging
  - `qrcode-terminal` for QR login
  - `typescript`, `tsx`, `@types/node`

## Persistence / Schema

- Formal schema lives in `wxbot/bookkeeping-platform/sql/postgres_schema.sql`
- Runtime schema bootstrapping is not automatic; README explicitly says schema must be applied before startup
- Local SQLite artifacts still exist in the tree, for example `wxbot/bookkeeping-platform/bookkeeping.db`, but repo docs and runtime guards treat PostgreSQL as the only supported runtime source of truth

## Build / Run Commands

- Python core startup: `wxbot/bookkeeping-platform/reporting_server.py`
- Python tests: `python -m unittest ...`
- WeChat adapter startup: `python -m wechat_adapter.main`
- WhatsApp build: `npm run build`
- WhatsApp test: `npm test`
- WhatsApp runtime: `npm start` or `node dist/index.js`

## Configuration Surfaces

- Python env vars:
  - `BOOKKEEPING_DB_DSN`
  - `BOOKKEEPING_CORE_TOKEN`
  - `BOOKKEEPING_MASTER_USERS`
  - `BOOKKEEPING_TEST_DSN`
  - `QUOTE_ADMIN_PASSWORD`
- WeChat config file:
  - `wxbot/bookkeeping-platform/config.wechat.json`
- WhatsApp config file:
  - `wxbot/whatsapp-bookkeeping/config.json`

## Practical Reading List

- Core entrypoint: `wxbot/bookkeeping-platform/reporting_server.py`
- Manual router: `wxbot/bookkeeping-platform/bookkeeping_web/app.py`
- Core domain layer: `wxbot/bookkeeping-platform/bookkeeping_core/`
- WeChat thin adapter: `wxbot/bookkeeping-platform/wechat_adapter/main.py`
- WhatsApp thin adapter: `wxbot/whatsapp-bookkeeping/src/index.ts`
