# Bookkeeping Platform

统一记账核心，多个聊天入口共用同一套业务逻辑。

当前已落地：

- `bookkeeping_core`
- `wechat_adapter`
- `POST /api/sync/events` 总库接收接口

后续可继续接：

- `whatsapp_adapter`
- `telegram_adapter`
- 后台 API / 管理系统

## 启动总账中心

当前 `reporting_server.py` 已支持：

- SQLite 文件路径
- PostgreSQL DSN
- 实时同步接收 Token

### SQLite 方式

```bash
BOOKKEEPING_SYNC_TOKEN="replace-with-sync-token" \
python3 "/Users/lcc/SeeSee/wxbot/bookkeeping-platform/reporting_server.py" \
  --db "/Users/lcc/SeeSee/wxbot/bookkeeping-platform/data/bookkeeping.db"
```

### PostgreSQL 方式

```bash
BOOKKEEPING_SYNC_TOKEN="replace-with-sync-token" \
PYTHONPATH="/Users/lcc/SeeSee/wxbot/bookkeeping-platform" \
python3 "/Users/lcc/SeeSee/wxbot/bookkeeping-platform/reporting_server.py" \
  --db "postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping"
```

说明：

- `--db` 传 PostgreSQL DSN 时，会自动切到 PostgreSQL 后端
- `/api/sync/events` 需要 `Authorization: Bearer <TOKEN>`
- 当前接收端支持幂等事件入库，重复推送不会重复记账

### 手工验证同步接口

```bash
curl -X POST "https://your-domain.com/api/sync/events" \
  -H "Authorization: Bearer replace-with-sync-token" \
  -H "Content-Type: application/json" \
  -d '{
    "events": [
      {
        "event_id": "manual-check-1",
        "event_type": "group.set",
        "schema_version": 1,
        "platform": "whatsapp",
        "source_machine": "wa-node-01",
        "occurred_at": "2026-03-20T10:15:30Z",
        "payload": {
          "group_id": "12036340001@g.us",
          "group_num": 7,
          "chat_name": "测试群"
        }
      }
    ]
  }'
```

## 启动 WeChat

先编辑 `C:\wxbot\bookkeeping-platform\config.wechat.json`：

- `listen_chats`: 需要监听的微信群名称
- `master_users`: 管理员微信显示名或备注名

启动：

```powershell
C:\Users\lccst\AppData\Local\Programs\Python\Python311\python.exe -m wechat_adapter.main
```
