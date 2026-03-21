from __future__ import annotations

import logging
import os
import sys
import time

from bookkeeping_core.database import BookkeepingDB
from bookkeeping_core.runtime import UnifiedBookkeepingRuntime

from .client import WeChatPlatformAPI
from .config import load_config, save_config
from .core_api import WeChatCoreApiClient


def _execute_actions(platform_api: WeChatPlatformAPI, actions) -> None:
    for action in actions:
        action_type = action.get("action_type")
        if action_type == "send_text":
            platform_api.send_text(action["chat_id"], action["text"])
        elif action_type == "send_file":
            platform_api.send_file(action["chat_id"], action["file_path"])


def main() -> int:
    config = load_config()
    logging.basicConfig(level=getattr(logging, config.log_level.upper(), logging.INFO), format="%(asctime)s [%(levelname)s] %(message)s")
    logger = logging.getLogger("wechat-adapter")
    db = BookkeepingDB(config.db_path)
    platform_api = WeChatPlatformAPI(
        listen_chats=config.listen_chats,
        language=config.language,
        runtime_dir=config.runtime_dir,
        config=config,
        db=db,
        logger=logger,
    )
    runtime = None
    remote_core = None
    if config.core_api.enabled():
        remote_core = WeChatCoreApiClient(
            endpoint=config.core_api.endpoint,
            token=config.core_api.token,
            request_timeout_seconds=config.core_api.request_timeout_seconds,
        )
        logger.info("WeChat adapter running in remote core mode: %s", config.core_api.endpoint)
    else:
        runtime = UnifiedBookkeepingRuntime(db=db, master_users=config.master_users, export_dir=config.export_dir)
        logger.info("WeChat adapter running in local core mode")

    exit_code = 0
    try:
        platform_api.ensure_listeners()
        config.listen_chats = list(platform_api.listen_chats)
        save_config(config)
        logger.info("WeChat self identity: nickname=%s wxid=%s", getattr(platform_api, "self_name", ""), getattr(platform_api, "self_wxid", ""))
        logger.info("WeChat adapter started. Listening chats: %s", ", ".join(platform_api.listen_chats))
        while True:
            for message in platform_api.poll_messages():
                actions = remote_core.send_envelope(message) if remote_core is not None else runtime.process_envelope(message)
                _execute_actions(platform_api, actions)
            if runtime is not None:
                _execute_actions(platform_api, runtime.flush_due_actions())
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

