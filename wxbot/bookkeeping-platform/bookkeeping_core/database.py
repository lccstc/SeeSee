from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from .models import ReminderPayload
from .quotes import (
    normalize_quote_amount_range,
    normalize_quote_form_factor,
    normalize_quote_multiplier,
)


DBRow = dict[str, Any]
_QUOTE_EXCEPTION_SUPPRESSION_NOTE_PREFIX = "quote_exception_suppression:"
_QUOTE_EXCEPTION_SUPPRESSION_NOTE_VERSION = 1
_QUOTE_EXCEPTION_SUPPRESSION_TRANSLATION = str.maketrans(
    {
        "\uff08": "(",
        "\uff09": ")",
        "\uff1d": "=",
        "\uff1a": ":",
        "\uff0c": ",",
        "\uff0b": "+",
        "\uff0d": "-",
        "\u3000": " ",
    }
)


def is_postgres_dsn(target: str | Path) -> bool:
    value = str(target)
    return value.startswith("postgres://") or value.startswith("postgresql://")


def require_postgres_dsn(target: str | Path, *, context: str) -> str:
    value = str(target or "").strip()
    if not is_postgres_dsn(value):
        raise ValueError(f"{context} must use a PostgreSQL DSN")
    return value


class _BookkeepingStoreBase:
    """Shared bookkeeping persistence methods for the unified core store."""

    def _last_insert_id(self, cursor) -> int:
        value = getattr(cursor, "lastrowid", None)
        if value:
            return int(value)
        try:
            row = self.conn.execute("SELECT LASTVAL() AS id").fetchone()
        except Exception:
            return 0
        return int(row["id"]) if row and row.get("id") is not None else 0

    def _refresh_group_profile_if_exists(
        self,
        *,
        platform: str,
        group_key: str,
        chat_id: str,
        chat_name: str,
    ) -> None:
        self.conn.execute(
            """
            UPDATE groups
            SET platform = ?,
                chat_id = ?,
                chat_name = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE group_key = ?
            """,
            (platform, chat_id, chat_name, group_key),
        )
        self.conn.execute(
            """
            UPDATE quote_group_profiles
            SET chat_name = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE platform = ?
              AND chat_id = ?
            """,
            (chat_name, platform, chat_id),
        )

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
        parse_version: str = "1",
        usd_amount: float | None = None,
        unit_face_value: float | None = None,
        unit_count: float | None = None,
        created_at: str | None = None,
        deleted: int = 0,
        settled: int = 0,
        settled_at: str | None = None,
        ngn_rate_override: float | None = None,
    ) -> int:
        ngn_rate = (
            ngn_rate_override if ngn_rate_override is not None else self.get_ngn_rate()
        )
        cur = self.conn.execute(
            """
            INSERT INTO transactions (
              platform, group_key, group_num, chat_id, chat_name,
              sender_id, sender_name, message_id, input_sign, amount,
              category, rate, rmb_value, raw, parse_version, usd_amount,
              unit_face_value, unit_count, ngn_rate, created_at,
              deleted, settled, settled_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, COALESCE(?, CURRENT_TIMESTAMP), ?, ?, ?)
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
                parse_version,
                usd_amount,
                unit_face_value,
                unit_count,
                ngn_rate,
                created_at,
                deleted,
                settled,
                settled_at,
            ),
        )
        self._refresh_group_profile_if_exists(
            platform=platform,
            group_key=group_key,
            chat_id=chat_id,
            chat_name=chat_name,
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def record_incoming_message(
        self,
        *,
        platform: str,
        group_key: str,
        chat_id: str,
        chat_name: str,
        message_id: str,
        is_group: bool,
        sender_id: str,
        sender_name: str,
        sender_kind: str,
        content_type: str,
        text: str | None,
        from_self: bool,
        received_at: str | None,
        raw_payload: dict[str, Any],
    ) -> bool:
        cur = self.conn.execute(
            """
            INSERT INTO incoming_messages (
              platform, group_key, chat_id, chat_name, message_id,
              is_group, sender_id, sender_name, sender_kind, content_type,
              text, from_self, received_at, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(platform, chat_id, message_id) DO NOTHING
            """,
            (
                platform,
                group_key,
                chat_id,
                chat_name,
                message_id,
                1 if is_group else 0,
                sender_id,
                sender_name,
                sender_kind,
                content_type,
                text,
                1 if from_self else 0,
                received_at,
                json.dumps(raw_payload, ensure_ascii=False, sort_keys=True),
            ),
        )
        if is_group:
            self._refresh_group_profile_if_exists(
                platform=platform,
                group_key=group_key,
                chat_id=chat_id,
                chat_name=chat_name,
            )
        self.conn.commit()
        return bool(cur.rowcount)

    def get_incoming_message(
        self, *, platform: str, chat_id: str, message_id: str
    ) -> DBRow | None:
        return self.conn.execute(
            """
            SELECT *
            FROM incoming_messages
            WHERE platform = ? AND chat_id = ? AND message_id = ?
            """,
            (platform, chat_id, message_id),
        ).fetchone()

    def query_incoming_messages(
        self,
        *,
        platform: str | None = None,
        chat_id: str | None = None,
        message_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[DBRow], int]:
        where_parts = []
        params: list = []
        if platform is not None:
            where_parts.append("platform = ?")
            params.append(platform)
        if chat_id is not None:
            where_parts.append("chat_id = ?")
            params.append(chat_id)
        if message_id is not None:
            where_parts.append("message_id = ?")
            params.append(message_id)
        where_clause = " AND ".join(where_parts) if where_parts else "1=1"

        count_row = self.conn.execute(
            f"SELECT COUNT(*) AS cnt FROM incoming_messages WHERE {where_clause}",
            params,
        ).fetchone()
        total = int(count_row["cnt"])

        params.extend([limit, offset])
        rows = self.conn.execute(
            f"""
            SELECT id, platform, chat_id, chat_name, message_id, sender_id, sender_name,
                   sender_kind, content_type, text, from_self, received_at, raw_json,
                   created_at
            FROM incoming_messages
            WHERE {where_clause}
            ORDER BY created_at DESC, id DESC
            LIMIT ? OFFSET ?
            """,
            params,
        ).fetchall()
        return list(rows), total

    def get_incoming_messages_with_transactions(
        self,
        *,
        platform: str | None = None,
        chat_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        where_parts = []
        params: list = []
        if platform is not None:
            where_parts.append("im.platform = ?")
            params.append(platform)
        if chat_id is not None:
            where_parts.append("im.chat_id = ?")
            params.append(chat_id)
        where_clause = " AND ".join(where_parts) if where_parts else "1=1"

        count_row = self.conn.execute(
            f"SELECT COUNT(*) AS cnt FROM incoming_messages im WHERE {where_clause}",
            params,
        ).fetchone()
        total = int(count_row["cnt"])

        params.extend([limit, offset])
        rows = self.conn.execute(
            f"""
            SELECT im.id, im.platform, im.chat_id, im.chat_name, im.message_id,
                   im.sender_id, im.sender_name, im.sender_kind, im.content_type,
                   im.text, im.from_self, im.received_at, im.created_at,
                   t.id AS tx_id, t.amount AS tx_amount, t.category AS tx_category,
                   t.input_sign AS tx_input_sign, t.created_at AS tx_created_at
            FROM incoming_messages im
            LEFT JOIN transactions t ON t.platform = im.platform
                                   AND t.chat_id = im.chat_id
                                   AND t.message_id = im.message_id
                                   AND t.deleted = 0
            WHERE {where_clause}
            ORDER BY im.created_at DESC, im.id DESC
            LIMIT ? OFFSET ?
            """,
            params,
        ).fetchall()
        results = []
        for row in rows:
            msg = {
                "id": int(row["id"]),
                "platform": str(row["platform"] or ""),
                "chat_id": str(row["chat_id"] or ""),
                "chat_name": str(row["chat_name"] or ""),
                "message_id": str(row["message_id"] or ""),
                "sender_id": str(row["sender_id"] or ""),
                "sender_name": str(row["sender_name"] or ""),
                "sender_kind": str(row["sender_kind"] or ""),
                "content_type": str(row["content_type"] or ""),
                "text": str(row["text"] or ""),
                "from_self": bool(row["from_self"]),
                "received_at": str(row["received_at"] or ""),
                "created_at": str(row["created_at"] or ""),
            }
            if row["tx_id"] is not None:
                msg["transaction"] = {
                    "id": int(row["tx_id"]),
                    "amount": str(row["tx_amount"] or ""),
                    "category": str(row["tx_category"] or ""),
                    "input_sign": int(row["tx_input_sign"]),
                    "created_at": str(row["tx_created_at"] or ""),
                }
            else:
                msg["transaction"] = None
            results.append(msg)
        return results, total

    def count_incoming_messages(self) -> int:
        row = self.conn.execute(
            "SELECT COUNT(*) AS cnt FROM incoming_messages"
        ).fetchone()
        return int(row["cnt"])

    def undo_last(self, group_key: str) -> DBRow | None:
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
        self.conn.execute(
            "UPDATE transactions SET deleted = 1 WHERE id = ?", (row["id"],)
        )
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
            "by_category": {
                row["category"]: {
                    "count": int(row["count"]),
                    "total_rmb": float(row["total_rmb"]),
                }
                for row in cat_rows
            },
        }

    def get_history(self, group_key: str, limit: int = 20) -> list[DBRow]:
        return self.conn.execute(
            "SELECT * FROM transactions WHERE group_key = ? AND deleted = 0 ORDER BY id DESC LIMIT ?",
            (group_key, limit),
        ).fetchall()

    def get_history_by_category(
        self, group_key: str, category: str, limit: int = 50
    ) -> list[DBRow]:
        return self.conn.execute(
            "SELECT * FROM transactions WHERE group_key = ? AND deleted = 0 AND category = ? ORDER BY id DESC LIMIT ?",
            (group_key, category, limit),
        ).fetchall()

    def list_latest_transactions(self, limit: int = 8) -> list[DBRow]:
        return self.conn.execute(
            """
            SELECT
              tx.*,
              g.business_role AS business_role,
              g.group_num AS mapped_group_num,
              edit.edited_by AS edited_by,
              edit.edited_at AS edited_at
            FROM transactions tx
            LEFT JOIN groups g ON g.group_key = tx.group_key
            LEFT JOIN (
              SELECT DISTINCT ON (transaction_id)
                transaction_id,
                edited_by,
                edited_at
              FROM transaction_edit_logs
              ORDER BY transaction_id, edited_at DESC, id DESC
            ) edit ON edit.transaction_id = tx.id
            WHERE tx.deleted = 0
            ORDER BY tx.created_at DESC, tx.id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    def clear_group(self, group_key: str) -> int:
        cur = self.conn.execute(
            "UPDATE transactions SET deleted = 1 WHERE group_key = ? AND deleted = 0",
            (group_key,),
        )
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
                    "total_ngn": float(row["total_ngn"])
                    if row["total_ngn"] is not None
                    else None,
                }
            )
        return [
            {"category": key, "rate_groups": value}
            for key, value in category_map.items()
        ]

    def get_unsettled_transactions(self, group_key: str) -> list[DBRow]:
        return self.conn.execute(
            "SELECT * FROM transactions WHERE group_key = ? AND deleted = 0 AND settled = 0 ORDER BY id ASC",
            (group_key,),
        ).fetchall()

    def get_groups_with_unsettled_transactions(self) -> list[DBRow]:
        return self.conn.execute(
            "SELECT DISTINCT platform, group_key, chat_id, chat_name FROM transactions WHERE deleted = 0 AND settled = 0 ORDER BY group_key"
        ).fetchall()

    def set_group(
        self,
        *,
        platform: str,
        group_key: str,
        chat_id: str,
        chat_name: str,
        group_num: int,
    ) -> bool:
        if group_num < 0 or group_num > 9:
            return False
        self.conn.execute(
            """
            INSERT INTO groups (group_key, platform, chat_id, chat_name, group_num, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(group_key) DO UPDATE SET
              platform = excluded.platform,
              chat_id = excluded.chat_id,
              chat_name = excluded.chat_name,
              group_num = excluded.group_num,
              updated_at = CURRENT_TIMESTAMP
            """,
            (group_key, platform, chat_id, chat_name, group_num),
        )
        self.conn.commit()
        return True

    def get_group_num(self, group_key: str) -> int | None:
        row = self.conn.execute(
            "SELECT group_num FROM groups WHERE group_key = ?", (group_key,)
        ).fetchone()
        return int(row["group_num"]) if row and row["group_num"] is not None else None

    def is_group_active(self, group_key: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM groups WHERE group_key = ? AND group_num IS NOT NULL",
            (group_key,),
        ).fetchone()
        return row is not None

    def get_groups_by_num(self, group_num: int) -> list[DBRow]:
        return self.conn.execute(
            "SELECT * FROM groups WHERE group_num = ? ORDER BY chat_name", (group_num,)
        ).fetchall()

    def get_group_number_stats(self) -> dict[int, int]:
        stats = {index: 0 for index in range(10)}
        rows = self.conn.execute(
            "SELECT group_num, COUNT(*) AS cnt FROM groups WHERE group_num IS NOT NULL GROUP BY group_num"
        ).fetchall()
        for row in rows:
            stats[int(row["group_num"])] = int(row["cnt"])
        return stats

    def get_all_groups(self) -> list[DBRow]:
        return self.conn.execute(
            """
            SELECT
              g.*,
              COALESCE(tx.tx_balance, 0) AS tx_balance
            FROM groups g
            LEFT JOIN (
              SELECT group_key, SUM(rmb_value) AS tx_balance
              FROM transactions
              WHERE deleted = 0
              GROUP BY group_key
            ) tx ON tx.group_key = g.group_key
            ORDER BY g.chat_name
            """
        ).fetchall()

    def list_groups(self) -> list[DBRow]:
        return self.get_all_groups()

    def get_group_count(self) -> int:
        row = self.conn.execute(
            "SELECT COUNT(DISTINCT group_key) AS cnt FROM transactions WHERE deleted = 0"
        ).fetchone()
        return int(row["cnt"])

    def get_total_transaction_count(self) -> int:
        row = self.conn.execute(
            "SELECT COUNT(*) AS cnt FROM transactions WHERE deleted = 0"
        ).fetchone()
        return int(row["cnt"])

    def add_to_whitelist(
        self, user_key: str, added_by: str, note: str | None = None
    ) -> None:
        self.conn.execute(
            """
            INSERT INTO whitelist (user_key, added_by, note)
            VALUES (?, ?, ?)
            ON CONFLICT(user_key) DO NOTHING
            """,
            (user_key, added_by, note),
        )
        self.conn.commit()

    def remove_from_whitelist(self, user_key: str) -> bool:
        cur = self.conn.execute("DELETE FROM whitelist WHERE user_key = ?", (user_key,))
        self.conn.commit()
        return cur.rowcount > 0

    def is_whitelisted(self, user_key: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM whitelist WHERE user_key = ?", (user_key,)
        ).fetchone()
        return row is not None

    def get_whitelist(self) -> list[DBRow]:
        return self.conn.execute("SELECT * FROM whitelist ORDER BY added_at").fetchall()

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

    def remove_admin(self, user_key: str) -> bool:
        cur = self.conn.execute("DELETE FROM admins WHERE user_key = ?", (user_key,))
        self.conn.commit()
        return cur.rowcount > 0

    def is_admin(self, user_key: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM admins WHERE user_key = ?", (user_key,)
        ).fetchone()
        return row is not None

    def get_admins(self) -> list[DBRow]:
        return self.conn.execute("SELECT * FROM admins ORDER BY added_at").fetchall()

    def bind_identity(
        self,
        *,
        platform: str,
        chat_id: str,
        observed_id: str,
        observed_name: str,
        canonical_id: str,
    ) -> None:
        keys = []
        for value in (observed_id, observed_name):
            value = str(value or "").strip()
            if value and value not in keys:
                keys.append(value)
        scopes = [str(chat_id or "").strip(), "*"]
        scopes = [scope for scope in scopes if scope]
        for scope in scopes:
            for key in keys:
                self.conn.execute(
                    """
                    INSERT INTO identity_bindings (platform, chat_id, observed_key, canonical_id, observed_name, updated_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(platform, chat_id, observed_key) DO UPDATE SET
                      canonical_id = excluded.canonical_id,
                      observed_name = excluded.observed_name,
                      updated_at = CURRENT_TIMESTAMP
                    """,
                    (platform, scope, key, canonical_id, observed_name or observed_id),
                )
        self.conn.commit()

    def resolve_identity(
        self, *, platform: str, chat_id: str, observed_id: str, observed_name: str
    ) -> str:
        scopes = [str(chat_id or "").strip(), "*"]
        scopes = [scope for scope in scopes if scope]
        for key in (observed_id, observed_name):
            key = str(key or "").strip()
            if not key:
                continue
            for scope in scopes:
                row = self.conn.execute(
                    "SELECT canonical_id FROM identity_bindings WHERE platform = ? AND chat_id = ? AND observed_key = ?",
                    (platform, scope, key),
                ).fetchone()
                if row is not None and row["canonical_id"]:
                    return str(row["canonical_id"])
        return str(observed_id or observed_name or "")

    def set_ngn_rate(self, rate: str) -> None:
        self.conn.execute(
            "UPDATE settings SET value = ?, updated_at = CURRENT_TIMESTAMP WHERE key = 'ngn_rate'",
            (rate,),
        )
        self.conn.commit()

    def get_ngn_rate(self) -> float | None:
        row = self.conn.execute(
            "SELECT value FROM settings WHERE key = 'ngn_rate'"
        ).fetchone()
        if row is None or not row["value"]:
            return None
        return float(row["value"])

    def export_group_csv(self, group_key: str, export_dir: str | Path) -> Path | None:
        rows = self.conn.execute(
            "SELECT * FROM transactions WHERE group_key = ? AND deleted = 0 ORDER BY id ASC",
            (group_key,),
        ).fetchall()
        if not rows:
            return None
        export_dir = Path(export_dir)
        export_dir.mkdir(parents=True, exist_ok=True)
        safe_name = "".join(
            ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in group_key
        )
        path = export_dir / f"{safe_name}.csv"
        with path.open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                [
                    "id",
                    "platform",
                    "group_key",
                    "chat_name",
                    "sender_name",
                    "sign",
                    "amount",
                    "category",
                    "rate",
                    "rmb_value",
                    "raw",
                    "created_at",
                ]
            )
            for row in rows:
                writer.writerow(
                    [
                        row["id"],
                        row["platform"],
                        row["group_key"],
                        row["chat_name"],
                        row["sender_name"],
                        "+" if row["input_sign"] > 0 else "-",
                        row["amount"],
                        row["category"],
                        row["rate"] or "",
                        row["rmb_value"],
                        row["raw"],
                        row["created_at"],
                    ]
                )
        return path

    def add_manual_adjustment(
        self,
        *,
        period_id: int,
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
              period_id, group_key, opening_delta, income_delta, expense_delta,
              closing_delta, note, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                period_id,
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

    def get_manual_adjustments(self, period_id: int) -> list[DBRow]:
        return self.conn.execute(
            "SELECT * FROM manual_adjustments WHERE period_id = ? ORDER BY id ASC",
            (period_id,),
        ).fetchall()

    def get_manual_adjustment_total(
        self, group_key: str, up_to_period_id: int | None = None
    ) -> float:
        if up_to_period_id is None:
            row = self.conn.execute(
                "SELECT COALESCE(SUM(closing_delta), 0) AS total FROM manual_adjustments WHERE group_key = ?",
                (group_key,),
            ).fetchone()
        else:
            row = self.conn.execute(
                """
                SELECT COALESCE(SUM(closing_delta), 0) AS total
                FROM manual_adjustments
                WHERE group_key = ? AND period_id <= ?
                """,
                (group_key, up_to_period_id),
            ).fetchone()
        return float(row["total"] or 0)

    def list_finance_adjustment_entries(
        self,
        *,
        period_id: int | None = None,
        start_at: str | None = None,
        end_at: str | None = None,
        include_unscoped_only: bool = False,
    ) -> list[DBRow]:
        conditions: list[str] = []
        params: list[object] = []
        if include_unscoped_only:
            conditions.append("entry.period_id IS NULL")
        elif period_id is not None:
            conditions.append("entry.period_id = ?")
            params.append(period_id)
        if start_at is not None:
            conditions.append("entry.created_at >= ?")
            params.append(start_at)
        if end_at is not None:
            conditions.append("entry.created_at <= ?")
            params.append(end_at)
        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)
        return self.conn.execute(
            f"""
            SELECT
              entry.*,
              g.platform AS platform,
              g.chat_id AS chat_id,
              g.chat_name AS chat_name,
              g.group_num AS group_num,
              g.business_role AS mapped_business_role
            FROM finance_adjustment_entries entry
            LEFT JOIN groups g ON g.group_key = entry.group_key
            {where_clause}
            ORDER BY entry.created_at DESC, entry.id DESC
            """,
            params,
        ).fetchall()

    def list_finance_adjustment_entries_by_transaction_ids(
        self, transaction_ids: list[int]
    ) -> list[DBRow]:
        normalized_ids = sorted(
            {int(item) for item in transaction_ids if int(item) > 0}
        )
        if not normalized_ids:
            return []
        placeholders = ",".join("?" for _ in normalized_ids)
        return self.conn.execute(
            f"""
            SELECT
              entry.*,
              g.platform AS platform,
              g.chat_id AS chat_id,
              g.chat_name AS chat_name,
              g.group_num AS group_num,
              g.business_role AS mapped_business_role
            FROM finance_adjustment_entries entry
            LEFT JOIN groups g ON g.group_key = entry.group_key
            WHERE entry.linked_transaction_id IN ({placeholders})
            ORDER BY entry.created_at DESC, entry.id DESC
            """,
            normalized_ids,
        ).fetchall()

    def get_group_by_key(self, group_key: str) -> DBRow | None:
        return self.conn.execute(
            "SELECT * FROM groups WHERE group_key = ?",
            (group_key,),
        ).fetchone()

    def list_accounting_periods(self) -> list[DBRow]:
        return self.conn.execute(
            "SELECT * FROM accounting_periods ORDER BY id ASC"
        ).fetchall()

    def get_accounting_period(self, period_id: int) -> DBRow | None:
        return self.conn.execute(
            "SELECT * FROM accounting_periods WHERE id = ?",
            (period_id,),
        ).fetchone()

    def insert_accounting_period(
        self,
        *,
        start_at: str,
        end_at: str,
        closed_at: str,
        closed_by: str,
        note: str | None = None,
        has_adjustment: int = 0,
        snapshot_version: int = 1,
    ) -> int:
        cur = self.conn.execute(
            """
            INSERT INTO accounting_periods (
              start_at, end_at, closed_at, closed_by, note, has_adjustment, snapshot_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            RETURNING id
            """,
            (
                start_at,
                end_at,
                closed_at,
                closed_by,
                note,
                has_adjustment,
                snapshot_version,
            ),
        )
        row = cur.fetchone()
        if row is not None:
            if hasattr(row, "keys") and "id" in row.keys():
                return int(row["id"])
            if isinstance(row, dict) and row.get("id") is not None:
                return int(row["id"])
        if cur.lastrowid is not None:
            return int(cur.lastrowid)
        raise RuntimeError("failed to insert accounting_periods row")

    def insert_period_group_snapshot(
        self,
        *,
        period_id: int,
        group_key: str,
        platform: str,
        chat_name: str,
        group_num: int | None,
        business_role: str | None,
        opening_balance: float,
        income: float,
        expense: float,
        closing_balance: float,
        transaction_count: int,
        anomaly_flags_json: str = "[]",
    ) -> int:
        cur = self.conn.execute(
            """
            INSERT INTO period_group_snapshots (
              period_id, group_key, platform, chat_name, group_num, business_role,
              opening_balance, income, expense, closing_balance, transaction_count,
              anomaly_flags_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            RETURNING id
            """,
            (
                period_id,
                group_key,
                platform,
                chat_name,
                group_num,
                business_role,
                opening_balance,
                income,
                expense,
                closing_balance,
                transaction_count,
                anomaly_flags_json,
            ),
        )
        row = cur.fetchone()
        if row is not None:
            if hasattr(row, "keys") and "id" in row.keys():
                return int(row["id"])
            if isinstance(row, dict) and row.get("id") is not None:
                return int(row["id"])
        if cur.lastrowid is not None:
            return int(cur.lastrowid)
        raise RuntimeError("failed to insert period_group_snapshots row")

    def list_period_group_snapshots(self, period_id: int) -> list[DBRow]:
        return self.conn.execute(
            """
            SELECT *
            FROM period_group_snapshots
            WHERE period_id = ?
            ORDER BY id ASC
            """,
            (period_id,),
        ).fetchall()

    def get_group_balance_before(self, group_key: str, before_at: str) -> float:
        row = self.conn.execute(
            """
            SELECT COALESCE(SUM(rmb_value), 0) AS total
            FROM transactions
            WHERE group_key = ?
              AND created_at < ?
              AND (deleted = 0 OR settled = 1)
            """,
            (group_key, before_at),
        ).fetchone()
        return float(row["total"] or 0)

    def list_group_transactions_between(
        self, group_key: str, start_at: str, end_at: str
    ) -> list[DBRow]:
        return self.conn.execute(
            """
            SELECT *
            FROM transactions
            WHERE group_key = ?
              AND created_at > ?
              AND created_at <= ?
              AND (deleted = 0 OR settled = 1)
            ORDER BY created_at ASC, id ASC
            """,
            (group_key, start_at, end_at),
        ).fetchall()

    def list_period_transactions(self, period_id: int) -> list[DBRow]:
        return self.conn.execute(
            """
            SELECT
              tx.*,
              g.business_role AS business_role,
              g.group_num AS mapped_group_num,
              edit.edited_by AS edited_by,
              edit.edited_at AS edited_at,
              edit.note AS edit_note
            FROM transactions tx
            INNER JOIN accounting_periods period ON period.id = ?
            LEFT JOIN groups g ON g.group_key = tx.group_key
            LEFT JOIN (
              SELECT DISTINCT ON (transaction_id)
                transaction_id,
                edited_by,
                edited_at,
                note
              FROM transaction_edit_logs
              ORDER BY transaction_id, edited_at DESC, id DESC
            ) edit ON edit.transaction_id = tx.id
            WHERE tx.created_at > period.start_at
              AND tx.created_at <= period.end_at
              AND (tx.deleted = 0 OR tx.settled = 1)
            ORDER BY tx.created_at DESC, tx.id DESC
            """,
            (period_id,),
        ).fetchall()

    def list_current_window_transactions(
        self, start_after: str | None = None
    ) -> list[DBRow]:
        if start_after is None:
            return self.conn.execute(
                """
                SELECT
                  tx.*,
                  g.business_role AS business_role,
                  g.group_num AS mapped_group_num,
                  edit.edited_by AS edited_by,
                  edit.edited_at AS edited_at,
                  edit.note AS edit_note
                FROM transactions tx
                LEFT JOIN groups g ON g.group_key = tx.group_key
                LEFT JOIN (
                  SELECT DISTINCT ON (transaction_id)
                    transaction_id,
                    edited_by,
                    edited_at,
                    note
                  FROM transaction_edit_logs
                  ORDER BY transaction_id, edited_at DESC, id DESC
                ) edit ON edit.transaction_id = tx.id
                WHERE tx.deleted = 0
                  AND tx.settled = 0
                ORDER BY tx.created_at DESC, tx.id DESC
                """
            ).fetchall()
        return self.conn.execute(
            """
            SELECT
              tx.*,
              g.business_role AS business_role,
              g.group_num AS mapped_group_num,
              edit.edited_by AS edited_by,
              edit.edited_at AS edited_at,
              edit.note AS edit_note
            FROM transactions tx
            LEFT JOIN groups g ON g.group_key = tx.group_key
            LEFT JOIN (
              SELECT DISTINCT ON (transaction_id)
                transaction_id,
                edited_by,
                edited_at,
                note
              FROM transaction_edit_logs
              ORDER BY transaction_id, edited_at DESC, id DESC
            ) edit ON edit.transaction_id = tx.id
            WHERE tx.deleted = 0
              AND tx.settled = 0
              AND tx.created_at > ?
            ORDER BY tx.created_at DESC, tx.id DESC
            """,
            (start_after,),
        ).fetchall()

    def list_transactions_in_date_range(
        self, start_at: str, end_at: str
    ) -> list[DBRow]:
        return self.conn.execute(
            """
            SELECT
              tx.*,
              g.business_role AS business_role,
              g.group_num AS mapped_group_num,
              edit.edited_by AS edited_by,
              edit.edited_at AS edited_at,
              edit.note AS edit_note
            FROM transactions tx
            LEFT JOIN groups g ON g.group_key = tx.group_key
            LEFT JOIN (
              SELECT DISTINCT ON (transaction_id)
                transaction_id,
                edited_by,
                edited_at,
                note
              FROM transaction_edit_logs
              ORDER BY transaction_id, edited_at DESC, id DESC
            ) edit ON edit.transaction_id = tx.id
            WHERE tx.deleted = 0
              AND tx.created_at >= ?
              AND tx.created_at <= ?
            ORDER BY tx.created_at DESC, tx.id DESC
            """,
            (start_at, end_at),
        ).fetchall()

    def mark_transactions_closed(
        self,
        transaction_ids: list[int],
        *,
        settled_at: str,
        commit: bool = True,
    ) -> int:
        ids = [int(item) for item in transaction_ids]
        if not ids:
            return 0
        placeholders = ",".join("?" for _ in ids)
        cur = self.conn.execute(
            f"""
            UPDATE transactions
            SET settled = 1,
                settled_at = ?
            WHERE id IN ({placeholders})
              AND deleted = 0
              AND settled = 0
            """,
            [settled_at, *ids],
        )
        if commit:
            self.conn.commit()
        return int(cur.rowcount or 0)

    def list_accounting_period_snapshots(self) -> list[DBRow]:
        return self.conn.execute(
            """
            SELECT
              p.id AS period_id,
              p.closed_at AS closed_at,
              s.group_key AS group_key,
              s.closing_balance AS closing_balance
            FROM accounting_periods p
            INNER JOIN period_group_snapshots s ON s.period_id = p.id
            ORDER BY p.closed_at ASC, p.id ASC, s.id ASC
            """
        ).fetchall()

    def replace_period_card_stats(self, period_id: int, rows: list[dict]) -> None:
        self.conn.execute(
            "DELETE FROM period_card_stats WHERE period_id = ?", (period_id,)
        )
        for row in rows:
            self.conn.execute(
                """
                INSERT INTO period_card_stats (
                  period_id, group_key, business_role, card_type, usd_amount, rate,
                  rmb_amount, unit_face_value, unit_count, sample_raw
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    period_id,
                    row["group_key"],
                    row["business_role"],
                    row["card_type"],
                    row["usd_amount"],
                    row["rate"],
                    row["rmb_amount"],
                    row["unit_face_value"],
                    row["unit_count"],
                    row["sample_raw"],
                ),
            )

    def list_period_card_stats(self, period_id: int) -> list[DBRow]:
        return self.conn.execute(
            """
            SELECT *
            FROM period_card_stats
            WHERE period_id = ?
            ORDER BY id ASC
            """,
            (period_id,),
        ).fetchall()

    def save_group_combination(
        self, *, name: str, group_numbers: list[int], note: str, created_by: str
    ) -> int:
        cur = self.conn.execute(
            """
            INSERT INTO group_combinations (name, note, created_by, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(name) DO UPDATE SET
              note = excluded.note,
              updated_at = CURRENT_TIMESTAMP
            """,
            (name, note, created_by),
        )
        if cur.lastrowid:
            combination_id = int(cur.lastrowid)
        else:
            row = self.conn.execute(
                "SELECT id FROM group_combinations WHERE name = ?", (name,)
            ).fetchone()
            combination_id = int(row["id"])
        self.conn.execute(
            "DELETE FROM group_combination_items WHERE combination_id = ?",
            (combination_id,),
        )
        for group_num in sorted(set(group_numbers)):
            self.conn.execute(
                "INSERT INTO group_combination_items (combination_id, group_num) VALUES (?, ?)",
                (combination_id, group_num),
            )
        self.conn.commit()
        return combination_id

    def list_group_combinations(self) -> list[DBRow]:
        return self.conn.execute(
            """
            SELECT
              gc.id,
              gc.name,
              gc.note,
              gc.created_by,
              gc.created_at,
              gc.updated_at,
              COALESCE(STRING_AGG(CAST(gci.group_num AS TEXT), ',' ORDER BY gci.group_num), '') AS group_numbers
            FROM group_combinations gc
            LEFT JOIN group_combination_items gci ON gci.combination_id = gc.id
            GROUP BY gc.id, gc.name, gc.note, gc.created_by, gc.created_at, gc.updated_at
            ORDER BY gc.name
            """
        ).fetchall()

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
              platform, chat_id, sender_id, message, amount, category, rate,
              rmb_value, ngn_value, duration_minutes, remind_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                platform,
                chat_id,
                sender_id,
                message,
                amount,
                category,
                rate,
                rmb_value,
                ngn_value,
                duration_minutes,
                remind_at,
            ),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def get_due_reminders(self, now_text: str) -> list[ReminderPayload]:
        rows = self.conn.execute(
            "SELECT * FROM reminders WHERE sent = 0 AND remind_at <= ? ORDER BY id ASC",
            (now_text,),
        ).fetchall()
        return [self._reminder_from_row(row) for row in rows]

    def mark_reminder_sent(self, reminder_id: int) -> None:
        self.conn.execute("UPDATE reminders SET sent = 1 WHERE id = ?", (reminder_id,))
        self.conn.commit()

    def record_parse_result(
        self,
        *,
        platform: str,
        chat_id: str,
        message_id: str,
        classification: str,
        parse_status: str,
        raw_text: str | None = None,
    ) -> int:
        cur = self.conn.execute(
            """
            INSERT INTO message_parse_results (
              platform, chat_id, message_id, classification, parse_status, raw_text
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(platform, chat_id, message_id) DO UPDATE SET
              classification = excluded.classification,
              parse_status = excluded.parse_status,
              raw_text = excluded.raw_text
            """,
            (platform, chat_id, message_id, classification, parse_status, raw_text),
        )
        self.conn.commit()
        return self._last_insert_id(cur)

    def record_quote_document(
        self,
        *,
        platform: str,
        source_group_key: str,
        chat_id: str,
        chat_name: str,
        message_id: str,
        source_name: str,
        sender_id: str,
        raw_text: str,
        message_time: str,
        parser_template: str,
        parser_version: str,
        confidence: float,
        parse_status: str,
    ) -> int:
        cur = self.conn.execute(
            """
            INSERT INTO quote_documents (
              platform, source_group_key, chat_id, chat_name, message_id,
              source_name, sender_id, raw_text, message_time, parser_template,
              parser_version, confidence, parse_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                platform,
                source_group_key,
                chat_id,
                chat_name,
                message_id,
                source_name,
                sender_id,
                raw_text,
                message_time,
                parser_template,
                parser_version,
                confidence,
                parse_status,
            ),
        )
        self.conn.commit()
        return self._last_insert_id(cur)

    def deactivate_old_quotes_for_group(self, *, source_group_key: str) -> None:
        """同一群发新消息时，将旧的 active 报价标记为 inactive。"""
        self.conn.execute(
            "UPDATE quote_price_rows SET quote_status = 'inactive' "
            "WHERE source_group_key = ? AND quote_status = 'active'",
            (source_group_key,),
        )
        self.conn.commit()

    def upsert_quote_price_row_with_history(
        self,
        *,
        quote_document_id: int,
        message_id: str,
        platform: str,
        source_group_key: str,
        chat_id: str,
        chat_name: str,
        source_name: str,
        sender_id: str,
        card_type: str,
        country_or_currency: str,
        amount_range: str,
        multiplier: str | None,
        form_factor: str,
        price: float,
        quote_status: str,
        restriction_text: str,
        source_line: str,
        raw_text: str,
        message_time: str,
        effective_at: str,
        expires_at: str | None,
        parser_template: str,
        parser_version: str,
        confidence: float,
    ) -> int:
        active_rows = self.conn.execute(
            """
            SELECT id
            FROM quote_price_rows
            WHERE platform = ?
              AND source_group_key = ?
              AND card_type = ?
              AND country_or_currency = ?
              AND amount_range = ?
              AND form_factor = ?
              AND COALESCE(multiplier, '') = COALESCE(?, '')
              AND expires_at IS NULL
            ORDER BY effective_at DESC, id DESC
            """,
            (
                platform,
                source_group_key,
                card_type,
                country_or_currency,
                amount_range,
                form_factor,
                multiplier,
            ),
        ).fetchall()
        for row in active_rows:
            self.conn.execute(
                "UPDATE quote_price_rows SET expires_at = ?, quote_status = 'superseded' WHERE id = ?",
                (effective_at, row["id"]),
            )
        cur = self.conn.execute(
            """
            INSERT INTO quote_price_rows (
              quote_document_id, platform, source_group_key, chat_id, chat_name,
              message_id, source_name, sender_id, card_type, country_or_currency,
              amount_range, multiplier, form_factor, price, quote_status,
              restriction_text, source_line, raw_text, message_time, effective_at,
              expires_at, parser_template, parser_version, confidence
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                quote_document_id,
                platform,
                source_group_key,
                chat_id,
                chat_name,
                message_id,
                source_name,
                sender_id,
                card_type,
                country_or_currency,
                amount_range,
                multiplier,
                form_factor,
                price,
                quote_status,
                restriction_text,
                source_line,
                raw_text,
                message_time,
                effective_at,
                expires_at,
                parser_template,
                parser_version,
                confidence,
            ),
        )
        self.conn.commit()
        return self._last_insert_id(cur)

    def record_quote_exception(
        self,
        *,
        quote_document_id: int,
        platform: str,
        source_group_key: str,
        chat_id: str,
        chat_name: str,
        source_name: str,
        sender_id: str,
        reason: str,
        source_line: str,
        raw_text: str,
        message_time: str,
        parser_template: str,
        parser_version: str,
        confidence: float,
    ) -> int:
        cur = self.conn.execute(
            """
            INSERT INTO quote_parse_exceptions (
              quote_document_id, platform, source_group_key, chat_id, chat_name,
              source_name, sender_id, reason, source_line, raw_text, message_time,
              parser_template, parser_version, confidence
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                quote_document_id,
                platform,
                source_group_key,
                chat_id,
                chat_name,
                source_name,
                sender_id,
                reason,
                source_line,
                raw_text,
                message_time,
                parser_template,
                parser_version,
                confidence,
            ),
        )
        self.conn.commit()
        return self._last_insert_id(cur)

    @staticmethod
    def _normalize_quote_exception_text_for_suppression(text: str) -> str:
        normalized_lines: list[str] = []
        for raw_line in str(text or "").translate(
            _QUOTE_EXCEPTION_SUPPRESSION_TRANSLATION
        ).splitlines():
            line = re.sub(r"\s+", " ", raw_line).strip()
            if line:
                normalized_lines.append(line)
        return "\n".join(normalized_lines)

    def build_quote_exception_suppression_signature(
        self,
        *,
        source_group_key: str,
        reason: str,
        source_line: str,
        raw_text: str,
    ) -> str:
        parts = (
            str(source_group_key or "").strip(),
            str(reason or "").strip(),
            self._normalize_quote_exception_text_for_suppression(source_line),
            self._normalize_quote_exception_text_for_suppression(raw_text),
        )
        return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()

    def encode_quote_exception_suppression_note(
        self,
        *,
        source_group_key: str,
        reason: str,
        source_line: str,
        raw_text: str,
        note: str = "",
    ) -> str:
        payload = {
            "version": _QUOTE_EXCEPTION_SUPPRESSION_NOTE_VERSION,
            "signature": self.build_quote_exception_suppression_signature(
                source_group_key=source_group_key,
                reason=reason,
                source_line=source_line,
                raw_text=raw_text,
            ),
        }
        marker = f"{_QUOTE_EXCEPTION_SUPPRESSION_NOTE_PREFIX}{json.dumps(payload, ensure_ascii=False)}"
        suffix = str(note or "").strip()
        return marker if not suffix else f"{marker}\n{suffix}"

    @staticmethod
    def _parse_quote_exception_suppression_note(note: str) -> dict[str, Any] | None:
        text = str(note or "").strip()
        if not text.startswith(_QUOTE_EXCEPTION_SUPPRESSION_NOTE_PREFIX):
            return None
        payload_line = text.splitlines()[0][len(_QUOTE_EXCEPTION_SUPPRESSION_NOTE_PREFIX) :]
        try:
            payload = json.loads(payload_line)
        except json.JSONDecodeError:
            return None
        if not isinstance(payload, dict):
            return None
        return payload

    def _quote_exception_suppression_signature_from_row(self, row: DBRow) -> str:
        payload = self._parse_quote_exception_suppression_note(
            str(row.get("resolution_note") or "")
        )
        signature = str((payload or {}).get("signature") or "").strip()
        if signature:
            return signature
        return self.build_quote_exception_suppression_signature(
            source_group_key=str(row.get("source_group_key") or ""),
            reason=str(row.get("reason") or ""),
            source_line=str(row.get("source_line") or ""),
            raw_text=str(row.get("raw_text") or ""),
        )

    def is_quote_exception_suppressed(
        self,
        *,
        source_group_key: str,
        reason: str,
        source_line: str,
        raw_text: str,
    ) -> bool:
        target_signature = self.build_quote_exception_suppression_signature(
            source_group_key=source_group_key,
            reason=reason,
            source_line=source_line,
            raw_text=raw_text,
        )
        rows = self.conn.execute(
            """
            SELECT source_group_key, reason, source_line, raw_text, resolution_note
            FROM quote_parse_exceptions
            WHERE source_group_key = ?
              AND reason = ?
              AND resolution_status = 'ignored'
            ORDER BY id DESC
            """,
            (source_group_key, reason),
        ).fetchall()
        for row in rows:
            if self._quote_exception_suppression_signature_from_row(
                self._serialize_quote_db_row(row)
            ) == target_signature:
                return True
        return False

    def record_quote_exception_unless_suppressed(
        self,
        *,
        quote_document_id: int,
        platform: str,
        source_group_key: str,
        chat_id: str,
        chat_name: str,
        source_name: str,
        sender_id: str,
        reason: str,
        source_line: str,
        raw_text: str,
        message_time: str,
        parser_template: str,
        parser_version: str,
        confidence: float,
    ) -> int:
        if self.is_quote_exception_suppressed(
            source_group_key=source_group_key,
            reason=reason,
            source_line=source_line,
            raw_text=raw_text,
        ):
            return 0
        return self.record_quote_exception(
            quote_document_id=quote_document_id,
            platform=platform,
            source_group_key=source_group_key,
            chat_id=chat_id,
            chat_name=chat_name,
            source_name=source_name,
            sender_id=sender_id,
            reason=reason,
            source_line=source_line,
            raw_text=raw_text,
            message_time=message_time,
            parser_template=parser_template,
            parser_version=parser_version,
            confidence=confidence,
        )

    def list_quote_dictionary_aliases(
        self,
        *,
        category: str | None = None,
        include_disabled: bool = True,
        limit: int = 1000,
    ) -> list[DBRow]:
        where_parts: list[str] = []
        params: list[Any] = []
        if category:
            where_parts.append("category = ?")
            params.append(category)
        if not include_disabled:
            where_parts.append("enabled = 1")
        where_clause = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""
        params.append(limit)
        rows = self.conn.execute(
            f"""
            SELECT *
            FROM quote_dictionary_aliases
            {where_clause}
            ORDER BY category ASC,
                     CASE WHEN scope_chat_id = '' THEN 1 ELSE 0 END ASC,
                     alias ASC,
                     id DESC
            LIMIT ?
            """,
            params,
        ).fetchall()
        return [self._serialize_quote_db_row(row) for row in rows]

    def list_quote_dictionary_aliases_for_scope(
        self,
        *,
        platform: str,
        chat_id: str,
    ) -> list[DBRow]:
        rows = self.conn.execute(
            """
            SELECT *
            FROM quote_dictionary_aliases
            WHERE enabled = 1
              AND (
                (scope_platform = '' AND scope_chat_id = '')
                OR (scope_platform = ? AND scope_chat_id = ?)
              )
            ORDER BY
              CASE WHEN scope_chat_id = '' THEN 1 ELSE 0 END ASC,
              category ASC,
              alias ASC,
              id DESC
            """,
            (platform, chat_id),
        ).fetchall()
        return [self._serialize_quote_db_row(row) for row in rows]

    def upsert_quote_dictionary_alias(
        self,
        *,
        category: str,
        alias: str,
        canonical_value: str,
        canonical_input: str = "",
        scope_platform: str = "",
        scope_chat_id: str = "",
        note: str = "",
        enabled: bool = True,
    ) -> int:
        cur = self.conn.execute(
            """
            INSERT INTO quote_dictionary_aliases (
              category, alias, canonical_value, canonical_input, scope_platform,
              scope_chat_id, note, enabled, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(category, alias, scope_platform, scope_chat_id) DO UPDATE SET
              canonical_value = excluded.canonical_value,
              canonical_input = excluded.canonical_input,
              note = excluded.note,
              enabled = excluded.enabled,
              updated_at = CURRENT_TIMESTAMP
            """,
            (
                category,
                alias,
                canonical_value,
                canonical_input,
                scope_platform,
                scope_chat_id,
                note,
                1 if enabled else 0,
            ),
        )
        self.conn.commit()
        row = self.conn.execute(
            """
            SELECT id
            FROM quote_dictionary_aliases
            WHERE category = ?
              AND alias = ?
              AND scope_platform = ?
              AND scope_chat_id = ?
            LIMIT 1
            """,
            (category, alias, scope_platform, scope_chat_id),
        ).fetchone()
        return int(row["id"]) if row else self._last_insert_id(cur)

    def set_quote_dictionary_alias_enabled(
        self,
        *,
        alias_id: int,
        enabled: bool,
    ) -> int:
        cur = self.conn.execute(
            """
            UPDATE quote_dictionary_aliases
            SET enabled = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (1 if enabled else 0, alias_id),
        )
        self.conn.commit()
        return int(getattr(cur, "rowcount", 0) or 0)

    def get_quote_exception(self, *, exception_id: int) -> DBRow | None:
        row = self.conn.execute(
            """
            SELECT *
            FROM quote_parse_exceptions
            WHERE id = ?
            LIMIT 1
            """,
            (exception_id,),
        ).fetchone()
        return self._serialize_quote_db_row(row) if row else None

    def resolve_quote_exception(
        self,
        *,
        exception_id: int,
        resolution_status: str,
        resolution_note: str = "",
    ) -> int:
        cur = self.conn.execute(
            """
            UPDATE quote_parse_exceptions
            SET resolution_status = ?,
                resolution_note = ?,
                resolved_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (resolution_status, resolution_note, exception_id),
        )
        self.conn.commit()
        return int(getattr(cur, "rowcount", 0) or 0)

    def update_quote_exception(
        self,
        *,
        exception_id: int,
        resolution_status: str,
        resolution_note: str = "",
        source_line: str | None = None,
    ) -> int:
        assignments = [
            "resolution_status = ?",
            "resolution_note = ?",
            "resolved_at = CASE WHEN ? = 'open' THEN NULL ELSE CURRENT_TIMESTAMP END",
        ]
        params: list[Any] = [
            resolution_status,
            resolution_note,
            resolution_status,
        ]
        if source_line is not None:
            assignments.append("source_line = ?")
            params.append(source_line)
        params.append(exception_id)
        cur = self.conn.execute(
            f"""
            UPDATE quote_parse_exceptions
            SET {", ".join(assignments)}
            WHERE id = ?
            """,
            params,
        )
        self.conn.commit()
        return int(getattr(cur, "rowcount", 0) or 0)

    def attach_quote_exception_to_restrictions(self, *, exception_id: int) -> DBRow:
        exception = self.conn.execute(
            "SELECT * FROM quote_parse_exceptions WHERE id = ? LIMIT 1",
            (exception_id,),
        ).fetchone()
        if not exception:
            return {"updated": 0, "attached": 0, "status": "not_found"}
        source_line = str(exception["source_line"] or "").strip()
        if str(exception["reason"] or "") != "blocked_or_question_line" or not source_line:
            return {"updated": 0, "attached": 0, "status": "not_attachable"}

        rows = self.conn.execute(
            """
            SELECT *
            FROM quote_price_rows
            WHERE quote_document_id = ?
              AND quote_status = 'active'
              AND expires_at IS NULL
            ORDER BY id ASC
            """,
            (exception["quote_document_id"],),
        ).fetchall()
        if not rows:
            return {"updated": 0, "attached": 0, "status": "no_target_rows"}

        card_hint = self._quote_exception_card_hint(source_line)
        target_rows = [
            row for row in rows if card_hint and str(row["card_type"] or "") == card_hint
        ]
        if not target_rows and card_hint:
            return {
                "updated": 0,
                "attached": 0,
                "status": "no_matching_card",
                "card_type": card_hint,
            }
        if not target_rows:
            card_types = {str(row["card_type"] or "") for row in rows}
            if len(card_types) != 1:
                return {"updated": 0, "attached": 0, "status": "ambiguous_target"}
            target_rows = list(rows)

        updated = 0
        for row in target_rows:
            current_text = str(row["restriction_text"] or "").strip()
            if source_line in current_text:
                continue
            next_text = self._append_quote_restriction(current_text, source_line)
            cur = self.conn.execute(
                "UPDATE quote_price_rows SET restriction_text = ? WHERE id = ?",
                (next_text, row["id"]),
            )
            updated += int(getattr(cur, "rowcount", 0) or 0)

        self.conn.execute(
            """
            UPDATE quote_parse_exceptions
            SET resolution_status = 'resolved',
                resolution_note = ?,
                resolved_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (f"attached_to_restrictions:{updated}", exception_id),
        )
        self.conn.commit()
        return {
            "updated": 1,
            "attached": updated,
            "status": "attached",
            "card_type": card_hint or "",
        }

    @staticmethod
    def _append_quote_restriction(current_text: str, source_line: str) -> str:
        if not current_text:
            return source_line
        return f"{current_text} | {source_line}"

    @staticmethod
    def _quote_exception_card_hint(source_line: str) -> str:
        normalized = source_line.lower()
        aliases = (
            ("razer", "Razer"),
            ("雷蛇", "Razer"),
            ("steam", "Steam"),
            ("蒸汽", "Steam"),
            ("xbox", "Xbox"),
            ("google play", "Google Play"),
            ("google", "Google Play"),
            ("谷歌", "Google Play"),
            ("roblox", "Roblox"),
            ("罗布乐思", "Roblox"),
            ("paysafe", "Paysafe"),
            ("安全支付", "Paysafe"),
            ("apple", "Apple"),
            ("itunes", "Apple"),
        )
        for alias, card_type in aliases:
            if alias.lower() in normalized:
                return card_type
        return ""

    def create_quote_inquiry_context(
        self,
        *,
        platform: str,
        source_group_key: str,
        chat_id: str,
        chat_name: str,
        card_type: str,
        country_or_currency: str,
        amount_range: str,
        multiplier: str | None = None,
        form_factor: str = "不限",
        requested_by: str = "web",
        prompt_text: str = "",
        expires_at: str | None = None,
    ) -> int:
        cur = self.conn.execute(
            """
            INSERT INTO quote_inquiry_contexts (
              platform, source_group_key, chat_id, chat_name, card_type,
              country_or_currency, amount_range, multiplier, form_factor,
              requested_by, prompt_text, status, expires_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'open', COALESCE(?, CURRENT_TIMESTAMP + INTERVAL '10 minutes'))
            """,
            (
                platform,
                source_group_key,
                chat_id,
                chat_name,
                card_type,
                country_or_currency,
                amount_range,
                multiplier,
                form_factor,
                requested_by,
                prompt_text,
                expires_at,
            ),
        )
        self.conn.commit()
        return self._last_insert_id(cur)

    def find_open_quote_inquiry_context(
        self,
        *,
        platform: str,
        chat_id: str,
    ) -> DBRow | None:
        row = self.conn.execute(
            """
            SELECT *
            FROM quote_inquiry_contexts
            WHERE platform = ?
              AND chat_id = ?
              AND status = 'open'
              AND expires_at >= CURRENT_TIMESTAMP
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """,
            (platform, chat_id),
        ).fetchone()
        return dict(row) if row else None

    def resolve_quote_inquiry_context(
        self,
        *,
        inquiry_id: int,
        resolved_message_id: str,
    ) -> int:
        cur = self.conn.execute(
            """
            UPDATE quote_inquiry_contexts
            SET status = 'resolved',
                resolved_message_id = ?,
                resolved_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (resolved_message_id, inquiry_id),
        )
        self.conn.commit()
        return int(getattr(cur, "rowcount", 0) or 0)

    def list_quote_inquiry_contexts(
        self,
        *,
        limit: int = 100,
    ) -> list[DBRow]:
        rows = self.conn.execute(
            """
            SELECT *
            FROM quote_inquiry_contexts
            ORDER BY
              CASE WHEN status = 'open' AND expires_at >= CURRENT_TIMESTAMP THEN 0 ELSE 1 END ASC,
              created_at DESC,
              id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [self._serialize_quote_db_row(row) for row in rows]

    def upsert_quote_group_profile(
        self,
        *,
        platform: str,
        chat_id: str,
        chat_name: str,
        default_card_type: str = "",
        default_country_or_currency: str = "",
        default_form_factor: str = "不限",
        default_multiplier: str = "",
        parser_template: str = "",
        stale_after_minutes: int = 120,
        note: str = "",
        template_config: str = "",
    ) -> int:
        cur = self.conn.execute(
            """
            INSERT INTO quote_group_profiles (
              platform, chat_id, chat_name, default_card_type,
              default_country_or_currency, default_form_factor, default_multiplier,
              parser_template, stale_after_minutes, note, template_config, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(platform, chat_id) DO UPDATE SET
              chat_name = excluded.chat_name,
              default_card_type = excluded.default_card_type,
              default_country_or_currency = excluded.default_country_or_currency,
              default_form_factor = excluded.default_form_factor,
              default_multiplier = excluded.default_multiplier,
              parser_template = excluded.parser_template,
              stale_after_minutes = excluded.stale_after_minutes,
              note = excluded.note,
              template_config = excluded.template_config,
              updated_at = CURRENT_TIMESTAMP
            """,
            (
                platform,
                chat_id,
                chat_name,
                default_card_type,
                default_country_or_currency,
                default_form_factor,
                default_multiplier,
                parser_template,
                stale_after_minutes,
                note,
                template_config,
            ),
        )
        self.conn.commit()
        existing = self.get_quote_group_profile(platform=platform, chat_id=chat_id)
        return int(existing["id"]) if existing else self._last_insert_id(cur)

    def get_quote_group_profile(self, *, platform: str, chat_id: str) -> DBRow | None:
        row = self.conn.execute(
            """
            SELECT *
            FROM quote_group_profiles
            WHERE platform = ? AND chat_id = ?
            LIMIT 1
            """,
            (platform, chat_id),
        ).fetchone()
        return self._serialize_quote_db_row(row) if row else None

    def get_quote_group_profile_by_name(self, *, platform: str, chat_name: str) -> DBRow | None:
        row = self.conn.execute(
            """
            SELECT *
            FROM quote_group_profiles
            WHERE platform = ? AND chat_name = ?
            ORDER BY updated_at DESC, id DESC
            LIMIT 1
            """,
            (platform, chat_name),
        ).fetchone()
        return self._serialize_quote_db_row(row) if row else None

    def list_quote_group_profiles(self, *, limit: int = 200) -> list[DBRow]:
        rows = self.conn.execute(
            """
            SELECT *
            FROM quote_group_profiles
            ORDER BY updated_at DESC, id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [self._serialize_quote_db_row(row) for row in rows]

    def delete_quote_group_profile(self, *, profile_id: int) -> bool:
        cursor = self.conn.execute(
            """
            DELETE FROM quote_group_profiles
            WHERE id = ?
            """,
            (profile_id,),
        )
        self.conn.commit()
        return bool(getattr(cursor, "rowcount", 0))

    def append_rule_to_group_profile(self, *, platform: str, chat_id: str, new_rule: dict) -> bool:
        row = self.get_quote_group_profile(platform=platform, chat_id=chat_id)
        if not row:
            return False
        
        import json
        from .template_engine import TemplateConfig
        
        raw_config = str(row.get("template_config") or "")
        try:
            config = TemplateConfig.from_json(raw_config) if raw_config.strip() else TemplateConfig()
        except ValueError:
            config = TemplateConfig()
            
        config.rules.append(new_rule)
        
        self.conn.execute(
            """
            UPDATE quote_group_profiles 
            SET template_config = ?, updated_at = CURRENT_TIMESTAMP
            WHERE platform = ? AND chat_id = ?
            """,
            (config.to_json(), platform, chat_id)
        )
        self.conn.commit()
        return True

    def list_quote_board(self, *, limit: int = 500) -> list[DBRow]:
        rows = self.conn.execute(
            """
            SELECT
              qpr.*,
              COALESCE(NULLIF(g.chat_name, ''), qpr.chat_name) AS chat_name
            FROM quote_price_rows AS qpr
            LEFT JOIN groups AS g
              ON g.group_key = qpr.source_group_key
             AND g.platform = qpr.platform
            WHERE qpr.quote_status = 'active' AND qpr.expires_at IS NULL
            ORDER BY card_type ASC, country_or_currency ASC, amount_range ASC,
                     COALESCE(multiplier, '') ASC, form_factor ASC, price DESC,
                     effective_at DESC, id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        grouped: dict[tuple[str, str, str, str, str], Any] = {}
        for row in rows:
            normalized_amount = self._quote_amount_board_key(str(row["amount_range"] or "不限"))
            normalized_form_factor = normalize_quote_form_factor(
                str(row["form_factor"] or "不限")
            )
            normalized_multiplier = normalize_quote_multiplier(
                str(row["multiplier"] or "")
            )
            key = (
                str(row["card_type"] or ""),
                str(row["country_or_currency"] or ""),
                normalized_amount,
                normalized_multiplier,
                normalized_form_factor,
            )
            current = grouped.get(key)
            if current is None:
                grouped[key] = row
                continue
            current_price = float(current["price"])
            next_price = float(row["price"])
            if next_price > current_price or (
                next_price == current_price
                and str(row["effective_at"] or "") > str(current["effective_at"] or "")
            ):
                grouped[key] = row
        normalized_rows: list[DBRow] = []
        for row in grouped.values():
            item = self._quote_row_with_change(self._serialize_quote_db_row(row))
            item["amount_range"] = self._quote_amount_board_key(
                str(item.get("amount_range") or "不限")
            )
            item["form_factor"] = normalize_quote_form_factor(
                str(item.get("form_factor") or "不限")
            )
            item["multiplier"] = normalize_quote_multiplier(
                str(item.get("multiplier") or "")
            ) or None
            item["amount_display"] = self._quote_amount_display(item)
            normalized_rows.append(item)
        return sorted(
            normalized_rows,
            key=lambda row: (
                str(row["card_type"] or ""),
                str(row["country_or_currency"] or ""),
                str(row["amount_range"] or ""),
                str(row["multiplier"] or ""),
                str(row["form_factor"] or ""),
                -float(row["price"] or 0),
                str(row["effective_at"] or ""),
                int(row["id"] or 0),
            ),
        )

    def _quote_row_with_change(self, row: DBRow) -> DBRow:
        result = dict(row)
        current_amount_key = self._quote_amount_board_key(str(result.get("amount_range") or "不限"))
        previous_rows = self.conn.execute(
            """
            SELECT price, effective_at, id, amount_range
            FROM quote_price_rows
            WHERE platform = ?
              AND source_group_key = ?
              AND card_type = ?
              AND country_or_currency = ?
              AND form_factor = ?
              AND COALESCE(multiplier, '') = COALESCE(?, '')
              AND id <> ?
              AND quote_document_id <> ?
              AND effective_at <= ?
            ORDER BY effective_at DESC, id DESC
            """,
            (
                result["platform"],
                result["source_group_key"],
                result["card_type"],
                result["country_or_currency"],
                result["form_factor"],
                result["multiplier"],
                result["id"],
                result["quote_document_id"],
                result["effective_at"],
            ),
        ).fetchall()
        previous = next(
            (
                row
                for row in previous_rows
                if self._quote_amount_board_key(str(row["amount_range"] or "不限")) == current_amount_key
            ),
            None,
        )
        if not previous:
            result["change_status"] = "new"
            result["previous_price"] = None
            result["price_change"] = None
            result["previous_effective_at"] = None
            return result

        previous_price = float(previous["price"])
        current_price = float(result["price"])
        delta = round(current_price - previous_price, 6)
        if delta > 0:
            change_status = "up"
        elif delta < 0:
            change_status = "down"
        else:
            change_status = "flat"
        result["change_status"] = change_status
        result["previous_price"] = previous_price
        result["price_change"] = delta
        result["previous_effective_at"] = str(previous["effective_at"] or "")
        return result

    @staticmethod
    def _quote_amount_board_key(amount_range: str) -> str:
        text = str(amount_range or "").strip()
        if not text:
            return "不限"
        if text == "不限":
            return text
        text = text.replace("／", "/").replace("－", "-").replace("—", "-").replace("~", "-")
        parts = re.split(r"([/-])", text)
        normalized_parts: list[str] = []
        for part in parts:
            if not part:
                continue
            if part in {"-", "/"}:
                normalized_parts.append(part)
                continue
            stripped = re.sub(r"\s+", "", part)
            if not stripped:
                continue
            if re.fullmatch(r"\d+(?:\.\d+)?", stripped):
                normalized_parts.append(f"{float(stripped):g}")
            else:
                normalized_parts.append(stripped)
        return "".join(normalized_parts) or "不限"

    @staticmethod
    def _quote_stale_after_minutes(row: DBRow) -> int:
        if str(row.get("card_type") or "").lower() == "apple":
            return 30
        return 120

    def _quote_amount_display(self, row: DBRow) -> str:
        amount = self._quote_amount_board_key(str(row.get("amount_range") or ""))
        multiplier = normalize_quote_multiplier(str(row.get("multiplier") or ""))
        if multiplier:
            return f"{amount} / {multiplier}" if amount else multiplier
        return amount

    def _prune_dominated_quote_rows(self, rows: list[DBRow]) -> list[DBRow]:
        grouped: dict[tuple[str, str, str], list[DBRow]] = {}
        for row in rows:
            key = (
                str(row.get("card_type") or ""),
                str(row.get("country_or_currency") or ""),
                normalize_quote_form_factor(str(row.get("form_factor") or "不限")),
            )
            grouped.setdefault(key, []).append(row)

        result: list[DBRow] = []
        for items in grouped.values():
            for candidate in items:
                if self._quote_row_is_dominated(candidate, items):
                    continue
                result.append(candidate)
        return result

    def _quote_row_is_dominated(self, candidate: DBRow, peers: list[DBRow]) -> bool:
        candidate_range = self._quote_amount_bounds(str(candidate.get("amount_range") or ""))
        if candidate_range is None:
            return False
        candidate_price = float(candidate.get("price") or 0)
        candidate_multiplier = normalize_quote_multiplier(
            str(candidate.get("multiplier") or "")
        )
        for other in peers:
            if other is candidate:
                continue
            other_multiplier = normalize_quote_multiplier(str(other.get("multiplier") or ""))
            if candidate_multiplier:
                # Generic rows (no multiplier) are stronger conditions and can dominate
                # multiplier-specific lower prices; specific multipliers only compare
                # within the same multiplier bucket.
                if other_multiplier not in ("", candidate_multiplier):
                    continue
            elif other_multiplier:
                continue
            other_range = self._quote_amount_bounds(str(other.get("amount_range") or ""))
            if other_range is None:
                continue
            if not self._range_contains(other_range, candidate_range):
                continue
            other_price = float(other.get("price") or 0)
            if other_price < candidate_price:
                continue
            if other_price == candidate_price:
                if str(other.get("effective_at") or "") < str(candidate.get("effective_at") or ""):
                    continue
                if int(other.get("id") or 0) < int(candidate.get("id") or 0):
                    continue
            return True
        return False

    @staticmethod
    def _quote_amount_bounds(amount_range: str) -> tuple[float, float] | None:
        text = normalize_quote_amount_range(amount_range)
        if not text or text == "不限":
            return None
        numeric_tokens = re.findall(r"\d+(?:\.\d+)?", text)
        if not numeric_tokens:
            return None
        values = [float(token) for token in numeric_tokens]
        start = min(values)
        end = max(values)
        if end < start:
            start, end = end, start
        return start, end

    @staticmethod
    def _range_contains(outer: tuple[float, float], inner: tuple[float, float]) -> bool:
        return outer[0] <= inner[0] and outer[1] >= inner[1]

    def list_quote_matches(
        self,
        *,
        card_type: str,
        country_or_currency: str,
        amount: float,
        form_factor: str | None = None,
        limit: int = 50,
    ) -> tuple[list[DBRow], int]:
        where_parts = [
            "quote_status = 'active'",
            "expires_at IS NULL",
            "card_type = ?",
            "country_or_currency = ?",
        ]
        params: list = [card_type, country_or_currency]
        where_clause = " AND ".join(where_parts)
        rows = self.conn.execute(
            f"""
            SELECT *
            FROM quote_price_rows
            WHERE {where_clause}
            ORDER BY price DESC, effective_at DESC, id DESC
            LIMIT 500
            """,
            params,
        ).fetchall()
        matched = [
            self._quote_row_with_change(self._serialize_quote_db_row(row))
            for row in rows
            if self._quote_row_matches_amount(row, amount)
            and (
                not form_factor
                or normalize_quote_form_factor(str(row["form_factor"] or "不限"))
                == normalize_quote_form_factor(form_factor)
            )
        ]
        return matched[:limit], len(matched)

    @staticmethod
    def _quote_row_matches_amount(row: DBRow, amount: float) -> bool:
        card_type = str(row.get("card_type") or "")
        multiplier = str(row.get("multiplier") or "")
        if card_type == "Apple" and multiplier == "50X":
            return amount >= 50 and amount <= 500 and amount % 50 == 0
        amount_range = str(row.get("amount_range") or "").strip()
        if not amount_range or amount_range == "不限":
            return True
        match = re.fullmatch(r"(\d+(?:\.\d+)?)(?:-(\d+(?:\.\d+)?))?", amount_range)
        if match is None:
            return False
        start = float(match.group(1))
        end = float(match.group(2) or match.group(1))
        return start <= amount <= end

    def list_quote_history(
        self,
        *,
        card_type: str | None = None,
        country_or_currency: str | None = None,
        amount_range: str | None = None,
        multiplier: str | None = None,
        form_factor: str | None = None,
        source_group_key: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[DBRow], int]:
        where_parts = []
        params: list = []
        if card_type is not None:
            where_parts.append("card_type = ?")
            params.append(card_type)
        if country_or_currency is not None:
            where_parts.append("country_or_currency = ?")
            params.append(country_or_currency)
        if amount_range is not None:
            where_parts.append("amount_range = ?")
            params.append(amount_range)
        if multiplier is not None:
            where_parts.append("COALESCE(multiplier, '') = COALESCE(?, '')")
            params.append(multiplier)
        if form_factor is not None:
            where_parts.append("form_factor = ?")
            params.append(form_factor)
        if source_group_key is not None:
            where_parts.append("source_group_key = ?")
            params.append(source_group_key)
        where_clause = " AND ".join(where_parts) if where_parts else "1=1"

        count_row = self.conn.execute(
            f"SELECT COUNT(*) AS cnt FROM quote_price_rows WHERE {where_clause}",
            params,
        ).fetchone()
        total = int(count_row["cnt"])

        params.extend([limit, offset])
        rows = self.conn.execute(
            f"""
            SELECT *
            FROM quote_price_rows
            WHERE {where_clause}
            ORDER BY effective_at DESC, id DESC
            LIMIT ? OFFSET ?
            """,
            params,
        ).fetchall()
        return [self._serialize_quote_db_row(row) for row in rows], total

    def list_quote_rankings(
        self,
        *,
        card_type: str,
        country_or_currency: str,
        amount_range: str,
        multiplier: str | None = None,
        form_factor: str,
        limit: int = 50,
    ) -> tuple[list[DBRow], int]:
        normalized_form_factor = normalize_quote_form_factor(form_factor)
        normalized_amount_range = self._quote_amount_board_key(amount_range)
        normalized_multiplier = normalize_quote_multiplier(str(multiplier or ""))
        params: list = [card_type, country_or_currency]
        rows = self.conn.execute(
            """
            SELECT *
            FROM quote_price_rows
            WHERE quote_status = 'active'
              AND expires_at IS NULL
              AND card_type = ?
              AND country_or_currency = ?
            ORDER BY price DESC, effective_at DESC, id DESC
            """,
            params,
        ).fetchall()
        filtered = [
            row
            for row in rows
            if normalize_quote_form_factor(str(row["form_factor"] or "不限")) == normalized_form_factor
            and self._quote_amount_board_key(str(row["amount_range"] or "不限"))
            == normalized_amount_range
            and normalize_quote_multiplier(str(row["multiplier"] or ""))
            == normalized_multiplier
        ]
        total = len(filtered)
        ranking_rows: list[DBRow] = []
        for row in filtered[:limit]:
            item = self._quote_row_with_change(self._serialize_quote_db_row(row))
            item["amount_range"] = self._quote_amount_board_key(
                str(item.get("amount_range") or "不限")
            )
            item["amount_display"] = self._quote_amount_display(item)
            ranking_rows.append(item)
        return ranking_rows, total

    def list_quote_exceptions(
        self,
        *,
        source_group_key: str | None = None,
        resolution_status: str | None = None,
        limit: int = 10,
        offset: int = 0,
    ) -> dict[str, Any]:
        where_parts = []
        params: list = []
        if source_group_key is not None:
            where_parts.append("source_group_key = ?")
            params.append(source_group_key)
        if resolution_status and resolution_status != "all":
            where_parts.append("resolution_status = ?")
            params.append(resolution_status)
        where_clause = " AND ".join(where_parts) if where_parts else "1=1"
        count_row = self.conn.execute(
            f"SELECT COUNT(*) AS cnt FROM quote_parse_exceptions WHERE {where_clause}",
            params,
        ).fetchone()
        total = int(count_row["cnt"])
        stats_where_parts = []
        stats_params: list[Any] = []
        if source_group_key is not None:
            stats_where_parts.append("source_group_key = ?")
            stats_params.append(source_group_key)
        stats_where_clause = (
            " AND ".join(stats_where_parts) if stats_where_parts else "1=1"
        )
        stats_row = self.conn.execute(
            f"""
            SELECT
              SUM(CASE WHEN resolution_status = 'open' THEN 1 ELSE 0 END) AS open_total,
              SUM(CASE WHEN resolution_status <> 'open' THEN 1 ELSE 0 END) AS handled_total
            FROM quote_parse_exceptions
            WHERE {stats_where_clause}
            """,
            stats_params,
        ).fetchone()
        params.extend([limit, offset])
        rows = self.conn.execute(
            f"""
            SELECT
              qpe.*,
              COALESCE(NULLIF(g.chat_name, ''), qpe.chat_name) AS chat_name
            FROM quote_parse_exceptions AS qpe
            LEFT JOIN groups AS g
              ON g.group_key = qpe.source_group_key
             AND g.platform = qpe.platform
            WHERE {where_clause}
            ORDER BY
              CASE WHEN resolution_status = 'open' THEN 0 ELSE 1 END ASC,
              created_at DESC,
              id DESC
            LIMIT ? OFFSET ?
            """,
            params,
        ).fetchall()
        serialized_rows = [self._serialize_quote_db_row(row) for row in rows]
        return {
            "rows": serialized_rows,
            "total": total,
            "open_total": int(stats_row["open_total"] or 0),
            "handled_total": int(stats_row["handled_total"] or 0),
            "limit": limit,
            "offset": offset,
            "has_prev": offset > 0,
            "has_next": offset + len(serialized_rows) < total,
            "resolution_status": resolution_status or "open",
        }

    def _serialize_quote_db_row(self, row) -> dict:
        result = dict(row)
        for key in ("id", "quote_document_id"):
            if result.get(key) is not None:
                result[key] = int(result[key])
        for key in ("price", "confidence"):
            if result.get(key) is not None:
                result[key] = float(result[key])
        for key in (
            "message_time",
            "effective_at",
            "expires_at",
            "resolved_at",
            "created_at",
            "updated_at",
        ):
            if result.get(key) is not None:
                result[key] = str(result[key])
        if "card_type" in result and "amount_range" in result:
            result["amount_display"] = self._quote_amount_display(result)
            result["stale_after_minutes"] = self._quote_stale_after_minutes(result)
        if "reason" in result and "source_line" in result:
            result["reason_label"] = self._quote_exception_reason_label(result)
            result["suggested_action"] = self._quote_exception_suggested_action(result)
        return result

    @staticmethod
    def _quote_exception_reason_label(row: DBRow) -> str:
        reason = str(row.get("reason") or "")
        if reason == "blocked_or_question_line":
            return "限制/问价说明"
        if reason == "missing_group_template":
            return "群模板未配置"
        if reason == "missing_context":
            return "缺少上下文"
        if reason == "modifier_rule":
            return "派生价规则"
        if reason == "low_confidence_or_non_active":
            return "低置信或非可用报价"
        if reason == "unparsed_price_line":
            return "价格行未识别"
        return reason or "未知异常"

    @staticmethod
    def _quote_exception_suggested_action(row: DBRow) -> str:
        reason = str(row.get("reason") or "")
        source_line = str(row.get("source_line") or "")
        if reason == "blocked_or_question_line":
            return "这是限制或需要询问的说明，不是可直接入墙价格；确认无误可忽略。"
        if reason == "missing_group_template":
            return "这个群已经进报价采集范围，但还没有可用模板；先到异常区整理成固定模板再上墙。"
        if reason == "missing_context" and re.fullmatch(r"\d+(?:\.\d+)?", source_line.strip()):
            return "这是短回复价格；需要先有询价上下文，或手动补卡种/国家/面额。"
        if reason == "missing_context":
            return "缺卡种、国家或面额；需要补模板或建立询价上下文。"
        if reason == "modifier_rule":
            return "派生价规则未找到可应用的基准价；需要确认它作用到哪一段报价。"
        if reason == "low_confidence_or_non_active":
            return "系统不敢自动生效；需要人工确认后再处理。"
        return "先看异常行，不要看整份原文；确认不是报价可忽略。"

    def query_parse_results(
        self,
        *,
        platform: str | None = None,
        chat_id: str | None = None,
        classification: str | None = None,
        parse_status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[DBRow], int]:
        where_parts = []
        params: list = []
        if platform is not None:
            where_parts.append("platform = ?")
            params.append(platform)
        if chat_id is not None:
            where_parts.append("chat_id = ?")
            params.append(chat_id)
        if classification is not None:
            where_parts.append("classification = ?")
            params.append(classification)
        if parse_status is not None:
            where_parts.append("parse_status = ?")
            params.append(parse_status)
        where_clause = " AND ".join(where_parts) if where_parts else "1=1"

        count_row = self.conn.execute(
            f"SELECT COUNT(*) AS cnt FROM message_parse_results WHERE {where_clause}",
            params,
        ).fetchone()
        total = int(count_row["cnt"])

        params.extend([limit, offset])
        rows = self.conn.execute(
            f"""
            SELECT id, platform, chat_id, message_id, classification,
                   parse_status, raw_text, created_at
            FROM message_parse_results
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            params,
        ).fetchall()
        return list(rows), total

    def get_message_triple(
        self, *, platform: str, chat_id: str, message_id: str
    ) -> dict | None:
        row = self.conn.execute(
            """
            SELECT im.id, im.platform, im.chat_id, im.chat_name, im.message_id,
                   im.sender_id, im.sender_name, im.sender_kind, im.content_type,
                   im.text, im.from_self, im.received_at, im.created_at,
                   pr.classification AS pr_classification, pr.parse_status AS pr_parse_status,
                   pr.raw_text AS pr_raw_text,
                   t.id AS tx_id, t.amount AS tx_amount, t.category AS tx_category,
                   t.input_sign AS tx_input_sign, t.rmb_value AS tx_rmb_value,
                   t.created_at AS tx_created_at
            FROM incoming_messages im
            LEFT JOIN message_parse_results pr ON pr.platform = im.platform
                                           AND pr.chat_id = im.chat_id
                                           AND pr.message_id = im.message_id
            LEFT JOIN transactions t ON t.platform = im.platform
                                      AND t.chat_id = im.chat_id
                                      AND t.message_id = im.message_id
                                      AND t.deleted = 0
            WHERE im.platform = ? AND im.chat_id = ? AND im.message_id = ?
            """,
            (platform, chat_id, message_id),
        ).fetchone()
        if row is None:
            return None
        result = {
            "message": {
                "id": int(row["id"]),
                "platform": str(row["platform"] or ""),
                "chat_id": str(row["chat_id"] or ""),
                "chat_name": str(row["chat_name"] or ""),
                "message_id": str(row["message_id"] or ""),
                "sender_id": str(row["sender_id"] or ""),
                "sender_name": str(row["sender_name"] or ""),
                "sender_kind": str(row["sender_kind"] or ""),
                "content_type": str(row["content_type"] or ""),
                "text": str(row["text"] or ""),
                "from_self": bool(row["from_self"]),
                "received_at": str(row["received_at"] or ""),
                "created_at": str(row["created_at"] or ""),
            },
            "parse_result": None,
            "transaction": None,
        }
        if row["pr_classification"] is not None:
            result["parse_result"] = {
                "classification": str(row["pr_classification"]),
                "parse_status": str(row["pr_parse_status"]),
                "raw_text": str(row["pr_raw_text"] or ""),
            }
        if row["tx_id"] is not None:
            result["transaction"] = {
                "id": int(row["tx_id"]),
                "amount": str(row["tx_amount"] or ""),
                "category": str(row["tx_category"] or ""),
                "input_sign": int(row["tx_input_sign"]),
                "rmb_value": str(row["tx_rmb_value"] or ""),
                "created_at": str(row["tx_created_at"] or ""),
            }
        return result

    @staticmethod
    def _reminder_from_row(row: DBRow) -> ReminderPayload:
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
        return sql.replace("?", "%s")

    def execute(self, sql: str, params=()):
        cursor = self._raw_connection.execute(self._translate(sql), tuple(params))
        return _PostgresCursorCompat(cursor)

    def commit(self) -> None:
        self._raw_connection.commit()

    def rollback(self) -> None:
        self._raw_connection.rollback()

    def close(self) -> None:
        self._raw_connection.close()


class BookkeepingDB(_BookkeepingStoreBase):
    def __init__(self, db_path: str | Path) -> None:
        try:
            import psycopg
        except ImportError as exc:
            raise RuntimeError(
                "PostgreSQL backend requires psycopg to be installed"
            ) from exc

        dsn = require_postgres_dsn(db_path, context="Bookkeeping database")
        self.db_path = dsn
        self._raw_conn = psycopg.connect(dsn)
        self.conn = _PostgresConnectionCompat(self._raw_conn)
        self._init_schema()

    def close(self) -> None:
        self._raw_conn.close()

    def _init_schema(self) -> None:
        self._ensure_support_tables()
        self._verify_schema()
        self.conn.execute(
            """
            INSERT INTO settings (key, value, updated_at)
            VALUES ('ngn_rate', '', CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO NOTHING
            """
        )
        self.conn.commit()

    def _ensure_support_tables(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS accounting_periods (
              id BIGSERIAL PRIMARY KEY,
              start_at TIMESTAMP NOT NULL,
              end_at TIMESTAMP NOT NULL,
              closed_at TIMESTAMP NOT NULL,
              closed_by TEXT NOT NULL,
              note TEXT,
              has_adjustment INTEGER NOT NULL DEFAULT 0,
              snapshot_version INTEGER NOT NULL DEFAULT 1
            )
            """
        )
        self.conn.execute(
            """
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
            )
            """
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS period_group_card_stats (
              id BIGSERIAL PRIMARY KEY,
              period_id BIGINT NOT NULL,
              group_key TEXT NOT NULL,
              card_type TEXT NOT NULL,
              country_or_currency TEXT NOT NULL,
              unit_count_net INTEGER NOT NULL DEFAULT 0,
              usd_amount_net NUMERIC(18, 4) NOT NULL DEFAULT 0,
              UNIQUE (period_id, group_key, card_type, country_or_currency)
            )
            """
        )
        self.conn.execute(
            """
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
            )
            """
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS period_adjustments (
              id BIGSERIAL PRIMARY KEY,
              period_id BIGINT NOT NULL,
              group_key TEXT NOT NULL,
              adjustment_type TEXT NOT NULL,
              amount NUMERIC(18, 4) NOT NULL,
              note TEXT NOT NULL,
              created_by TEXT NOT NULL,
              created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS transaction_edit_logs (
              id BIGSERIAL PRIMARY KEY,
              transaction_id BIGINT NOT NULL,
              edited_by TEXT NOT NULL,
              note TEXT,
              before_json TEXT NOT NULL,
              after_json TEXT NOT NULL,
              edited_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS outbound_actions (
              id BIGSERIAL PRIMARY KEY,
              action_type TEXT NOT NULL,
              chat_id TEXT NOT NULL,
              text TEXT,
              file_path TEXT,
              caption TEXT,
              status TEXT NOT NULL DEFAULT 'pending',
              created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
              claimed_at TIMESTAMP,
              dispatched_at TIMESTAMP
            )
            """
        )
        self.conn.execute(
            """
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
            )
            """
        )
        self.conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_incoming_messages_group_created
            ON incoming_messages(group_key, created_at DESC)
            """
        )
        self.conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_incoming_messages_chat_received
            ON incoming_messages(platform, chat_id, received_at DESC)
            """
        )
        self.conn.execute(
            """
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
            )
            """
        )
        self.conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_message_parse_results_created
            ON message_parse_results(created_at DESC)
            """
        )
        self.conn.execute(
            """
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
            )
            """
        )
        self.conn.execute(
            """
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
            )
            """
        )
        self.conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_quote_price_rows_active
            ON quote_price_rows(card_type, country_or_currency, amount_range, multiplier, form_factor, effective_at DESC)
            """
        )
        self.conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_quote_price_rows_source_lookup
            ON quote_price_rows(source_group_key, card_type, country_or_currency, amount_range, form_factor, effective_at DESC)
            """
        )
        self.conn.execute(
            """
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
            )
            """
        )
        self.conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_quote_parse_exceptions_created
            ON quote_parse_exceptions(created_at DESC)
            """
        )
        self.conn.execute(
            """
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
            )
            """
        )
        self.conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_quote_inquiry_contexts_open
            ON quote_inquiry_contexts(platform, chat_id, status, expires_at DESC)
            """
        )
        self.conn.execute(
            """
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
            )
            """
        )
        self.conn.execute(
            """
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
            )
            """
        )
        self.conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_quote_dictionary_aliases_lookup
            ON quote_dictionary_aliases(category, scope_platform, scope_chat_id, enabled)
            """
        )
        for column_name, ddl in (
            ("resolution_status", "ALTER TABLE quote_parse_exceptions ADD COLUMN resolution_status TEXT NOT NULL DEFAULT 'open'"),
            ("resolution_note", "ALTER TABLE quote_parse_exceptions ADD COLUMN resolution_note TEXT NOT NULL DEFAULT ''"),
            ("resolved_at", "ALTER TABLE quote_parse_exceptions ADD COLUMN resolved_at TIMESTAMP"),
        ):
            if not self._table_has_column("quote_parse_exceptions", column_name):
                self.conn.execute(ddl)
        for column_name, ddl in (
            ("default_country_or_currency", "ALTER TABLE quote_group_profiles ADD COLUMN default_country_or_currency TEXT NOT NULL DEFAULT ''"),
            ("default_form_factor", "ALTER TABLE quote_group_profiles ADD COLUMN default_form_factor TEXT NOT NULL DEFAULT '不限'"),
            ("default_multiplier", "ALTER TABLE quote_group_profiles ADD COLUMN default_multiplier TEXT NOT NULL DEFAULT ''"),
            ("template_config", "ALTER TABLE quote_group_profiles ADD COLUMN template_config TEXT NOT NULL DEFAULT ''"),
        ):
            if not self._table_has_column("quote_group_profiles", column_name):
                self.conn.execute(ddl)
        for column_name, ddl in (
            ("canonical_input", "ALTER TABLE quote_dictionary_aliases ADD COLUMN canonical_input TEXT NOT NULL DEFAULT ''"),
        ):
            if not self._table_has_column("quote_dictionary_aliases", column_name):
                self.conn.execute(ddl)
        if not self._table_has_column("outbound_actions", "claimed_at"):
            self.conn.execute(
                """
                ALTER TABLE outbound_actions
                ADD COLUMN claimed_at TIMESTAMP
                """
            )
        # Keep future period snapshots/card stats tied to a real period row.
        # Use NOT VALID so existing legacy rows do not block startup migration.
        if not self._constraint_exists(
            "period_group_snapshots", "fk_period_group_snapshots_period_id"
        ):
            self.conn.execute(
                """
                ALTER TABLE period_group_snapshots
                ADD CONSTRAINT fk_period_group_snapshots_period_id
                FOREIGN KEY (period_id) REFERENCES accounting_periods(id)
                NOT VALID
                """
            )
        if not self._constraint_exists(
            "period_card_stats", "fk_period_card_stats_period_id"
        ):
            self.conn.execute(
                """
                ALTER TABLE period_card_stats
                ADD CONSTRAINT fk_period_card_stats_period_id
                FOREIGN KEY (period_id) REFERENCES accounting_periods(id)
                NOT VALID
                """
            )
        self.conn.commit()

    def _table_has_column(self, table_name: str, column_name: str) -> bool:
        row = self.conn.execute(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = CURRENT_SCHEMA()
              AND table_name = ?
              AND column_name = ?
            LIMIT 1
            """,
            (table_name, column_name),
        ).fetchone()
        return row is not None

    def _constraint_exists(self, table_name: str, constraint_name: str) -> bool:
        row = self.conn.execute(
            """
            SELECT 1
            FROM pg_constraint c
            INNER JOIN pg_class t ON t.oid = c.conrelid
            INNER JOIN pg_namespace n ON n.oid = t.relnamespace
            WHERE n.nspname = CURRENT_SCHEMA()
              AND t.relname = ?
              AND c.conname = ?
            LIMIT 1
            """,
            (table_name, constraint_name),
        ).fetchone()
        return row is not None

    def _verify_schema(self) -> None:
        required_columns = {
            "transactions": {
                "id",
                "platform",
                "group_key",
                "group_num",
                "chat_id",
                "chat_name",
                "sender_id",
                "sender_name",
                "message_id",
                "input_sign",
                "amount",
                "category",
                "rate",
                "rmb_value",
                "raw",
                "ngn_rate",
                "usd_amount",
                "unit_face_value",
                "unit_count",
                "parse_version",
                "created_at",
                "deleted",
                "settled",
                "settled_at",
            },
            "accounting_periods": {
                "id",
                "start_at",
                "end_at",
                "closed_at",
                "closed_by",
                "note",
                "has_adjustment",
                "snapshot_version",
            },
            "period_group_snapshots": {
                "id",
                "period_id",
                "group_key",
                "platform",
                "chat_name",
                "group_num",
                "business_role",
                "opening_balance",
                "income",
                "expense",
                "closing_balance",
                "transaction_count",
                "anomaly_flags_json",
            },
            "period_card_stats": {
                "id",
                "period_id",
                "group_key",
                "business_role",
                "card_type",
                "usd_amount",
                "rate",
                "rmb_amount",
                "unit_face_value",
                "unit_count",
                "sample_raw",
            },
            "groups": {
                "group_key",
                "platform",
                "chat_id",
                "chat_name",
                "group_num",
                "business_role",
                "role_source",
                "capture_enabled",
                "status",
                "created_at",
                "updated_at",
            },
            "settings": {"key", "value", "updated_at"},
            "whitelist": {"user_key", "added_by", "added_at", "note"},
            "admins": {"user_key", "added_by", "added_at", "note"},
            "reminders": {
                "id",
                "platform",
                "chat_id",
                "sender_id",
                "message",
                "amount",
                "category",
                "rate",
                "rmb_value",
                "ngn_value",
                "duration_minutes",
                "remind_at",
                "created_at",
                "sent",
            },
            "identity_bindings": {
                "platform",
                "chat_id",
                "observed_key",
                "canonical_id",
                "observed_name",
                "updated_at",
            },
            "manual_adjustments": {
                "id",
                "period_id",
                "group_key",
                "opening_delta",
                "income_delta",
                "expense_delta",
                "closing_delta",
                "note",
                "created_by",
                "created_at",
            },
            "finance_adjustment_entries": {
                "id",
                "period_id",
                "linked_transaction_id",
                "group_key",
                "business_role",
                "card_type",
                "usd_amount",
                "rate",
                "rmb_amount",
                "note",
                "created_by",
                "created_at",
            },
            "group_combinations": {
                "id",
                "name",
                "note",
                "created_by",
                "created_at",
                "updated_at",
            },
            "group_combination_items": {"combination_id", "group_num"},
            "transaction_edit_logs": {
                "id",
                "transaction_id",
                "edited_by",
                "note",
                "before_json",
                "after_json",
                "edited_at",
            },
            "outbound_actions": {
                "id",
                "action_type",
                "chat_id",
                "text",
                "file_path",
                "caption",
                "status",
                "created_at",
                "claimed_at",
                "dispatched_at",
            },
            "ingested_events": {
                "event_id",
                "event_type",
                "platform",
                "source_machine",
                "schema_version",
                "occurred_at",
                "ingested_at",
            },
            "incoming_messages": {
                "id",
                "platform",
                "group_key",
                "chat_id",
                "chat_name",
                "message_id",
                "is_group",
                "sender_id",
                "sender_name",
                "sender_kind",
                "content_type",
                "text",
                "from_self",
                "received_at",
                "raw_json",
                "created_at",
            },
            "quote_documents": {
                "id",
                "platform",
                "source_group_key",
                "chat_id",
                "chat_name",
                "message_id",
                "source_name",
                "sender_id",
                "raw_text",
                "message_time",
                "parser_template",
                "parser_version",
                "confidence",
                "parse_status",
                "created_at",
            },
            "quote_price_rows": {
                "id",
                "quote_document_id",
                "platform",
                "source_group_key",
                "chat_id",
                "chat_name",
                "message_id",
                "source_name",
                "sender_id",
                "card_type",
                "country_or_currency",
                "amount_range",
                "multiplier",
                "form_factor",
                "price",
                "quote_status",
                "restriction_text",
                "source_line",
                "raw_text",
                "message_time",
                "effective_at",
                "expires_at",
                "parser_template",
                "parser_version",
                "confidence",
                "created_at",
            },
            "quote_parse_exceptions": {
                "id",
                "quote_document_id",
                "platform",
                "source_group_key",
                "chat_id",
                "chat_name",
                "source_name",
                "sender_id",
                "reason",
                "source_line",
                "raw_text",
                "message_time",
                "parser_template",
                "parser_version",
                "confidence",
                "resolution_status",
                "resolution_note",
                "resolved_at",
                "created_at",
            },
            "quote_inquiry_contexts": {
                "id",
                "platform",
                "source_group_key",
                "chat_id",
                "chat_name",
                "card_type",
                "country_or_currency",
                "amount_range",
                "multiplier",
                "form_factor",
                "requested_by",
                "prompt_text",
                "status",
                "expires_at",
                "resolved_message_id",
                "resolved_at",
                "created_at",
            },
            "quote_group_profiles": {
                "id",
                "platform",
                "chat_id",
                "chat_name",
                "default_card_type",
                "default_country_or_currency",
                "default_form_factor",
                "default_multiplier",
                "parser_template",
                "stale_after_minutes",
                "note",
                "template_config",
                "created_at",
                "updated_at",
            },
            "quote_dictionary_aliases": {
                "id",
                "category",
                "alias",
                "canonical_value",
                "canonical_input",
                "scope_platform",
                "scope_chat_id",
                "note",
                "enabled",
                "created_at",
                "updated_at",
            },
        }
        mismatches: list[str] = []
        for table_name, expected_columns in required_columns.items():
            rows = self.conn.execute(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = current_schema()
                  AND table_name = ?
                """,
                (table_name,),
            ).fetchall()
            actual_columns = {str(row["column_name"]) for row in rows}
            if not actual_columns:
                mismatches.append(f"missing table: {table_name}")
                continue
            missing_columns = sorted(expected_columns - actual_columns)
            if missing_columns:
                mismatches.append(
                    f"missing columns in {table_name}: {', '.join(missing_columns)}"
                )
        if mismatches:
            raise RuntimeError(
                "PostgreSQL schema mismatch. Apply the current postgres_schema.sql before starting the runtime: "
                + "; ".join(mismatches)
            )

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
        parse_version: str = "1",
        usd_amount: float | None = None,
        unit_face_value: float | None = None,
        unit_count: float | None = None,
        created_at: str | None = None,
        deleted: int = 0,
        settled: int = 0,
        settled_at: str | None = None,
        ngn_rate_override: float | None = None,
    ) -> int:
        ngn_rate = (
            ngn_rate_override if ngn_rate_override is not None else self.get_ngn_rate()
        )
        cur = self.conn.execute(
            """
            INSERT INTO transactions (
              platform, group_key, group_num, chat_id, chat_name,
              sender_id, sender_name, message_id, input_sign, amount,
              category, rate, rmb_value, raw, parse_version, usd_amount,
              unit_face_value, unit_count, ngn_rate, created_at,
              deleted, settled, settled_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, COALESCE(?, CURRENT_TIMESTAMP), ?, ?, ?)
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
                parse_version,
                usd_amount,
                unit_face_value,
                unit_count,
                ngn_rate,
                created_at,
                deleted,
                settled,
                settled_at,
            ),
        )
        row = cur.fetchone()
        self._refresh_group_profile_if_exists(
            platform=platform,
            group_key=group_key,
            chat_id=chat_id,
            chat_name=chat_name,
        )
        self.conn.commit()
        return int(row["id"])

    def get_transaction_by_id(self, transaction_id: int) -> DBRow | None:
        return self.conn.execute(
            """
            SELECT
              tx.*,
              g.business_role AS business_role,
              g.group_num AS mapped_group_num
            FROM transactions tx
            LEFT JOIN groups g ON g.group_key = tx.group_key
            WHERE tx.id = ?
            """,
            (transaction_id,),
        ).fetchone()

    def get_latest_edit_log(self, transaction_id: int) -> DBRow | None:
        return self.conn.execute(
            """
            SELECT *
            FROM transaction_edit_logs
            WHERE transaction_id = ?
            ORDER BY edited_at DESC, id DESC
            LIMIT 1
            """,
            (transaction_id,),
        ).fetchone()

    def update_transaction_fields(
        self,
        *,
        transaction_id: int,
        sender_name: str,
        amount: float,
        category: str,
        rate: float | None,
        rmb_value: float,
        usd_amount: float | None,
        commit: bool = True,
    ) -> int:
        cur = self.conn.execute(
            """
            UPDATE transactions
            SET sender_name = ?,
                amount = ?,
                category = ?,
                rate = ?,
                rmb_value = ?,
                usd_amount = ?,
                parse_version = 'web-edit'
            WHERE id = ?
            """,
            (
                sender_name,
                amount,
                category,
                rate,
                rmb_value,
                usd_amount,
                transaction_id,
            ),
        )
        if commit:
            self.conn.commit()
        return int(cur.rowcount or 0)

    def add_transaction_edit_log(
        self,
        *,
        transaction_id: int,
        edited_by: str,
        note: str | None,
        before_json: str,
        after_json: str,
        commit: bool = True,
    ) -> int:
        cur = self.conn.execute(
            """
            INSERT INTO transaction_edit_logs (
              transaction_id, edited_by, note, before_json, after_json
            ) VALUES (?, ?, ?, ?, ?)
            RETURNING id
            """,
            (transaction_id, edited_by, note, before_json, after_json),
        )
        row = cur.fetchone()
        if commit:
            self.conn.commit()
        return int(row["id"])

    def enqueue_outbound_actions(
        self, actions: list[dict], *, commit: bool = True
    ) -> int:
        inserted = 0
        for action in actions:
            action_type = str(action.get("action_type") or "").strip()
            chat_id = str(action.get("chat_id") or "").strip()
            if action_type not in {"send_text", "send_file"} or not chat_id:
                continue
            self.conn.execute(
                """
                INSERT INTO outbound_actions (
                  action_type, chat_id, text, file_path, caption, status, claimed_at, dispatched_at
                ) VALUES (?, ?, ?, ?, ?, 'pending', NULL, NULL)
                """,
                (
                    action_type,
                    chat_id,
                    action.get("text"),
                    action.get("file_path"),
                    action.get("caption"),
                ),
            )
            inserted += 1
        if commit:
            self.conn.commit()
        return inserted

    def claim_outbound_actions(self, *, limit: int = 50) -> list[DBRow]:
        # The long-lived runtime connection serves many read-only HTTP requests.
        # Refresh the PostgreSQL snapshot before polling the outbound queue so
        # actions written by other request-scoped connections become visible.
        self.conn.rollback()
        try:
            # Keep outbound polling responsive even when DB is under lock pressure.
            self.conn.execute("SET LOCAL lock_timeout = '1000ms'")
            self.conn.execute("SET LOCAL statement_timeout = '4000ms'")
        except Exception:
            # Non-Postgres drivers may not support these settings.
            pass

        try:
            rows = self.conn.execute(
                """
                SELECT *
                FROM outbound_actions
                WHERE status = 'pending'
                   OR (
                        status = 'claimed'
                    AND claimed_at IS NOT NULL
                    AND claimed_at <= CURRENT_TIMESTAMP - INTERVAL '30 seconds'
                   )
                ORDER BY created_at ASC, id ASC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            if not rows:
                return []
            ids = [int(row["id"]) for row in rows]
            placeholders = ",".join("?" for _ in ids)
            self.conn.execute(
                f"""
                UPDATE outbound_actions
                SET status = 'claimed',
                    claimed_at = CURRENT_TIMESTAMP
                WHERE id IN ({placeholders})
                """,
                ids,
            )
            self.conn.commit()
            return rows
        except Exception:
            # Outbound polling should fail open (empty queue) rather than block
            # core message ingestion and trigger adapter timeouts.
            self.conn.rollback()
            return []

    def acknowledge_outbound_actions(
        self, results: list[dict], *, commit: bool = True
    ) -> int:
        updated = 0
        for item in results:
            try:
                action_id = int(item["id"])
            except (KeyError, TypeError, ValueError):
                continue
            success = bool(item.get("success"))
            if success:
                cur = self.conn.execute(
                    """
                    UPDATE outbound_actions
                    SET status = 'delivered',
                        claimed_at = NULL,
                        dispatched_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (action_id,),
                )
            else:
                cur = self.conn.execute(
                    """
                    UPDATE outbound_actions
                    SET status = 'pending',
                        claimed_at = NULL,
                        dispatched_at = NULL
                    WHERE id = ?
                    """,
                    (action_id,),
                )
            updated += int(cur.rowcount or 0)
        if commit:
            self.conn.commit()
        return updated

    def add_to_whitelist(
        self, user_key: str, added_by: str, note: str | None = None
    ) -> None:
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
        period_id: int,
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
              period_id, group_key, opening_delta, income_delta, expense_delta,
              closing_delta, note, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            RETURNING id
            """,
            (
                period_id,
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

    def add_finance_adjustment_entry(
        self,
        *,
        period_id: int | None,
        linked_transaction_id: int | None,
        group_key: str,
        business_role: str | None,
        card_type: str,
        usd_amount: float,
        rate: float | None,
        rmb_amount: float,
        note: str,
        created_by: str,
    ) -> int:
        cur = self.conn.execute(
            """
            INSERT INTO finance_adjustment_entries (
              period_id, linked_transaction_id, group_key, business_role, card_type,
              usd_amount, rate, rmb_amount, note, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            RETURNING id
            """,
            (
                period_id,
                linked_transaction_id,
                group_key,
                business_role,
                card_type,
                usd_amount,
                rate,
                rmb_amount,
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
            (
                platform,
                chat_id,
                sender_id,
                message,
                amount,
                category,
                rate,
                rmb_value,
                ngn_value,
                duration_minutes,
                remind_at,
            ),
        )
        row = cur.fetchone()
        self.conn.commit()
        return int(row["id"])
