from __future__ import annotations

from dataclasses import dataclass

from .database import BookkeepingDB
from .models import ParsedTransaction


@dataclass(slots=True)
class StructuredTransactionRecord:
    platform: str
    group_key: str
    group_num: int | None
    chat_id: str
    chat_name: str
    sender_id: str
    sender_name: str
    message_id: str
    created_at: str | None
    input_sign: int
    amount: float
    category: str
    rate: float | None
    rmb_value: float
    raw: str
    parse_version: str = "1"
    usd_amount: float | None = None
    unit_face_value: float | None = None
    unit_count: float | None = None


def build_runtime_record(
    *,
    platform: str,
    group_key: str,
    group_num: int | None,
    chat_id: str,
    chat_name: str,
    sender_id: str,
    sender_name: str,
    message_id: str,
    created_at: str | None,
    parsed: ParsedTransaction,
) -> StructuredTransactionRecord:
    return StructuredTransactionRecord(
        platform=platform,
        group_key=group_key,
        group_num=group_num,
        chat_id=chat_id,
        chat_name=chat_name,
        sender_id=sender_id,
        sender_name=sender_name,
        message_id=message_id,
        created_at=created_at,
        input_sign=parsed.input_sign,
        amount=parsed.amount,
        category=parsed.category,
        rate=parsed.rate,
        rmb_value=parsed.rmb_value,
        raw=parsed.raw,
        parse_version="1",
    )


def build_sync_created_record(
    *,
    platform: str,
    group_key: str,
    group_num: int | None,
    chat_id: str,
    chat_name: str,
    sender_id: str,
    sender_name: str,
    message_id: str,
    created_at: str | None,
    input_sign: int,
    amount: float,
    category: str,
    rate: float | None,
    rmb_value: float,
    raw: str,
) -> StructuredTransactionRecord:
    return StructuredTransactionRecord(
        platform=platform,
        group_key=group_key,
        group_num=group_num,
        chat_id=chat_id,
        chat_name=chat_name,
        sender_id=sender_id,
        sender_name=sender_name,
        message_id=message_id,
        created_at=created_at,
        input_sign=input_sign,
        amount=amount,
        category=category,
        rate=rate,
        rmb_value=rmb_value,
        raw=raw,
        parse_version="1",
    )


def persist_transaction_record(db: BookkeepingDB, record: StructuredTransactionRecord) -> int:
    return db.add_transaction(
        platform=record.platform,
        group_key=record.group_key,
        group_num=record.group_num,
        chat_id=record.chat_id,
        chat_name=record.chat_name,
        sender_id=record.sender_id,
        sender_name=record.sender_name,
        message_id=record.message_id,
        input_sign=record.input_sign,
        amount=record.amount,
        category=record.category,
        rate=record.rate,
        rmb_value=record.rmb_value,
        raw=record.raw,
        created_at=record.created_at,
        parse_version=record.parse_version,
        usd_amount=record.usd_amount,
        unit_face_value=record.unit_face_value,
        unit_count=record.unit_count,
    )
