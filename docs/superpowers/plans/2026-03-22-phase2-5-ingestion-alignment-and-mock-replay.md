# Phase 2.5 Ingestion Alignment and Mock Replay Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Superseded note (2026-03-22):** `/api/sync/events` 与 WhatsApp 本地 V1 兼容链路已退役。本文中凡是要求继续保留 compatibility sync 或 `sync_events.py` 的描述，仅代表历史背景，不再作为现行执行依据。

**Goal:** Align live runtime input and mock replay input behind one stable transaction-ingestion contract so P1/P2 period snapshots become reproducible without touching real adapter cutover.

**Architecture:** Keep WeChat and WhatsApp adapters on the existing `POST /api/core/messages` boundary. Add a thin ingestion layer between runtime/mock payloads and `BookkeepingDB.add_transaction()` so runtime messages and test mock records all persist through one stable contract, then make mock replay and legacy backfill both capable of generating complete `accounting_periods`, `period_group_snapshots`, and `period_card_stats`.

**Tech Stack:** Python 3, sqlite3, optional PostgreSQL via `psycopg` compatibility layer, `unittest`, WSGI app, existing `bookkeeping_core` services.

---

## Scope Boundary

这份计划只覆盖 P2.5 前置层：

- 统一入账契约
- mock 数据与回放夹具
- `/workbench` 与 `/history` 的账期快照前置条件
- 兼容性 settlement bootstrap 的最小补齐
- SQLite 与 PostgreSQL 假连接双通验证

这份计划**不**覆盖：

- WeChat / WhatsApp 真实入口切流
- 真实生产数据库批量迁移执行
- 新的复杂交易语法或更激进的 parser 扩展
- P3 主体治理
- P4 异常工作流
- 页面视觉重做

## Acceptance Criteria

P2.5 完成的验收标准：

1. runtime mock 回放可以生成非空 `accounting_periods`、`period_group_snapshots`、`period_card_stats`
2. compatibility sync mock 回放可以生成同样可读的 period 快照
3. `/api/workbench` 在 mock 数据下返回非空 `card_stats`
4. `/api/history` 在 mock 数据下返回非空 `card_rankings`
5. compatibility-only 的 `backfill_legacy_periods()` 如果被调用，能够补出 `period_card_stats`
6. 上述行为在 SQLite 和 PostgreSQL 假连接下都可通过 `unittest`

## Execution Notes

- 执行工作目录：`/Users/lcc/SeeSee/wxbot/bookkeeping-platform`
- 执行时遵循 `@test-driven-development` 与 `@verification-before-completion`
- 按仓库规则，本计划**不包含** `git commit`、分支或合并步骤
- 在没有额外批准前，不改 WeChat / WhatsApp 适配器对真实环境的接入方式
- 所有数据库验证优先使用临时 SQLite 文件和现有 fake psycopg 夹具，不对真实库写入
- 旧总账数据不再作为主交付目标；legacy settlement 迁移只保留兼容/bootstrap 价值，不作为 P2.5 主路径

## File Structure

- Create: `wxbot/bookkeeping-platform/bookkeeping_core/ingestion.py`
  责任：定义稳定的结构化入账契约、runtime/sync/mock 三种来源的构造函数、统一持久化入口
- Create: `wxbot/bookkeeping-platform/tests/support/__init__.py`
  责任：让测试辅助模块成为可复用包
- Create: `wxbot/bookkeeping-platform/tests/support/bookkeeping_replay.py`
  责任：统一提供 mock envelope、mock sync event、结构化记录、关账回放、场景工厂
- Create: `wxbot/bookkeeping-platform/tests/test_ingestion_alignment.py`
  责任：覆盖统一入账契约、runtime/sync builder 对齐、mock replay 到 period snapshot 的主路径
- Modify: `wxbot/bookkeeping-platform/bookkeeping_core/database.py`
  责任：让 `add_transaction()` 显式持久化 `parse_version`、`usd_amount`、`unit_face_value`、`unit_count`，并保持 SQLite / PostgreSQL 实现一致
- Modify: `wxbot/bookkeeping-platform/bookkeeping_core/service.py`
  责任：把 runtime 的交易落库从内联 `add_transaction()` 切到统一 ingestion contract
