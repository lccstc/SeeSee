CREATE TABLE IF NOT EXISTS transactions (
  id BIGSERIAL PRIMARY KEY,
  platform TEXT NOT NULL,
  group_key TEXT NOT NULL,
  group_num INTEGER,
  chat_id TEXT NOT NULL,
  chat_name TEXT NOT NULL,
  sender_id TEXT NOT NULL,
  sender_name TEXT NOT NULL,
  message_id TEXT,
  input_sign INTEGER NOT NULL,
  amount NUMERIC(18, 4) NOT NULL,
  category TEXT NOT NULL,
  rate NUMERIC(18, 6),
  rmb_value NUMERIC(18, 4) NOT NULL,
  raw TEXT NOT NULL,
  ngn_rate NUMERIC(18, 6),
  usd_amount NUMERIC(18, 4),
  unit_face_value NUMERIC(18, 6),
  unit_count NUMERIC(18, 6),
  parse_version TEXT NOT NULL DEFAULT '1',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  deleted INTEGER NOT NULL DEFAULT 0,
  settled INTEGER NOT NULL DEFAULT 0,
  settled_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS accounting_periods (
  id BIGSERIAL PRIMARY KEY,
  start_at TIMESTAMP NOT NULL,
  end_at TIMESTAMP NOT NULL,
  closed_at TIMESTAMP NOT NULL,
  closed_by TEXT NOT NULL,
  note TEXT,
  has_adjustment INTEGER NOT NULL DEFAULT 0,
  snapshot_version INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS period_group_snapshots (
  id BIGSERIAL PRIMARY KEY,
  period_id BIGINT NOT NULL,
  group_key TEXT NOT NULL,
  platform TEXT NOT NULL,
  chat_name TEXT NOT NULL,
  group_num INTEGER,
  business_role TEXT,
  opening_balance NUMERIC(18, 4) NOT NULL DEFAULT 0,
  income NUMERIC(18, 4) NOT NULL DEFAULT 0,
  expense NUMERIC(18, 4) NOT NULL DEFAULT 0,
  closing_balance NUMERIC(18, 4) NOT NULL DEFAULT 0,
  transaction_count INTEGER NOT NULL DEFAULT 0,
  anomaly_flags_json TEXT NOT NULL DEFAULT '[]',
  UNIQUE (period_id, group_key)
);

CREATE TABLE IF NOT EXISTS period_card_stats (
  id BIGSERIAL PRIMARY KEY,
  period_id BIGINT NOT NULL,
  group_key TEXT NOT NULL,
  business_role TEXT,
  card_type TEXT NOT NULL,
  usd_amount NUMERIC(18, 4) NOT NULL DEFAULT 0,
  rate NUMERIC(18, 6),
  rmb_amount NUMERIC(18, 4) NOT NULL DEFAULT 0,
  unit_face_value NUMERIC(18, 6),
  unit_count NUMERIC(18, 6),
  sample_raw TEXT
);

CREATE TABLE IF NOT EXISTS groups (
  group_key TEXT PRIMARY KEY,
  platform TEXT NOT NULL,
  chat_id TEXT NOT NULL,
  chat_name TEXT NOT NULL,
  group_num INTEGER,
  business_role TEXT,
  role_source TEXT,
  capture_enabled INTEGER NOT NULL DEFAULT 1,
  status TEXT NOT NULL DEFAULT 'active',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS settings (
  key TEXT PRIMARY KEY,
  value TEXT,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS whitelist (
  user_key TEXT PRIMARY KEY,
  added_by TEXT NOT NULL,
  added_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  note TEXT
);

CREATE TABLE IF NOT EXISTS admins (
  user_key TEXT PRIMARY KEY,
  added_by TEXT NOT NULL,
  added_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  note TEXT
);

CREATE TABLE IF NOT EXISTS reminders (
  id BIGSERIAL PRIMARY KEY,
  platform TEXT NOT NULL,
  chat_id TEXT NOT NULL,
  sender_id TEXT NOT NULL,
  message TEXT NOT NULL,
  amount NUMERIC(18, 4) NOT NULL,
  category TEXT NOT NULL,
  rate NUMERIC(18, 6),
  rmb_value NUMERIC(18, 4) NOT NULL,
  ngn_value NUMERIC(18, 4),
  duration_minutes INTEGER NOT NULL DEFAULT 0,
  remind_at TIMESTAMP NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  sent INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS identity_bindings (
  platform TEXT NOT NULL,
  chat_id TEXT NOT NULL,
  observed_key TEXT NOT NULL,
  canonical_id TEXT NOT NULL,
  observed_name TEXT,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (platform, chat_id, observed_key)
);

CREATE TABLE IF NOT EXISTS manual_adjustments (
  id BIGSERIAL PRIMARY KEY,
  period_id BIGINT NOT NULL,
  group_key TEXT NOT NULL,
  opening_delta NUMERIC(18, 4) NOT NULL DEFAULT 0,
  income_delta NUMERIC(18, 4) NOT NULL DEFAULT 0,
  expense_delta NUMERIC(18, 4) NOT NULL DEFAULT 0,
  closing_delta NUMERIC(18, 4) NOT NULL DEFAULT 0,
  note TEXT NOT NULL,
  created_by TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS finance_adjustment_entries (
  id BIGSERIAL PRIMARY KEY,
  period_id BIGINT,
  linked_transaction_id BIGINT,
  group_key TEXT NOT NULL,
  business_role TEXT,
  card_type TEXT NOT NULL,
  usd_amount NUMERIC(18, 4) NOT NULL DEFAULT 0,
  rate NUMERIC(18, 6),
  rmb_amount NUMERIC(18, 4) NOT NULL,
  note TEXT NOT NULL,
  created_by TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS group_combinations (
  id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  note TEXT,
  created_by TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS group_combination_items (
  combination_id BIGINT NOT NULL,
  group_num INTEGER NOT NULL,
  PRIMARY KEY (combination_id, group_num)
);

CREATE TABLE IF NOT EXISTS ingested_events (
  event_id TEXT PRIMARY KEY,
  event_type TEXT NOT NULL,
  platform TEXT NOT NULL,
  source_machine TEXT NOT NULL,
  schema_version INTEGER NOT NULL,
  occurred_at TIMESTAMP NOT NULL,
  ingested_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS incoming_messages (
  id BIGSERIAL PRIMARY KEY,
  platform TEXT NOT NULL,
  group_key TEXT NOT NULL,
  chat_id TEXT NOT NULL,
  chat_name TEXT NOT NULL,
  message_id TEXT NOT NULL,
  is_group INTEGER NOT NULL DEFAULT 0,
  sender_id TEXT NOT NULL,
  sender_name TEXT NOT NULL,
  sender_kind TEXT NOT NULL DEFAULT 'user',
  content_type TEXT NOT NULL DEFAULT 'text',
  text TEXT,
  from_self INTEGER NOT NULL DEFAULT 0,
  received_at TIMESTAMP,
  raw_json TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (platform, chat_id, message_id)
);

CREATE INDEX IF NOT EXISTS idx_tx_group_key ON transactions(group_key, deleted);
CREATE INDEX IF NOT EXISTS idx_tx_platform_group ON transactions(platform, group_key, deleted);
CREATE INDEX IF NOT EXISTS idx_tx_settled ON transactions(group_key, settled, deleted);
CREATE INDEX IF NOT EXISTS idx_groups_num ON groups(group_num);
CREATE INDEX IF NOT EXISTS idx_manual_adjustments_period ON manual_adjustments(period_id, group_key);
CREATE INDEX IF NOT EXISTS idx_finance_adjustments_period ON finance_adjustment_entries(period_id, created_at);
CREATE INDEX IF NOT EXISTS idx_finance_adjustments_group ON finance_adjustment_entries(group_key, created_at);
CREATE INDEX IF NOT EXISTS idx_ingested_events_platform ON ingested_events(platform, occurred_at);
CREATE INDEX IF NOT EXISTS idx_incoming_messages_group_created ON incoming_messages(group_key, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_incoming_messages_chat_received ON incoming_messages(platform, chat_id, received_at DESC);

CREATE TABLE IF NOT EXISTS message_parse_results (
  id BIGSERIAL PRIMARY KEY,
  platform TEXT NOT NULL,
  chat_id TEXT NOT NULL,
  message_id TEXT NOT NULL,
  classification TEXT NOT NULL,
  parse_status TEXT NOT NULL,
  raw_text TEXT,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (platform, chat_id, message_id)
);

CREATE INDEX IF NOT EXISTS idx_message_parse_results_created ON message_parse_results(created_at DESC);

CREATE TABLE IF NOT EXISTS quote_documents (
  id BIGSERIAL PRIMARY KEY,
  platform TEXT NOT NULL,
  source_group_key TEXT NOT NULL,
  chat_id TEXT NOT NULL,
  chat_name TEXT NOT NULL,
  message_id TEXT NOT NULL,
  source_name TEXT NOT NULL,
  sender_id TEXT NOT NULL,
  raw_text TEXT NOT NULL,
  message_time TIMESTAMP NOT NULL,
  parser_kind TEXT NOT NULL DEFAULT 'unknown',
  parser_template TEXT NOT NULL,
  parser_version TEXT NOT NULL,
  confidence NUMERIC(6, 4) NOT NULL,
  parse_status TEXT NOT NULL,
  message_fingerprint TEXT NOT NULL DEFAULT '',
  snapshot_hypothesis TEXT NOT NULL DEFAULT 'unresolved',
  snapshot_hypothesis_reason TEXT NOT NULL DEFAULT '',
  rejection_reasons_json JSONB NOT NULL DEFAULT '[]'::jsonb,
  run_kind TEXT NOT NULL DEFAULT 'runtime',
  replay_of_quote_document_id BIGINT REFERENCES quote_documents(id) ON DELETE SET NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (platform, chat_id, message_id)
);

CREATE TABLE IF NOT EXISTS quote_snapshot_decisions (
  id BIGSERIAL PRIMARY KEY,
  quote_document_id BIGINT NOT NULL UNIQUE REFERENCES quote_documents(id) ON DELETE CASCADE,
  system_hypothesis TEXT NOT NULL DEFAULT 'unresolved',
  hypothesis_reason TEXT NOT NULL DEFAULT '',
  hypothesis_evidence_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  resolved_decision TEXT NOT NULL DEFAULT 'unresolved',
  decision_source TEXT NOT NULL DEFAULT 'system',
  confirmed_by TEXT NOT NULL DEFAULT '',
  confirmed_at TIMESTAMP,
  decision_note TEXT NOT NULL DEFAULT '',
  decision_history_json JSONB NOT NULL DEFAULT '[]'::jsonb,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS quote_candidate_rows (
  id BIGSERIAL PRIMARY KEY,
  quote_document_id BIGINT NOT NULL REFERENCES quote_documents(id) ON DELETE CASCADE,
  row_ordinal INTEGER NOT NULL,
  source_line TEXT NOT NULL,
  source_line_index INTEGER,
  line_confidence NUMERIC(6, 4) NOT NULL,
  normalized_sku_key TEXT NOT NULL,
  normalization_status TEXT NOT NULL,
  row_publishable BOOLEAN NOT NULL DEFAULT FALSE,
  publishability_basis TEXT NOT NULL,
  restriction_parse_status TEXT NOT NULL,
  card_type TEXT,
  country_or_currency TEXT,
  amount_range TEXT,
  multiplier TEXT,
  form_factor TEXT,
  price NUMERIC(18, 6),
  quote_status TEXT NOT NULL,
  restriction_text TEXT NOT NULL DEFAULT '',
  field_sources_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  rejection_reasons_json JSONB NOT NULL DEFAULT '[]'::jsonb,
  parser_template TEXT NOT NULL,
  parser_version TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (quote_document_id, row_ordinal)
);

CREATE TABLE IF NOT EXISTS quote_validation_runs (
  id BIGSERIAL PRIMARY KEY,
  quote_document_id BIGINT NOT NULL REFERENCES quote_documents(id) ON DELETE CASCADE,
  validator_version TEXT NOT NULL,
  run_kind TEXT NOT NULL DEFAULT 'runtime',
  message_decision TEXT NOT NULL,
  validation_status TEXT NOT NULL,
  candidate_row_count INTEGER NOT NULL DEFAULT 0,
  publishable_row_count INTEGER NOT NULL DEFAULT 0,
  rejected_row_count INTEGER NOT NULL DEFAULT 0,
  held_row_count INTEGER NOT NULL DEFAULT 0,
  summary_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS quote_validation_row_results (
  id BIGSERIAL PRIMARY KEY,
  validation_run_id BIGINT NOT NULL REFERENCES quote_validation_runs(id) ON DELETE CASCADE,
  quote_candidate_row_id BIGINT NOT NULL REFERENCES quote_candidate_rows(id) ON DELETE CASCADE,
  row_ordinal INTEGER NOT NULL,
  schema_status TEXT NOT NULL,
  business_status TEXT NOT NULL,
  final_decision TEXT NOT NULL,
  decision_basis TEXT NOT NULL,
  rejection_reasons_json JSONB NOT NULL DEFAULT '[]'::jsonb,
  hold_reasons_json JSONB NOT NULL DEFAULT '[]'::jsonb,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (validation_run_id, quote_candidate_row_id)
);

CREATE TABLE IF NOT EXISTS quote_price_rows (
  id BIGSERIAL PRIMARY KEY,
  quote_document_id BIGINT NOT NULL,
  platform TEXT NOT NULL,
  source_group_key TEXT NOT NULL,
  chat_id TEXT NOT NULL,
  chat_name TEXT NOT NULL,
  message_id TEXT NOT NULL,
  source_name TEXT NOT NULL,
  sender_id TEXT NOT NULL,
  card_type TEXT NOT NULL,
  country_or_currency TEXT NOT NULL,
  amount_range TEXT NOT NULL,
  multiplier TEXT,
  form_factor TEXT NOT NULL,
  price NUMERIC(18, 6) NOT NULL,
  quote_status TEXT NOT NULL,
  restriction_text TEXT NOT NULL DEFAULT '',
  source_line TEXT NOT NULL,
  raw_text TEXT NOT NULL,
  message_time TIMESTAMP NOT NULL,
  effective_at TIMESTAMP NOT NULL,
  expires_at TIMESTAMP,
  parser_template TEXT NOT NULL,
  parser_version TEXT NOT NULL,
  confidence NUMERIC(6, 4) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_quote_price_rows_active
  ON quote_price_rows(card_type, country_or_currency, amount_range, multiplier, form_factor, effective_at DESC);

CREATE INDEX IF NOT EXISTS idx_quote_price_rows_source_lookup
  ON quote_price_rows(source_group_key, card_type, country_or_currency, amount_range, form_factor, effective_at DESC);

CREATE UNIQUE INDEX IF NOT EXISTS quote_price_rows_one_live_row
  ON quote_price_rows(
    source_group_key,
    card_type,
    country_or_currency,
    amount_range,
    form_factor,
    COALESCE(multiplier, '')
  )
  WHERE quote_status = 'active' AND expires_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_quote_validation_runs_document_created
  ON quote_validation_runs(quote_document_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_quote_snapshot_decisions_document
  ON quote_snapshot_decisions(quote_document_id);

CREATE INDEX IF NOT EXISTS idx_quote_validation_row_results_run_decision
  ON quote_validation_row_results(validation_run_id, final_decision, row_ordinal);

CREATE TABLE IF NOT EXISTS quote_parse_exceptions (
  id BIGSERIAL PRIMARY KEY,
  quote_document_id BIGINT NOT NULL,
  platform TEXT NOT NULL,
  source_group_key TEXT NOT NULL,
  chat_id TEXT NOT NULL,
  chat_name TEXT NOT NULL,
  source_name TEXT NOT NULL,
  sender_id TEXT NOT NULL,
  reason TEXT NOT NULL,
  source_line TEXT NOT NULL,
  raw_text TEXT NOT NULL,
  message_time TIMESTAMP NOT NULL,
  parser_template TEXT NOT NULL,
  parser_version TEXT NOT NULL,
  confidence NUMERIC(6, 4) NOT NULL,
  resolution_status TEXT NOT NULL DEFAULT 'open',
  resolution_note TEXT NOT NULL DEFAULT '',
  resolved_at TIMESTAMP,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_quote_parse_exceptions_created
  ON quote_parse_exceptions(created_at DESC);

CREATE TABLE IF NOT EXISTS quote_inquiry_contexts (
  id BIGSERIAL PRIMARY KEY,
  platform TEXT NOT NULL,
  source_group_key TEXT NOT NULL,
  chat_id TEXT NOT NULL,
  chat_name TEXT NOT NULL,
  card_type TEXT NOT NULL,
  country_or_currency TEXT NOT NULL,
  amount_range TEXT NOT NULL,
  multiplier TEXT,
  form_factor TEXT NOT NULL DEFAULT '不限',
  requested_by TEXT NOT NULL DEFAULT 'web',
  prompt_text TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'open',
  expires_at TIMESTAMP NOT NULL,
  resolved_message_id TEXT,
  resolved_at TIMESTAMP,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_quote_inquiry_contexts_open
  ON quote_inquiry_contexts(platform, chat_id, status, expires_at DESC);

CREATE TABLE IF NOT EXISTS quote_group_profiles (
  id BIGSERIAL PRIMARY KEY,
  platform TEXT NOT NULL,
  chat_id TEXT NOT NULL,
  chat_name TEXT NOT NULL,
  default_card_type TEXT NOT NULL DEFAULT '',
  default_country_or_currency TEXT NOT NULL DEFAULT '',
  default_form_factor TEXT NOT NULL DEFAULT '不限',
  default_multiplier TEXT NOT NULL DEFAULT '',
  parser_template TEXT NOT NULL DEFAULT '',
  stale_after_minutes INTEGER NOT NULL DEFAULT 120,
  note TEXT NOT NULL DEFAULT '',
  template_config TEXT NOT NULL DEFAULT '',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(platform, chat_id)
);

CREATE TABLE IF NOT EXISTS quote_repair_cases (
  id BIGSERIAL PRIMARY KEY,
  origin_exception_id BIGINT NOT NULL REFERENCES quote_parse_exceptions(id) ON DELETE CASCADE,
  origin_quote_document_id BIGINT NOT NULL REFERENCES quote_documents(id) ON DELETE CASCADE,
  origin_validation_run_id BIGINT REFERENCES quote_validation_runs(id) ON DELETE SET NULL,
  platform TEXT NOT NULL,
  source_group_key TEXT NOT NULL,
  chat_id TEXT NOT NULL,
  chat_name TEXT NOT NULL,
  group_profile_id BIGINT REFERENCES quote_group_profiles(id) ON DELETE SET NULL,
  lifecycle_state TEXT NOT NULL,
  current_failure_reason TEXT NOT NULL,
  parser_template_snapshot TEXT NOT NULL DEFAULT '',
  parser_version_snapshot TEXT NOT NULL DEFAULT '',
  message_time_snapshot TIMESTAMP,
  raw_message_snapshot TEXT NOT NULL,
  source_line_snapshot TEXT NOT NULL,
  profile_snapshot_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  validation_summary_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  case_summary_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  baseline_attempt_id BIGINT,
  case_fingerprint TEXT NOT NULL DEFAULT '',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(origin_exception_id)
);

CREATE INDEX IF NOT EXISTS idx_quote_repair_cases_group_created
  ON quote_repair_cases(source_group_key, created_at DESC);

CREATE TABLE IF NOT EXISTS quote_repair_case_attempts (
  id BIGSERIAL PRIMARY KEY,
  repair_case_id BIGINT NOT NULL REFERENCES quote_repair_cases(id) ON DELETE CASCADE,
  attempt_kind TEXT NOT NULL,
  attempt_number INTEGER NOT NULL,
  trigger TEXT NOT NULL DEFAULT '',
  quote_document_id BIGINT REFERENCES quote_documents(id) ON DELETE SET NULL,
  validation_run_id BIGINT REFERENCES quote_validation_runs(id) ON DELETE SET NULL,
  replayed_from_quote_document_id BIGINT REFERENCES quote_documents(id) ON DELETE SET NULL,
  group_profile_id BIGINT REFERENCES quote_group_profiles(id) ON DELETE SET NULL,
  profile_snapshot_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  remaining_lines_json JSONB NOT NULL DEFAULT '[]'::jsonb,
  attempt_summary_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  outcome_state TEXT NOT NULL,
  failure_note TEXT NOT NULL DEFAULT '',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(repair_case_id, attempt_number)
);

CREATE INDEX IF NOT EXISTS idx_quote_repair_case_attempts_case_created
  ON quote_repair_case_attempts(repair_case_id, created_at DESC);

ALTER TABLE quote_repair_cases
  ADD CONSTRAINT fk_quote_repair_cases_baseline_attempt
  FOREIGN KEY (baseline_attempt_id) REFERENCES quote_repair_case_attempts(id)
  ON DELETE SET NULL;

CREATE TABLE IF NOT EXISTS quote_dictionary_aliases (
  id BIGSERIAL PRIMARY KEY,
  category TEXT NOT NULL,
  alias TEXT NOT NULL,
  canonical_value TEXT NOT NULL,
  canonical_input TEXT NOT NULL DEFAULT '',
  scope_platform TEXT NOT NULL DEFAULT '',
  scope_chat_id TEXT NOT NULL DEFAULT '',
  note TEXT NOT NULL DEFAULT '',
  enabled INTEGER NOT NULL DEFAULT 1,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(category, alias, scope_platform, scope_chat_id)
);

CREATE INDEX IF NOT EXISTS idx_quote_dictionary_aliases_lookup
  ON quote_dictionary_aliases(category, scope_platform, scope_chat_id, enabled);
