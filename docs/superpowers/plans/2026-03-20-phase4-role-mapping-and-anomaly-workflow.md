# Phase 4 Role Mapping and Anomaly Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add deterministic role-mapping governance, current-workspace anomaly signals, and manual correction / audit workflow so finance can spot wrong records before closing a period instead of only after the fact.

**Architecture:** Introduce two focused services: `role_mapping.py` applies the confirmed precedence rules (`manual subject/group assignment > /set group number mapping > unassigned`), and `anomalies.py` scans unsettled transactions plus current-period card aggregates to produce reviewable cases rather than mutating records automatically. Persist role-mapping rules, anomaly cases, and anomaly-case items explicitly, and reuse the already-present `anomaly_flags_json` plus `manual_adjustments` audit trail in the workbench API.

**Tech Stack:** Python 3, sqlite3, optional PostgreSQL via `psycopg` compatibility layer, `unittest`, WSGI app, vanilla HTML/CSS/JS.

---

## Scope Boundary

这份计划只覆盖：

- 角色映射规则管理
- 当前未跑账工作区
- 待配对 / 疑似错账 / 待处理 信号
- 回看原始记录、修正记录、操作日志

这份计划**不**覆盖：

- AI 自动修正
- 自动确认某条记录一定错误
- 主体自动归并
- 更复杂的利润归属模型

依赖假设：

- P1 的账期与卡种快照已经可用
- P2 的工作台页面和 API 已经落地
- P3 的主体表如果已经存在，则用于补充角色来源；如果尚未落地，则先按群角色工作

## Execution Notes

- 执行工作目录：`/Users/lcc/SeeSee/wxbot/bookkeeping-platform`
- 执行时遵循 `@test-driven-development` 与 `@verification-before-completion`
- 按仓库规则，本计划**不包含** `git commit`、分支或合并步骤
- 所有异常规则都必须是“可解释、可复现”的确定性逻辑，不能引入隐式自动改账
- 关闭账期时只允许写入异常标记和审计信息，不允许偷偷修正文档没授权的业务数据

## File Structure

- Create: `wxbot/bookkeeping-platform/bookkeeping_core/role_mapping.py`
  责任：封装角色映射规则、优先级应用与回填
- Create: `wxbot/bookkeeping-platform/bookkeeping_core/anomalies.py`
  责任：封装当前未跑账工作区扫描、配对尝试、异常 case 构建
- Create: `wxbot/bookkeeping-platform/tests/test_anomalies.py`
  责任：覆盖角色映射、异常分类、审计展示
- Modify: `wxbot/bookkeeping-platform/bookkeeping_core/database.py`
  责任：增加角色映射规则表、异常 case 表与仓储方法
- Modify: `wxbot/bookkeeping-platform/sql/postgres_schema.sql`
  责任：同步 PostgreSQL 下的新治理表
- Modify: `wxbot/bookkeeping-platform/bookkeeping_core/periods.py`
  责任：关闭账期时把异常摘要落进 `anomaly_flags_json`
- Modify: `wxbot/bookkeeping-platform/bookkeeping_core/reporting.py`
  责任：把当前工作区信号、异常列表、修正审计统一暴露给工作台
- Modify: `wxbot/bookkeeping-platform/bookkeeping_web/app.py`
  责任：新增角色映射、异常列表、审计流 API
- Modify: `wxbot/bookkeeping-platform/bookkeeping_web/pages.py`
  责任：为工作台增加当前工作区、异常筛选、审计回看面板
- Modify: `wxbot/bookkeeping-platform/tests/test_webapp.py`
  责任：覆盖治理 API 与工作台集成
- Modify: `wxbot/bookkeeping-platform/tests/test_postgres_backend.py`
  责任：验证 PostgreSQL 假连接也能初始化治理表与异常查询
- Modify: `wxbot/bookkeeping-platform/README.md`
  责任：记录角色映射规则、异常状态和手工核查流程

### Task 1: Add Role Mapping Rules and Precedence