- Modify: `wxbot/bookkeeping-platform/bookkeeping_core/sync_events.py`
  责任：把 compatibility sync 的 `transaction.created` 落库切到统一 ingestion contract，保持幂等和回滚语义不变
- Modify: `wxbot/bookkeeping-platform/bookkeeping_core/periods.py`
  责任：让 `backfill_legacy_periods()` 同步补出 `period_card_stats`，避免 compatibility bootstrap 只有 group snapshot 没有 card stats
- Modify: `wxbot/bookkeeping-platform/tests/test_runtime.py`
  责任：补 runtime 通过统一 contract 产出稳定字段的回归
- Modify: `wxbot/bookkeeping-platform/tests/test_analytics.py`
  责任：改用共享 replay helper 构造 workbench / history 所需 mock 数据，避免 `_make_tx` 继续分叉
- Modify: `wxbot/bookkeeping-platform/tests/test_webapp.py`
  责任：新增 mock replay 驱动下的 `/api/workbench`、`/api/history` 端到端回归
- Modify: `wxbot/bookkeeping-platform/tests/test_postgres_backend.py`
  责任：保证统一 ingestion + replay 路径在 fake PostgreSQL 下仍可序列化并可读
- Modify: `wxbot/bookkeeping-platform/README.md`
  责任：记录 P2.5 mock replay 验证路径，以及 legacy settlement bootstrap 只是兼容路径

### Task 1: Add Structured Ingestion Contract and Persistence API

**Files:**
- Create: `wxbot/bookkeeping-platform/bookkeeping_core/ingestion.py`
- Create: `wxbot/bookkeeping-platform/tests/support/__init__.py`
- Create: `wxbot/bookkeeping-platform/tests/support/bookkeeping_replay.py`
- Create: `wxbot/bookkeeping-platform/tests/test_ingestion_alignment.py`
- Modify: `wxbot/bookkeeping-platform/bookkeeping_core/database.py`
- Test: `wxbot/bookkeeping-platform/tests/test_ingestion_alignment.py`

- [ ] **Step 1: Write the failing contract test**

```python
class StructuredTransactionContractTests(unittest.TestCase):
    def test_structured_record_persists_parse_and_card_fields(self) -> None:
        from bookkeeping_core.ingestion import StructuredTransactionRecord, persist_transaction_record
        from tests.support.bookkeeping_replay import ensure_group, close_period_for_test

        ensure_group(
            self.db,
            platform="wechat",
            group_key="wechat:g-align",
            chat_id="g-align",
            chat_name="对齐测试群",
            group_num=5,
        )

        record = StructuredTransactionRecord(
            platform="wechat",
            group_key="wechat:g-align",
            group_num=5,
            chat_id="g-align",
            chat_name="对齐测试群",
            sender_id="user-1",
            sender_name="User One",
            message_id="msg-align-1",
            created_at="2026-03-22 09:10:00",
            input_sign=1,
            amount=60,
            category="steam",
            rate=10,
            rmb_value=60,
            raw="steam+60",
            parse_version="mock-card-v1",
            usd_amount=600,
            unit_face_value=20,
            unit_count=30,
        )

        persist_transaction_record(self.db, record)
        period_id = close_period_for_test(self.db, start_at="2026-03-22 09:00:00", end_at="2026-03-22 10:00:00")

        tx_row = self.db.get_history("wechat:g-align", 1)[0]
        card_row = self.db.list_period_card_stats(period_id)[0]

        self.assertEqual(str(tx_row["parse_version"]), "mock-card-v1")
        self.assertEqual(float(tx_row["usd_amount"]), 600.0)
        self.assertEqual(float(card_row["usd_amount"]), 600.0)
        self.assertEqual(float(card_row["unit_face_value"]), 20.0)
        self.assertEqual(float(card_row["unit_count"]), 30.0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_ingestion_alignment.StructuredTransactionContractTests.test_structured_record_persists_parse_and_card_fields -v`
Expected: FAIL with `ImportError` / `AttributeError` for missing `StructuredTransactionRecord` or with assertion failures because `add_transaction()` does not persist the explicit analysis fields

- [ ] **Step 3: Write the minimal ingestion contract and database persistence**

