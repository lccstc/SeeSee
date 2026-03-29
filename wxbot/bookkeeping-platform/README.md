# Bookkeeping Platform

统一记账核心，多个聊天入口共用同一套业务逻辑。

WhatsApp 本地记账 bot 已降级为薄适配层；正式 runtime 走 `POST /api/core/messages`。

当前已落地：

- `bookkeeping_core`
- `wechat_adapter`
- `POST /api/core/messages` 正式 runtime 入口
- `GET /api/accounting-periods` 和 `POST /api/accounting-periods/close` 账期接口
- 首页驾驶舱、账期工作台、跑账历史页

后续可继续接：

- `whatsapp_adapter`
- `telegram_adapter`
- 后台 API / 管理系统

## 启动总账中心

当前正式 runtime 只接受 PostgreSQL DSN。

### PostgreSQL 方式

```bash
BOOKKEEPING_CORE_TOKEN="replace-with-core-token" \
BOOKKEEPING_DB_DSN="postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping" \
PYTHONPATH="/Users/lcc/SeeSee/wxbot/bookkeeping-platform" \
python3 "/Users/lcc/SeeSee/wxbot/bookkeeping-platform/reporting_server.py" \
  --db "postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping"
```

说明：

- `--db` 必须传 PostgreSQL DSN；不再支持运行时回落到 SQLite
- `BOOKKEEPING_DB_DSN` 可作为默认值，避免每次重复输入
- `BOOKKEEPING_CORE_TOKEN` / `--core-token` 是适配器调用 `POST /api/core/messages` 时使用的 Bearer Token
- `POST /api/core/messages` 是正式 runtime 入口，负责在线消息处理与动作返回
- 启动前必须先把当前版本的 `sql/postgres_schema.sql` 应用到目标数据库；运行时不再自动补列、补账或升级旧 schema

## 账期接口

- `GET /api/accounting-periods`：查看最近账期列表
- `POST /api/accounting-periods/close`：按 `start_at < created_at <= end_at` 关闭一个全局账期，提交 `start_at`、`end_at`、`closed_by`，可选 `note`

## 页面与分析接口

页面入口：

- `GET /`：首页驾驶舱，只展示当前总余额、当日已实现利润、当日美元面额、未归属/待处理群数，以及最近识别的结构化交易流
- `GET /workbench`：账期工作台，按 `period_id` 查看指定账期摘要、当前未扎账窗口、群快照、卡种统计，并承接关账/修正/组合治理
- `GET /reconciliation`：对账中心，给财务按组合/组号查账、筛异常、录财务加账、导出逐笔明细或汇总 CSV；简明说明见 `docs/对账中心简明使用说明.md`
- `GET /history`：跑账历史页，按日期区间查看账期列表与卡种排行

分析接口：

- `GET /api/dashboard`：返回首页驾驶舱数据，兼容原有 `current_groups`、`combinations`、`recent_periods`，并新增 `summary`、`latest_transactions`
- `GET /api/workbench?period_id=<账期ID>`：返回账期工作台数据，包含 `periods`、`selected_period`、`live_window`、`summary`、`transactions`、`group_rows`、`card_stats`
- `GET /api/history?start_date=2026-03-01&end_date=2026-03-31&card_keyword=steam&sort_by=usd_amount`：返回区间账期列表、区间汇总与卡种排行

参数说明：

- `period_id`：可选，未传时默认选最近关闭账期
- `start_date` / `end_date`：按账期 `closed_at` 的日期部分做闭区间过滤
- `card_keyword`：可选，按卡种名称模糊过滤排行
- `sort_by`：支持 `usd_amount`、`rmb_amount`、`unit_count`、`period_count`

### 人工验证页面

1. 启动 `reporting_server.py`
2. 打开 `/`，确认首页只保留 4 张信号卡、最近识别交易流和跳转入口，不再出现组合管理与人工修正表单
3. 关闭一个账期后打开 `/workbench?period_id=<新账期ID>`，确认账期摘要、当前未扎账窗口、群快照、卡种统计都能加载
4. 在 `/workbench` 上确认关账表单、人工修正区、组合管理区都可见，并且组合列表可以刷新
5. 打开 `/history?start_date=2026-03-01&end_date=2026-03-31`，确认区间账期列表与卡种排行正常加载
6. 使用 `card_keyword` 和 `sort_by` 反复切换，确认排行刷新且时间范围不变

### 回归验证

```bash
export BOOKKEEPING_TEST_DSN="postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test"
python3 -m unittest tests.test_analytics -v
python3 -m unittest tests.test_webapp -v
python3 -m unittest -v tests.test_periods tests.test_reporting tests.test_analytics tests.test_webapp tests.test_postgres_backend
```

建议按下面顺序验证：

```bash
export BOOKKEEPING_TEST_DSN="postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test"
python3 -m unittest tests.test_postgres_backend -v
python3 -m unittest tests.test_ingestion_alignment tests.test_periods tests.test_reporting tests.test_analytics tests.test_webapp tests.test_postgres_backend -v
```

## 启动 WeChat

先编辑 `C:\wxbot\bookkeeping-platform\config.wechat.json`：

- `listen_chats`: 需要监听的微信群名称
- `master_users`: 管理员微信显示名或备注名
- `core_api.endpoint`: 远端总账中心地址，填写主机根地址，例如 `https://your-ngrok-host.ngrok-free.dev`
- `core_api.token`: 远端总账中心 Bearer Token
- `core_api.request_timeout_seconds`: 远端请求超时秒数

说明：

- WeChat 适配器现在只支持 remote core mode
- 不再需要 `db_path`
- 正式事实源只有远端总账 PostgreSQL

启动：

```powershell
C:\Users\lccst\AppData\Local\Programs\Python\Python311\python.exe -m wechat_adapter.main
```
