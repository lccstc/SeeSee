from __future__ import annotations

import sqlite3
from pathlib import Path

from .database import BookkeepingDB


def import_whatsapp_legacy_db(legacy_db_path: str | Path, target_db: BookkeepingDB) -> dict[str, int]:
    legacy_conn = sqlite3.connect(str(legacy_db_path))
    legacy_conn.row_factory = sqlite3.Row

    counts = {"groups": 0, "transactions": 0, "settlements": 0}

    try:
        groups = legacy_conn.execute("SELECT * FROM groups ORDER BY created_at ASC, group_id ASC").fetchall()
        for row in groups:
            group_id = str(row["group_id"])
            target_db.set_group(
                platform="whatsapp",
                group_key=f"whatsapp:{group_id}",
                chat_id=group_id,
                chat_name=group_id,
                group_num=int(row["group_num"]) if row["group_num"] is not None else 0,
            )
            counts["groups"] += 1

        settlements = legacy_conn.execute("SELECT * FROM settlements ORDER BY settled_at ASC, id ASC").fetchall()
        for row in settlements:
            target_db.conn.execute(
                """
                INSERT INTO settlements (
                  platform, group_key, settle_date, total_rmb, detail, settled_at, settled_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "whatsapp",
                    f"whatsapp:{row['group_id']}",
                    str(row["settle_date"]),
                    float(row["total_rmb"]),
                    str(row["detail"]),
                    str(row["settled_at"]),
                    str(row["settled_by"]),
                ),
            )
            counts["settlements"] += 1

        transactions = legacy_conn.execute(
            "SELECT * FROM transactions WHERE deleted = 0 ORDER BY created_at ASC, id ASC"
        ).fetchall()
        for row in transactions:
            group_id = str(row["group_id"])
            group_key = f"whatsapp:{group_id}"
            group_row = target_db.conn.execute(
                "SELECT chat_name, group_num FROM groups WHERE group_key = ?",
                (group_key,),
            ).fetchone()
            target_db.add_transaction(
                platform="whatsapp",
                group_key=group_key,
                group_num=int(group_row["group_num"]) if group_row and group_row["group_num"] is not None else None,
                chat_id=group_id,
                chat_name=str(group_row["chat_name"]) if group_row is not None else group_id,
                sender_id=str(row["sender_id"]),
                sender_name=str(row["sender_id"]),
                message_id=f"legacy-whatsapp-{row['id']}",
                input_sign=int(row["input_sign"]),
                amount=float(row["amount"]),
                category=str(row["category"]),
                rate=float(row["rate"]) if row["rate"] is not None else None,
                rmb_value=float(row["rmb_value"]),
                raw=str(row["raw"]),
                created_at=str(row["created_at"]),
                deleted=int(row["deleted"]),
                settled=int(row["settled"]),
                ngn_rate_override=float(row["ngn_rate"]) if row["ngn_rate"] is not None else None,
            )
            counts["transactions"] += 1

        target_db._backfill_settlement_links()
        target_db.conn.commit()
        return counts
    finally:
        legacy_conn.close()
