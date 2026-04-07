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
  parser_template TEXT NOT NULL,
  parser_version TEXT NOT NULL,
  confidence NUMERIC(6, 4) NOT NULL,
  parse_status TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (platform, chat_id, message_id)
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
  parser_template TEXT NOT NULL DEFAULT '',
  stale_after_minutes INTEGER NOT NULL DEFAULT 120,
  note TEXT NOT NULL DEFAULT '',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(platform, chat_id)
);
