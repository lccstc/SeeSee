# Graph Report - .  (2026-04-12)

## Corpus Check
- 75 files · ~93,633 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1110 nodes · 2341 edges · 38 communities detected
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 201 edges (avg confidence: 0.53)
- Token cost: 0 input · 0 output

## God Nodes (most connected - your core abstractions)
1. `_BookkeepingStoreBase` - 109 edges
2. `WebAppTests` - 78 edges
3. `BookkeepingDB` - 46 edges
4. `TemplateConfig` - 44 edges
5. `_respond_json()` - 42 edges
6. `UnifiedRuntimeTests` - 40 edges
7. `AnalyticsService` - 39 edges
8. `ReconciliationService` - 31 edges
9. `CommandHandler` - 31 edges
10. `AccountingPeriodService` - 28 edges

## Surprising Connections (you probably didn't know these)
- `Fetch Binance P2P ads. Returns list of {price, nick, min, max}.` --uses--> `AccountingPeriodService`  [INFERRED]
  wxbot/bookkeeping-platform/bookkeeping_core/commands.py → wxbot/bookkeeping-platform/bookkeeping_core/periods.py
- `Fetch and display Binance P2P USDT/CNY top 10 BUY and SELL prices.` --uses--> `AccountingPeriodService`  [INFERRED]
  wxbot/bookkeeping-platform/bookkeeping_core/commands.py → wxbot/bookkeeping-platform/bookkeeping_core/periods.py
- `WeChatPlatformAPI` --uses--> `NormalizedMessageEnvelope`  [INFERRED]
  wxbot/bookkeeping-platform/wechat_adapter/client.py → wxbot/bookkeeping-platform/bookkeeping_core/contracts.py
- `WeChatCoreApiClient` --uses--> `NormalizedMessageEnvelope`  [INFERRED]
  wxbot/bookkeeping-platform/wechat_adapter/core_api.py → wxbot/bookkeeping-platform/bookkeeping_core/contracts.py
- `Auto-detect template rules from an exception's source text.` --uses--> `AnalyticsService`  [INFERRED]
  wxbot/bookkeeping-platform/bookkeeping_web/app.py → wxbot/bookkeeping-platform/bookkeeping_core/analytics.py

## Hyperedges (group relationships)
- **核心架构** — reporting_server, bookkeeping_core, bookkeeping_web, postgres_db [EXTRACTED 1.00]
- **消息适配层** — whatsapp_adapter, wechat_adapter, core_api_endpoint [EXTRACTED 1.00]

## Communities

### Community 0 - "Database Layer"
Cohesion: 0.04
Nodes (19): _append_quote_restriction(), BookkeepingDB, _BookkeepingStoreBase, is_postgres_dsn(), _normalize_quote_exception_text_for_suppression(), _parse_quote_exception_suppression_note(), _PostgresConnectionCompat, _PostgresCursorCompat (+11 more)

### Community 1 - "Template Engine Tests"
Cohesion: 0.02
Nodes (26): TemplateConfig, Data Engine v1 报价模板引擎测试。, 标注生成的 pattern 应该能反过来匹配原始文本。, 模拟完整标注流程：fields → annotations → pattern → 能匹配原始行, Real C-531 group message parsing verification., End-to-end: exception → annotate → new rule → re-parse succeeds., Multi-quote lines are auto-split and parsed as individual quotes., Lines with == should normalize to = and match as price. (+18 more)

### Community 2 - "Accounting Periods"
Cohesion: 0.04
Nodes (23): AccountingPeriodService, _build_card_stats(), _cleanup_old_backups(), _format_group_close_receipt(), _parse_db_timestamp(), _signed_amount(), _extract_search_path_schema(), PostgresTestCase (+15 more)

### Community 3 - "Web App Routes"
Cohesion: 0.07
Nodes (78): _build_quote_harvest_preview_payload(), _build_quote_result_preview_payload(), _call_optional_db_method(), create_app(), _ensure_runtime_database_is_ready(), _filter_callable_kwargs(), _group_parser_section_signature(), _handle_accounting_period_close() (+70 more)

### Community 4 - "Web App Tests"
Cohesion: 0.05
Nodes (1): WebAppTests

### Community 5 - "Quote Parsing"
Cohesion: 0.08
Nodes (50): NormalizedMessageEnvelope, _contains_price(), _count_structured_quote_lines(), _country_pair_split_pattern(), _extract_fixed_sheet_amount_price(), _extract_standalone_reply_price(), _has_quote_context_signal(), _infer_card_type() (+42 more)

### Community 6 - "Message Contracts"
Cohesion: 0.05
Nodes (26): CoreActionCollector, from_dict(), _normalized_sender_kind(), _required_text(), send_file_action(), send_text_action(), SendFileAction, SendTextAction (+18 more)

