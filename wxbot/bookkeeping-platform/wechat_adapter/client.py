from __future__ import annotations

import os
from pathlib import Path

from bookkeeping_core.models import IncomingMessage


def prepare_runtime(runtime_dir: str | Path) -> None:
    runtime_dir = Path(runtime_dir)
    appdata_dir = runtime_dir / "appdata"
    cache_dir = runtime_dir / "comtypes_cache"
    appdata_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("APPDATA", str(appdata_dir))
    os.environ.setdefault("COMTYPES_CACHE", str(cache_dir))


class WeChatPlatformAPI:
    def __init__(self, listen_chats: list[str], language: str, runtime_dir: str) -> None:
        prepare_runtime(runtime_dir)
        from wxautox import WeChat

        self.listen_chats = list(dict.fromkeys(listen_chats))
        self.wx = WeChat(language=language, myinfo=True)
        self.self_name = getattr(self.wx, "nickname", "") or ""
        self.self_wxid = ((getattr(self.wx, "myinfo", None) or {}).get("id") or "")
        self._listeners_ready = False
        self._sender_cache: dict[tuple[str, str, str], dict[str, str]] = {}

    def ensure_listeners(self) -> None:
        if self._listeners_ready:
            return
        valid_chats: list[str] = []
        for chat in self.listen_chats:
            try:
                self.wx.AddListenChat(chat, exact=False)
                valid_chats.append(chat)
            except Exception:
                continue
        self.listen_chats = valid_chats
        self._listeners_ready = True

    def add_listener(self, chat_name: str) -> bool:
        chat_name = chat_name.strip()
        if not chat_name:
            return False
        if chat_name in self.listen_chats:
            return True
        try:
            self.wx.AddListenChat(chat_name, exact=False)
            self.listen_chats.append(chat_name)
            self._listeners_ready = True
            return True
        except Exception:
            return False

    def remove_listener(self, chat_name: str) -> bool:
        chat_name = chat_name.strip()
        if chat_name not in self.listen_chats:
            return False
        self.listen_chats = [name for name in self.listen_chats if name != chat_name]
        return True

    def poll_messages(self) -> list[IncomingMessage]:
        self.ensure_listeners()
        payload = self.wx.GetListenMessage()
        messages: list[IncomingMessage] = []
        if isinstance(payload, dict):
            for items in payload.values():
                if isinstance(items, list):
                    for item in items:
                        normalized = self._normalize_message(item)
                        if normalized is not None and normalized.chat_name in self.listen_chats:
                            messages.append(normalized)
        elif isinstance(payload, list):
            for item in payload:
                normalized = self._normalize_message(item)
                if normalized is not None and normalized.chat_name in self.listen_chats:
                    messages.append(normalized)
        return messages

    def send_text(self, chat_id: str, text: str) -> bool:
        try:
            result = self.wx.SendMsg(text, who=chat_id, exact=False)
            if isinstance(result, dict):
                return bool(result.get("status", True))
            return True
        except Exception:
            return False

    def send_file(self, chat_id: str, file_path: str) -> bool:
        try:
            result = self.wx.SendFiles(file_path, who=chat_id, exact=False)
            if isinstance(result, dict):
                return bool(result.get("status", True))
            return True
        except Exception:
            return False

    def _normalize_message(self, item) -> IncomingMessage | None:
        if item is None or not hasattr(item, "details"):
            return None
        details = dict(item.details)
        chat_name = str(details.get("chat_name") or "")
        from_self = str(details.get("type") or "") == "self"
        sender_name = str(details.get("sender_remark") or details.get("sender") or "")
        if from_self:
            if self.self_name:
                sender_name = self.self_name
            sender_id = self.self_wxid or sender_name or str(details.get("sender") or "")
        else:
            sender_id, sender_name = self._resolve_sender_identity(details)
        return IncomingMessage(
            platform="wechat",
            message_id=str(details.get("id") or ""),
            chat_id=chat_name,
            chat_name=chat_name,
            sender_id=sender_id,
            sender_name=sender_name,
            content=str(details.get("content") or "").strip(),
            is_group=str(details.get("chat_type") or "") == "group",
            from_self=from_self,
            raw=details,
        )

    def _resolve_sender_identity(self, details: dict) -> tuple[str, str]:
        sender = str(details.get("sender") or "")
        sender_remark = str(details.get("sender_remark") or "")
        chat_name = str(details.get("chat_name") or "")
        cache_key = (chat_name, sender, sender_remark)
        cached = self._sender_cache.get(cache_key)
        if cached:
            return cached["id"], cached["name"]

        sender_name = sender_remark or sender
        sender_id = sender_name or sender

        self._sender_cache[cache_key] = {"id": sender_id, "name": sender_name}
        if len(self._sender_cache) > 500:
            self._sender_cache = dict(list(self._sender_cache.items())[-250:])
        return sender_id, sender_name
