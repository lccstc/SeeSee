# Phase 3 Subject Directory and Manual Merge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add explicit customer / supplier subjects and the subject-directory page so finance can manage one business counterpart across multiple groups instead of reading raw group balances one chat at a time.

**Architecture:** Keep `groups` as the ingestion unit, but introduce explicit `business_subjects` and `subject_group_links` tables for manual subject management. Compute subject metrics by aggregating linked active groups over real-time balances and period snapshots, and expose that through a dedicated `subjects.py` service plus a focused subject-directory route instead of overloading the generic reporting service.

**Tech Stack:** Python 3, sqlite3, optional PostgreSQL via `psycopg` compatibility layer, `unittest`, WSGI app, vanilla HTML/CSS/JS.

---

## Scope Boundary

这份计划只覆盖：

- 客户 / 供应商主体模型
- 手工把多个群归并到同一主体
- 主体总表搜索、排序、月度统计

这份计划**不**覆盖：

- 自动归并主体
- AI 建议归并
- 异常匹配与错账排查
- 首页全局搜索

依赖假设：

- `groups.business_role` 已经可用，主体角色默认来自主体自身字段，群只负责补充和过滤
- 主体页面先做“手工治理 + 指标展示”，不掺入自动判断逻辑

## Execution Notes

- 执行工作目录：`/Users/lcc/SeeSee/wxbot/bookkeeping-platform`
- 执行时遵循 `@test-driven-development` 与 `@verification-before-completion`
- 按仓库规则，本计划**不包含** `git commit`、分支或合并步骤
- 所有主体汇总都要显式区分“实时余额”和“当月业务金额”，避免混淆当前值与历史范围值
- 主体搜索默认只返回 `active` 群，内部群与未归属群必须能被过滤掉

## File Structure

- Create: `wxbot/bookkeeping-platform/bookkeeping_core/subjects.py`
  责任：封装主体创建、群挂接、月度指标聚合、搜索排序
- Create: `wxbot/bookkeeping-platform/tests/test_subjects.py`
  责任：覆盖主体 schema、手工归并、月度汇总和排序行为
- Modify: `wxbot/bookkeeping-platform/bookkeeping_core/database.py`
  责任：增加主体表、主体-群关联表与仓储方法
- Modify: `wxbot/bookkeeping-platform/sql/postgres_schema.sql`
  责任：同步 PostgreSQL 下的主体 schema
- Modify: `wxbot/bookkeeping-platform/bookkeeping_web/app.py`
  责任：新增主体目录页和主体 API
- Modify: `wxbot/bookkeeping-platform/bookkeeping_web/pages.py`
  责任：新增主体总表页面 shell、搜索栏和排序控件
- Modify: `wxbot/bookkeeping-platform/tests/test_webapp.py`
  责任：覆盖主体页、主体创建、群归并、搜索排序接口
- Modify: `wxbot/bookkeeping-platform/tests/test_postgres_backend.py`
  责任：保证 PostgreSQL 假连接也能初始化主体表并返回主体汇总
- Modify: `wxbot/bookkeeping-platform/README.md`
  责任：记录主体治理 API 和人工验证流程

### Task 1: Add Subject Schema and Repository Methods

**Files:**
- Modify: `wxbot/bookkeeping-platform/bookkeeping_core/database.py`
- Modify: `wxbot/bookkeeping-platform/sql/postgres_schema.sql`
- Create: `wxbot/bookkeeping-platform/tests/test_subjects.py`
- Modify: `wxbot/bookkeeping-platform/tests/test_postgres_backend.py`
- Test: `wxbot/bookkeeping-platform/tests/test_subjects.py`

- [ ] **Step 1: Write the failing subject-schema test**

```python
class SubjectSchemaTests(unittest.TestCase):
    def test_bootstraps_subject_tables(self) -> None:
        db = BookkeepingDB(self.db_path)
        tables = {
            row["name"]
            for row in db.conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
        self.assertIn("business_subjects", tables)
        self.assertIn("subject_group_links", tables)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_subjects.SubjectSchemaTests.test_bootstraps_subject_tables -v`
Expected: FAIL with missing `business_subjects` / `subject_group_links`

- [ ] **Step 3: Write the minimal schema and repository API**

```python
CREATE TABLE IF NOT EXISTS business_subjects (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  role TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'active',
  note TEXT,
  created_by TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS subject_group_links (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  subject_id INTEGER NOT NULL,
  group_key TEXT NOT NULL,
  linked_by TEXT NOT NULL,
  linked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(subject_id, group_key)
);
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_subjects.SubjectSchemaTests.test_bootstraps_subject_tables -v`
Expected: PASS

### Task 2: Add Manual Subject Merge Service

**Files:**
- Create: `wxbot/bookkeeping-platform/bookkeeping_core/subjects.py`
- Modify: `wxbot/bookkeeping-platform/tests/test_subjects.py`
- Test: `wxbot/bookkeeping-platform/tests/test_subjects.py`

- [ ] **Step 1: Write the failing manual-merge test**

```python
def test_linking_multiple_groups_to_one_subject_returns_single_subject_view(self) -> None:
    subject_id = SubjectService(self.db).create_subject(
        name="深圳客户A",
        role="customer",
        created_by="finance-a",
    )
    SubjectService(self.db).link_groups(subject_id=subject_id, group_keys=["wechat:g-1", "wechat:g-2"], linked_by="finance-a")

    rows = SubjectService(self.db).list_subjects(month="2026-03")

    self.assertEqual(len(rows), 1)
    self.assertEqual(rows[0]["group_count"], 2)
    self.assertEqual(rows[0]["name"], "深圳客户A")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_subjects.SubjectMergeTests.test_linking_multiple_groups_to_one_subject_returns_single_subject_view -v`