**Files:**
- Create: `wxbot/bookkeeping-platform/bookkeeping_core/role_mapping.py`
- Modify: `wxbot/bookkeeping-platform/bookkeeping_core/database.py`
- Modify: `wxbot/bookkeeping-platform/sql/postgres_schema.sql`
- Create: `wxbot/bookkeeping-platform/tests/test_anomalies.py`
- Test: `wxbot/bookkeeping-platform/tests/test_anomalies.py`

- [ ] **Step 1: Write the failing role-mapping test**

```python
class RoleMappingTests(unittest.TestCase):
    def test_manual_mapping_overrides_group_number_mapping(self) -> None:
        service = RoleMappingService(self.db)
        service.save_group_number_rule(group_num=5, business_role="customer", updated_by="finance-a")
        service.save_manual_group_role(group_key="wechat:g-1", business_role="supplier", updated_by="finance-a")

        resolved = service.resolve_group_role("wechat:g-1")

        self.assertEqual(resolved["business_role"], "supplier")
        self.assertEqual(resolved["source"], "manual")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_anomalies.RoleMappingTests.test_manual_mapping_overrides_group_number_mapping -v`
Expected: FAIL with missing `RoleMappingService` or missing role-rule tables

- [ ] **Step 3: Implement deterministic role mapping**

```python
class RoleMappingService:
    def resolve_group_role(self, group_key: str) -> dict:
        manual = self.db.get_manual_group_role(group_key)
        if manual is not None:
            return {"business_role": str(manual["business_role"]), "source": "manual"}
        group_row = self.db.get_group_by_key(group_key)
        number_rule = self.db.get_group_number_role(int(group_row["group_num"])) if group_row and group_row["group_num"] is not None else None
        if number_rule is not None:
            return {"business_role": str(number_rule["business_role"]), "source": "group_num"}
        return {"business_role": "unassigned", "source": "unassigned"}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_anomalies.RoleMappingTests.test_manual_mapping_overrides_group_number_mapping -v`
Expected: PASS

### Task 2: Add Current Workspace Anomaly Detection

**Files:**
- Create: `wxbot/bookkeeping-platform/bookkeeping_core/anomalies.py`
- Modify: `wxbot/bookkeeping-platform/bookkeeping_core/reporting.py`
- Modify: `wxbot/bookkeeping-platform/tests/test_anomalies.py`
- Test: `wxbot/bookkeeping-platform/tests/test_anomalies.py`

- [ ] **Step 1: Write the failing anomaly-classification test**

```python
def test_current_workspace_classifies_pending_mismatch_and_unprocessable_rows(self) -> None:
    payload = AnomalyService(self.db).build_current_workspace(end_at="2026-03-20 12:00:00")

    self.assertEqual(payload["summary"]["pending_count"], 1)
    self.assertEqual(payload["summary"]["mismatch_count"], 1)
    self.assertEqual(payload["summary"]["unprocessable_count"], 1)
    self.assertEqual(payload["items"][0]["status"], "pending")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_anomalies.AnomalyDetectionTests.test_current_workspace_classifies_pending_mismatch_and_unprocessable_rows -v`
Expected: FAIL with missing `AnomalyService` or missing current-workspace payload

- [ ] **Step 3: Implement deterministic workspace scanning**

```python
class AnomalyService:
    def build_current_workspace(self, *, end_at: str) -> dict:
        txs = self.db.list_unsettled_transactions_before(end_at=end_at)
        cases = self._pair_transactions_by_card_and_usd_amount(txs)
        return {
            "summary": self._summarize_cases(cases),
            "items": [self._serialize_case(item) for item in cases],
        }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_anomalies.AnomalyDetectionTests.test_current_workspace_classifies_pending_mismatch_and_unprocessable_rows -v`
Expected: PASS

### Task 3: Add Reviewable Cases and Audit Endpoints

