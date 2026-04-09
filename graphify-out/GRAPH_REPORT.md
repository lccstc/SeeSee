# Graph Report - .  (2026-04-09)

## Corpus Check
- 70 files · ~65,408 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 862 nodes · 1953 edges · 28 communities detected
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 112 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## God Nodes (most connected - your core abstractions)
1. `_BookkeepingStoreBase` - 96 edges
2. `WebAppTests` - 55 edges
3. `UnifiedRuntimeTests` - 50 edges
4. `BookkeepingDB` - 46 edges
5. `AnalyticsService` - 37 edges
6. `_respond_json()` - 35 edges
7. `CommandHandler` - 32 edges
8. `ReconciliationService` - 29 edges
9. `QuoteBackendTests` - 28 edges
10. `PostgresTestCase` - 28 edges

## Surprising Connections (you probably didn't know these)
- `WeChatPlatformAPI` --uses--> `NormalizedMessageEnvelope`  [INFERRED]
  wxbot/bookkeeping-platform/wechat_adapter/client.py → wxbot/bookkeeping-platform/bookkeeping_core/contracts.py
- `WeChatCoreApiClient` --uses--> `NormalizedMessageEnvelope`  [INFERRED]
  wxbot/bookkeeping-platform/wechat_adapter/core_api.py → wxbot/bookkeeping-platform/bookkeeping_core/contracts.py
- `_FakeListenedChat` --uses--> `WeChatCoreApiClient`  [INFERRED]
  wxbot/bookkeeping-platform/tests/test_runtime.py → wxbot/bookkeeping-platform/wechat_adapter/core_api.py
- `UnifiedRuntimeTests` --uses--> `WeChatCoreApiClient`  [INFERRED]
  wxbot/bookkeeping-platform/tests/test_runtime.py → wxbot/bookkeeping-platform/wechat_adapter/core_api.py
- `BookkeepingService` --uses--> `CommandHandler`  [INFERRED]
  wxbot/bookkeeping-platform/bookkeeping_core/service.py → wxbot/bookkeeping-platform/bookkeeping_core/commands.py

## Hyperedges (group relationships)
- **核心架构** — reporting_server, bookkeeping_core, bookkeeping_web, postgres_db [EXTRACTED 1.00]
- **消息适配层** — whatsapp_adapter, wechat_adapter, core_api_endpoint [EXTRACTED 1.00]
- **报价系统** — quote_wall, quote_parser_refactor, quote_template [EXTRACTED 1.00]

## Communities

### Community 0 - "数据库层"
Cohesion: 0.04
Nodes (19): _append_quote_restriction(), BookkeepingDB, _BookkeepingStoreBase, is_postgres_dsn(), _PostgresConnectionCompat, _PostgresCursorCompat, _quote_amount_bounds(), _quote_amount_display() (+11 more)

### Community 1 - "账期管理"
Cohesion: 0.04
Nodes (23): AccountingPeriodService, _build_card_stats(), _cleanup_old_backups(), _format_group_close_receipt(), _parse_db_timestamp(), _signed_amount(), _extract_search_path_schema(), PostgresTestCase (+15 more)

### Community 2 - "客户端运行时"
Cohesion: 0.04
Nodes (16): _apply_chat_hint(), _normalize_chat_name(), prepare_runtime(), _resolve_listened_chat_name(), WeChatPlatformAPI, _clean_chat_names(), CoreApiConfig, getConfig() (+8 more)

### Community 3 - "报价与消息合约"
Cohesion: 0.09
Nodes (65): NormalizedMessageEnvelope, _build_exception(), _contains_price(), _contains_question_keyword(), _country_pair_split_pattern(), _derive_modifier_rows(), _document_confidence(), _extract_amount_range() (+57 more)

### Community 4 - "Web 应用框架"
Cohesion: 0.09
Nodes (58): _call_optional_db_method(), create_app(), _ensure_runtime_database_is_ready(), _filter_callable_kwargs(), _handle_accounting_period_close(), _handle_accounting_period_settle_all(), _handle_accounting_periods(), _handle_adjustments() (+50 more)

### Community 5 - "消息合约与动作"
Cohesion: 0.05
Nodes (16): CoreActionCollector, from_dict(), _normalized_sender_kind(), _required_text(), send_file_action(), send_text_action(), SendFileAction, SendTextAction (+8 more)

### Community 6 - "分析服务"
Cohesion: 0.12
Nodes (24): AnalyticsService, _attach_group_usd_amounts(), _card_rows(), _count_transactions_by_role(), _date_text(), _financial_rows(), _input_direction(), _int_or_none() (+16 more)

### Community 7 - "Web 应用测试"
Cohesion: 0.07
Nodes (1): WebAppTests

### Community 8 - "系统架构与文档"
Cohesion: 0.06
Nodes (29): bookkeeping_core 业务核心, bookkeeping_web Web 层, POST /api/core/messages 核心入口, 阶段A 证据链, 阶段B 结构化解析, 阶段C 关联与回溯, 阶段D 差额追踪, PostgreSQL 数据库 (+21 more)

### Community 9 - "对账服务"
Cohesion: 0.12
Nodes (8): _csv_number(), _expected_transaction_rmb(), _int_or_none(), _normalize_group_num(), _normalize_text(), _normalize_timestamp(), ReconciliationService, _sort_group_num()

### Community 10 - "命令处理器"
Cohesion: 0.17
Nodes (4): CommandHandler, _format_period_close_message(), _NullActionCollector, _parse_db_timestamp()

