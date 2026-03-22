# Phase 2.7 Deprecate /api/sync/events Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove `/api/sync/events` as a supported interface and clean up the code, tests, and documentation that still treat it as an active path, because message delivery has already moved to the new sending entrypoint.

**Architecture:** Keep the live online path on the new sending entrypoint and retire `/api/sync/events` from the WSGI surface. This plan only removes the deprecated interface and its directly related maintenance burden; it does not expand into broader runtime redesign or follow-on anomaly workflow work.

**Tech Stack:** Python 3, sqlite3, optional PostgreSQL via `psycopg` compatibility layer, `unittest`, WSGI app, existing `bookkeeping_core` services.

---

## Scope Boundary

这份计划只覆盖 `/api/sync/events` 相关内容退场：

- 移除 `/api/sync/events` 路由和处理函数
- 清理围绕该接口保留的测试
- 清理 README / 当前有效设计文档里的接口说明
- 退役或隔离 `sync_events.py`，避免继续作为在线接口依赖

这份计划**不**覆盖：

- P2 工作台通用交易明细补齐
- P4 当前未跑账工作区异常治理
- 新的交易语法、parser 扩展或 runtime 合同重构
- 历史数据迁移执行
- settlement bootstrap / `backfill_legacy_periods()` 的历史补账逻辑

## Acceptance Criteria

P2.7 完成的验收标准：

1. `bookkeeping_web.app` 不再暴露 `POST /api/sync/events`
2. 对 `/api/sync/events` 的 Web 回归要么删除，要么改为断言 `404`
3. `README.md` 不再指导用户调用 `/api/sync/events`
4. 当前有效设计/实施文档不再把 `/api/sync/events` 写成仍需维护的在线接口
5. 主代码路径不再为了 `/api/sync/events` 保留 import、handler 或成功路径测试

## Execution Notes

- 执行工作目录：`/Users/lcc/SeeSee/wxbot/bookkeeping-platform`
- 执行时遵循 `@test-driven-development` 与 `@verification-before-completion`
- 按仓库规则，本计划**不包含** `git commit`、分支或合并步骤
- 这份计划只有一个目标：让 `/api/sync/events` 废弃掉，不顺带做别的功能
- 历史计划文档可以保留事实记录，但当前 README / 有效设计文档不能继续把这个接口写成活跃入口
- 若 `sync_events.py` 暂时不删，也必须与在线入口解耦，不能再被 `app.py` 主路径引用

## File Structure

- Modify: `wxbot/bookkeeping-platform/bookkeeping_web/app.py`
  责任：删除 `/api/sync/events` 路由、handler 和相关 import
- Delete or Retire: `wxbot/bookkeeping-platform/bookkeeping_core/sync_events.py`
  责任：删除或隔离旧接口处理逻辑，避免继续作为在线入口实现
- Modify: `wxbot/bookkeeping-platform/tests/test_webapp.py`
  责任：删除 `/api/sync/events` 成功路径测试，新增废弃断言
- Modify: `wxbot/bookkeeping-platform/README.md`
  责任：删除 `/api/sync/events` 使用说明、curl 示例和维护承诺
- Modify: `docs/superpowers/specs/2026-03-21-unified-bookkeeping-core-design.md`
  责任：更新当前有效设计说明，避免继续把 `/api/sync/events` 描述成活跃接口
- Modify: `docs/superpowers/plans/2026-03-21-unified-bookkeeping-core-implementation.md`
  责任：增加 superseded note 或更新说明，避免后续继续按旧接口推进

### Task 1: Lock the Deprecation With Failing Web Tests

**Files:**
- Modify: `wxbot/bookkeeping-platform/tests/test_webapp.py`
- Test: `wxbot/bookkeeping-platform/tests/test_webapp.py`

- [ ] **Step 1: Write the failing deprecation test**

```python
def test_sync_events_route_is_no_longer_supported(self) -> None:
    status, payload = self._request("POST", "/api/sync/events", {"events": []})
    self.assertEqual(status, 404)
```