**Files:**
- Create: `wxbot/bookkeeping-platform/bookkeeping_core/anomalies.py`
- Modify: `wxbot/bookkeeping-platform/bookkeeping_core/database.py`
- Modify: `wxbot/bookkeeping-platform/bookkeeping_core/reporting.py`
- Modify: `wxbot/bookkeeping-platform/tests/test_anomalies.py`
- Modify: `wxbot/bookkeeping-platform/tests/test_webapp.py`
- Test: `wxbot/bookkeeping-platform/tests/test_webapp.py`

- [ ] **Step 1: Write the failing review-flow test**

```python
def test_anomaly_review_endpoint_returns_case_raw_records_and_adjustment_audit(self) -> None:
    status, payload = self._request("GET", "/api/anomalies/current")
    self.assertEqual(status, 200)
    case_id = payload["items"][0]["id"]

    status, detail = self._request("GET", f"/api/anomalies/{case_id}")
    self.assertEqual(status, 200)
    self.assertIn("raw_records", detail)
    self.assertIn("adjustments", detail)
    self.assertIn("operation_log", detail)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_webapp.WebAppTests.test_anomaly_review_endpoint_returns_case_raw_records_and_adjustment_audit -v`
Expected: FAIL with `404` for `/api/anomalies/current` or `/api/anomalies/<id>`

- [ ] **Step 3: Implement case storage and review payloads**

```python
if path == "/api/anomalies/current" and method == "GET":
    return _with_db(db_file, start_response, _handle_current_anomalies, environ)
if path.startswith("/api/anomalies/") and method == "GET":
    return _with_db(db_file, start_response, _handle_anomaly_detail, environ)
if path == "/api/role-mappings" and method == "POST":
    return _with_db(db_file, start_response, _handle_role_mapping_save, environ)
```

- [ ] **Step 4: Run the focused regression suite**

Run: `python3 -m unittest -v tests.test_anomalies tests.test_webapp`
Expected: PASS with anomaly review and audit payloads covered

### Task 4: Integrate Anomaly Signals into the Workbench

**Files:**
- Modify: `wxbot/bookkeeping-platform/bookkeeping_core/periods.py`
- Modify: `wxbot/bookkeeping-platform/bookkeeping_core/reporting.py`
- Modify: `wxbot/bookkeeping-platform/bookkeeping_web/app.py`
- Modify: `wxbot/bookkeeping-platform/bookkeeping_web/pages.py`
- Modify: `wxbot/bookkeeping-platform/README.md`
- Test: `wxbot/bookkeeping-platform/tests/test_webapp.py`

- [ ] **Step 1: Write the failing workbench-integration test**

```python
def test_workbench_payload_includes_current_workspace_signals_and_period_anomaly_flags(self) -> None:
    status, payload = self._request("GET", "/api/workbench")
    self.assertEqual(status, 200)
    self.assertIn("current_workspace", payload)
    self.assertIn("summary", payload["current_workspace"])

    period_id = payload["periods"][0]["id"]
    status, period_payload = self._request(
        "GET",
        "/api/workbench",
        query_string=f"period_id={period_id}",
    )
    self.assertEqual(status, 200)
    self.assertIn("anomaly_flags", period_payload["group_rows"][0])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_webapp.WebAppTests.test_workbench_payload_includes_current_workspace_signals_and_period_anomaly_flags -v`
Expected: FAIL with missing `current_workspace` or missing anomaly flags in period rows

- [ ] **Step 3: Wire anomaly signals into workbench and period close**

```python
workspace = AnomalyService(self.db).build_current_workspace(end_at=end_at)
self.db.insert_period_group_snapshot(
    ...,
    anomaly_flags_json=json.dumps(self._flags_for_group(group_key, workspace)),
)
payload["current_workspace"] = workspace
```

- [ ] **Step 4: Run the focused verification suite**

Run: `python3 -m unittest -v tests.test_anomalies tests.test_webapp tests.test_postgres_backend`
Expected: PASS with role mapping, anomaly workflow, and workbench integration covered