### Community 7 - "Analytics Service"
Cohesion: 0.12
Nodes (24): AnalyticsService, _attach_group_usd_amounts(), _card_rows(), _count_transactions_by_role(), _date_text(), _financial_rows(), _input_direction(), _int_or_none() (+16 more)

### Community 8 - "Template Engine Core"
Cohesion: 0.12
Nodes (47): auto_detect_line_type(), _auto_detect_normalized_line(), _build_amount_label_matcher(), build_annotations_from_fields(), _canonicalize_bracket_quote_line(), _clean_card_type(), _compile_group_parser_quote_pattern(), derive_result_template_preview() (+39 more)

### Community 9 - "Runtime Tests"
Cohesion: 0.06
Nodes (3): _FakeListenedChat, _message(), UnifiedRuntimeTests

### Community 10 - "Bot Commands"
Cohesion: 0.15
Nodes (7): CommandHandler, _fetch_binance_p2p(), _format_period_close_message(), _NullActionCollector, _parse_db_timestamp(), Fetch Binance P2P ads. Returns list of {price, nick, min, max}., Fetch and display Binance P2P USDT/CNY top 10 BUY and SELL prices.

### Community 11 - "WeChat Adapter"
Cohesion: 0.11
Nodes (17): _apply_chat_hint(), _normalize_chat_name(), prepare_runtime(), _resolve_listened_chat_name(), WeChatPlatformAPI, _clean_chat_names(), CoreApiConfig, getConfig() (+9 more)

### Community 12 - "Reconciliation"
Cohesion: 0.12
Nodes (8): _csv_number(), _expected_transaction_rmb(), _int_or_none(), _normalize_group_num(), _normalize_text(), _normalize_timestamp(), ReconciliationService, _sort_group_num()

### Community 13 - "Architecture Overview"
Cohesion: 0.07
Nodes (27): bookkeeping_core 业务核心, bookkeeping_web Web 层, POST /api/core/messages 核心入口, 阶段A 证据链, 阶段B 结构化解析, 阶段C 关联与回溯, 阶段D 差额追踪, PostgreSQL 数据库 (+19 more)

### Community 14 - "Reporting Service"
Cohesion: 0.1
Nodes (9): Auto-detect template rules from an exception's source text., Save multiple template rules to a group's config at once., ReportingService, default_business_role_for_group_num(), normalize_business_role(), resolve_business_role(), resolve_role_source(), _serialize_envelope() (+1 more)

### Community 15 - "Quote Card Demo"
Cohesion: 0.15
Nodes (18): _brand_colors(), _calc_height(), _find_font(), parse_quote_text(), QuoteBrandGroup, QuoteCard, QuoteLineItem, QuoteSubSection (+10 more)

### Community 16 - "Core API Client"
Cohesion: 0.16
Nodes (10): CoreApiClient, executeCoreActions(), isAbortError(), isRecord(), _parse_whoami_text(), safeReadText(), _validate_action(), validateCoreAction() (+2 more)

### Community 17 - "WhatsApp Client"
Cohesion: 0.14
Nodes (1): WhatsAppClient

### Community 18 - "WhatsApp Entry"
Cohesion: 0.22
Nodes (10): acknowledgeCoreActionResults(), createCoreApiClient(), createSelfMessageTracker(), executeLocalCoreActions(), flushCoreOutboundActions(), main(), normalizeMessage(), normalizeTimestamp() (+2 more)

### Community 19 - "Quote Text Demo"
Cohesion: 0.27
Nodes (11): format_a(), format_b(), format_c(), _ngn_fmt(), parse_quote_text(), QuoteBrandGroup, QuoteCard, QuoteLineItem (+3 more)

### Community 20 - "SSH/SCP Setup"
Cohesion: 0.17
Nodes (12): 常用模板, 1. 适用场景, 2. Windows 端一次性配置（管理员 PowerShell）, 3. Mac 端连通性测试, 4. 传输命令（SCP）, 5. 可选：使用 rsync（显示更详细进度）, 6. 常见问题排查, 6.1 `Operation timed out` (+4 more)

### Community 21 - "Web Pages"
Cohesion: 0.42
Nodes (8): render_dashboard_page(), render_history_page(), _render_layout(), render_quote_dictionary_page(), render_quotes_page(), render_reconciliation_page(), render_role_mapping_page(), render_workbench_page()

### Community 22 - "Replay Testing"
Cohesion: 0.32
Nodes (4): ensure_group(), _patch_transaction_by_message_id(), replay_runtime_scenario(), Shared bookkeeping core for multi-platform chat adapters.

### Community 23 - "README Startup"
Cohesion: 0.32
Nodes (8): 启动顺序, 1. `web` 可以操作，但群发没发出去, 2. WhatsApp 扫码后又掉线, 3. WeChat 能收消息，但 web 群发不落地, 启动顺序 README, Web 一键结账, 第三步：启动 WeChat 薄适配层, 第二步：启动 WhatsApp 薄适配层

