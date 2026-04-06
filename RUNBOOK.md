# SeeSee Mac Runtime Runbook

## Machine Responsibility
- This Mac hosts the runtime for `bookkeeping-core` and `whatsapp-bot`.
- Source runtime paths:
  - `wxbot/bookkeeping-platform`
  - `wxbot/whatsapp-bookkeeping`

## Dependencies
- PostgreSQL 16 on `127.0.0.1:5432`
- Python virtual environment for core service (`.venv`)
- Node.js + npm + PM2 for WhatsApp entry service

## Startup Order
1. Ensure PostgreSQL is running.
2. Start `bookkeeping-core`.
3. Start `whatsapp-bot`.
4. Check service health and logs.

## Start Commands
- Preferred script (both services):
  - `wxbot/scripts/start_services.sh`
- Core only (PM2 ecosystem):
  - `cd wxbot/bookkeeping-platform`
  - `pm2 start ecosystem.config.cjs`
- WhatsApp only:
  - `cd wxbot/whatsapp-bookkeeping`
  - `pm2 start npm --name whatsapp-bot --cwd "$(pwd)" -- start`

## Health Check
- `wxbot/scripts/check_services.sh`
- Manual checks:
  - `pm2 status bookkeeping-core whatsapp-bot`
  - `curl -fsS http://127.0.0.1:8765/`

## Config Files (No Secrets In Git)
- `wxbot/bookkeeping-platform/ecosystem.config.cjs`: PM2 + runtime env for core (local only, ignored).
- `wxbot/bookkeeping-platform/config.wechat.json`: WeChat adapter local runtime config (local only, ignored).
- `wxbot/whatsapp-bookkeeping/config.json`: WhatsApp bridge runtime config (local only, ignored).
- Examples:
  - `wxbot/bookkeeping-platform/ecosystem.config.example.cjs`
  - `wxbot/bookkeeping-platform/config.wechat.example.json`
  - `wxbot/whatsapp-bookkeeping/config.example.json`
