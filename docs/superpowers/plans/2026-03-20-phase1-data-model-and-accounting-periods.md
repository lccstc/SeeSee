# Phase 1 Data Model and Accounting Periods Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade `bookkeeping-platform` from a per-group bookkeeping runtime into a phase-one finance foundation with explicit global accounting periods, persisted period snapshots, and minimal period query APIs that later dashboard/workbench plans can build on.

**Architecture:** Keep `wechat_adapter` and sync ingestion stable, and add a thin domain layer dedicated to accounting periods instead of mixing more lifecycle logic into the already large `database.py`. Persist explicit `accounting_periods`, `period_group_snapshots`, and `period_card_stats` records; reuse existing `transactions` as the source of truth during migration and backfill historical `settlements` into the new period model so old data stays queryable.

**Tech Stack:** Python 3, sqlite3, optional PostgreSQL via `psycopg` compatibility layer, `unittest`, WSGI app, existing `bookkeeping_core` service boundaries.

---

## Scope Boundary

这份第一计划只覆盖一期里的“数据模型 + 跑账区间”基础层，不覆盖以下内容：

- 首页驾驶舱视觉改版
- 首页异常工作流和老板摘要指标
- 客户 / 供应商主体归并
- 历史页、总表页的完整交互

建议把后续工作拆成另外三份计划：

1. `2026-03-20-phase2-dashboard-workbench-and-history-surfaces.md`
2. `2026-03-20-phase3-subject-directory-and-manual-merge.md`
3. `2026-03-20-phase4-role-mapping-and-anomaly-workflow.md`

## Execution Notes

- 执行工作目录：`/Users/lcc/SeeSee/wxbot/bookkeeping-platform`
- 执行时遵循 `@test-driven-development` 与 `@verification-before-completion`
- 按仓库规则，本计划**不包含** `git commit`、分支或合并步骤
- 所有新增 schema 必须同时覆盖 SQLite 和 PostgreSQL

## File Structure

- Create: `wxbot/bookkeeping-platform/bookkeeping_core/periods.py`
  责任：封装全局跑账区间生命周期、快照构建、历史回填，不把更多流程塞进 `database.py`
- Modify: `wxbot/bookkeeping-platform/bookkeeping_core/database.py:31-174`
  责任：补齐一期基础 schema、迁移和回填入口
- Modify: `wxbot/bookkeeping-platform/bookkeeping_core/database.py:334-389`
  责任：保留旧 `settle_transactions()` 行为，同时为 period service 提供显式 period 查询 / 持久化接口
- Modify: `wxbot/bookkeeping-platform/bookkeeping_core/database.py:552-649`
  责任：让人工修正、组合分组和新 period 模型能一起工作
- Modify: `wxbot/bookkeeping-platform/bookkeeping_core/database.py:672-713`
  责任：把已有 `settlements` 数据回填到新 period 模型
- Modify: `wxbot/bookkeeping-platform/bookkeeping_core/database.py:802-979`
  责任：保持 PostgreSQL 兼容实现与 SQLite 行为一致
- Modify: `wxbot/bookkeeping-platform/sql/postgres_schema.sql:1-137`
  责任：声明 PostgreSQL 下的新表和索引
- Modify: `wxbot/bookkeeping-platform/bookkeeping_core/reporting.py:12-124`
  责任：从显式 period snapshot 读取账期结果，而不是临时重算
- Modify: `wxbot/bookkeeping-platform/bookkeeping_web/app.py:199-260`
  责任：暴露 period 列表 / 详情 / 关闭账期接口，并让 dashboard 读取最新 period 数据
- Modify: `wxbot/bookkeeping-platform/README.md`
  责任：记录新的 period API、迁移约束和手工验证步骤
- Create: `wxbot/bookkeeping-platform/tests/test_periods.py`
  责任：覆盖 schema、回填、半开区间和 period snapshot 落库行为
- Modify: `wxbot/bookkeeping-platform/tests/test_reporting.py:68-230`
  责任：把账期断言从“按 settlement 临时推导”切到“按显式 accounting period 读取”
- Modify: `wxbot/bookkeeping-platform/tests/test_webapp.py:82-211`
  责任：新增 API 级别回归，保证 dashboard 与新 period 接口兼容
- Modify: `wxbot/bookkeeping-platform/tests/test_postgres_backend.py:67-109`
  责任：保证 PostgreSQL 假连接也能初始化新 schema 并写入 / 读取新 period 数据

