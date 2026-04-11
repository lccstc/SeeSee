# Graph Report - wxbot/bookkeeping-platform  (2026-04-10)

## Corpus Check
- 43 files · ~63,442 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 849 nodes · 1739 edges · 23 communities detected
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## God Nodes (most connected - your core abstractions)
1. `_BookkeepingStoreBase` - 99 edges
2. `WebAppTests` - 53 edges
3. `_respond_json()` - 39 edges
4. `UnifiedRuntimeTests` - 39 edges
5. `AnalyticsService` - 30 edges
6. `CommandHandler` - 28 edges
7. `ReconciliationService` - 27 edges
8. `BookkeepingDB` - 22 edges
9. `_read_json_body()` - 21 edges
10. `_read_query_params()` - 17 edges

## Surprising Connections (you probably didn't know these)
- `UnifiedRuntimeTests` --inherits--> `PostgresTestCase`  [EXTRACTED]
  /Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/tests/test_runtime.py →   _Bridges community 1 → community 8_
- `WebAppTests` --inherits--> `PostgresTestCase`  [EXTRACTED]
  /Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/tests/test_webapp.py →   _Bridges community 1 → community 5_

## Communities

### Community 0 - "Community 0"
Cohesion: 0.04
Nodes (19): _append_quote_restriction(), BookkeepingDB, _BookkeepingStoreBase, is_postgres_dsn(), _PostgresConnectionCompat, _PostgresCursorCompat, _quote_amount_bounds(), _quote_amount_display() (+11 more)

### Community 1 - "Community 1"
Cohesion: 0.03
Nodes (18): PostgresTestCase, DashboardAnalyticsTests, HistoryAnalyticsTests, KnifeNettingAnalyticsTests, _make_tx(), MockReplayWorkbenchTests, _set_transaction_fields(), WorkbenchAnalyticsTests (+10 more)

### Community 2 - "Community 2"
Cohesion: 0.07
Nodes (72): _build_quote_harvest_preview_payload(), _call_optional_db_method(), create_app(), _ensure_runtime_database_is_ready(), _filter_callable_kwargs(), _handle_accounting_period_close(), _handle_accounting_period_settle_all(), _handle_accounting_periods() (+64 more)

### Community 3 - "Community 3"
Cohesion: 0.03
Nodes (21): Data Engine v1 报价模板引擎测试。, 标注生成的 pattern 应该能反过来匹配原始文本。, 模拟完整标注流程：fields → annotations → pattern → 能匹配原始行, Real C-531 group message parsing verification., End-to-end: exception → annotate → new rule → re-parse succeeds., Multi-quote lines are auto-split and parsed as individual quotes., Lines with == should normalize to = and match as price., e.g. 美金USD:5.20, 欧元EUR:6.00 (+13 more)

### Community 4 - "Community 4"
Cohesion: 0.05
Nodes (24): CoreActionCollector, from_dict(), _normalized_sender_kind(), NormalizedMessageEnvelope, _required_text(), send_file_action(), send_text_action(), SendFileAction (+16 more)

### Community 5 - "Community 5"
Cohesion: 0.07
Nodes (1): WebAppTests

### Community 6 - "Community 6"
Cohesion: 0.13
Nodes (22): AnalyticsService, _attach_group_usd_amounts(), _card_rows(), _count_transactions_by_role(), _date_text(), _financial_rows(), _input_direction(), _int_or_none() (+14 more)

### Community 7 - "Community 7"
Cohesion: 0.09
Nodes (18): _apply_chat_hint(), _normalize_chat_name(), prepare_runtime(), _resolve_listened_chat_name(), WeChatPlatformAPI, _clean_chat_names(), CoreApiConfig, load_config() (+10 more)

### Community 8 - "Community 8"
Cohesion: 0.06
Nodes (3): _FakeListenedChat, _message(), UnifiedRuntimeTests

### Community 9 - "Community 9"
Cohesion: 0.1
Nodes (31): _contains_price(), _country_pair_split_pattern(), _extract_fixed_sheet_amount_price(), _extract_standalone_reply_price(), _infer_card_type(), _infer_country_or_currency(), _infer_country_or_currency_candidates(), _infer_dictionary_alias() (+23 more)