```python
@dataclass(slots=True)
class StructuredTransactionRecord:
    platform: str
    group_key: str
    group_num: int | None
    chat_id: str
    chat_name: str
    sender_id: str
    sender_name: str
    message_id: str
    created_at: str | None
    input_sign: int
    amount: float
    category: str
    rate: float | None
    rmb_value: float
    raw: str
    parse_version: str = "1"
    usd_amount: float | None = None
    unit_face_value: float | None = None
    unit_count: float | None = None


def persist_transaction_record(db: BookkeepingDB, record: StructuredTransactionRecord) -> int:
    return db.add_transaction(
        platform=record.platform,
        group_key=record.group_key,
        group_num=record.group_num,
        chat_id=record.chat_id,
        chat_name=record.chat_name,
        sender_id=record.sender_id,
        sender_name=record.sender_name,
        message_id=record.message_id,
        input_sign=record.input_sign,
        amount=record.amount,
        category=record.category,
        rate=record.rate,
        rmb_value=record.rmb_value,
        raw=record.raw,
        created_at=record.created_at,
        parse_version=record.parse_version,
        usd_amount=record.usd_amount,
        unit_face_value=record.unit_face_value,
        unit_count=record.unit_count,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_ingestion_alignment.StructuredTransactionContractTests.test_structured_record_persists_parse_and_card_fields -v`
Expected: PASS

### Task 2: Route Runtime and Compatibility Sync Through One Contract

**Files:**
- Modify: `wxbot/bookkeeping-platform/bookkeeping_core/ingestion.py`
- Modify: `wxbot/bookkeeping-platform/bookkeeping_core/service.py`
- Modify: `wxbot/bookkeeping-platform/bookkeeping_core/sync_events.py`
- Modify: `wxbot/bookkeeping-platform/tests/test_ingestion_alignment.py`
- Modify: `wxbot/bookkeeping-platform/tests/test_runtime.py`
- Modify: `wxbot/bookkeeping-platform/tests/test_webapp.py`
- Test: `wxbot/bookkeeping-platform/tests/test_ingestion_alignment.py`

- [ ] **Step 1: Write the failing builder-alignment test**

```python
class RecordBuilderTests(unittest.TestCase):
    def test_runtime_and_sync_builders_share_one_structured_shape(self) -> None:
        from bookkeeping_core.ingestion import build_runtime_record, build_sync_created_record
        from bookkeeping_core.models import ParsedTransaction

        parsed = ParsedTransaction(
            input_sign=1,
            amount=100,
            category="rmb",
            rate=None,
            rmb_value=100,
            raw="+100rmb",
        )

        runtime_record = build_runtime_record(
            platform="wechat",
            group_key="wechat:g-1",
            group_num=5,
            chat_id="g-1",
            chat_name="运行时群",
            sender_id="u-runtime",
            sender_name="Runtime",
            message_id="msg-runtime-1",
            created_at="2026-03-22 09:15:00",
            parsed=parsed,
        )
        sync_record = build_sync_created_record(
            platform="whatsapp",
            group_key="whatsapp:12036340001@g.us",
            group_num=5,
            chat_id="12036340001@g.us",
            chat_name="兼容群",
            sender_id="u-sync",
            sender_name="Sync",
            message_id="whatsapp-local-tx-501",
            created_at="2026-03-22 09:15:00",
            input_sign=1,
            amount=100,
            category="rmb",
            rate=None,
            rmb_value=100,
            raw="+100rmb",
        )

        self.assertEqual(runtime_record.parse_version, "1")
        self.assertEqual(sync_record.parse_version, "1")
        self.assertEqual(runtime_record.amount, 100)
        self.assertEqual(sync_record.amount, 100)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_ingestion_alignment.RecordBuilderTests.test_runtime_and_sync_builders_share_one_structured_shape -v`
Expected: FAIL with missing builder functions

- [ ] **Step 3: Implement the builders and replace inline inserts**

