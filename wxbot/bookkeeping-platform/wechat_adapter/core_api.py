from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any, Callable
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from bookkeeping_core.contracts import CoreAction, NormalizedMessageEnvelope


class WeChatCoreApiClient:
    def __init__(
        self,
        *,
        endpoint: str,
        token: str,
        request_timeout_seconds: float,
        opener: Callable[..., Any] = urlopen,
    ) -> None:
        self.endpoint = endpoint.strip()
        self.token = token.strip()
        self.request_timeout_seconds = request_timeout_seconds
        self.opener = opener

    def send_envelope(self, envelope: NormalizedMessageEnvelope) -> list[CoreAction]:
        request = Request(
            urljoin(self.endpoint.rstrip("/") + "/", "/api/core/messages"),
            data=json.dumps(asdict(envelope), ensure_ascii=False).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.token}",
            },
            method="POST",
        )
        with self.opener(request, timeout=self.request_timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8") or "{}")
        actions = payload.get("actions", [])
        if not isinstance(actions, list):
            raise ValueError("Core API response missing actions")
        return [self._validate_action(action) for action in actions]

    def fetch_outbound_actions(self) -> list[CoreAction]:
        request = Request(
            urljoin(self.endpoint.rstrip("/") + "/", "/api/core/actions"),
            data=b"{}",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.token}",
            },
            method="POST",
        )
        with self.opener(request, timeout=self.request_timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8") or "{}")
        actions = payload.get("actions", [])
        if not isinstance(actions, list):
            raise ValueError("Core API response missing actions")
        return [self._validate_action(action) for action in actions]

    def acknowledge_outbound_actions(self, items: list[dict[str, object]]) -> int:
        if not items:
            return 0
        request = Request(
            urljoin(self.endpoint.rstrip("/") + "/", "/api/core/actions/ack"),
            data=json.dumps({"items": items}, ensure_ascii=False).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.token}",
            },
            method="POST",
        )
        with self.opener(request, timeout=self.request_timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8") or "{}")
        updated = payload.get("updated", 0)
        return int(updated) if isinstance(updated, (int, float)) else 0

    def resolve_identity(self, envelope: NormalizedMessageEnvelope) -> tuple[str, bool] | None:
        probe = NormalizedMessageEnvelope(
            platform=envelope.platform,
            message_id=f"{envelope.message_id}::whoami",
            chat_id=envelope.chat_id,
            chat_name=envelope.chat_name or envelope.chat_id,
            is_group=envelope.is_group,
            sender_id=envelope.sender_id,
            sender_name=envelope.sender_name,
            sender_kind=envelope.sender_kind,
            content_type="text",
            text="/whoami",
            from_self=envelope.from_self,
            received_at=envelope.received_at,
        )
        actions = self.send_envelope(probe)
        for action in actions:
            if action.get("action_type") != "send_text":
                continue
            text = str(action.get("text") or "")
            parsed = self._parse_whoami_text(text)
            if parsed is not None:
                return parsed
        return None

    @staticmethod
    def _validate_action(action: Any) -> CoreAction:
        if not isinstance(action, dict):
            raise ValueError("Invalid core action payload")
        action_type = action.get("action_type")
        if action_type == "send_text":
            chat_id = str(action.get("chat_id") or "").strip()
            text = str(action.get("text") or "")
            if not chat_id or text == "":
                raise ValueError("Invalid core action payload: send_text")
            result: dict[str, Any] = {
                "action_type": "send_text",
                "chat_id": chat_id,
                "text": text,
            }
            if isinstance(action.get("id"), int):
                result["id"] = action["id"]
            return result
        if action_type == "send_file":
            chat_id = str(action.get("chat_id") or "").strip()
            file_path = str(action.get("file_path") or "").strip()
            if not chat_id or not file_path:
                raise ValueError("Invalid core action payload: send_file")
            result: dict[str, Any] = {
                "action_type": "send_file",
                "chat_id": chat_id,
                "file_path": file_path,
            }
            caption = action.get("caption")
            if isinstance(caption, str) and caption:
                result["caption"] = caption
            if isinstance(action.get("id"), int):
                result["id"] = action["id"]
            return result
        raise ValueError(f"Unknown core action: {action_type}")

    @staticmethod
    def _parse_whoami_text(text: str) -> tuple[str, bool] | None:
        line_map: dict[str, str] = {}
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            line_map[key.strip().lower()] = value.strip()
        canonical_id = line_map.get("id", "")
        if not canonical_id:
            return None
        is_master = line_map.get("is_master", "").lower() == "true"
        return canonical_id, is_master
