from __future__ import annotations

from pathlib import Path
from typing import Any

from .contracts import CoreAction, NormalizedMessageEnvelope
from .quotes import QuoteCaptureService
from .service import BookkeepingService


class UnifiedBookkeepingRuntime:
    def __init__(self, *, db, master_users: list[str], export_dir: str | Path) -> None:
        self.service = BookkeepingService(
            db=db,
            master_users=master_users,
            export_dir=export_dir,
        )
        self.quote_capture = QuoteCaptureService(db)
        self._queued_actions: list[CoreAction] = []

    def process_envelope(self, envelope: NormalizedMessageEnvelope | dict[str, Any]) -> list[CoreAction]:
        raw_payload: dict[str, Any]
        if isinstance(envelope, dict):
            raw_payload = dict(envelope)
            envelope = NormalizedMessageEnvelope.from_dict(envelope)
        else:
            raw_payload = self._serialize_envelope(envelope)

        if not self._record_incoming_message(envelope, raw_payload):
            return []
        self.quote_capture.capture_from_message(envelope, raw_text=envelope.text)
        return self.service.process_envelope(envelope)

    def flush_due_actions(self) -> list[CoreAction]:
        return self.service.flush_due_actions()

    def enqueue_actions(self, actions: list[CoreAction]) -> None:
        self._queued_actions.extend(actions)

    def drain_outbound_actions(self) -> list[CoreAction]:
        pending = list(self._queued_actions)
        self._queued_actions.clear()
        pending.extend(self.service.flush_due_actions())
        return pending

    def _record_incoming_message(self, envelope: NormalizedMessageEnvelope, raw_payload: dict[str, Any]) -> bool:
        return self.service.db.record_incoming_message(
            platform=envelope.platform,
            group_key=f"{envelope.platform}:{envelope.chat_id}",
            chat_id=envelope.chat_id,
            chat_name=envelope.chat_name,
            message_id=envelope.message_id,
            is_group=envelope.is_group,
            sender_id=envelope.sender_id,
            sender_name=envelope.sender_name,
            sender_kind=envelope.sender_kind,
            content_type=envelope.content_type,
            text=envelope.text,
            from_self=envelope.from_self,
            received_at=envelope.received_at,
            raw_payload=raw_payload,
        )

    @staticmethod
    def _serialize_envelope(envelope: NormalizedMessageEnvelope) -> dict[str, Any]:
        return {
            "platform": envelope.platform,
            "message_id": envelope.message_id,
            "chat_id": envelope.chat_id,
            "chat_name": envelope.chat_name,
            "is_group": envelope.is_group,
            "sender_id": envelope.sender_id,
            "sender_name": envelope.sender_name,
            "sender_kind": envelope.sender_kind,
            "content_type": envelope.content_type,
            "text": envelope.text,
            "from_self": envelope.from_self,
            "received_at": envelope.received_at,
        }