### Task 1: Add Phase-One Schema Primitives

**Files:**
- Create: `wxbot/bookkeeping-platform/tests/test_periods.py`
- Modify: `wxbot/bookkeeping-platform/bookkeeping_core/database.py:31-174`
- Modify: `wxbot/bookkeeping-platform/sql/postgres_schema.sql:1-137`
- Test: `wxbot/bookkeeping-platform/tests/test_periods.py`

- [ ] **Step 1: Write the failing schema test**

```python
class PeriodSchemaTests(unittest.TestCase):
    def test_bootstraps_phase1_tables_and_columns(self) -> None:
        db = BookkeepingDB(self.db_path)
        tables = {
            row["name"]
            for row in db.conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        self.assertIn("accounting_periods", tables)
        self.assertIn("period_group_snapshots", tables)
        self.assertIn("period_card_stats", tables)

        group_columns = {
            row["name"] for row in db.conn.execute("PRAGMA table_info(groups)").fetchall()
        }
        self.assertTrue(
            {"business_role", "role_source", "capture_enabled", "status"}.issubset(group_columns)
        )

        tx_columns = {
            row["name"] for row in db.conn.execute("PRAGMA table_info(transactions)").fetchall()
        }
        self.assertTrue(
            {"usd_amount", "unit_face_value", "unit_count", "parse_version"}.issubset(tx_columns)
        )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_periods.PeriodSchemaTests.test_bootstraps_phase1_tables_and_columns -v`
Expected: FAIL with missing table / missing column assertions for `accounting_periods`, `period_group_snapshots`, `period_card_stats`

- [ ] **Step 3: Write the minimal schema and migration code**

```python
self.conn.executescript(
    """
    CREATE TABLE IF NOT EXISTS accounting_periods (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      start_at TEXT NOT NULL,
      end_at TEXT NOT NULL,
      closed_at TEXT NOT NULL,
      closed_by TEXT NOT NULL,
      note TEXT,
      has_adjustment INTEGER NOT NULL DEFAULT 0,
      snapshot_version INTEGER NOT NULL DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS period_group_snapshots (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      period_id INTEGER NOT NULL,
      group_key TEXT NOT NULL,
      platform TEXT NOT NULL,
      chat_name TEXT NOT NULL,
      group_num INTEGER,
      business_role TEXT,
      opening_balance REAL NOT NULL,
      income REAL NOT NULL,
      expense REAL NOT NULL,
      closing_balance REAL NOT NULL,
      transaction_count INTEGER NOT NULL DEFAULT 0,
      anomaly_flags_json TEXT NOT NULL DEFAULT '[]',
      UNIQUE(period_id, group_key)
    );

    CREATE TABLE IF NOT EXISTS period_card_stats (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      period_id INTEGER NOT NULL,
      group_key TEXT NOT NULL,
      business_role TEXT,
      card_type TEXT NOT NULL,
      usd_amount REAL NOT NULL,
      rate REAL,
      rmb_amount REAL NOT NULL,
      unit_face_value REAL,
      unit_count REAL,
      sample_raw TEXT
    );
    """
)
self._ensure_column("groups", "business_role", "business_role TEXT")
self._ensure_column("groups", "role_source", "role_source TEXT")
self._ensure_column("groups", "capture_enabled", "capture_enabled INTEGER NOT NULL DEFAULT 1")
self._ensure_column("groups", "status", "status TEXT NOT NULL DEFAULT 'active'")
self._ensure_column("transactions", "usd_amount", "usd_amount REAL")
self._ensure_column("transactions", "unit_face_value", "unit_face_value REAL")
self._ensure_column("transactions", "unit_count", "unit_count REAL")
self._ensure_column("transactions", "parse_version", "parse_version TEXT")
self.conn.execute("UPDATE transactions SET usd_amount = amount WHERE usd_amount IS NULL")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_periods.PeriodSchemaTests.test_bootstraps_phase1_tables_and_columns -v`
Expected: PASS

### Task 2: Backfill Historical Settlements Into Accounting Periods

**Files:**
- Create: `wxbot/bookkeeping-platform/bookkeeping_core/periods.py`
- Modify: `wxbot/bookkeeping-platform/bookkeeping_core/database.py:672-713`
- Modify: `wxbot/bookkeeping-platform/tests/test_periods.py`
- Test: `wxbot/bookkeeping-platform/tests/test_periods.py`

