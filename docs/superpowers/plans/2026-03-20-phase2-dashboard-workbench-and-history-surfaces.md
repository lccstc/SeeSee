# Phase 2 Dashboard, Workbench, and History Surfaces Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the phase-one accounting-period foundation into usable read surfaces: a signal-first dashboard, a period-detail workbench, and a history-analysis page that finance can operate without reading raw tables.

**Architecture:** Keep `transactions`, `accounting_periods`, `period_group_snapshots`, and `period_card_stats` as the only data sources, and add a thin `analytics.py` layer that aggregates dashboard cards, workbench tables, and history rankings for the web layer. Split page shell rendering into `bookkeeping_web/pages.py` so `app.py` stays focused on routing, payload validation, and JSON serialization instead of growing into one giant inline HTML blob.

**Tech Stack:** Python 3, sqlite3, optional PostgreSQL via `psycopg` compatibility layer, `unittest`, WSGI app, vanilla HTML/CSS/JS.

---

## Scope Boundary

这份计划只覆盖“一期里把数据读出来给人看”的页面与 API：

- 首页驾驶舱
- 跑账详情工作台
- 跑账历史页
- 页面内搜索与排序

这份计划**不**覆盖：

- 客户 / 供应商主体归并
- 主体总表
- 自动角色映射
- 当前未跑账工作区的异常匹配与排错工作流
- 依赖主体归并才能严格成立的首页风险卡片

依赖假设：

- `groups.business_role` 先沿用人工维护结果
- 主体级聚合与归并延后到下一份计划
- 可疑记录与异常预警延后到第四份计划
- `高风险负余额金额` 这类严格依赖主体口径的首页卡片延后到第三份计划

## Execution Notes

- 执行工作目录：`/Users/lcc/SeeSee/wxbot/bookkeeping-platform`
- 执行时遵循 `@test-driven-development` 与 `@verification-before-completion`
- 按仓库规则，本计划**不包含** `git commit`、分支或合并步骤
- 所有新增查询都必须同时兼容 SQLite 与 PostgreSQL 假连接测试
- 每个页面都必须显式展示时间范围，避免把“当前余额”和“账期快照”混成一个口径

## File Structure

- Create: `wxbot/bookkeeping-platform/bookkeeping_core/analytics.py`
  责任：聚合首页卡片、账期工作台摘要、历史页区间分析与卡种排行
- Create: `wxbot/bookkeeping-platform/bookkeeping_web/pages.py`
  责任：提供首页、工作台、历史页的 HTML shell 和共享导航，不再把全部页面模板堆进 `app.py`
- Create: `wxbot/bookkeeping-platform/tests/test_analytics.py`
  责任：覆盖 dashboard / workbench / history 聚合口径
- Modify: `wxbot/bookkeeping-platform/bookkeeping_core/reporting.py`
  责任：保留现有兼容接口，同时把更复杂的读模型委托给 `analytics.py`
- Modify: `wxbot/bookkeeping-platform/bookkeeping_web/app.py`
  责任：新增页面路由和 JSON 端点，并保持现有 `/api/dashboard` 不回归
- Modify: `wxbot/bookkeeping-platform/tests/test_webapp.py`
  责任：覆盖新页面路由、工作台接口、历史分析接口
- Modify: `wxbot/bookkeeping-platform/tests/test_postgres_backend.py`
  责任：验证新聚合查询在 PostgreSQL 假连接下仍能返回可序列化结果
- Modify: `wxbot/bookkeeping-platform/README.md`
  责任：记录新页面地址、接口参数和人工验证步骤

### Task 1: Add Dashboard Signal Aggregation

**Files:**
- Create: `wxbot/bookkeeping-platform/bookkeeping_core/analytics.py`
- Create: `wxbot/bookkeeping-platform/tests/test_analytics.py`
- Modify: `wxbot/bookkeeping-platform/bookkeeping_core/reporting.py`
- Test: `wxbot/bookkeeping-platform/tests/test_analytics.py`

