from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .models import ReminderPayload


DBRow = dict[str, Any]


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
        return int(cur.lastrowid) if cur.lastrowid else 0

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