- [ ] **Step 1: Write the failing backfill test**

```python
def test_existing_settlements_are_backfilled_into_accounting_periods(self) -> None:
    group_key = "wechat:g-legacy"
    self.db.set_group(
        platform="wechat",
        group_key=group_key,
        chat_id="g-legacy",
        chat_name="历史客户群",
        group_num=5,
    )
    tx_id = self.db.add_transaction(
        platform="wechat",
        group_key=group_key,
        group_num=5,
        chat_id="g-legacy",
        chat_name="历史客户群",
        sender_id="u-1",
        sender_name="Alice",
        message_id="msg-legacy-1",
        input_sign=1,
        amount=300,
        category="rmb",
        rate=None,
        rmb_value=300,
        raw="rmb+300",
        created_at="2026-03-19 09:00:00",
    )
    self.db.conn.execute(
        "UPDATE transactions SET settled = 1, settlement_id = 12, settled_at = ? WHERE id = ?",
        ("2026-03-19 10:00:00", tx_id),
    )
    self.db.conn.execute(
        """
        INSERT INTO settlements (id, platform, group_key, settle_date, total_rmb, detail, settled_at, settled_by)
        VALUES (12, 'wechat', ?, '2026-03-19 10:00:00', 300, 'RMB: 1 txs +300.00', '2026-03-19 10:00:00', 'finance-a')
        """,
        (group_key,),
    )
    self.db.conn.commit()

    AccountingPeriodService(self.db).backfill_legacy_periods()

    periods = self.db.list_accounting_periods(limit=10)
    self.assertEqual(len(periods), 1)
    rows = self.db.list_period_group_snapshots(int(periods[0]["id"]))
    self.assertEqual(len(rows), 1)
    self.assertEqual(round(float(rows[0]["closing_balance"]), 2), 300.00)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_periods.PeriodBackfillTests.test_existing_settlements_are_backfilled_into_accounting_periods -v`
Expected: FAIL with `AttributeError` for missing `AccountingPeriodService` or missing `list_accounting_periods`

- [ ] **Step 3: Implement legacy backfill and repository methods**

```python
class AccountingPeriodService:
    def __init__(self, db: BookkeepingDB) -> None:
        self.db = db

    def backfill_legacy_periods(self) -> None:
        period_rows = self.db.conn.execute(
            """
            SELECT DISTINCT settled_at
            FROM settlements
            ORDER BY settled_at ASC
            """
        ).fetchall()
        previous_cutoff = "0001-01-01 00:00:00"
        for item in period_rows:
            settled_at = str(item["settled_at"])
            owner = self.db.conn.execute(
                """
                SELECT settled_by
                FROM settlements
                WHERE settled_at = ?
                ORDER BY id ASC
                LIMIT 1
                """,
                (settled_at,),
            ).fetchone()
            period_id = self.db.insert_accounting_period(
                start_at=previous_cutoff,
                end_at=settled_at,
                closed_at=settled_at,
                closed_by=str(owner["settled_by"]) if owner is not None else "legacy-backfill",
                note="legacy settlement backfill",
            )
            groups = self.db.conn.execute(
                "SELECT DISTINCT group_key FROM settlements WHERE settled_at = ? ORDER BY group_key",
                (settled_at,),
            ).fetchall()
            for group in groups:
                self._persist_group_snapshot(period_id, str(group["group_key"]), previous_cutoff, settled_at)
            previous_cutoff = settled_at
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_periods.PeriodBackfillTests.test_existing_settlements_are_backfilled_into_accounting_periods -v`
Expected: PASS

### Task 3: Close Global Accounting Periods Using Half-Open Windows

**Files:**
- Create: `wxbot/bookkeeping-platform/bookkeeping_core/periods.py`
- Modify: `wxbot/bookkeeping-platform/bookkeeping_core/database.py:334-389`
- Modify: `wxbot/bookkeeping-platform/bookkeeping_core/database.py:552-649`
- Modify: `wxbot/bookkeeping-platform/tests/test_periods.py`
- Test: `wxbot/bookkeeping-platform/tests/test_periods.py`

- [ ] **Step 1: Write the failing period-close test**

