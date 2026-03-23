from __future__ import annotations

import logging
import os
import sys
import time

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
    exit_code = 0
    try:
        if not config.core_api.enabled():
            raise RuntimeError("WeChat adapter now requires core_api.endpoint and core_api.token")
        platform_api = WeChatPlatformAPI(
            listen_chats=config.listen_chats,
            language=config.language,
            runtime_dir=config.runtime_dir,
            config=config,
            logger=logger,
        )
        remote_core = WeChatCoreApiClient(
            endpoint=config.core_api.endpoint,
            token=config.core_api.token,
            request_timeout_seconds=config.core_api.request_timeout_seconds,
        )
        logger.info("WeChat adapter running in remote core mode: %s", config.core_api.endpoint)
        platform_api.ensure_listeners()
        config.listen_chats = list(platform_api.listen_chats)
        save_config(config)
        logger.info("WeChat self identity: nickname=%s wxid=%s", getattr(platform_api, "self_name", ""), getattr(platform_api, "self_wxid", ""))
        logger.info("WeChat adapter started. Listening chats: %s", ", ".join(platform_api.listen_chats))
        while True:
            for message in platform_api.poll_messages():
                actions = remote_core.send_envelope(message)
                _execute_actions(platform_api, actions)
            time.sleep(config.poll_interval_seconds)
    except KeyboardInterrupt:
        logger.info("WeChat adapter stopped by user")
    except Exception:
        logger.exception("Fatal error")
        exit_code = 1
    return exit_code


if __name__ == "__main__":
    code = main()
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(code)

