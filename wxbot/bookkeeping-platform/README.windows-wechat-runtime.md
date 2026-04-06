# Windows WeChat Runtime Notes

This machine is responsible for the WeChat adapter entry.

## Runtime owner
- Host: Windows machine
- Runtime project path: `C:\\SeeSee\\wxbot\\bookkeeping-platform`
- Repo sync path: `wxbot/bookkeeping-platform`

## Start command
- PowerShell: `powershell -ExecutionPolicy Bypass -File .\\start-wechat-adapter.ps1`
- Direct Python: `python -m wechat_adapter.main`

## Core dependency
- Depends on `core_api.endpoint` from `config.wechat.json`
- Current runtime points to LAN core service (set on this machine)

## Required config keys
- `listen_chats`
- `master_users`
- `poll_interval_seconds`
- `log_level`
- `language`
- `export_dir`
- `runtime_dir`
- `core_api.endpoint`
- `core_api.token`
- `core_api.request_timeout_seconds`

## Communication with bookkeeping core
- WeChat adapter pushes inbound envelopes to core API
- Core API returns outbound actions (`send_text`, `send_file`)
- Adapter sends action results back through acknowledge API

## Security
- Do not commit real `config.wechat.json`
- Use `config.wechat.example.json` as template
- Keep runtime/cache/log directories local only