```python
def test_close_period_uses_half_open_window_and_persists_group_snapshot(self) -> None:
    group_key = "wechat:g-half-open"
    self.db.set_group(
        platform="wechat",
        group_key=group_key,
        chat_id="g-half-open",
        chat_name="半开区间群",
        group_num=5,
    )
    self.db.add_transaction(
        platform="wechat",
        group_key=group_key,
        group_num=5,
        chat_id="g-half-open",
        chat_name="半开区间群",
        sender_id="u-1",
        sender_name="Alice",
        message_id="msg-a",
        input_sign=1,
        amount=100,
        category="rmb",
        rate=None,
        rmb_value=100,
        raw="rmb+100",
        created_at="2026-03-20 09:30:00",
    )
    self.db.add_transaction(
        platform="wechat",
        group_key=group_key,
        group_num=5,
        chat_id="g-half-open",
        chat_name="半开区间群",
        sender_id="u-1",
        sender_name="Alice",
        message_id="msg-b",
        input_sign=-1,
        amount=40,
        category="rmb",
        rate=None,
        rmb_value=-40,
        raw="-40rmb",
        created_at="2026-03-20 10:00:00",
    )

    service = AccountingPeriodService(self.db)
    period_id = service.close_period(
        start_at="2026-03-20 09:30:00",
        end_at="2026-03-20 10:00:00",
        closed_by="finance-a",
        note="morning close",
    )

    snapshot = self.db.list_period_group_snapshots(period_id)[0]
    self.assertEqual(round(float(snapshot["opening_balance"]), 2), 0.00)
    self.assertEqual(round(float(snapshot["income"]), 2), 0.00)
    self.assertEqual(round(float(snapshot["expense"]), 2), 40.00)
    self.assertEqual(round(float(snapshot["closing_balance"]), 2), -40.00)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_periods.PeriodLifecycleTests.test_close_period_uses_half_open_window_and_persists_group_snapshot -v`
Expected: FAIL because `close_period()` and `list_period_group_snapshots()` do not exist yet

- [ ] **Step 3: Implement the minimal period lifecycle**

```python
def close_period(self, *, start_at: str, end_at: str, closed_by: str, note: str = "") -> int:
    period_id = self.db.insert_accounting_period(
        start_at=start_at,
        end_at=end_at,
        closed_at=end_at,
        closed_by=closed_by,
        note=note,
    )
    groups = self.db.get_all_groups()
    for group in groups:
        group_key = str(group["group_key"])
        opening = self.db.sum_group_balance_before(group_key, start_at, inclusive=False)
        txs = self.db.list_transactions_between(group_key, start_at, end_at)
        income = sum(float(tx["rmb_value"]) for tx in txs if float(tx["rmb_value"]) > 0)
        expense = sum(abs(float(tx["rmb_value"])) for tx in txs if float(tx["rmb_value"]) < 0)
        closing = opening + income - expense
        self.db.insert_period_group_snapshot(
            period_id=period_id,
            group_key=group_key,
            platform=str(group["platform"]),
            chat_name=str(group["chat_name"]),
            group_num=int(group["group_num"]) if group["group_num"] is not None else None,
            business_role=group["business_role"],
            opening_balance=opening,
            income=income,
            expense=expense,
            closing_balance=closing,
            transaction_count=len(txs),
        )
        self.db.replace_period_card_stats(period_id=period_id, group_key=group_key, txs=txs)
    return period_id
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_periods.PeriodLifecycleTests.test_close_period_uses_half_open_window_and_persists_group_snapshot -v`
Expected: PASS

### Task 4: Switch Reporting to Explicit Period Snapshots

**Files:**
- Modify: `wxbot/bookkeeping-platform/bookkeeping_core/reporting.py:12-124`
- Modify: `wxbot/bookkeeping-platform/tests/test_reporting.py:68-230`
- Modify: `wxbot/bookkeeping-platform/tests/test_periods.py`
- Test: `wxbot/bookkeeping-platform/tests/test_reporting.py`

- [ ] **Step 1: Write the failing reporting test**

```python
def test_reporting_reads_latest_accounting_period_snapshot(self) -> None:
    service = AccountingPeriodService(self.db)
    period_id = service.close_period(
        start_at="2026-03-19 00:00:00",
        end_at="2026-03-19 10:30:00",
        closed_by="finance-a",
        note="phase1 close",
    )

    rows = ReportingService(self.db).get_period_group_rows(period_id)
    self.assertEqual(len(rows), 1)
    self.assertEqual(rows[0]["settlement_id"], period_id)
    self.assertEqual(round(rows[0]["closing_balance"], 2), 380.00)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_reporting.ReportingTests.test_reporting_reads_latest_accounting_period_snapshot -v`
