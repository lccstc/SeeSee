from __future__ import annotations

import csv
import sqlite3
from datetime import datetime
from pathlib import Path

from .models import ReminderPayload


def _looks_like_postgres_dsn(target: str | Path) -> bool:
    value = str(target)
    return value.startswith("postgres://") or value.startswith("postgresql://")


class BookkeepingDB:
    def __new__(cls, db_path: str | Path):
        if cls is BookkeepingDB and _looks_like_postgres_dsn(db_path):
            return super().__new__(PostgresBookkeepingDB)
        return super().__new__(cls)

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA busy_timeout=5000")
        self._init_schema()

    def _init_schema(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS transactions (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              platform TEXT NOT NULL,
              group_key TEXT NOT NULL,
              group_num INTEGER,
              chat_id TEXT NOT NULL,
              chat_name TEXT NOT NULL,
              sender_id TEXT NOT NULL,
              sender_name TEXT NOT NULL,
              message_id TEXT,
              input_sign INTEGER NOT NULL,
              amount REAL NOT NULL,
              category TEXT NOT NULL,
              rate REAL,
              rmb_value REAL NOT NULL,
              raw TEXT NOT NULL,
              ngn_rate REAL,
              created_at TEXT NOT NULL DEFAULT (datetime('now')),
              deleted INTEGER NOT NULL DEFAULT 0,
              settled INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS settlements (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              platform TEXT NOT NULL,
              group_key TEXT NOT NULL,
              settle_date TEXT NOT NULL,
              total_rmb REAL NOT NULL,
              detail TEXT NOT NULL,
              settled_at TEXT NOT NULL DEFAULT (datetime('now')),
              settled_by TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS groups (
              group_key TEXT PRIMARY KEY,
              platform TEXT NOT NULL,
              chat_id TEXT NOT NULL,
              chat_name TEXT NOT NULL,
              group_num INTEGER,
              created_at TEXT NOT NULL DEFAULT (datetime('now')),
              updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS settings (
              key TEXT PRIMARY KEY,
              value TEXT,
              updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS whitelist (
              user_key TEXT PRIMARY KEY,
              added_by TEXT NOT NULL,
              added_at TEXT NOT NULL DEFAULT (datetime('now')),
              note TEXT
            );

            CREATE TABLE IF NOT EXISTS admins (
              user_key TEXT PRIMARY KEY,
              added_by TEXT NOT NULL,
              added_at TEXT NOT NULL DEFAULT (datetime('now')),
              note TEXT
            );

            CREATE TABLE IF NOT EXISTS reminders (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              platform TEXT NOT NULL,
              chat_id TEXT NOT NULL,
              sender_id TEXT NOT NULL,
              message TEXT NOT NULL,
              amount REAL NOT NULL,
              category TEXT NOT NULL,
              rate REAL,
              rmb_value REAL NOT NULL,
              ngn_value REAL,
              duration_minutes INTEGER NOT NULL DEFAULT 0,
              remind_at TEXT NOT NULL,
              created_at TEXT NOT NULL DEFAULT (datetime('now')),
              sent INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS identity_bindings (
              platform TEXT NOT NULL,
              chat_id TEXT NOT NULL,
              observed_key TEXT NOT NULL,
              canonical_id TEXT NOT NULL,
              observed_name TEXT,
              updated_at TEXT NOT NULL DEFAULT (datetime('now')),
              PRIMARY KEY (platform, chat_id, observed_key)
            );

            CREATE TABLE IF NOT EXISTS manual_adjustments (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              settlement_id INTEGER NOT NULL,
              group_key TEXT NOT NULL,
              opening_delta REAL NOT NULL DEFAULT 0,
              income_delta REAL NOT NULL DEFAULT 0,
              expense_delta REAL NOT NULL DEFAULT 0,
              closing_delta REAL NOT NULL DEFAULT 0,
              note TEXT NOT NULL,
              created_by TEXT NOT NULL,
              created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS group_combinations (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT NOT NULL UNIQUE,
              note TEXT,
              created_by TEXT NOT NULL,
              created_at TEXT NOT NULL DEFAULT (datetime('now')),
              updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS group_combination_items (
              combination_id INTEGER NOT NULL,
              group_num INTEGER NOT NULL,
              PRIMARY KEY (combination_id, group_num)
            );

            CREATE TABLE IF NOT EXISTS ingested_events (
              event_id TEXT PRIMARY KEY,
              event_type TEXT NOT NULL,
              platform TEXT NOT NULL,
              source_machine TEXT NOT NULL,
              schema_version INTEGER NOT NULL,
              occurred_at TEXT NOT NULL,
              ingested_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE INDEX IF NOT EXISTS idx_tx_group_key ON transactions(group_key, deleted);
            CREATE INDEX IF NOT EXISTS idx_tx_platform_group ON transactions(platform, group_key, deleted);
            CREATE INDEX IF NOT EXISTS idx_tx_settled ON transactions(group_key, settled, deleted);
            CREATE INDEX IF NOT EXISTS idx_groups_num ON groups(group_num);
            CREATE INDEX IF NOT EXISTS idx_manual_adjustments_settlement ON manual_adjustments(settlement_id, group_key);
            """
        )
        self._ensure_column("transactions", "settlement_id", "settlement_id INTEGER")
        self._ensure_column("transactions", "settled_at", "settled_at TEXT")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_tx_settlement_id ON transactions(settlement_id)")
        self.conn.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('ngn_rate', '')")
        self._backfill_settlement_links()
        self.conn.commit()

    def _ensure_column(self, table_name: str, column_name: str, definition: str) -> None:
        rows = self.conn.execute(f"PRAGMA table_info({table_name})").fetchall()
        columns = {str(row["name"]) for row in rows}
        if column_name not in columns:
            self.conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {definition}")

    @staticmethod
    def _utcnow_text() -> str:
        return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    def add_transaction(
        self,
        *,
        platform: str,
        group_key: str,
        group_num: int | None,
        chat_id: str,
        chat_name: str,
        sender_id: str,
        sender_name: str,
        message_id: str,
        input_sign: int,
        amount: float,
        category: str,
        rate: float | None,
        rmb_value: float,
        raw: str,
        created_at: str | None = None,
        deleted: int = 0,
        settled: int = 0,
        settlement_id: int | None = None,
        settled_at: str | None = None,
        ngn_rate_override: float | None = None,
    ) -> int:
        ngn_rate = ngn_rate_override if ngn_rate_override is not None else self.get_ngn_rate()
        cur = self.conn.execute(
            """
            INSERT INTO transactions (
              platform, group_key, group_num, chat_id, chat_name,
              sender_id, sender_name, message_id, input_sign, amount,
              category, rate, rmb_value, raw, ngn_rate, created_at,
              deleted, settled, settlement_id, settled_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, COALESCE(?, datetime('now')), ?, ?, ?, ?)
            """,
            (
                platform,
                group_key,
                group_num,
                chat_id,
                chat_name,
                sender_id,
                sender_name,
                message_id,
                input_sign,
                amount,
                category,
                rate,
                rmb_value,
                raw,
                ngn_rate,
                created_at,
                deleted,
                settled,
                settlement_id,
                settled_at,
            ),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def undo_last(self, group_key: str) -> sqlite3.Row | None:
        row = self.conn.execute(
            """
            SELECT * FROM transactions
            WHERE group_key = ? AND deleted = 0
            ORDER BY id DESC LIMIT 1
            """,
            (group_key,),
        ).fetchone()
        if row is None:
            return None
        self.conn.execute("UPDATE transactions SET deleted = 1 WHERE id = ?", (row["id"],))
        self.conn.commit()
        return row

    def get_balance(self, group_key: str) -> dict:
        total_row = self.conn.execute(
            "SELECT COALESCE(SUM(rmb_value), 0) AS total, COUNT(*) AS count FROM transactions WHERE group_key = ? AND deleted = 0",
            (group_key,),
        ).fetchone()
        cat_rows = self.conn.execute(
            "SELECT category, COUNT(*) AS count, SUM(rmb_value) AS total_rmb FROM transactions WHERE group_key = ? AND deleted = 0 GROUP BY category ORDER BY category",
            (group_key,),
        ).fetchall()
        return {
            "total": float(total_row["total"]),
            "count": int(total_row["count"]),
            "by_category": {row["category"]: {"count": int(row["count"]), "total_rmb": float(row["total_rmb"])} for row in cat_rows},
        }

    def get_history(self, group_key: str, limit: int = 20) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM transactions WHERE group_key = ? AND deleted = 0 ORDER BY id DESC LIMIT ?",
            (group_key, limit),
        ).fetchall()

    def get_history_by_category(self, group_key: str, category: str, limit: int = 50) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM transactions WHERE group_key = ? AND deleted = 0 AND category = ? ORDER BY id DESC LIMIT ?",
            (group_key, category, limit),
        ).fetchall()

    def clear_group(self, group_key: str) -> int:
        cur = self.conn.execute("UPDATE transactions SET deleted = 1 WHERE group_key = ? AND deleted = 0", (group_key,))
        self.conn.commit()
        return cur.rowcount

    def get_category_mingxi(self, group_key: str) -> list[dict]:
        rows = self.conn.execute(
            """
            SELECT category, rate, COUNT(*) AS count,
                   SUM(input_sign * amount) AS total_amount,
                   SUM(rmb_value) AS total_rmb,
                   SUM(ngn_rate * rmb_value) AS total_ngn
            FROM transactions
            WHERE group_key = ? AND deleted = 0 AND settled = 0
            GROUP BY category, rate
            ORDER BY category, rate
            """,
            (group_key,),
        ).fetchall()
        category_map: dict[str, list[dict]] = {}
        for row in rows:
            total_rmb = float(row["total_rmb"] or 0)
            if total_rmb == 0:
                continue
            category_map.setdefault(row["category"], []).append(
                {
                    "rate": row["rate"],
                    "count": int(row["count"]),
                    "total_amount": float(row["total_amount"] or 0),
                    "total_rmb": total_rmb,
                    "total_ngn": float(row["total_ngn"]) if row["total_ngn"] is not None else None,
                }
            )
        return [{"category": key, "rate_groups": value} for key, value in category_map.items()]

    def get_unsettled_transactions(self, group_key: str) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM transactions WHERE group_key = ? AND deleted = 0 AND settled = 0 ORDER BY id ASC",
            (group_key,),
        ).fetchall()

    def get_groups_with_unsettled_transactions(self) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT DISTINCT platform, group_key, chat_id, chat_name FROM transactions WHERE deleted = 0 AND settled = 0 ORDER BY group_key"
        ).fetchall()

    def settle_transactions(
        self,
        platform: str,
        group_key: str,
        txs: list[sqlite3.Row],
        settled_by: str,
        settled_at: str | None = None,
    ) -> dict:
        if not txs:
            return {"total_rmb": 0.0, "detail": ""}
        settled_at_text = settled_at or self._utcnow_text()
        total_rmb = sum(float(tx["rmb_value"]) for tx in txs)
        detail_map: dict[str, dict] = {}
        for tx in txs:
            bucket = detail_map.setdefault(tx["category"], {"count": 0, "total": 0.0})
            bucket["count"] += 1
            bucket["total"] += float(tx["rmb_value"])
        detail = "; ".join(
            f"{cat.upper()}: {info['count']} txs {'+' if info['total'] >= 0 else '-'}{abs(info['total']):.2f}"
            for cat, info in detail_map.items()
        )
        placeholders = ",".join("?" for _ in txs)
        ids = [int(tx["id"]) for tx in txs]
        cur = self.conn.execute(
            "INSERT INTO settlements (platform, group_key, settle_date, total_rmb, detail, settled_at, settled_by) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (platform, group_key, settled_at_text, total_rmb, detail, settled_at_text, settled_by),
        )
        settlement_id = int(cur.lastrowid)
        self.conn.execute(
            f"UPDATE transactions SET settled = 1, settlement_id = ?, settled_at = ? WHERE id IN ({placeholders})",
            [settlement_id, settled_at_text, *ids],
        )
        self.conn.commit()
        return {"total_rmb": total_rmb, "detail": detail, "settlement_id": settlement_id, "settled_at": settled_at_text}

    def get_settlements(self, group_key: str, limit: int = 10) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM settlements WHERE group_key = ? ORDER BY id DESC LIMIT ?",
            (group_key, limit),
        ).fetchall()

    def get_settlement_by_id(self, settlement_id: int) -> sqlite3.Row | None:
        return self.conn.execute(
            "SELECT * FROM settlements WHERE id = ?",
            (settlement_id,),
        ).fetchone()

    def get_previous_settlement(self, group_key: str, settlement_id: int) -> sqlite3.Row | None:
        return self.conn.execute(
            """
            SELECT * FROM settlements
            WHERE group_key = ? AND id < ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (group_key, settlement_id),
        ).fetchone()

    def set_group(self, *, platform: str, group_key: str, chat_id: str, chat_name: str, group_num: int) -> bool:
        if group_num < 0 or group_num > 9:
            return False
        self.conn.execute(
            """
            INSERT INTO groups (group_key, platform, chat_id, chat_name, group_num, updated_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
            ON CONFLICT(group_key) DO UPDATE SET
              platform = excluded.platform,
              chat_id = excluded.chat_id,
              chat_name = excluded.chat_name,
              group_num = excluded.group_num,
              updated_at = datetime('now')
            """,
            (group_key, platform, chat_id, chat_name, group_num),
        )
        self.conn.commit()
        return True

    def get_group_num(self, group_key: str) -> int | None:
        row = self.conn.execute("SELECT group_num FROM groups WHERE group_key = ?", (group_key,)).fetchone()
        return int(row["group_num"]) if row and row["group_num"] is not None else None

    def is_group_active(self, group_key: str) -> bool:
        row = self.conn.execute("SELECT 1 FROM groups WHERE group_key = ? AND group_num IS NOT NULL", (group_key,)).fetchone()
        return row is not None

    def get_groups_by_num(self, group_num: int) -> list[sqlite3.Row]:
        return self.conn.execute("SELECT * FROM groups WHERE group_num = ? ORDER BY chat_name", (group_num,)).fetchall()

    def get_group_number_stats(self) -> dict[int, int]:
        stats = {index: 0 for index in range(10)}
        rows = self.conn.execute("SELECT group_num, COUNT(*) AS cnt FROM groups WHERE group_num IS NOT NULL GROUP BY group_num").fetchall()
        for row in rows:
            stats[int(row["group_num"])] = int(row["cnt"])
        return stats

    def get_all_groups(self) -> list[sqlite3.Row]:
        return self.conn.execute(
            """
            SELECT
              g.*,
              COALESCE(SUM(t.rmb_value), 0) AS tx_balance
            FROM groups g
            LEFT JOIN transactions t ON t.group_key = g.group_key AND t.deleted = 0
            GROUP BY g.group_key, g.platform, g.chat_id, g.chat_name, g.group_num, g.created_at, g.updated_at
            ORDER BY g.chat_name
            """
        ).fetchall()

    def get_group_count(self) -> int:
        row = self.conn.execute("SELECT COUNT(DISTINCT group_key) AS cnt FROM transactions WHERE deleted = 0").fetchone()
        return int(row["cnt"])

    def get_total_transaction_count(self) -> int:
        row = self.conn.execute("SELECT COUNT(*) AS cnt FROM transactions WHERE deleted = 0").fetchone()
        return int(row["cnt"])

    def add_to_whitelist(self, user_key: str, added_by: str, note: str | None = None) -> None:
        self.conn.execute(
            "INSERT OR IGNORE INTO whitelist (user_key, added_by, note) VALUES (?, ?, ?)",
            (user_key, added_by, note),
        )
        self.conn.commit()

    def remove_from_whitelist(self, user_key: str) -> bool:
        cur = self.conn.execute("DELETE FROM whitelist WHERE user_key = ?", (user_key,))
        self.conn.commit()
        return cur.rowcount > 0

    def is_whitelisted(self, user_key: str) -> bool:
        row = self.conn.execute("SELECT 1 FROM whitelist WHERE user_key = ?", (user_key,)).fetchone()
        return row is not None

    def get_whitelist(self) -> list[sqlite3.Row]:
        return self.conn.execute("SELECT * FROM whitelist ORDER BY added_at").fetchall()

    def add_admin(self, user_key: str, added_by: str, note: str | None = None) -> None:
        self.conn.execute(
            "INSERT OR IGNORE INTO admins (user_key, added_by, note) VALUES (?, ?, ?)",
            (user_key, added_by, note),
        )
        self.conn.commit()

    def remove_admin(self, user_key: str) -> bool:
        cur = self.conn.execute("DELETE FROM admins WHERE user_key = ?", (user_key,))
        self.conn.commit()
        return cur.rowcount > 0

    def is_admin(self, user_key: str) -> bool:
        row = self.conn.execute("SELECT 1 FROM admins WHERE user_key = ?", (user_key,)).fetchone()
        return row is not None

    def get_admins(self) -> list[sqlite3.Row]:
        return self.conn.execute("SELECT * FROM admins ORDER BY added_at").fetchall()

    def bind_identity(self, *, platform: str, chat_id: str, observed_id: str, observed_name: str, canonical_id: str) -> None:
        keys = []
        for value in (observed_id, observed_name):
            value = str(value or '').strip()
            if value and value not in keys:
                keys.append(value)
        scopes = [str(chat_id or '').strip(), '*']
        scopes = [scope for scope in scopes if scope]
        for scope in scopes:
            for key in keys:
                self.conn.execute(
                    """
                    INSERT INTO identity_bindings (platform, chat_id, observed_key, canonical_id, observed_name, updated_at)
                    VALUES (?, ?, ?, ?, ?, datetime('now'))
                    ON CONFLICT(platform, chat_id, observed_key) DO UPDATE SET
                      canonical_id = excluded.canonical_id,
                      observed_name = excluded.observed_name,
                      updated_at = datetime('now')
                    """,
                    (platform, scope, key, canonical_id, observed_name or observed_id),
                )
        self.conn.commit()

    def resolve_identity(self, *, platform: str, chat_id: str, observed_id: str, observed_name: str) -> str:
        scopes = [str(chat_id or '').strip(), '*']
        scopes = [scope for scope in scopes if scope]
        for key in (observed_id, observed_name):
            key = str(key or '').strip()
            if not key:
                continue
            for scope in scopes:
                row = self.conn.execute(
                    "SELECT canonical_id FROM identity_bindings WHERE platform = ? AND chat_id = ? AND observed_key = ?",
                    (platform, scope, key),
                ).fetchone()
                if row is not None and row["canonical_id"]:
                    return str(row["canonical_id"])
        return str(observed_id or observed_name or '')

    def set_ngn_rate(self, rate: str) -> None:
        self.conn.execute("UPDATE settings SET value = ?, updated_at = datetime('now') WHERE key = 'ngn_rate'", (rate,))
        self.conn.commit()

    def get_ngn_rate(self) -> float | None:
        row = self.conn.execute("SELECT value FROM settings WHERE key = 'ngn_rate'").fetchone()
        if row is None or not row["value"]:
            return None
        return float(row["value"])

    def export_group_csv(self, group_key: str, export_dir: str | Path) -> Path | None:
        rows = self.conn.execute("SELECT * FROM transactions WHERE group_key = ? AND deleted = 0 ORDER BY id ASC", (group_key,)).fetchall()
        if not rows:
            return None
        export_dir = Path(export_dir)
        export_dir.mkdir(parents=True, exist_ok=True)
        safe_name = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in group_key)
        path = export_dir / f"{safe_name}.csv"
        with path.open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.writer(handle)
            writer.writerow(["id", "platform", "group_key", "chat_name", "sender_name", "sign", "amount", "category", "rate", "rmb_value", "raw", "created_at"])
            for row in rows:
                writer.writerow([row["id"], row["platform"], row["group_key"], row["chat_name"], row["sender_name"], "+" if row["input_sign"] > 0 else "-", row["amount"], row["category"], row["rate"] or "", row["rmb_value"], row["raw"], row["created_at"]])
        return path

    def add_manual_adjustment(
        self,
        *,
        settlement_id: int,
        group_key: str,
        opening_delta: float,
        income_delta: float,
        expense_delta: float,
        closing_delta: float,
        note: str,
        created_by: str,
    ) -> int:
        cur = self.conn.execute(
            """
            INSERT INTO manual_adjustments (
              settlement_id, group_key, opening_delta, income_delta, expense_delta,
              closing_delta, note, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                settlement_id,
                group_key,
                opening_delta,
                income_delta,
                expense_delta,
                closing_delta,
                note,
                created_by,
            ),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def get_manual_adjustments(self, settlement_id: int) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM manual_adjustments WHERE settlement_id = ? ORDER BY id ASC",
            (settlement_id,),
        ).fetchall()

    def get_manual_adjustment_total(self, group_key: str, up_to_settlement_id: int | None = None) -> float:
        if up_to_settlement_id is None:
            row = self.conn.execute(
                "SELECT COALESCE(SUM(closing_delta), 0) AS total FROM manual_adjustments WHERE group_key = ?",
                (group_key,),
            ).fetchone()
        else:
            row = self.conn.execute(
                """
                SELECT COALESCE(SUM(closing_delta), 0) AS total
                FROM manual_adjustments
                WHERE group_key = ? AND settlement_id <= ?
                """,
                (group_key, up_to_settlement_id),
            ).fetchone()
        return float(row["total"] or 0)

    def save_group_combination(self, *, name: str, group_numbers: list[int], note: str, created_by: str) -> int:
        cur = self.conn.execute(
            """
            INSERT INTO group_combinations (name, note, created_by, updated_at)
            VALUES (?, ?, ?, datetime('now'))
            ON CONFLICT(name) DO UPDATE SET
              note = excluded.note,
              updated_at = datetime('now')
            """,
            (name, note, created_by),
        )
        if cur.lastrowid:
            combination_id = int(cur.lastrowid)
        else:
            row = self.conn.execute("SELECT id FROM group_combinations WHERE name = ?", (name,)).fetchone()
            combination_id = int(row["id"])
        self.conn.execute("DELETE FROM group_combination_items WHERE combination_id = ?", (combination_id,))
        for group_num in sorted(set(group_numbers)):
            self.conn.execute(
                "INSERT INTO group_combination_items (combination_id, group_num) VALUES (?, ?)",
                (combination_id, group_num),
            )
        self.conn.commit()
        return combination_id

    def list_group_combinations(self) -> list[sqlite3.Row]:
        return self.conn.execute(
            """
            SELECT
              gc.id,
              gc.name,
              gc.note,
              gc.created_by,
              gc.created_at,
              gc.updated_at,
              GROUP_CONCAT(gci.group_num, ',') AS group_numbers
            FROM group_combinations gc
            LEFT JOIN group_combination_items gci ON gci.combination_id = gc.id
            GROUP BY gc.id, gc.name, gc.note, gc.created_by, gc.created_at, gc.updated_at
            ORDER BY gc.name
            """
        ).fetchall()

    def create_reminder(self, *, platform: str, chat_id: str, sender_id: str, message: str, amount: float, category: str, rate: float | None, rmb_value: float, ngn_value: float | None, duration_minutes: int, remind_at: str) -> int:
        cur = self.conn.execute(
            """
            INSERT INTO reminders (
              platform, chat_id, sender_id, message, amount, category, rate,
              rmb_value, ngn_value, duration_minutes, remind_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (platform, chat_id, sender_id, message, amount, category, rate, rmb_value, ngn_value, duration_minutes, remind_at),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def get_due_reminders(self, now_text: str) -> list[ReminderPayload]:
        rows = self.conn.execute("SELECT * FROM reminders WHERE sent = 0 AND remind_at <= ? ORDER BY id ASC", (now_text,)).fetchall()
        return [self._reminder_from_row(row) for row in rows]

    def mark_reminder_sent(self, reminder_id: int) -> None:
        self.conn.execute("UPDATE reminders SET sent = 1 WHERE id = ?", (reminder_id,))
        self.conn.commit()

    def _backfill_settlement_links(self) -> None:
        groups = self.conn.execute(
            "SELECT DISTINCT group_key FROM settlements ORDER BY group_key"
        ).fetchall()
        for row in groups:
            group_key = str(row["group_key"])
            settlements = self.conn.execute(
                """
                SELECT id, settled_at
                FROM settlements
                WHERE group_key = ?
                ORDER BY settled_at ASC, id ASC
                """,
                (group_key,),
            ).fetchall()
            previous_cutoff = ""
            for settlement in settlements:
                settlement_id = int(settlement["id"])
                settled_at = str(settlement["settled_at"])
                txs = self.conn.execute(
                    """
                    SELECT id
                    FROM transactions
                    WHERE group_key = ?
                      AND deleted = 0
                      AND settled = 1
                      AND settlement_id IS NULL
                      AND created_at > ?
                      AND created_at <= ?
                    ORDER BY created_at ASC, id ASC
                    """,
                    (group_key, previous_cutoff, settled_at),
                ).fetchall()
                if txs:
                    placeholders = ",".join("?" for _ in txs)
                    ids = [int(item["id"]) for item in txs]
                    self.conn.execute(
                        f"UPDATE transactions SET settlement_id = ?, settled_at = ? WHERE id IN ({placeholders})",
                        [settlement_id, settled_at, *ids],
                    )
                previous_cutoff = settled_at
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    @staticmethod
    def _reminder_from_row(row: sqlite3.Row) -> ReminderPayload:
        return ReminderPayload(
            id=int(row["id"]),
            platform=row["platform"],
            chat_id=row["chat_id"],
            sender_id=row["sender_id"],
            message=row["message"],
            amount=float(row["amount"]),
            category=row["category"],
            rate=float(row["rate"]) if row["rate"] is not None else None,
            rmb_value=float(row["rmb_value"]),
            ngn_value=float(row["ngn_value"]) if row["ngn_value"] is not None else None,
            duration_minutes=int(row["duration_minutes"]),
            remind_at=row["remind_at"],
        )


class _PostgresCursorCompat:
    def __init__(self, cursor) -> None:
        self._cursor = cursor
        self.rowcount = getattr(cursor, "rowcount", 0)
        self.lastrowid = getattr(cursor, "lastrowid", None)

    def fetchone(self):
        row = self._cursor.fetchone()
        return self._normalize(row)

    def fetchall(self):
        return [self._normalize(row) for row in self._cursor.fetchall()]

    def _normalize(self, row):
        if row is None:
            return None
        if isinstance(row, dict):
            return row
        if hasattr(row, "keys"):
            return dict(row)
        description = getattr(self._cursor, "description", None) or []
        names: list[str] = []
        for item in description:
            if isinstance(item, (tuple, list)):
                names.append(str(item[0]))
            else:
                names.append(str(getattr(item, "name", "")))
        if names:
            return {names[idx]: row[idx] for idx in range(len(names))}
        return row


class _PostgresConnectionCompat:
    def __init__(self, raw_connection) -> None:
        self._raw_connection = raw_connection

    @staticmethod
    def _translate(sql: str) -> str:
        return sql.replace("datetime('now')", "CURRENT_TIMESTAMP").replace("?", "%s")

    def execute(self, sql: str, params=()):
        cursor = self._raw_connection.execute(self._translate(sql), tuple(params))
        return _PostgresCursorCompat(cursor)

    def commit(self) -> None:
        self._raw_connection.commit()

    def rollback(self) -> None:
        self._raw_connection.rollback()

    def close(self) -> None:
        self._raw_connection.close()


class PostgresBookkeepingDB(BookkeepingDB):
    def __init__(self, db_path: str | Path) -> None:
        try:
            import psycopg
        except ImportError as exc:
            raise RuntimeError("PostgreSQL backend requires psycopg to be installed") from exc

        self.db_path = str(db_path)
        self._raw_conn = psycopg.connect(str(db_path))
        self.conn = _PostgresConnectionCompat(self._raw_conn)
        self._init_schema()

    def _init_schema(self) -> None:
        schema_path = Path(__file__).resolve().parents[1] / "sql" / "postgres_schema.sql"
        statements = [item.strip() for item in schema_path.read_text(encoding="utf-8-sig").split(";") if item.strip()]
        for statement in statements:
            self.conn.execute(statement)
        self.conn.execute(
            """
            INSERT INTO settings (key, value, updated_at)
            VALUES ('ngn_rate', '', CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO NOTHING
            """
        )
        self.conn.commit()

    def _ensure_column(self, table_name: str, column_name: str, definition: str) -> None:
        return None

    def add_transaction(
        self,
        *,
        platform: str,
        group_key: str,
        group_num: int | None,
        chat_id: str,
        chat_name: str,
        sender_id: str,
        sender_name: str,
        message_id: str,
        input_sign: int,
        amount: float,
        category: str,
        rate: float | None,
        rmb_value: float,
        raw: str,
        created_at: str | None = None,
        deleted: int = 0,
        settled: int = 0,
        settlement_id: int | None = None,
        settled_at: str | None = None,
        ngn_rate_override: float | None = None,
    ) -> int:
        ngn_rate = ngn_rate_override if ngn_rate_override is not None else self.get_ngn_rate()
        cur = self.conn.execute(
            """
            INSERT INTO transactions (
              platform, group_key, group_num, chat_id, chat_name,
              sender_id, sender_name, message_id, input_sign, amount,
              category, rate, rmb_value, raw, ngn_rate, created_at,
              deleted, settled, settlement_id, settled_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, COALESCE(?, CURRENT_TIMESTAMP), ?, ?, ?, ?)
            RETURNING id
            """,
            (
                platform,
                group_key,
                group_num,
                chat_id,
                chat_name,
                sender_id,
                sender_name,
                message_id,
                input_sign,
                amount,
                category,
                rate,
                rmb_value,
                raw,
                ngn_rate,
                created_at,
                deleted,
                settled,
                settlement_id,
                settled_at,
            ),
        )
        row = cur.fetchone()
        self.conn.commit()
        return int(row["id"])

    def settle_transactions(
        self,
        platform: str,
        group_key: str,
        txs: list[sqlite3.Row],
        settled_by: str,
        *,
        settled_at: str | None = None,
    ) -> dict:
        if not txs:
            return {"settlement_id": None, "total_rmb": 0.0, "detail": ""}

        settled_at = settled_at or self._utcnow_text()
        total_rmb = sum(float(tx["rmb_value"]) for tx in txs)
        detail_map: dict[str, dict[str, float]] = {}
        for tx in txs:
            item = detail_map.setdefault(str(tx["category"]), {"count": 0.0, "total": 0.0})
            item["count"] += 1
            item["total"] += float(tx["rmb_value"])
        detail = "; ".join(
            f"{category.upper()}: {int(info['count'])} txs {'+' if info['total'] >= 0 else '-'}{abs(info['total']):.2f}"
            for category, info in detail_map.items()
        )
        cur = self.conn.execute(
            """
            INSERT INTO settlements (
              platform, group_key, settle_date, total_rmb, detail, settled_at, settled_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            RETURNING id
            """,
            (platform, group_key, "unsettled", total_rmb, detail, settled_at, settled_by),
        )
        settlement_row = cur.fetchone()
        settlement_id = int(settlement_row["id"])
        ids = [int(tx["id"]) for tx in txs]
        placeholders = ",".join("?" for _ in ids)
        self.conn.execute(
            f"UPDATE transactions SET settled = 1, settlement_id = ?, settled_at = ? WHERE id IN ({placeholders})",
            [settlement_id, settled_at, *ids],
        )
        self.conn.commit()
        return {"settlement_id": settlement_id, "total_rmb": total_rmb, "detail": detail}

    def add_to_whitelist(self, user_key: str, added_by: str, note: str | None = None) -> None:
        self.conn.execute(
            """
            INSERT INTO whitelist (user_key, added_by, note)
            VALUES (?, ?, ?)
            ON CONFLICT(user_key) DO NOTHING
            """,
            (user_key, added_by, note),
        )
        self.conn.commit()

    def add_admin(self, user_key: str, added_by: str, note: str | None = None) -> None:
        self.conn.execute(
            """
            INSERT INTO admins (user_key, added_by, note)
            VALUES (?, ?, ?)
            ON CONFLICT(user_key) DO NOTHING
            """,
            (user_key, added_by, note),
        )
        self.conn.commit()

    def add_manual_adjustment(
        self,
        *,
        settlement_id: int,
        group_key: str,
        opening_delta: float,
        income_delta: float,
        expense_delta: float,
        closing_delta: float,
        note: str,
        created_by: str,
    ) -> int:
        cur = self.conn.execute(
            """
            INSERT INTO manual_adjustments (
              settlement_id, group_key, opening_delta, income_delta, expense_delta,
              closing_delta, note, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            RETURNING id
            """,
            (
                settlement_id,
                group_key,
                opening_delta,
                income_delta,
                expense_delta,
                closing_delta,
                note,
                created_by,
            ),
        )
        row = cur.fetchone()
        self.conn.commit()
        return int(row["id"])

    def create_reminder(
        self,
        *,
        platform: str,
        chat_id: str,
        sender_id: str,
        message: str,
        amount: float,
        category: str,
        rate: float | None,
        rmb_value: float,
        ngn_value: float | None,
        duration_minutes: int,
        remind_at: str,
    ) -> int:
        cur = self.conn.execute(
            """
            INSERT INTO reminders (
              platform, chat_id, sender_id, message, amount, category,
              rate, rmb_value, ngn_value, duration_minutes, remind_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            RETURNING id
            """,
            (platform, chat_id, sender_id, message, amount, category, rate, rmb_value, ngn_value, duration_minutes, remind_at),
        )
        row = cur.fetchone()
        self.conn.commit()
        return int(row["id"])
