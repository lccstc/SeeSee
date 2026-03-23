from __future__ import annotations

from pathlib import Path
from typing import Any

from .contracts import CoreAction, NormalizedMessageEnvelope
from .service import BookkeepingService


class UnifiedBookkeepingRuntime:
    def __init__(self, *, db, master_users: list[str], export_dir: str | Path) -> None:
        self.service = BookkeepingService(
            db=db,
            master_users=master_users,
            export_dir=export_dir,
        )
        self._queued_actions: list[CoreAction] = []

    def process_envelope(self, envelope: NormalizedMessageEnvelope | dict[str, Any]) -> list[CoreAction]:
        if isinstance(envelope, dict):
            envelope = NormalizedMessageEnvelope.from_dict(envelope)
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
