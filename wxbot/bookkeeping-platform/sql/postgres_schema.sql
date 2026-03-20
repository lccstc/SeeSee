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
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  deleted INTEGER NOT NULL DEFAULT 0,
  settled INTEGER NOT NULL DEFAULT 0,
  settlement_id BIGINT,
  settled_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS settlements (
  id BIGSERIAL PRIMARY KEY,
  platform TEXT NOT NULL,
  group_key TEXT NOT NULL,
  settle_date TEXT NOT NULL,
  total_rmb NUMERIC(18, 4) NOT NULL,
  detail TEXT NOT NULL,
  settled_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  settled_by TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS groups (
  group_key TEXT PRIMARY KEY,
  platform TEXT NOT NULL,
  chat_id TEXT NOT NULL,
  chat_name TEXT NOT NULL,
  group_num INTEGER,
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
  settlement_id BIGINT NOT NULL,
  group_key TEXT NOT NULL,
  opening_delta NUMERIC(18, 4) NOT NULL DEFAULT 0,
  income_delta NUMERIC(18, 4) NOT NULL DEFAULT 0,
  expense_delta NUMERIC(18, 4) NOT NULL DEFAULT 0,
  closing_delta NUMERIC(18, 4) NOT NULL DEFAULT 0,
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

CREATE INDEX IF NOT EXISTS idx_tx_group_key ON transactions(group_key, deleted);
CREATE INDEX IF NOT EXISTS idx_tx_platform_group ON transactions(platform, group_key, deleted);
CREATE INDEX IF NOT EXISTS idx_tx_settled ON transactions(group_key, settled, deleted);
CREATE INDEX IF NOT EXISTS idx_tx_settlement_id ON transactions(settlement_id);
CREATE INDEX IF NOT EXISTS idx_groups_num ON groups(group_num);
CREATE INDEX IF NOT EXISTS idx_manual_adjustments_settlement ON manual_adjustments(settlement_id, group_key);
CREATE INDEX IF NOT EXISTS idx_ingested_events_platform ON ingested_events(platform, occurred_at);
