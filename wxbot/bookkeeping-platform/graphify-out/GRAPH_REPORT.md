# Graph Report - .  (2026-04-12)

## Corpus Check
- 43 files · ~80,561 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 973 nodes · 2199 edges · 22 communities detected
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 195 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## God Nodes (most connected - your core abstractions)
1. `_BookkeepingStoreBase` - 109 edges
2. `WebAppTests` - 78 edges
3. `UnifiedRuntimeTests` - 51 edges
4. `BookkeepingDB` - 48 edges
5. `TemplateConfig` - 44 edges
6. `_respond_json()` - 42 edges
7. `AnalyticsService` - 39 edges
8. `CommandHandler` - 33 edges
9. `ReconciliationService` - 31 edges
10. `AccountingPeriodService` - 28 edges

## Surprising Connections (you probably didn't know these)
- `Data Engine v1 报价模板引擎测试。` --uses--> `TemplateConfig`  [INFERRED]
  tests/test_template_engine.py → bookkeeping_core/template_engine.py
- `Multiple unmatched lines merge into one message-level exception.` --uses--> `TemplateConfig`  [INFERRED]
  tests/test_template_engine.py → bookkeeping_core/template_engine.py
- `模拟完整标注流程：fields → annotations → pattern → 能匹配原始行` --uses--> `TemplateConfig`  [INFERRED]
  tests/test_template_engine.py → bookkeeping_core/template_engine.py
- `Real C-531 group message parsing verification.` --uses--> `TemplateConfig`  [INFERRED]
  tests/test_template_engine.py → bookkeeping_core/template_engine.py
- `Multi-quote lines are auto-split and parsed as individual quotes.` --uses--> `TemplateConfig`  [INFERRED]
  tests/test_template_engine.py → bookkeeping_core/template_engine.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.04
Nodes (19): _append_quote_restriction(), BookkeepingDB, _BookkeepingStoreBase, is_postgres_dsn(), _normalize_quote_exception_text_for_suppression(), _parse_quote_exception_suppression_note(), _PostgresConnectionCompat, _PostgresCursorCompat (+11 more)

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
Cohesion: 0.08
Nodes (67): ParsedQuoteDocument, ParsedQuoteException, ParsedQuoteRow, auto_detect_line_type(), _auto_detect_normalized_line(), _build_amount_label_matcher(), build_annotations_from_fields(), _canonicalize_bracket_quote_line() (+59 more)

### Community 5 - "Community 5"
Cohesion: 0.05
Nodes (1): WebAppTests

### Community 6 - "Community 6"
Cohesion: 0.05
Nodes (16): _clean_chat_names(), CoreApiConfig, load_config(), save_config(), WeChatConfig, _parse_whoami_text(), _validate_action(), WeChatCoreApiClient (+8 more)

### Community 7 - "Community 7"
Cohesion: 0.05
Nodes (27): CoreActionCollector, from_dict(), _normalized_sender_kind(), NormalizedMessageEnvelope, _required_text(), send_file_action(), send_text_action(), SendFileAction (+19 more)

### Community 8 - "Community 8"
Cohesion: 0.13
Nodes (22): AnalyticsService, _attach_group_usd_amounts(), _card_rows(), _count_transactions_by_role(), _date_text(), _financial_rows(), _input_direction(), _int_or_none() (+14 more)

### Community 9 - "Community 9"
Cohesion: 0.11
Nodes (34): _contains_price(), _count_structured_quote_lines(), _country_pair_split_pattern(), _extract_fixed_sheet_amount_price(), _extract_standalone_reply_price(), _has_quote_context_signal(), _infer_card_type(), _infer_country_or_currency() (+26 more)

### Community 10 - "Community 10"
Cohesion: 0.15
Nodes (7): CommandHandler, _fetch_binance_p2p(), _format_period_close_message(), _NullActionCollector, _parse_db_timestamp(), Fetch Binance P2P ads. Returns list of {price, nick, min, max}., Fetch and display Binance P2P USDT/CNY top 10 BUY and SELL prices.

### Community 11 - "Community 11"
Cohesion: 0.12
Nodes (8): _csv_number(), _expected_transaction_rmb(), _int_or_none(), _normalize_group_num(), _normalize_text(), _normalize_timestamp(), ReconciliationService, _sort_group_num()

