from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class IncomingMessage:
    platform: str
    message_id: str
    chat_id: str
    chat_name: str
    sender_id: str
    sender_name: str
    content: str
    is_group: bool
    from_self: bool
    raw: dict


@dataclass(slots=True)
class ParsedTransaction:
    input_sign: int
    amount: float
    category: str
    rate: float | None
    rmb_value: float
    raw: str


@dataclass(slots=True)
class ReminderPayload:
    id: int
    platform: str
    chat_id: str
    sender_id: str
    message: str
    amount: float
    category: str
    rate: float | None
    rmb_value: float
    ngn_value: float | None
    duration_minutes: int
    remind_at: str
