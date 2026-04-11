# Graph Report - .  (2026-04-12)

## Corpus Check
- 54 files · ~96,281 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1048 nodes · 2272 edges · 32 communities detected
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 171 edges (avg confidence: 0.5)
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
9. `CommandHandler` - 30 edges
10. `AccountingPeriodService` - 26 edges

## Surprising Connections (you probably didn't know these)
- `Data Engine v1 报价模板引擎测试。` --uses--> `TemplateConfig`  [INFERRED]
  wxbot/bookkeeping-platform/tests/test_template_engine.py → wxbot/bookkeeping-platform/bookkeeping_core/template_engine.py
- `Multiple unmatched lines merge into one message-level exception.` --uses--> `TemplateConfig`  [INFERRED]
  wxbot/bookkeeping-platform/tests/test_template_engine.py → wxbot/bookkeeping-platform/bookkeeping_core/template_engine.py
- `模拟完整标注流程：fields → annotations → pattern → 能匹配原始行` --uses--> `TemplateConfig`  [INFERRED]
  wxbot/bookkeeping-platform/tests/test_template_engine.py → wxbot/bookkeeping-platform/bookkeeping_core/template_engine.py
- `Real C-531 group message parsing verification.` --uses--> `TemplateConfig`  [INFERRED]
  wxbot/bookkeeping-platform/tests/test_template_engine.py → wxbot/bookkeeping-platform/bookkeeping_core/template_engine.py
- `Multi-quote lines are auto-split and parsed as individual quotes.` --uses--> `TemplateConfig`  [INFERRED]
  wxbot/bookkeeping-platform/tests/test_template_engine.py → wxbot/bookkeeping-platform/bookkeeping_core/template_engine.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.04
Nodes (22): _append_quote_restriction(), BookkeepingDB, _BookkeepingStoreBase, is_postgres_dsn(), _normalize_quote_exception_text_for_suppression(), _parse_quote_exception_suppression_note(), _PostgresConnectionCompat, _PostgresCursorCompat (+14 more)

### Community 1 - "Community 1"
Cohesion: 0.04
Nodes (23): AccountingPeriodService, _build_card_stats(), _cleanup_old_backups(), _format_group_close_receipt(), _parse_db_timestamp(), _signed_amount(), _extract_search_path_schema(), PostgresTestCase (+15 more)

### Community 2 - "Community 2"
Cohesion: 0.02
Nodes (18): Data Engine v1 报价模板引擎测试。, 模拟完整标注流程：fields → annotations → pattern → 能匹配原始行, Real C-531 group message parsing verification., Multi-quote lines are auto-split and parsed as individual quotes., Multiple unmatched lines merge into one message-level exception., TestBuildAnnotations, TestC531RealData, TestCleanCardType (+10 more)

### Community 3 - "Community 3"
Cohesion: 0.07
Nodes (78): _build_quote_harvest_preview_payload(), _build_quote_result_preview_payload(), _call_optional_db_method(), create_app(), _ensure_runtime_database_is_ready(), _filter_callable_kwargs(), _group_parser_section_signature(), _handle_accounting_period_close() (+70 more)

### Community 4 - "Community 4"
Cohesion: 0.06
Nodes (59): Auto-detect template rules from an exception's source text., Save multiple template rules to a group's config at once., NormalizedMessageEnvelope, _contains_price(), _count_structured_quote_lines(), _country_pair_split_pattern(), _extract_fixed_sheet_amount_price(), _extract_standalone_reply_price() (+51 more)

### Community 5 - "Community 5"
Cohesion: 0.05
Nodes (1): WebAppTests

### Community 6 - "Community 6"
Cohesion: 0.06
Nodes (23): CoreActionCollector, from_dict(), _normalized_sender_kind(), _required_text(), send_file_action(), send_text_action(), SendFileAction, SendTextAction (+15 more)

### Community 7 - "Community 7"
Cohesion: 0.13
Nodes (22): AnalyticsService, _attach_group_usd_amounts(), _card_rows(), _count_transactions_by_role(), _date_text(), _financial_rows(), _input_direction(), _int_or_none() (+14 more)

### Community 8 - "Community 8"
Cohesion: 0.12
Nodes (47): auto_detect_line_type(), _auto_detect_normalized_line(), _build_amount_label_matcher(), build_annotations_from_fields(), _canonicalize_bracket_quote_line(), _clean_card_type(), _compile_group_parser_quote_pattern(), derive_result_template_preview() (+39 more)

### Community 9 - "Community 9"
Cohesion: 0.06
Nodes (3): _FakeListenedChat, _message(), UnifiedRuntimeTests

### Community 10 - "Community 10"
Cohesion: 0.11
Nodes (17): _apply_chat_hint(), _normalize_chat_name(), prepare_runtime(), _resolve_listened_chat_name(), WeChatPlatformAPI, _clean_chat_names(), CoreApiConfig, getConfig() (+9 more)

### Community 11 - "Community 11"
Cohesion: 0.12
Nodes (8): _csv_number(), _expected_transaction_rmb(), _int_or_none(), _normalize_group_num(), _normalize_text(), _normalize_timestamp(), ReconciliationService, _sort_group_num()

### Community 12 - "Community 12"
Cohesion: 0.17
Nodes (4): CommandHandler, _format_period_close_message(), _NullActionCollector, _parse_db_timestamp()

### Community 13 - "Community 13"
Cohesion: 0.1
Nodes (3): Lines with == should normalize to = and match as price., e.g. 美金USD:5.20, 欧元EUR:6.00, TestAutoDetect

