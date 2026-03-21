"""Historical compatibility importer for `/api/sync/events`.

This module keeps the legacy sync ingestion path alive for backfill and
compatibility imports. It is not the live runtime entrypoint; live message
processing happens through `/api/core/messages`.
"""


from __future__ import annotations

from typing import Any


class _CommitSuppressedConnection:
    def __init__(self, inner_conn) -> None:
        self._inner_conn = inner_conn

    def execute(self, sql: str, params=()):
        return self._inner_conn.execute(sql, params)

    def commit(self) -> None:
        return None

    def rollback(self) -> None:
        self._inner_conn.rollback()

    def close(self) -> None:
        self._inner_conn.close()

    def __getattr__(self, name: str):
        return getattr(self._inner_conn, name)


def ingest_sync_events(db, events: list[dict[str, Any]]) -> dict[str, int]:
    accepted = 0
    duplicates = 0

    for event in events:
        event_id = str(event["event_id"])
        existing = db.conn.execute(
            "SELECT 1 FROM ingested_events WHERE event_id = ?",
            (event_id,),
        ).fetchone()
        if existing is not None:
            duplicates += 1
            continue

        original_conn = db.conn
        db.conn = _CommitSuppressedConnection(original_conn)
        try:
            _apply_event(db, event)
            original_conn.execute(
                """
                INSERT INTO ingested_events (
                  event_id, event_type, platform, source_machine, schema_version, occurred_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    str(event["event_type"]),
                    str(event["platform"]),
                    str(event["source_machine"]),
                    int(event["schema_version"]),
                    str(event["occurred_at"]),
                ),
            )
            original_conn.commit()
            accepted += 1
        except Exception:
            original_conn.rollback()
            raise
        finally:
            db.conn = original_conn

    return {"accepted": accepted, "duplicates": duplicates}


def _apply_event(db, event: dict[str, Any]) -> None:
    event_type = str(event["event_type"])
    platform = str(event["platform"])
    payload = dict(event["payload"])

    if platform != "whatsapp":
        raise ValueError(f"Unsupported platform: {platform}")

    if event_type == "group.set":
        _apply_group_set(db, payload)
        return
    if event_type == "transaction.created":
        _apply_transaction_created(db, platform, payload)
        return
    if event_type == "transaction.deleted":
        _apply_transaction_deleted(db, platform, payload)
        return
    if event_type == "transactions.cleared":
        _apply_transactions_cleared(db, platform, payload)
        return
    if event_type == "settlement.created":
        _apply_settlement_created(db, platform, payload)
        return
    raise ValueError(f"Unsupported event_type: {event_type}")


def _apply_group_set(db, payload: dict[str, Any]) -> None:
    group_id = str(payload["group_id"])
    db.set_group(
        platform="whatsapp",
        group_key=_group_key(group_id),
        chat_id=group_id,
        chat_name=str(payload.get("chat_name") or group_id),
        group_num=int(payload["group_num"]),
    )


def _apply_transaction_created(db, platform: str, payload: dict[str, Any]) -> None:
    group_id = str(payload["group_id"])
    group_key = _group_key(group_id)
    if payload.get("group_num") is not None:
        db.set_group(
            platform=platform,
            group_key=group_key,
            chat_id=group_id,
            chat_name=str(payload.get("chat_name") or group_id),
            group_num=int(payload["group_num"]),
        )

    db.add_transaction(
        platform=platform,
        group_key=group_key,
        group_num=int(payload["group_num"]) if payload.get("group_num") is not None else db.get_group_num(group_key),
        chat_id=group_id,
        chat_name=str(payload.get("chat_name") or group_id),
        sender_id=str(payload["sender_id"]),
        sender_name=str(payload.get("sender_name") or payload["sender_id"]),
        message_id=_message_id(payload["source_transaction_id"]),
        input_sign=int(payload["input_sign"]),
        amount=float(payload["amount"]),
        category=str(payload["category"]),
        rate=float(payload["rate"]) if payload.get("rate") is not None else None,
        rmb_value=float(payload["rmb_value"]),
        raw=str(payload["raw"]),
        created_at=str(payload["created_at"]).replace("T", " ").replace("Z", "") if payload.get("created_at") else None,
    )


def _apply_transaction_deleted(db, platform: str, payload: dict[str, Any]) -> None:
    group_id = str(payload["group_id"])
    db.conn.execute(
        """
        UPDATE transactions
        SET deleted = 1
        WHERE platform = ? AND group_key = ? AND message_id = ?
        """,
        (
            platform,
            _group_key(group_id),
            _message_id(payload["source_transaction_id"]),
        ),
    )


def _apply_transactions_cleared(db, platform: str, payload: dict[str, Any]) -> None:
    group_id = str(payload["group_id"])
    source_ids = [str(item) for item in payload.get("source_transaction_ids", []) if str(item).strip()]
    if not source_ids:
        return
    placeholders = ",".join("?" for _ in source_ids)
    db.conn.execute(
        f"""
        UPDATE transactions
        SET deleted = 1
        WHERE platform = ? AND group_key = ? AND message_id IN ({placeholders})
        """,
        [platform, _group_key(group_id), *[_message_id(item) for item in source_ids]],
    )


def _apply_settlement_created(db, platform: str, payload: dict[str, Any]) -> None:
    group_id = str(payload["group_id"])
    group_key = _group_key(group_id)
    tx_source_ids = [str(item) for item in payload.get("source_transaction_ids", []) if str(item).strip()]
    if not tx_source_ids:
        return

    placeholders = ",".join("?" for _ in tx_source_ids)
    rows = db.conn.execute(
        f"""
        SELECT *
        FROM transactions
        WHERE platform = ? AND group_key = ? AND message_id IN ({placeholders}) AND deleted = 0
        ORDER BY id ASC
        """,
        [platform, group_key, *[_message_id(item) for item in tx_source_ids]],
    ).fetchall()
    if not rows:
        return

    db.settle_transactions(
        platform,
        group_key,
        rows,
        str(payload["settled_by"]),
        settled_at=str(payload["settled_at"]).replace("T", " ").replace("Z", ""),
    )


def _group_key(group_id: str) -> str:
    return f"whatsapp:{group_id}"


def _message_id(source_transaction_id: Any) -> str:
    return f"whatsapp-local-tx-{source_transaction_id}"