- [ ] **Step 1: Write the failing dashboard-summary test**

```python
class DashboardAnalyticsTests(unittest.TestCase):
    def test_dashboard_cards_report_total_balance_today_profit_and_total_usd(self) -> None:
        service = AnalyticsService(self.db)

        payload = service.build_dashboard_summary(today="2026-03-20")

        self.assertEqual(round(payload["current_total_balance"], 2), 860.00)
        self.assertEqual(round(payload["today_realized_profit"], 2), 55.00)
        self.assertEqual(round(payload["today_total_usd_amount"], 2), 1250.00)
        self.assertEqual(payload["unassigned_group_count"], 1)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_analytics.DashboardAnalyticsTests.test_dashboard_cards_report_total_balance_today_profit_and_total_usd -v`
Expected: FAIL with `ImportError` for missing `AnalyticsService` or missing dashboard summary keys

- [ ] **Step 3: Write the minimal dashboard aggregation**

```python
class AnalyticsService:
    def __init__(self, db: BookkeepingDB) -> None:
        self.db = db

    def build_dashboard_summary(self, *, today: str) -> dict:
        current_rows = ReportingService(self.db).get_current_group_rows()
        today_periods = [
            row for row in self.db.list_accounting_periods()
            if str(row["closed_at"]).startswith(today)
        ]
        return {
            "current_total_balance": self._sum_formal_balances(current_rows),
            "today_realized_profit": self._sum_period_profit(today_periods),
            "today_total_usd_amount": self._sum_period_usd_amount(today_periods),
            "unassigned_group_count": self._count_unassigned_groups(),
        }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_analytics.DashboardAnalyticsTests.test_dashboard_cards_report_total_balance_today_profit_and_total_usd -v`
Expected: PASS

### Task 2: Add Period Workbench Read Model

**Files:**
- Create: `wxbot/bookkeeping-platform/bookkeeping_core/analytics.py`
- Modify: `wxbot/bookkeeping-platform/bookkeeping_core/reporting.py`
- Modify: `wxbot/bookkeeping-platform/tests/test_analytics.py`
- Test: `wxbot/bookkeeping-platform/tests/test_analytics.py`

- [ ] **Step 1: Write the failing workbench test**

```python
def test_period_workbench_returns_selected_period_summary_and_card_stats(self) -> None:
    period_id = AccountingPeriodService(self.db).close_period(
        start_at="2026-03-20 08:00:00",
        end_at="2026-03-20 10:00:00",
        closed_by="finance-a",
    )

    payload = AnalyticsService(self.db).build_period_workbench(period_id=period_id)

    self.assertEqual(payload["selected_period"]["id"], period_id)
    self.assertEqual(round(payload["summary"]["profit"], 2), 35.00)
    self.assertEqual(payload["card_stats"][0]["card_type"], "steam")
    self.assertGreaterEqual(len(payload["periods"]), 1)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_analytics.WorkbenchAnalyticsTests.test_period_workbench_returns_selected_period_summary_and_card_stats -v`
Expected: FAIL with missing `build_period_workbench` or missing `card_stats`

- [ ] **Step 3: Implement the workbench aggregation**

```python
def build_period_workbench(self, *, period_id: int | None) -> dict:
    periods = self._list_recent_periods()
    selected = self._pick_selected_period(periods, period_id)
    rows = self.db.list_period_group_snapshots(int(selected["id"])) if selected else []
    card_stats = self.db.list_period_card_stats(int(selected["id"])) if selected else []
    return {
        "periods": periods,
        "selected_period": selected,
        "summary": self._summarize_period(rows, card_stats),
        "group_rows": [self._serialize_snapshot(row) for row in rows],
        "card_stats": [self._serialize_card_stat(row) for row in card_stats],
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_analytics.WorkbenchAnalyticsTests.test_period_workbench_returns_selected_period_summary_and_card_stats -v`
Expected: PASS

### Task 3: Add History Range Analysis and Card Ranking

