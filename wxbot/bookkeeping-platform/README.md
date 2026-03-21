# Bookkeeping Platform

统一记账核心，多个聊天入口共用同一套业务逻辑。

WhatsApp 本地记账 bot 已降级为薄适配层；正式 runtime 走 `POST /api/core/messages`，`/api/sync/events` 仅用于历史兼容导入，不承诺 live reply。

当前已落地：

- `bookkeeping_core`
- `wechat_adapter`
- `POST /api/core/messages` 正式 runtime 入口
- `POST /api/sync/events` 历史兼容导入入口
- `GET /api/accounting-periods` 和 `POST /api/accounting-periods/close` 账期接口
- 首页驾驶舱、账期工作台、跑账历史页

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
- `POST /api/core/messages` 是正式 runtime 入口，负责在线消息处理与动作返回
- `/api/sync/events` 需要 `Authorization: Bearer <TOKEN>`，仅用于历史兼容导入，不承诺 live reply
- 当前接收端按单个事件做原子提交；同一事件重复推送不会重复记账

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

## 账期接口

- `GET /api/accounting-periods`：查看最近账期列表
- `POST /api/accounting-periods/close`：按 `start_at < created_at <= end_at` 关闭一个全局账期，提交 `start_at`、`end_at`、`closed_by`，可选 `note`

## 页面与分析接口

页面入口：

- `GET /`：首页驾驶舱，展示当前总余额、当日已实现利润、当日美元面额、未分配群数
- `GET /workbench`：账期工作台，按 `period_id` 查看指定账期快照与卡种统计
- `GET /history`：跑账历史页，按日期区间查看账期列表与卡种排行

分析接口：

- `GET /api/dashboard`：返回首页驾驶舱数据，兼容原有 `current_groups`、`combinations`、`recent_periods`，并新增 `summary`
- `GET /api/workbench?period_id=<账期ID>`：返回账期工作台数据，包含 `periods`、`selected_period`、`summary`、`group_rows`、`card_stats`
- `GET /api/history?start_date=2026-03-01&end_date=2026-03-31&card_keyword=steam&sort_by=usd_amount`：返回区间账期列表、区间汇总与卡种排行

参数说明：

- `period_id`：可选，未传时默认选最近关闭账期
- `start_date` / `end_date`：按账期 `closed_at` 的日期部分做闭区间过滤
- `card_keyword`：可选，按卡种名称模糊过滤排行
- `sort_by`：支持 `usd_amount`、`rmb_amount`、`unit_count`、`period_count`

### 人工验证页面

1. 启动 `reporting_server.py`
2. 打开 `/`，确认首页卡片、当前群余额、最近账期、组合汇总可加载
3. 关闭一个账期后打开 `/workbench?period_id=<新账期ID>`，确认时间范围、群快照、卡种统计一致
4. 打开 `/history?start_date=2026-03-01&end_date=2026-03-31`，确认区间账期列表与卡种排行正常加载
5. 使用 `card_keyword` 和 `sort_by` 反复切换，确认排行刷新且时间范围不变

### 回归验证

```bash
python3 -m unittest tests.test_analytics -v
python3 -m unittest tests.test_webapp -v
python3 -m unittest -v tests.test_periods tests.test_reporting tests.test_analytics tests.test_webapp tests.test_postgres_backend
```

## 启动 WeChat

先编辑 `C:\wxbot\bookkeeping-platform\config.wechat.json`：

- `listen_chats`: 需要监听的微信群名称
- `master_users`: 管理员微信显示名或备注名
- `core_api.endpoint`: 远端总账中心地址，填写主机根地址，例如 `https://your-ngrok-host.ngrok-free.dev`
- `core_api.token`: 远端总账中心 Bearer Token
- `core_api.request_timeout_seconds`: 远端请求超时秒数
- `db_path`: 仅保留给 WeChat 本地适配器控制面使用，不再作为正式统一账本事实源

启动：

```powershell
C:\Users\lccst\AppData\Local\Programs\Python\Python311\python.exe -m wechat_adapter.main
```