### Community 24 - "Pain/SeeSee System"
Cohesion: 0.38
Nodes (7): 人工差错痛点, 回溯排错能力不足, SeeSee 施工日志, SeeSee 交接文档, SeeSee PRD-lite, SeeSee 礼品卡中介系统, SeeSee TODO 清单

### Community 25 - "Agents Config"
Cohesion: 0.33
Nodes (6): 项目性质, Core, graphify, SeeSee 项目上下文, WeChat 监听器, WhatsApp 监听器

### Community 26 - "WxAutoX Demo"
Cohesion: 1.0
Nodes (0): 

### Community 27 - "WSGI Config"
Cohesion: 1.0
Nodes (0): 

### Community 28 - "Quote Parser Test"
Cohesion: 1.0
Nodes (1): 旧测试已废弃。报价解析测试迁移到 tests/test_template_engine.py。

### Community 29 - "Seed Quote Demo"
Cohesion: 1.0
Nodes (0): 

### Community 30 - "Chat Context"
Cohesion: 1.0
Nodes (0): 

### Community 31 - "Graphify Reports"
Cohesion: 1.0
Nodes (2): Graphify Report references _BookkeepingStoreBase, Graphify Report (repo root)

### Community 32 - "WeChat Adapter Script"
Cohesion: 1.0
Nodes (0): 

### Community 33 - "Core API Test"
Cohesion: 1.0
Nodes (0): 

### Community 34 - "Chat Context Test"
Cohesion: 1.0
Nodes (0): 

### Community 35 - "WhatsApp Test"
Cohesion: 1.0
Nodes (0): 

### Community 36 - "Requirements"
Cohesion: 1.0
Nodes (1): psycopg

### Community 37 - "Graphify Platform Report"
Cohesion: 1.0
Nodes (1): Graphify Report (bookkeeping-platform)

## Knowledge Gaps
- **29 isolated node(s):** `Demo v2: Compact quote card with brand grouping.`, `A region/currency within a brand.`, `All regions under one brand.`, `Return (primary, light_bg) colors for a brand.`, `Draw right-aligned text where xy is (right_edge, top).` (+24 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `WxAutoX Demo`** (2 nodes): `demo_wxautox.py`, `main()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `WSGI Config`** (2 nodes): `wsgi.py`, `_parse_master_users()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Quote Parser Test`** (2 nodes): `test_quote_parser.py`, `旧测试已废弃。报价解析测试迁移到 tests/test_template_engine.py。`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Seed Quote Demo`** (2 nodes): `seed_quote_demo.py`, `main()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Chat Context`** (2 nodes): `chat-context.ts`, `resolveChatName()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Graphify Reports`** (2 nodes): `Graphify Report references _BookkeepingStoreBase`, `Graphify Report (repo root)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `WeChat Adapter Script`** (1 nodes): `start-wechat-adapter.ps1`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Core API Test`** (1 nodes): `core-api.test.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Chat Context Test`** (1 nodes): `chat-context.test.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `WhatsApp Test`** (1 nodes): `whatsapp.test.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Requirements`** (1 nodes): `psycopg`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Graphify Platform Report`** (1 nodes): `Graphify Report (bookkeeping-platform)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `TemplateConfig` connect `Template Engine Tests` to `Database Layer`, `Web App Tests`, `Quote Parsing`, `Message Contracts`, `Template Engine Core`, `Reporting Service`?**
  _High betweenness centrality (0.276) - this node is a cross-community bridge._
- **Why does `BookkeepingDB` connect `Database Layer` to `Template Engine Tests`, `Accounting Periods`, `Web App Tests`, `Message Contracts`, `Analytics Service`, `Reconciliation`, `Reporting Service`?**
  _High betweenness centrality (0.219) - this node is a cross-community bridge._
- **Why does `WebAppTests` connect `Web App Tests` to `Database Layer`, `Template Engine Tests`, `Accounting Periods`, `Quote Parsing`?**
  _High betweenness centrality (0.159) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `_BookkeepingStoreBase` (e.g. with `ReminderPayload` and `TemplateConfig`) actually correct?**
  _`_BookkeepingStoreBase` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `WebAppTests` (e.g. with `BookkeepingDB` and `AccountingPeriodService`) actually correct?**
  _`WebAppTests` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Are the 24 inferred relationships involving `BookkeepingDB` (e.g. with `Auto-detect template rules from an exception's source text.` and `Save multiple template rules to a group's config at once.`) actually correct?**
  _`BookkeepingDB` has 24 INFERRED edges - model-reasoned connections that need verification._
- **Are the 40 inferred relationships involving `TemplateConfig` (e.g. with `Auto-detect template rules from an exception's source text.` and `Save multiple template rules to a group's config at once.`) actually correct?**
  _`TemplateConfig` has 40 INFERRED edges - model-reasoned connections that need verification._