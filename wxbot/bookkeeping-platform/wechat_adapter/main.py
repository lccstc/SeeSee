from __future__ import annotations

import logging
import os
import sys
import time

from bookkeeping_core.database import BookkeepingDB
from bookkeeping_core.service import BookkeepingService

from .client import WeChatPlatformAPI
from .config import load_config, save_config


def _is_master(db: BookkeepingDB, config, sender_id: str) -> bool:
    return sender_id in set(config.master_users) or db.is_admin(sender_id)


def _handle_control_command(message, platform_api: WeChatPlatformAPI, config, logger, db: BookkeepingDB) -> bool:
    text = (message.content or "").strip()
    observed_id = message.sender_id or ""
    sender_name = message.sender_name or ""
    sender_id = db.resolve_identity(
        platform=message.platform,
        chat_id=message.chat_id,
        observed_id=observed_id,
        observed_name=sender_name,
    )
    is_master = _is_master(db, config, sender_id)

    if text.startswith("/"):
        logger.info(
            "[control:%s] %s (%s -> %s): %s | is_master=%s",
            message.chat_id,
            sender_name,
            observed_id,
            sender_id,
            text,
            is_master,
        )

    if text.startswith("/bindid"):
        parts = text.split(" ", 1)
        if len(parts) != 2 or not parts[1].strip():
            platform_api.send_text(message.chat_id, "格式: /bindid 真实微信号\n例: /bindid Button-Leo")
            return True
        canonical_id = parts[1].strip()
        if not _is_master(db, config, canonical_id) and not db.is_whitelisted(canonical_id):
            platform_api.send_text(message.chat_id, f"目标ID未在管理员或白名单中: {canonical_id}")
            return True
        db.bind_identity(
            platform=message.platform,
            chat_id=message.chat_id,
            observed_id=observed_id,
            observed_name=sender_name,
            canonical_id=canonical_id,
        )
        platform_api.send_text(message.chat_id, f"绑定成功\nname={sender_name or '-'}\nobserved_id={observed_id or '-'}\ncanonical_id={canonical_id}")
        return True

    if text == "/whoami":
        platform_api.send_text(message.chat_id, f"name={sender_name or '-'}\nobserved_id={observed_id or '-'}\nid={sender_id or '-'}\nis_master={'true' if is_master else 'false'}")
        return True

    if not is_master:
        return False

    if text == "/groups":
        lines = ["当前监听名单:"]
        lines.extend(f"- {name}" for name in platform_api.listen_chats)
        platform_api.send_text(message.chat_id, "\n".join(lines))
        return True

    if text.startswith("/qxqz"):
        parts = text.split(" ", 1)
        if len(parts) != 2 or not parts[1].strip():
            platform_api.send_text(message.chat_id, "格式: /qxqz 群名\n例: /qxqz 皇家议事厅【1111】")
            return True
        target_chat = parts[1].strip()
        if not platform_api.remove_listener(target_chat):
            platform_api.send_text(message.chat_id, f"监听不存在: {target_chat}")
            return True
        config.listen_chats = list(platform_api.listen_chats)
        save_config(config)
        logger.info("Listen chat removed: %s", target_chat)
        platform_api.send_text(message.chat_id, f"已取消激活: {target_chat}")
        return True

    if not text.startswith("/jhqz"):
        return False

    parts = text.split(" ", 1)
    if len(parts) != 2 or not parts[1].strip():
        platform_api.send_text(message.chat_id, "格式: /jhqz 群名\n例: /jhqz 皇家议事厅【1111】")
        return True
    target_chat = parts[1].strip()
    if target_chat in platform_api.listen_chats:
        platform_api.send_text(message.chat_id, f"已激活: {target_chat}")
        return True
    if not platform_api.add_listener(target_chat):
        platform_api.send_text(message.chat_id, f"激活失败")
        return True
    config.listen_chats = list(platform_api.listen_chats)
    save_config(config)
    logger.info("New listen chat added: %s", target_chat)
    platform_api.send_text(message.chat_id, f"已激活: {target_chat}\n下一步请到该群里发送 /set 1-9 进行分组")
    return True


def main() -> int:
    config = load_config()
    logging.basicConfig(level=getattr(logging, config.log_level.upper(), logging.INFO), format="%(asctime)s [%(levelname)s] %(message)s")
    logger = logging.getLogger("wechat-adapter")
    platform_api = WeChatPlatformAPI(listen_chats=config.listen_chats, language=config.language, runtime_dir=config.runtime_dir)
    db = BookkeepingDB(config.db_path)
    service = BookkeepingService(db=db, platform_api=platform_api, master_users=config.master_users, export_dir=config.export_dir)

    exit_code = 0
    try:
        platform_api.ensure_listeners()
        config.listen_chats = list(platform_api.listen_chats)
        save_config(config)
        logger.info("WeChat self identity: nickname=%s wxid=%s", getattr(platform_api, "self_name", ""), getattr(platform_api, "self_wxid", ""))
        logger.info("WeChat adapter started. Listening chats: %s", ", ".join(platform_api.listen_chats))
        while True:
            for message in platform_api.poll_messages():
                if _handle_control_command(message, platform_api, config, logger, db):
                    continue
                service.handle_message(message)
            service.flush_due_reminders()
            time.sleep(config.poll_interval_seconds)
    except KeyboardInterrupt:
        logger.info("WeChat adapter stopped by user")
    except Exception:
        logger.exception("Fatal error")
        exit_code = 1
    finally:
        db.close()
    return exit_code


if __name__ == "__main__":
    code = main()
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(code)