**Files:**
- Create: `wxbot/bookkeeping-platform/bookkeeping_core/analytics.py`
- Modify: `wxbot/bookkeeping-platform/tests/test_analytics.py`
- Modify: `wxbot/bookkeeping-platform/tests/test_postgres_backend.py`
- Test: `wxbot/bookkeeping-platform/tests/test_analytics.py`

- [ ] **Step 1: Write the failing history-analysis test**

```python
def test_history_analysis_filters_periods_by_date_range_and_sorts_card_totals(self) -> None:
    payload = AnalyticsService(self.db).build_history_analysis(
        start_date="2026-03-01",
        end_date="2026-03-31",
        card_keyword="steam",
        sort_by="usd_amount",
    )

    self.assertEqual(len(payload["period_rows"]), 2)
    self.assertEqual(payload["card_rankings"][0]["card_type"], "steam")
    self.assertEqual(payload["range"]["start_date"], "2026-03-01")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_analytics.HistoryAnalyticsTests.test_history_analysis_filters_periods_by_date_range_and_sorts_card_totals -v`
Expected: FAIL with missing `build_history_analysis` or incorrect ordering

- [ ] **Step 3: Implement range analysis and ranking**

```python
def build_history_analysis(
    self,
    *,
    start_date: str,
    end_date: str,
    card_keyword: str = "",
    sort_by: str = "profit",
) -> dict:
    periods = self._select_periods_in_range(start_date, end_date)
    card_rows = self._collect_card_stats(periods, card_keyword=card_keyword)
    return {
        "range": {"start_date": start_date, "end_date": end_date},
        "period_rows": [self._serialize_period_row(row) for row in periods],
        "summary": self._summarize_history_periods(periods),
        "card_rankings": self._sort_card_rankings(card_rows, sort_by=sort_by),
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_analytics.HistoryAnalyticsTests.test_history_analysis_filters_periods_by_date_range_and_sorts_card_totals -v`
Expected: PASS

### Task 4: Add Page Shells and Web Routes

**Files:**
- Create: `wxbot/bookkeeping-platform/bookkeeping_web/pages.py`
- Modify: `wxbot/bookkeeping-platform/bookkeeping_web/app.py`
- Modify: `wxbot/bookkeeping-platform/tests/test_webapp.py`
- Modify: `wxbot/bookkeeping-platform/README.md`
- Test: `wxbot/bookkeeping-platform/tests/test_webapp.py`

- [ ] **Step 1: Write the failing webapp test**

```python
def test_dashboard_workbench_and_history_pages_render_and_fetch_json(self) -> None:
    for path in ("/", "/workbench", "/history"):
        status, html = self._request_text("GET", path)
        self.assertEqual(status, 200)
        self.assertIn("<main", html)

    status, workbench = self._request("GET", "/api/workbench", query_string="period_id=1")
    self.assertEqual(status, 200)
    self.assertIn("summary", workbench)

    status, history = self._request(
        "GET",
        "/api/history",
        query_string="start_date=2026-03-01&end_date=2026-03-31",
    )
    self.assertEqual(status, 200)
    self.assertIn("card_rankings", history)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_webapp.WebAppTests.test_dashboard_workbench_and_history_pages_render_and_fetch_json -v`
Expected: FAIL with `404` for `/workbench`, `/history`, `/api/workbench`, or `/api/history`

- [ ] **Step 3: Implement page rendering and endpoints**

```python
if path == "/":
    return _respond_html(start_response, render_dashboard_page())
if path == "/workbench":
    return _respond_html(start_response, render_workbench_page())
if path == "/history":
    return _respond_html(start_response, render_history_page())
if path == "/api/workbench" and method == "GET":
    return _with_db(db_file, start_response, _handle_workbench, environ)
if path == "/api/history" and method == "GET":
    return _with_db(db_file, start_response, _handle_history, environ)
```

- [ ] **Step 4: Run the focused regression suite**

Run: `python3 -m unittest -v tests.test_analytics tests.test_webapp`
Expected: PASS with dashboard, workbench, and history routes covered
