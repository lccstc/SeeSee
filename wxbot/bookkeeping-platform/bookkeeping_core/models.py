from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .contracts import NormalizedMessageEnvelope


@dataclass(slots=True, init=False)
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
    raw: dict[str, Any]
    sender_kind: str
    content_type: str
    received_at: str | None

    def __init__(
        self,
        *,
        platform: str,
        message_id: str,
        chat_id: str,
        chat_name: str,
        sender_id: str,
        sender_name: str,
        content: str,
        is_group: bool,
        from_self: bool,
        raw: dict[str, Any],
        sender_kind: str | None = None,
        content_type: str | None = None,
        received_at: str | None = None,
    ) -> None:
        self.platform = platform
        self.message_id = message_id
        self.chat_id = chat_id
        self.chat_name = chat_name
        self.sender_id = sender_id
        self.sender_name = sender_name
        self.content = content
        self.is_group = is_group
        self.raw = raw
        normalized_sender_kind = sender_kind if sender_kind is not None else ("self" if from_self else "user")
        normalized_from_self = bool(from_self) or normalized_sender_kind == "self"
        if normalized_from_self:
            normalized_sender_kind = "self"
        self.sender_kind = normalized_sender_kind
        self.from_self = normalized_from_self
        self.content_type = content_type or "text"
        self.received_at = received_at

    @property
    def text(self) -> str:
        return self.content

    @property
    def normalized(self) -> NormalizedMessageEnvelope:
        return NormalizedMessageEnvelope(
            platform=self.platform,
            message_id=self.message_id,
            chat_id=self.chat_id,
            chat_name=self.chat_name,
            is_group=self.is_group,
            sender_id=self.sender_id,
            sender_name=self.sender_name,
            sender_kind=self.sender_kind,
            content_type=self.content_type,
            text=self.content,
            from_self=self.from_self,
            received_at=self.received_at,
        )


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
