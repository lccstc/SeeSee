from __future__ import annotations

from pathlib import Path

from bookkeeping_core.database import BookkeepingDB
from bookkeeping_core.periods import AccountingPeriodService
from bookkeeping_core.runtime import UnifiedBookkeepingRuntime


def ensure_group(
    db: BookkeepingDB,
    *,
    platform: str,
    group_key: str,
    chat_id: str,
    chat_name: str,
    group_num: int,
    business_role: str | None = None,
) -> None:
    db.set_group(
        platform=platform,
        group_key=group_key,
        chat_id=chat_id,
        chat_name=chat_name,
        group_num=group_num,
    )
    if business_role is not None:
        db.conn.execute(
            "UPDATE groups SET business_role = ? WHERE group_key = ?",
            (business_role, group_key),
        )
        db.conn.commit()


def close_period_for_test(db: BookkeepingDB, *, start_at: str, end_at: str) -> int:
    return AccountingPeriodService(db).close_period(
        start_at=start_at,
        end_at=end_at,
        closed_by="test-support",
    )


def build_runtime_card_scenario(
    *,
    message_prefix: str = "runtime-card",
    chat_id: str = "g-runtime-card",
    chat_name: str = "回放卡片群",
    group_num: int = 6,
    business_role: str | None = "customer",
    start_at: str = "2026-03-20 08:00:00",
    end_at: str = "2026-03-20 10:00:00",
    closed_by: str = "finance-mock",
    note: str | None = None,
    opening_created_at: str = "2026-03-20 07:30:00",
    card_created_at: str = "2026-03-20 08:20:00",
    expense_created_at: str = "2026-03-20 09:20:00",
    opening_amount: float = 20.0,
    card_amount: float = 20.0,
    card_rate: float = 2.5,
    card_rmb_value: float = 50.0,
    card_type: str = "steam",
    card_usd_amount: float = 600.0,
    card_unit_face_value: float = 20.0,
    card_unit_count: float = 30.0,
    expense_amount: float = 15.0,
) -> dict:
    group_key = f"wechat:{chat_id}"
    sender_id = "finance-mock"
    sender_name = "Finance Mock"
    return {
        "groups": [
            {
                "platform": "wechat",
                "group_key": group_key,
                "chat_id": chat_id,
                "chat_name": chat_name,
                "group_num": group_num,
                "business_role": business_role,
            }
        ],
        "envelopes": [
            {
                "platform": "wechat",
                "message_id": f"{message_prefix}-opening",
                "chat_id": chat_id,
                "chat_name": chat_name,
                "is_group": True,
                "sender_id": sender_id,
                "sender_name": sender_name,
                "content_type": "text",
                "text": f"+{opening_amount:g}rmb",
                "received_at": opening_created_at,
                "tx_patch": {
                    "created_at": opening_created_at,
                },
            },
            {
                "platform": "wechat",
                "message_id": f"{message_prefix}-card",
                "chat_id": chat_id,
                "chat_name": chat_name,
                "is_group": True,
                "sender_id": sender_id,
                "sender_name": sender_name,
                "content_type": "text",
                "text": f"+{card_amount:g}rmb",
                "received_at": card_created_at,
                "tx_patch": {
                    "created_at": card_created_at,
                    "amount": card_amount,
                    "category": card_type,
                    "rate": card_rate,
                    "rmb_value": card_rmb_value,
                    "raw": f"{card_type}+{card_amount:g} {card_rate:g}",
                    "usd_amount": card_usd_amount,
                    "unit_face_value": card_unit_face_value,
                    "unit_count": card_unit_count,
                },
            },
            {
                "platform": "wechat",
                "message_id": f"{message_prefix}-expense",
                "chat_id": chat_id,
                "chat_name": chat_name,
                "is_group": True,
                "sender_id": sender_id,
                "sender_name": sender_name,
                "content_type": "text",
                "text": f"-{expense_amount:g}rmb",
                "received_at": expense_created_at,
                "tx_patch": {
                    "created_at": expense_created_at,
                },
            },
        ],
        "start_at": start_at,
        "end_at": end_at,
        "closed_by": closed_by,
        "note": note,
    }


def replay_runtime_scenario(db: BookkeepingDB, scenario: dict) -> int:
    runtime = UnifiedBookkeepingRuntime(
        db=db,
        master_users=list(scenario.get("master_users", ["finance-mock"])),
        export_dir=Path("/tmp"),
    )

    for group in scenario.get("groups", []):
        ensure_group(
            db,
            platform=str(group["platform"]),
            group_key=str(group["group_key"]),
            chat_id=str(group["chat_id"]),
            chat_name=str(group["chat_name"]),
            group_num=int(group["group_num"]),
            business_role=str(group["business_role"]) if group.get("business_role") is not None else None,
        )

    for envelope in scenario.get("envelopes", []):
        runtime.process_envelope(dict(envelope))
        tx_patch = envelope.get("tx_patch")
        if tx_patch:
            _patch_transaction_by_message_id(db, message_id=str(envelope["message_id"]), tx_patch=dict(tx_patch))

    return AccountingPeriodService(db).close_period(
        start_at=str(scenario["start_at"]),
        end_at=str(scenario["end_at"]),
        closed_by=str(scenario["closed_by"]),
        note=str(scenario["note"]) if scenario.get("note") is not None else None,
    )


def _patch_transaction_by_message_id(db: BookkeepingDB, *, message_id: str, tx_patch: dict) -> None:
    allowed_columns = {
        "created_at",
        "amount",
        "category",
        "rate",
        "rmb_value",
        "raw",
        "usd_amount",
        "unit_face_value",
        "unit_count",
    }
    columns = [column for column in tx_patch.keys() if column in allowed_columns]
    if not columns:
        return
    assignments = ", ".join(f"{column} = ?" for column in columns)
    values = [tx_patch[column] for column in columns]
    cursor = db.conn.execute(
        f"UPDATE transactions SET {assignments} WHERE message_id = ?",
        (*values, message_id),
    )
    if cursor.rowcount != 1:
        raise AssertionError(f"Expected one transaction for replayed message_id={message_id}")
    db.conn.commit()