### Community 11 - "核心 API 客户端"
Cohesion: 0.13
Nodes (15): CoreApiClient, executeCoreActions(), isAbortError(), isRecord(), _parse_whoami_text(), safeReadText(), _validate_action(), validateCoreAction() (+7 more)

### Community 12 - "消息摄入服务"
Cohesion: 0.12
Nodes (9): build_runtime_record(), build_sync_created_record(), StructuredTransactionRecord, ParsedTransaction, _parse_match(), parse_transaction(), RecordBuilderTests, ReplayScenarioContractTests (+1 more)

### Community 13 - "报表服务"
Cohesion: 0.16
Nodes (5): ReportingService, default_business_role_for_group_num(), normalize_business_role(), resolve_business_role(), resolve_role_source()

### Community 14 - "WhatsApp 客户端"
Cohesion: 0.14
Nodes (1): WhatsAppClient

### Community 15 - "WhatsApp 入口"
Cohesion: 0.22
Nodes (10): acknowledgeCoreActionResults(), createCoreApiClient(), createSelfMessageTracker(), executeLocalCoreActions(), flushCoreOutboundActions(), main(), normalizeMessage(), normalizeTimestamp() (+2 more)

### Community 16 - "报价解析测试"
Cohesion: 0.36
Nodes (3): _parse(), _parse_with_chat_name(), QuoteParserTests

### Community 17 - "Web 页面模板"
Cohesion: 0.42
Nodes (8): render_dashboard_page(), render_history_page(), _render_layout(), render_quote_dictionary_page(), render_quotes_page(), render_reconciliation_page(), render_role_mapping_page(), render_workbench_page()

### Community 18 - "重放与测试工具"
Cohesion: 0.32
Nodes (4): ensure_group(), _patch_transaction_by_message_id(), replay_runtime_scenario(), Shared bookkeeping core for multi-platform chat adapters.

### Community 19 - "项目文档与总览"
Cohesion: 0.32
Nodes (8): Hermes Agent, 人工差错痛点, 回溯排错能力不足, SeeSee 施工日志, SeeSee 交接文档, SeeSee PRD-lite, SeeSee 礼品卡中介系统, SeeSee TODO 清单

### Community 20 - "WeChat 演示"
Cohesion: 1.0
Nodes (0): 

### Community 21 - "WSGI 配置"
Cohesion: 1.0
Nodes (0): 

### Community 22 - "报价演示种子"
Cohesion: 1.0
Nodes (0): 

### Community 23 - "聊天上下文"
Cohesion: 1.0
Nodes (0): 

### Community 24 - "WeChat 适配启动"
Cohesion: 1.0
Nodes (0): 

### Community 25 - "核心 API 测试"
Cohesion: 1.0
Nodes (0): 

### Community 26 - "聊天上下文测试"
Cohesion: 1.0
Nodes (0): 

### Community 27 - "游戏化教学"
Cohesion: 1.0
Nodes (1): 游戏式教学 Cyber-MUD

## Knowledge Gaps
- **14 isolated node(s):** `Shared bookkeeping core for multi-platform chat adapters.`, `PostgreSQL 数据库`, `报价墙 PRD`, `报价墙 MVP 计划`, `群组固定模板解析` (+9 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `WeChat 演示`** (2 nodes): `demo_wxautox.py`, `main()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `WSGI 配置`** (2 nodes): `wsgi.py`, `_parse_master_users()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `报价演示种子`** (2 nodes): `seed_quote_demo.py`, `main()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `聊天上下文`** (2 nodes): `chat-context.ts`, `resolveChatName()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `WeChat 适配启动`** (1 nodes): `start-wechat-adapter.ps1`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `核心 API 测试`** (1 nodes): `core-api.test.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `聊天上下文测试`** (1 nodes): `chat-context.test.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `游戏化教学`** (1 nodes): `游戏式教学 Cyber-MUD`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `BookkeepingDB` connect `数据库层` to `账期管理`, `客户端运行时`, `消息合约与动作`, `分析服务`, `Web 应用测试`, `对账服务`, `消息摄入服务`, `报表服务`?**
  _High betweenness centrality (0.331) - this node is a cross-community bridge._
- **Why does `UnifiedRuntimeTests` connect `客户端运行时` to `数据库层`, `账期管理`, `报价与消息合约`, `消息合约与动作`, `命令处理器`, `核心 API 客户端`?**
  _High betweenness centrality (0.132) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `WebAppTests` (e.g. with `BookkeepingDB` and `AccountingPeriodService`) actually correct?**
  _`WebAppTests` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 11 inferred relationships involving `UnifiedRuntimeTests` (e.g. with `NormalizedMessageEnvelope` and `BookkeepingDB`) actually correct?**
  _`UnifiedRuntimeTests` has 11 INFERRED edges - model-reasoned connections that need verification._
- **Are the 24 inferred relationships involving `BookkeepingDB` (e.g. with `StructuredTransactionRecord` and `ReconciliationService`) actually correct?**
  _`BookkeepingDB` has 24 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `AnalyticsService` (e.g. with `BookkeepingDB` and `ReportingService`) actually correct?**
  _`AnalyticsService` has 7 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Shared bookkeeping core for multi-platform chat adapters.`, `PostgreSQL 数据库`, `报价墙 PRD` to the rest of the system?**
  _14 weakly-connected nodes found - possible documentation gaps or missing edges._