### Community 10 - "Community 10"
Cohesion: 0.12
Nodes (8): _csv_number(), _expected_transaction_rmb(), _int_or_none(), _normalize_group_num(), _normalize_text(), _normalize_timestamp(), ReconciliationService, _sort_group_num()

### Community 11 - "Community 11"
Cohesion: 0.17
Nodes (4): CommandHandler, _format_period_close_message(), _NullActionCollector, _parse_db_timestamp()

### Community 12 - "Community 12"
Cohesion: 0.11
Nodes (27): auto_detect_line_type(), build_annotations_from_fields(), _clean_card_type(), deduplicate_rules(), derive_strict_section_preview(), generate_strict_pattern_from_annotations(), looks_like_quote_line(), match_pattern() (+19 more)

### Community 13 - "Community 13"
Cohesion: 0.16
Nodes (5): ReportingService, default_business_role_for_group_num(), normalize_business_role(), resolve_business_role(), resolve_role_source()

### Community 14 - "Community 14"
Cohesion: 0.13
Nodes (11): main(), _parse_master_users(), _ReportingRequestHandler, _ReportingServerHandler, _resolve_db_target(), _ThreadingWSGIServer, ServerHandler, ReportingServerTests (+3 more)

### Community 15 - "Community 15"
Cohesion: 0.24
Nodes (6): AccountingPeriodService, _build_card_stats(), _cleanup_old_backups(), _format_group_close_receipt(), _parse_db_timestamp(), _signed_amount()

### Community 16 - "Community 16"
Cohesion: 0.29
Nodes (2): _extract_search_path_schema(), PostgresTestCase

### Community 17 - "Community 17"
Cohesion: 0.42
Nodes (8): render_dashboard_page(), render_history_page(), _render_layout(), render_quote_dictionary_page(), render_quotes_page(), render_reconciliation_page(), render_role_mapping_page(), render_workbench_page()

### Community 18 - "Community 18"
Cohesion: 0.32
Nodes (4): ensure_group(), _patch_transaction_by_message_id(), replay_runtime_scenario(), Shared bookkeeping core for multi-platform chat adapters.

### Community 19 - "Community 19"
Cohesion: 1.0
Nodes (0): 

### Community 20 - "Community 20"
Cohesion: 1.0
Nodes (1): 旧测试已废弃。报价解析测试迁移到 tests/test_template_engine.py。

### Community 21 - "Community 21"
Cohesion: 1.0
Nodes (0): 

### Community 22 - "Community 22"
Cohesion: 1.0
Nodes (0): 

## Knowledge Gaps
- **33 isolated node(s):** `Shared bookkeeping core for multi-platform chat adapters.`, `Auto-detect template rules from an exception's source text.`, `Save multiple template rules to a group's config at once.`, `ParsedTransaction`, `ReminderPayload` (+28 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 19`** (2 nodes): `wsgi.py`, `_parse_master_users()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 20`** (2 nodes): `test_quote_parser.py`, `旧测试已废弃。报价解析测试迁移到 tests/test_template_engine.py。`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 21`** (2 nodes): `seed_quote_demo.py`, `main()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 22`** (1 nodes): `start-wechat-adapter.ps1`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What connects `Shared bookkeeping core for multi-platform chat adapters.`, `Auto-detect template rules from an exception's source text.`, `Save multiple template rules to a group's config at once.` to the rest of the system?**
  _33 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.04 - nodes in this community are weakly interconnected._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.03 - nodes in this community are weakly interconnected._
- **Should `Community 2` be split into smaller, more focused modules?**
  _Cohesion score 0.07 - nodes in this community are weakly interconnected._
- **Should `Community 3` be split into smaller, more focused modules?**
  _Cohesion score 0.03 - nodes in this community are weakly interconnected._
- **Should `Community 4` be split into smaller, more focused modules?**
  _Cohesion score 0.05 - nodes in this community are weakly interconnected._
- **Should `Community 5` be split into smaller, more focused modules?**
  _Cohesion score 0.07 - nodes in this community are weakly interconnected._