### Community 12 - "Community 12"
Cohesion: 0.1
Nodes (9): Auto-detect template rules from an exception's source text., Save multiple template rules to a group's config at once., ReportingService, default_business_role_for_group_num(), normalize_business_role(), resolve_business_role(), resolve_role_source(), _serialize_envelope() (+1 more)

### Community 13 - "Community 13"
Cohesion: 0.2
Nodes (5): _apply_chat_hint(), _normalize_chat_name(), prepare_runtime(), _resolve_listened_chat_name(), WeChatPlatformAPI

### Community 14 - "Community 14"
Cohesion: 0.1
Nodes (3): Lines with == should normalize to = and match as price., e.g. 美金USD:5.20, 欧元EUR:6.00, TestAutoDetect

### Community 15 - "Community 15"
Cohesion: 0.13
Nodes (11): main(), _parse_master_users(), _ReportingRequestHandler, _ReportingServerHandler, _resolve_db_target(), _ThreadingWSGIServer, ServerHandler, ReportingServerTests (+3 more)

### Community 16 - "Community 16"
Cohesion: 0.42
Nodes (8): render_dashboard_page(), render_history_page(), _render_layout(), render_quote_dictionary_page(), render_quotes_page(), render_reconciliation_page(), render_role_mapping_page(), render_workbench_page()

### Community 17 - "Community 17"
Cohesion: 0.32
Nodes (4): ensure_group(), _patch_transaction_by_message_id(), replay_runtime_scenario(), Shared bookkeeping core for multi-platform chat adapters.

### Community 18 - "Community 18"
Cohesion: 1.0
Nodes (0): 

### Community 19 - "Community 19"
Cohesion: 1.0
Nodes (1): 旧测试已废弃。报价解析测试迁移到 tests/test_template_engine.py。

### Community 20 - "Community 20"
Cohesion: 1.0
Nodes (0): 

### Community 21 - "Community 21"
Cohesion: 1.0
Nodes (0): 

## Knowledge Gaps
- **2 isolated node(s):** `Shared bookkeeping core for multi-platform chat adapters.`, `旧测试已废弃。报价解析测试迁移到 tests/test_template_engine.py。`
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 18`** (2 nodes): `wsgi.py`, `_parse_master_users()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 19`** (2 nodes): `test_quote_parser.py`, `旧测试已废弃。报价解析测试迁移到 tests/test_template_engine.py。`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 20`** (2 nodes): `seed_quote_demo.py`, `main()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 21`** (1 nodes): `start-wechat-adapter.ps1`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `TemplateConfig` connect `Community 4` to `Community 0`, `Community 2`, `Community 5`, `Community 7`, `Community 9`, `Community 12`, `Community 14`?**
  _High betweenness centrality (0.340) - this node is a cross-community bridge._
- **Why does `BookkeepingDB` connect `Community 0` to `Community 1`, `Community 4`, `Community 5`, `Community 6`, `Community 7`, `Community 8`, `Community 11`, `Community 12`?**
  _High betweenness centrality (0.328) - this node is a cross-community bridge._
- **Why does `_BookkeepingStoreBase` connect `Community 0` to `Community 4`, `Community 7`?**
  _High betweenness centrality (0.185) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `_BookkeepingStoreBase` (e.g. with `ReminderPayload` and `TemplateConfig`) actually correct?**
  _`_BookkeepingStoreBase` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `WebAppTests` (e.g. with `BookkeepingDB` and `AccountingPeriodService`) actually correct?**
  _`WebAppTests` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Are the 11 inferred relationships involving `UnifiedRuntimeTests` (e.g. with `NormalizedMessageEnvelope` and `BookkeepingDB`) actually correct?**
  _`UnifiedRuntimeTests` has 11 INFERRED edges - model-reasoned connections that need verification._
- **Are the 26 inferred relationships involving `BookkeepingDB` (e.g. with `Auto-detect template rules from an exception's source text.` and `Save multiple template rules to a group's config at once.`) actually correct?**
  _`BookkeepingDB` has 26 INFERRED edges - model-reasoned connections that need verification._