### Community 14 - "Community 14"
Cohesion: 0.16
Nodes (5): ReportingService, default_business_role_for_group_num(), normalize_business_role(), resolve_business_role(), resolve_role_source()

### Community 15 - "Community 15"
Cohesion: 0.16
Nodes (10): CoreApiClient, executeCoreActions(), isAbortError(), isRecord(), _parse_whoami_text(), safeReadText(), _validate_action(), validateCoreAction() (+2 more)

### Community 16 - "Community 16"
Cohesion: 0.13
Nodes (11): main(), _parse_master_users(), _ReportingRequestHandler, _ReportingServerHandler, _resolve_db_target(), _ThreadingWSGIServer, ServerHandler, ReportingServerTests (+3 more)

### Community 17 - "Community 17"
Cohesion: 0.18
Nodes (15): _brand_colors(), _calc_height(), _find_font(), parse_quote_text(), QuoteBrandGroup, QuoteCard, QuoteLineItem, QuoteSubSection (+7 more)

### Community 18 - "Community 18"
Cohesion: 0.14
Nodes (1): WhatsAppClient

### Community 19 - "Community 19"
Cohesion: 0.22
Nodes (10): acknowledgeCoreActionResults(), createCoreApiClient(), createSelfMessageTracker(), executeLocalCoreActions(), flushCoreOutboundActions(), main(), normalizeMessage(), normalizeTimestamp() (+2 more)

### Community 20 - "Community 20"
Cohesion: 0.27
Nodes (11): format_a(), format_b(), format_c(), _ngn_fmt(), parse_quote_text(), QuoteBrandGroup, QuoteCard, QuoteLineItem (+3 more)

### Community 21 - "Community 21"
Cohesion: 0.42
Nodes (8): render_dashboard_page(), render_history_page(), _render_layout(), render_quote_dictionary_page(), render_quotes_page(), render_reconciliation_page(), render_role_mapping_page(), render_workbench_page()

### Community 22 - "Community 22"
Cohesion: 0.32
Nodes (4): ensure_group(), _patch_transaction_by_message_id(), replay_runtime_scenario(), Shared bookkeeping core for multi-platform chat adapters.

### Community 23 - "Community 23"
Cohesion: 1.0
Nodes (0): 

### Community 24 - "Community 24"
Cohesion: 1.0
Nodes (0): 

### Community 25 - "Community 25"
Cohesion: 1.0
Nodes (1): 旧测试已废弃。报价解析测试迁移到 tests/test_template_engine.py。

### Community 26 - "Community 26"
Cohesion: 1.0
Nodes (0): 

### Community 27 - "Community 27"
Cohesion: 1.0
Nodes (0): 

### Community 28 - "Community 28"
Cohesion: 1.0
Nodes (0): 

### Community 29 - "Community 29"
Cohesion: 1.0
Nodes (0): 

### Community 30 - "Community 30"
Cohesion: 1.0
Nodes (0): 

### Community 31 - "Community 31"
Cohesion: 1.0
Nodes (0): 

## Knowledge Gaps
- **9 isolated node(s):** `Demo v2: Compact quote card with brand grouping.`, `A region/currency within a brand.`, `All regions under one brand.`, `Return (primary, light_bg) colors for a brand.`, `Draw right-aligned text where xy is (right_edge, top).` (+4 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 23`** (2 nodes): `demo_wxautox.py`, `main()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 24`** (2 nodes): `wsgi.py`, `_parse_master_users()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 25`** (2 nodes): `test_quote_parser.py`, `旧测试已废弃。报价解析测试迁移到 tests/test_template_engine.py。`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 26`** (2 nodes): `seed_quote_demo.py`, `main()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 27`** (2 nodes): `chat-context.ts`, `resolveChatName()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 28`** (1 nodes): `start-wechat-adapter.ps1`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 29`** (1 nodes): `core-api.test.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 30`** (1 nodes): `chat-context.test.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 31`** (1 nodes): `whatsapp.test.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `TemplateConfig` connect `Community 4` to `Community 0`, `Community 2`, `Community 5`, `Community 8`, `Community 13`?**
  _High betweenness centrality (0.297) - this node is a cross-community bridge._
- **Why does `BookkeepingDB` connect `Community 0` to `Community 1`, `Community 4`, `Community 5`, `Community 6`, `Community 7`, `Community 11`, `Community 14`?**
  _High betweenness centrality (0.227) - this node is a cross-community bridge._
- **Why does `WebAppTests` connect `Community 5` to `Community 0`, `Community 1`, `Community 4`?**
  _High betweenness centrality (0.172) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `_BookkeepingStoreBase` (e.g. with `ReminderPayload` and `TemplateConfig`) actually correct?**
  _`_BookkeepingStoreBase` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `WebAppTests` (e.g. with `BookkeepingDB` and `AccountingPeriodService`) actually correct?**
  _`WebAppTests` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Are the 24 inferred relationships involving `BookkeepingDB` (e.g. with `Auto-detect template rules from an exception's source text.` and `Save multiple template rules to a group's config at once.`) actually correct?**
  _`BookkeepingDB` has 24 INFERRED edges - model-reasoned connections that need verification._
- **Are the 40 inferred relationships involving `TemplateConfig` (e.g. with `Auto-detect template rules from an exception's source text.` and `Save multiple template rules to a group's config at once.`) actually correct?**
  _`TemplateConfig` has 40 INFERRED edges - model-reasoned connections that need verification._