```python
def build_runtime_record(..., parsed: ParsedTransaction) -> StructuredTransactionRecord:
    return StructuredTransactionRecord(
        platform=platform,
        group_key=group_key,
        group_num=group_num,
        chat_id=chat_id,
        chat_name=chat_name,
        sender_id=sender_id,
        sender_name=sender_name,
        message_id=message_id,
        created_at=created_at,
        input_sign=parsed.input_sign,
        amount=parsed.amount,
        category=parsed.category,
        rate=parsed.rate,
        rmb_value=parsed.rmb_value,
        raw=parsed.raw,
        parse_version="1",
    )


def build_sync_created_record(..., raw: str, rmb_value: float) -> StructuredTransactionRecord:
    return StructuredTransactionRecord(
        platform=platform,
        group_key=group_key,
        group_num=group_num,
        chat_id=chat_id,
        chat_name=chat_name,
        sender_id=sender_id,
        sender_name=sender_name,
        message_id=message_id,
        created_at=created_at,
        input_sign=input_sign,
        amount=amount,
        category=category,
        rate=rate,
        rmb_value=rmb_value,
        raw=raw,
        parse_version="1",
    )
```

- [ ] **Step 4: Run the focused regression suite**

Run: `python3 -m unittest tests.test_ingestion_alignment.RecordBuilderTests tests.test_runtime.UnifiedRuntimeTests.test_same_transaction_text_from_wechat_and_whatsapp_produces_same_facts tests.test_webapp.WebAppTests.test_sync_endpoint_ingests_events_and_keeps_idempotency -v`
Expected: PASS

### Task 3: Add Reusable Mock Replay Scenarios for P2 Read Surfaces

**Files:**
- Modify: `wxbot/bookkeeping-platform/tests/support/bookkeeping_replay.py`
- Modify: `wxbot/bookkeeping-platform/tests/test_analytics.py`
- Modify: `wxbot/bookkeeping-platform/tests/test_webapp.py`
- Modify: `wxbot/bookkeeping-platform/tests/test_ingestion_alignment.py`
- Test: `wxbot/bookkeeping-platform/tests/test_analytics.py`

- [ ] **Step 1: Write the failing P2 replay test**

```python
class MockReplayWorkbenchTests(unittest.TestCase):
    def test_runtime_replay_generates_workbench_and_history_card_sections(self) -> None:
        from tests.support.bookkeeping_replay import build_runtime_card_scenario, replay_runtime_scenario

        scenario = build_runtime_card_scenario()
        period_id = replay_runtime_scenario(self.db, scenario)

        workbench = AnalyticsService(self.db).build_period_workbench(period_id=period_id)
        history = AnalyticsService(self.db).build_history_analysis(
            start_date="2026-03-01",
            end_date="2026-03-31",
            card_keyword="steam",
            sort_by="usd_amount",
        )

        self.assertGreater(len(workbench["card_stats"]), 0)
        self.assertGreater(len(history["card_rankings"]), 0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_analytics.MockReplayWorkbenchTests.test_runtime_replay_generates_workbench_and_history_card_sections -v`
Expected: FAIL with missing replay helper or empty `card_stats` / `card_rankings`

- [ ] **Step 3: Implement the replay helper and refactor the tests to use it**

```python
def replay_runtime_scenario(db: BookkeepingDB, scenario: dict) -> int:
    runtime = UnifiedBookkeepingRuntime(db=db, master_users=["finance-mock"], export_dir=Path("/tmp"))
    ensure_group(...)
    for envelope in scenario["envelopes"]:
        runtime.process_envelope(envelope)
    return AccountingPeriodService(db).close_period(
        start_at=scenario["start_at"],
        end_at=scenario["end_at"],
        closed_by=scenario["closed_by"],
        note=scenario.get("note"),
    )
```

- [ ] **Step 4: Run the focused regression suite**

Run: `python3 -m unittest tests.test_analytics.DashboardAnalyticsTests tests.test_analytics.WorkbenchAnalyticsTests tests.test_analytics.HistoryAnalyticsTests tests.test_analytics.MockReplayWorkbenchTests -v`
Expected: PASS

### Task 4: Make Legacy Settlement Bootstrap Produce Card Stats Too

**Files:**
- Modify: `wxbot/bookkeeping-platform/bookkeeping_core/periods.py`
- Modify: `wxbot/bookkeeping-platform/tests/test_periods.py`
- Modify: `wxbot/bookkeeping-platform/tests/test_reporting.py`
- Test: `wxbot/bookkeeping-platform/tests/test_periods.py`

- [ ] **Step 1: Write the failing backfill-card-stats test**