Expected: FAIL with missing `SubjectService` or missing link methods

- [ ] **Step 3: Implement the minimal subject service**

```python
class SubjectService:
    def __init__(self, db: BookkeepingDB) -> None:
        self.db = db

    def create_subject(self, *, name: str, role: str, created_by: str, note: str = "") -> int:
        return self.db.insert_subject(name=name, role=role, created_by=created_by, note=note)

    def link_groups(self, *, subject_id: int, group_keys: list[str], linked_by: str) -> None:
        self.db.replace_subject_group_links(subject_id=subject_id, group_keys=group_keys, linked_by=linked_by)

    def list_subjects(self, *, month: str, keyword: str = "", sort_by: str = "monthly_amount") -> list[dict]:
        return self._build_subject_rows(month=month, keyword=keyword, sort_by=sort_by)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_subjects.SubjectMergeTests.test_linking_multiple_groups_to_one_subject_returns_single_subject_view -v`
Expected: PASS

### Task 3: Add Subject Metrics, Search, and Sorting

**Files:**
- Create: `wxbot/bookkeeping-platform/bookkeeping_core/subjects.py`
- Modify: `wxbot/bookkeeping-platform/tests/test_subjects.py`
- Modify: `wxbot/bookkeeping-platform/tests/test_webapp.py`
- Test: `wxbot/bookkeeping-platform/tests/test_subjects.py`

- [ ] **Step 1: Write the failing metrics-and-sort test**

```python
def test_subject_listing_supports_keyword_filter_and_monthly_amount_sort(self) -> None:
    rows = SubjectService(self.db).list_subjects(
        month="2026-03",
        keyword="客户",
        sort_by="monthly_amount",
    )

    self.assertGreaterEqual(len(rows), 2)
    self.assertGreaterEqual(rows[0]["monthly_amount"], rows[1]["monthly_amount"])
    self.assertIn("current_balance", rows[0])
    self.assertIn("last_activity_at", rows[0])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_subjects.SubjectMetricsTests.test_subject_listing_supports_keyword_filter_and_monthly_amount_sort -v`
Expected: FAIL with missing monthly aggregation or unsupported sort key

- [ ] **Step 3: Implement subject metrics from balances and period snapshots**

```python
def _build_subject_rows(self, *, month: str, keyword: str, sort_by: str) -> list[dict]:
    rows = []
    for subject in self.db.list_subjects():
        group_keys = self.db.list_subject_group_keys(int(subject["id"]))
        rows.append(
            {
                "id": int(subject["id"]),
                "name": str(subject["name"]),
                "role": str(subject["role"]),
                "group_count": len(group_keys),
                "current_balance": self._sum_current_balance(group_keys),
                "monthly_amount": self._sum_monthly_amount(group_keys, month=month),
                "monthly_usd_amount": self._sum_monthly_usd_amount(group_keys, month=month),
                "last_activity_at": self._max_last_activity(group_keys),
            }
        )
    return self._filter_and_sort(rows, keyword=keyword, sort_by=sort_by)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_subjects.SubjectMetricsTests.test_subject_listing_supports_keyword_filter_and_monthly_amount_sort -v`
Expected: PASS

### Task 4: Add Subject Directory Page and API

**Files:**
- Modify: `wxbot/bookkeeping-platform/bookkeeping_web/app.py`
- Modify: `wxbot/bookkeeping-platform/bookkeeping_web/pages.py`
- Modify: `wxbot/bookkeeping-platform/tests/test_webapp.py`
- Modify: `wxbot/bookkeeping-platform/README.md`
- Test: `wxbot/bookkeeping-platform/tests/test_webapp.py`

- [ ] **Step 1: Write the failing subject-web test**

```python
def test_subject_directory_page_and_api_support_create_and_search(self) -> None:
    status, body = self._request_text("GET", "/subjects")
    self.assertEqual(status, 200)
    self.assertIn("<main", body)

    status, payload = self._request(
        "POST",
        "/api/subjects",
        {"name": "深圳客户A", "role": "customer", "created_by": "finance-a"},
    )
    self.assertEqual(status, 200)
    self.assertGreater(payload["subject_id"], 0)

    status, listing = self._request(
        "GET",
        "/api/subjects",
        query_string="month=2026-03&keyword=深圳",
    )
    self.assertEqual(status, 200)
    self.assertEqual(listing["items"][0]["name"], "深圳客户A")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_webapp.WebAppTests.test_subject_directory_page_and_api_support_create_and_search -v`
Expected: FAIL with `404` for `/subjects` or `/api/subjects`

- [ ] **Step 3: Implement page and API routes**

```python
if path == "/subjects" and method == "GET":
    return _respond_html(start_response, render_subjects_page())
if path == "/api/subjects" and method == "GET":
    return _with_db(db_file, start_response, _handle_subjects_list, environ)
if path == "/api/subjects" and method == "POST":
    return _with_db(db_file, start_response, _handle_subject_create, environ)
if path == "/api/subjects/links" and method == "POST":
    return _with_db(db_file, start_response, _handle_subject_links, environ)
```

- [ ] **Step 4: Run the focused regression suite**

Run: `python3 -m unittest -v tests.test_subjects tests.test_webapp`
Expected: PASS with subject schema, subject metrics, and subject routes covered