Expected: FAIL because `get_period_group_rows()` still depends on legacy `settlements`

- [ ] **Step 3: Refactor reporting to read persisted period rows**

```python
def get_period_group_rows(self, period_id: int) -> list[dict]:
    rows = self.db.list_period_group_snapshots(period_id)
    return [
        {
            "settlement_id": period_id,
            "group_key": str(row["group_key"]),
            "platform": str(row["platform"]),
            "chat_name": str(row["chat_name"]),
            "group_num": int(row["group_num"]) if row["group_num"] is not None else None,
            "opening_balance": float(row["opening_balance"]),
            "income": float(row["income"]),
            "expense": float(row["expense"]),
            "closing_balance": float(row["closing_balance"]),
            "settled_at": str(row["closed_at"]),
            "adjustment_count": int(row["adjustment_count"]),
        }
        for row in rows
    ]
```

- [ ] **Step 4: Run reporting regression tests**

Run: `python3 -m unittest tests.test_reporting -v`
Expected: PASS with existing period summary, adjustment, combination, import regression still green

### Task 5: Expose Minimal Period APIs and Keep Dashboard Compatible

**Files:**
- Modify: `wxbot/bookkeeping-platform/bookkeeping_web/app.py:199-260`
- Modify: `wxbot/bookkeeping-platform/tests/test_webapp.py:82-211`
- Modify: `wxbot/bookkeeping-platform/README.md`
- Test: `wxbot/bookkeeping-platform/tests/test_webapp.py`

- [ ] **Step 1: Write the failing web API tests**

```python
def test_accounting_period_endpoints_close_and_list_periods(self) -> None:
    status, payload = self._request(
        "POST",
        "/api/accounting-periods/close",
        {
            "start_at": "2026-03-20 00:00:00",
            "end_at": "2026-03-20 09:30:00",
            "closed_by": "finance-web",
            "note": "web close",
        },
    )
    self.assertEqual(status, 200)
    self.assertGreater(payload["period_id"], 0)

    status, periods = self._request("GET", "/api/accounting-periods")
    self.assertEqual(status, 200)
    self.assertEqual(len(periods["items"]), 1)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_webapp.WebAppTests.test_accounting_period_endpoints_close_and_list_periods -v`
Expected: FAIL with 404 for `/api/accounting-periods/close` or `/api/accounting-periods`

- [ ] **Step 3: Implement the minimal WSGI endpoints**

```python
if path == "/api/accounting-periods" and method == "GET":
    return _with_db(db_file, start_response, _handle_accounting_periods)
if path == "/api/accounting-periods/close" and method == "POST":
    return _with_db(db_file, start_response, _handle_close_accounting_period, environ)

def _handle_accounting_periods(db: BookkeepingDB, start_response, environ=None):
    payload = {"items": ReportingService(db).list_accounting_periods(limit=20)}
    return _respond_json(start_response, 200, payload)

def _handle_close_accounting_period(db: BookkeepingDB, start_response, environ):
    payload = _read_json_body(environ)
    period_id = AccountingPeriodService(db).close_period(
        start_at=str(payload["start_at"]),
        end_at=str(payload["end_at"]),
        closed_by=str(payload["closed_by"]),
        note=str(payload.get("note", "")),
    )
    return _respond_json(start_response, 200, {"period_id": period_id})
```

- [ ] **Step 4: Run web and documentation regression**

Run: `python3 -m unittest tests.test_webapp -v`
Expected: PASS with dashboard, adjustment, sync idempotency, and new accounting period endpoints all green

- [ ] **Step 5: Update README with the new operator path**

```markdown
### 账期接口

- `GET /api/accounting-periods`：列出最近账期
- `POST /api/accounting-periods/close`：按 `start_at < created_at <= end_at` 关闭一个全局账期

### 回归验证

`python3 -m unittest tests.test_periods tests.test_reporting tests.test_webapp tests.test_postgres_backend -v`
```

Run: `python3 -m unittest tests.test_periods tests.test_reporting tests.test_webapp tests.test_postgres_backend -v`
Expected: PASS
