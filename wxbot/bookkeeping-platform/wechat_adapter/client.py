from __future__ import annotations

import os
from pathlib import Path

from bookkeeping_core.contracts import NormalizedMessageEnvelope

from .config import save_config


def prepare_runtime(runtime_dir: str | Path) -> None:
    runtime_dir = Path(runtime_dir)
    appdata_dir = runtime_dir / "appdata"
    cache_dir = runtime_dir / "comtypes_cache"
    appdata_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("APPDATA", str(appdata_dir))
    os.environ.setdefault("COMTYPES_CACHE", str(cache_dir))


class WeChatPlatformAPI:
    def __init__(self, listen_chats: list[str], language: str, runtime_dir: str, config=None, db=None, logger=None) -> None:
        prepare_runtime(runtime_dir)
        from wxautox import WeChat

        self.listen_chats = list(dict.fromkeys(listen_chats))
        self.wx = WeChat(language=language, myinfo=True)
        self.self_name = getattr(self.wx, "nickname", "") or ""
        self.self_wxid = ((getattr(self.wx, "myinfo", None) or {}).get("id") or "")
        self.config = config
        self.db = db
        self.logger = logger
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

    def poll_messages(self) -> list[NormalizedMessageEnvelope]:
        self.ensure_listeners()
        payload = self.wx.GetListenMessage()
        messages: list[NormalizedMessageEnvelope] = []
        if isinstance(payload, dict):
            for chat_ref, items in payload.items():
                if isinstance(items, list):
                    chat_name_hint = self._resolve_listened_chat_name(chat_ref)
                    for item in items:
                        try:
                            normalized = self._normalize_message(item, chat_name_hint=chat_name_hint)
                        except Exception:
                            if self.logger is not None:
                                self.logger.warning("Dropped invalid WeChat payload item", exc_info=True)
                            continue
                        if normalized is not None and not self._handle_control_envelope(normalized):
                            messages.append(normalized)
        elif isinstance(payload, list):
            for item in payload:
                try:
                    normalized = self._normalize_message(item)
                except Exception:
                    if self.logger is not None:
                        self.logger.warning("Dropped invalid WeChat payload item", exc_info=True)
                    continue
                if normalized is not None and normalized.chat_name in self.listen_chats and not self._handle_control_envelope(normalized):
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

    def _handle_control_envelope(self, message: NormalizedMessageEnvelope) -> bool:
        text = (message.content or "").strip()
        if not text.startswith("/"):
            return False
        if text != "/groups" and not text.startswith("/qxqz") and not text.startswith("/jhqz"):
            return False

        observed_id = message.sender_id or ""
        sender_name = message.sender_name or ""
        sender_id = observed_id
        if self.db is not None:
            sender_id = self.db.resolve_identity(
                platform=message.platform,
                chat_id=message.chat_id,
                observed_id=observed_id,
                observed_name=sender_name,
            )

        master_users = set(getattr(self.config, "master_users", [])) if self.config is not None else set()
        is_master = bool(self.db and (sender_id in master_users or self.db.is_admin(sender_id)))

        if self.logger is not None:
            self.logger.info(
                "[control:%s] %s (%s -> %s): %s | is_master=%s",
                message.chat_id,
                sender_name,
                observed_id,
                sender_id,
                text,
                is_master,
            )

        if not is_master:
            return False

        if text == "/groups":
            lines = ["当前监听名单:"]
            lines.extend(f"- {name}" for name in self.listen_chats)
            self.send_text(message.chat_id, "\n".join(lines))
            return True

        if text.startswith("/qxqz"):
            parts = text.split(" ", 1)
            if len(parts) != 2 or not parts[1].strip():
                self.send_text(message.chat_id, "格式: /qxqz 群名\n例: /qxqz 皇家议事厅【1111】")
                return True
            target_chat = parts[1].strip()
            if not self.remove_listener(target_chat):
                self.send_text(message.chat_id, f"监听不存在: {target_chat}")
                return True
            if self.config is not None:
                self.config.listen_chats = list(self.listen_chats)
                save_config(self.config)
            if self.logger is not None:
                self.logger.info("Listen chat removed: %s", target_chat)
            self.send_text(message.chat_id, f"已取消激活: {target_chat}")
            return True

        if not text.startswith("/jhqz"):
            return False

        parts = text.split(" ", 1)
        if len(parts) != 2 or not parts[1].strip():
            self.send_text(message.chat_id, "格式: /jhqz 群名\n例: /jhqz 皇家议事厅【1111】")
            return True
        target_chat = parts[1].strip()
        if target_chat in self.listen_chats:
            self.send_text(message.chat_id, f"已激活: {target_chat}")
            return True
        if not self.add_listener(target_chat):
            self.send_text(message.chat_id, f"激活失败")
            return True
        if self.config is not None:
            self.config.listen_chats = list(self.listen_chats)
            save_config(self.config)
        if self.logger is not None:
            self.logger.info("New listen chat added: %s", target_chat)
        self.send_text(message.chat_id, f"已激活: {target_chat}\n下一步请到该群里发送 /set 1-9 进行分组")
        return True

    def _normalize_message(self, item, chat_name_hint: str = "") -> NormalizedMessageEnvelope | None:
        if item is None or not hasattr(item, "details"):
            return None
        details = dict(item.details)
        chat_name = str(details.get("chat_name") or chat_name_hint or "")
        from_self = str(details.get("type") or "") == "self"
        sender_name = str(details.get("sender_remark") or details.get("sender") or "")
        if from_self:
            if self.self_name:
                sender_name = self.self_name
            sender_id = self.self_wxid or sender_name or str(details.get("sender") or "")
        else:
            sender_id, sender_name = self._resolve_sender_identity(details)
        return NormalizedMessageEnvelope.from_dict(
            {
                "platform": "wechat",
                "message_id": str(details.get("id") or ""),
                "chat_id": chat_name,
                "chat_name": chat_name,
                "is_group": str(details.get("chat_type") or "") == "group",
                "sender_id": sender_id,
                "sender_name": sender_name,
                "sender_kind": "self" if from_self else "user",
                "content_type": str(details.get("content_type") or details.get("msg_type") or "text"),
                "text": str(details.get("content") or details.get("text") or "").strip(),
                "from_self": from_self,
                "received_at": details.get("received_at"),
            }
        )

    @staticmethod
    def _resolve_listened_chat_name(chat_ref) -> str:
        who = getattr(chat_ref, "who", "")
        if isinstance(who, str) and who.strip():
            return who.strip()
        name = getattr(chat_ref, "Name", "")
        if isinstance(name, str) and name.strip():
            return name.strip()
        return ""

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