- [ ] **Step 2: Run the focused test to verify it fails**

Run: `python3 -m unittest tests.test_webapp.WebAppTests.test_sync_events_route_is_no_longer_supported -v`
Expected: FAIL because `/api/sync/events` still exists

- [ ] **Step 3: Write the minimal route removal**

最小实现要求：

- 删除 `app.py` 中的 `/api/sync/events` 路由分支
- 删除 `_handle_sync_events(...)`
- 删除 `from bookkeeping_core.sync_events import ingest_sync_events`

- [ ] **Step 4: Re-run the focused test**

Run: `python3 -m unittest tests.test_webapp.WebAppTests.test_sync_events_route_is_no_longer_supported -v`
Expected: PASS

### Task 2: Remove Interface-Specific Maintenance Tests

**Files:**
- Modify: `wxbot/bookkeeping-platform/tests/test_webapp.py`
- Test: `wxbot/bookkeeping-platform/tests/test_webapp.py`

- [ ] **Step 1: Identify the obsolete sync-events tests**

要清掉的维护负担包括：

- `/api/sync/events` token 校验测试
- `/api/sync/events` 成功导入测试
- `ingested_events` 回滚语义测试
- README 中要求保留 sync/events 的断言

- [ ] **Step 2: Delete or rewrite those tests**

最小实现要求：

- 旧测试不再维护 `/api/sync/events` 成功路径
- 如仍需保留边界断言，只保留 “调用该接口返回 404”

- [ ] **Step 3: Run the Web regression suite**

Run: `python3 -m unittest tests.test_webapp -v`
Expected: PASS with no `/api/sync/events` success-path maintenance left

### Task 3: Remove /api/sync/events From README and Active Docs

**Files:**
- Modify: `wxbot/bookkeeping-platform/README.md`
- Modify: `docs/superpowers/specs/2026-03-21-unified-bookkeeping-core-design.md`
- Modify: `docs/superpowers/plans/2026-03-21-unified-bookkeeping-core-implementation.md`
- Test: `wxbot/bookkeeping-platform/tests/test_webapp.py`

- [ ] **Step 1: Write the failing documentation assertion**

```python
def test_readme_no_longer_mentions_sync_events_interface(self) -> None:
    readme_text = Path(__file__).resolve().parents[1].joinpath("README.md").read_text(encoding="utf-8")
    self.assertNotIn("/api/sync/events", readme_text)
```

- [ ] **Step 2: Update README and active docs**

最小实现要求：

- README 删除 `/api/sync/events` 说明和 curl 示例
- 当前有效设计说明不再把 `/api/sync/events` 写成活跃入口
- 当前有效实施计划补一条 superseded note，避免继续维护旧接口

- [ ] **Step 3: Re-run the focused documentation test**

Run: `python3 -m unittest tests.test_webapp.WebAppTests.test_readme_no_longer_mentions_sync_events_interface -v`
Expected: PASS

### Task 4: Retire or Isolate sync_events.py

**Files:**
- Delete or Retire: `wxbot/bookkeeping-platform/bookkeeping_core/sync_events.py`
- Modify: `wxbot/bookkeeping-platform/bookkeeping_web/app.py`
- Test: `wxbot/bookkeeping-platform/tests/test_webapp.py`

- [ ] **Step 1: Decide whether the file is deleted or isolated**

决策规则：

- 如果没有任何在线代码路径再需要它，直接删除
- 如果暂时保留作历史参考，也不能再被 `app.py`、README、主测试路径引用

- [ ] **Step 2: Apply the minimal cleanup**

最小实现要求：

- 主代码路径不再 import `sync_events.py`
- 主测试路径不再覆盖它的在线行为
- 文档不再把它描述成当前支持接口

- [ ] **Step 3: Run the final regression suite**

Run: `python3 -m unittest tests.test_runtime tests.test_webapp tests.test_ingestion_alignment tests.test_periods tests.test_reporting tests.test_analytics tests.test_postgres_backend -v`
Expected: PASS with `/api/sync/events` fully retired from the supported interface surface