```python
class AccountingPeriodBackfillTests(unittest.TestCase):
    def test_backfill_legacy_periods_also_creates_period_card_stats(self) -> None:
        tx_id = self.db.add_transaction(
            platform="wechat",
            group_key="wechat:g-legacy",
            group_num=5,
            chat_id="g-legacy",
            chat_name="兼容群",
            sender_id="u-legacy",
            sender_name="Legacy",
            message_id="msg-legacy-1",
            input_sign=1,
            amount=60,
            category="steam",
            rate=10,
            rmb_value=60,
            raw="steam+60",
            created_at="2026-03-20 09:00:00",
            parse_version="legacy-card-v1",
            usd_amount=600,
            unit_face_value=20,
            unit_count=30,
        )
        self.db.settle_transactions("wechat", "wechat:g-legacy", self.db.get_unsettled_transactions("wechat:g-legacy"), "finance-legacy", settled_at="2026-03-20 09:30:00")

        AccountingPeriodService(self.db).backfill_legacy_periods()
        period_id = int(self.db.list_accounting_periods()[0]["id"])
        card_rows = self.db.list_period_card_stats(period_id)

        self.assertEqual(len(card_rows), 1)
        self.assertEqual(float(card_rows[0]["usd_amount"]), 600.0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_periods.AccountingPeriodBackfillTests.test_backfill_legacy_periods_also_creates_period_card_stats -v`
Expected: FAIL because `backfill_legacy_periods()` currently leaves `period_card_stats` empty

- [ ] **Step 3: Implement the minimal card-stat backfill**

```python
def backfill_legacy_periods(self) -> int:
    ...
    for settlement in settlements:
        ...
        period_id = self.db.insert_accounting_period(...)
        self.db.insert_period_group_snapshot(...)
        card_rows = self._build_card_stats(period_id, group_key, group_row, txs)
        self.db.replace_period_card_stats(period_id, card_rows)
```

- [ ] **Step 4: Run the focused regression suite**

Run: `python3 -m unittest tests.test_periods.AccountingPeriodBackfillTests tests.test_reporting.ReportingTests.test_dashboard_payload_falls_back_to_legacy_settlements_when_no_periods -v`
Expected: PASS

### Task 5: Verify Fake PostgreSQL Compatibility and Document the P2.5 Path

**Files:**
- Modify: `wxbot/bookkeeping-platform/tests/test_postgres_backend.py`
- Modify: `wxbot/bookkeeping-platform/tests/test_webapp.py`
- Modify: `wxbot/bookkeeping-platform/README.md`
- Test: `wxbot/bookkeeping-platform/tests/test_postgres_backend.py`

- [ ] **Step 1: Write the failing fake-Postgres replay test**

```python
class PostgresBackendTests(unittest.TestCase):
    def test_postgres_dsn_mock_replay_can_fill_workbench_and_history(self) -> None:
        db = BookkeepingDB("postgresql://bookkeeping:test@localhost:5432/bookkeeping")
        try:
            scenario = build_runtime_card_scenario()
            period_id = replay_runtime_scenario(db, scenario)

            service = AnalyticsService(db)
            workbench = service.build_period_workbench(period_id=period_id)
            history = service.build_history_analysis(
                start_date="2026-03-01",
                end_date="2026-03-31",
                card_keyword="steam",
                sort_by="usd_amount",
            )

            self.assertGreater(len(workbench["card_stats"]), 0)
            self.assertGreater(len(history["card_rankings"]), 0)
            json.dumps(workbench)
            json.dumps(history)
        finally:
            db.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_postgres_backend.PostgresBackendTests.test_postgres_dsn_mock_replay_can_fill_workbench_and_history -v`
Expected: FAIL until the replay helper and explicit analysis-field persistence are PostgreSQL-safe

- [ ] **Step 3: Make the helper PostgreSQL-safe and update the docs**

```python
def ensure_group(...):
    db.set_group(...)


README additions:
- mock replay verification commands
- statement that `/api/core/messages` remains the live boundary
- statement that settlement bootstrap is compatibility-only and not the primary P2.5 acceptance path
```

- [ ] **Step 4: Run the final regression suite**

Run: `python3 -m unittest tests.test_ingestion_alignment tests.test_periods tests.test_reporting tests.test_analytics tests.test_webapp tests.test_postgres_backend -v`
Expected: PASS with SQLite and fake PostgreSQL both green
