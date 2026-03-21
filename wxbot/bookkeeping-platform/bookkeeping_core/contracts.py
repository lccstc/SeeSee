from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, NotRequired, TypedDict


class SendTextAction(TypedDict):
    action_type: Literal["send_text"]
    chat_id: str
    text: str


class SendFileAction(TypedDict):
    action_type: Literal["send_file"]
    chat_id: str
    file_path: str
    caption: NotRequired[str]


CoreAction = SendTextAction | SendFileAction


def _required_text(payload: dict[str, Any], field: str) -> str:
    value = payload.get(field)
    text = str(value).strip() if value is not None else ""
    if not text:
        raise ValueError(f"Missing required field: {field}")
    return text


def _normalized_sender_kind(payload: dict[str, Any]) -> tuple[str, bool]:
    sender_kind_value = payload.get("sender_kind")
    from_self = bool(payload.get("from_self"))
    if sender_kind_value is None:
        sender_kind = "self" if from_self else "user"
    else:
        sender_kind = str(sender_kind_value)
    if from_self or sender_kind == "self":
        return "self", True
    return sender_kind, False


@dataclass(slots=True)
class NormalizedMessageEnvelope:
    platform: str
    message_id: str
    chat_id: str
    chat_name: str
    is_group: bool
    sender_id: str
    sender_name: str
    sender_kind: str = "user"
    content_type: str = "text"
    text: str = ""
    from_self: bool = False
    received_at: str | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "NormalizedMessageEnvelope":
        platform = _required_text(payload, "platform")
        message_id = _required_text(payload, "message_id")
        chat_id = _required_text(payload, "chat_id")
        sender_id = _required_text(payload, "sender_id")
        sender_kind, from_self = _normalized_sender_kind(payload)
        return cls(
            platform=platform,
            message_id=message_id,
            chat_id=chat_id,
            chat_name=str(payload.get("chat_name") or payload.get("chat_id") or ""),
            is_group=bool(payload.get("is_group")),
            sender_id=sender_id,
            sender_name=str(payload.get("sender_name") or payload.get("sender_id") or ""),
            sender_kind=sender_kind,
            content_type=str(payload.get("content_type") or "text"),
            text=str(payload.get("text") or ""),
            from_self=from_self,
            received_at=str(payload["received_at"]) if payload.get("received_at") is not None else None,
        )

    @property
    def content(self) -> str:
        return self.text


def send_text_action(chat_id: str, text: str) -> CoreAction:
    return {
        "action_type": "send_text",
        "chat_id": chat_id,
        "text": text,
    }


def send_file_action(chat_id: str, file_path: str, caption: str | None = None) -> CoreAction:
    action: CoreAction = {
        "action_type": "send_file",
        "chat_id": chat_id,
        "file_path": file_path,
    }
    if caption:
        action["caption"] = caption
    return action


def core_action_to_dict(action: CoreAction) -> dict[str, Any]:
    if action["action_type"] not in ("send_text", "send_file"):
        raise ValueError(f"Unsupported core action type: {action['action_type']}")
    return dict(action)


class CoreActionCollector:
    def __init__(self) -> None:
        self.actions: list[CoreAction] = []

    def send_text(self, chat_id: str, text: str) -> bool:
        self.actions.append(send_text_action(chat_id, text))
        return True

    def send_file(self, chat_id: str, file_path: str, caption: str | None = None) -> bool:
        self.actions.append(send_file_action(chat_id, file_path, caption))
        return True
