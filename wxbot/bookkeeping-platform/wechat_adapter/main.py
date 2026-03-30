from __future__ import annotations

import logging
import os
import sys
import time
from collections import deque

from .client import WeChatPlatformAPI
from .config import load_config, save_config
from .core_api import WeChatCoreApiClient


def _execute_actions(platform_api: WeChatPlatformAPI, actions) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    for action in actions:
        action_type = action.get("action_type")
        success = False
        if action_type == "send_text":
            success = bool(platform_api.send_text(action["chat_id"], action["text"]))
        elif action_type == "send_file":
            success = bool(platform_api.send_file(action["chat_id"], action["file_path"]))
        else:
            raise ValueError(f"Unknown core action: {action_type}")
        if isinstance(action.get("id"), int):
            results.append(
                {
                    "id": action["id"],
                    "success": success,
                }
            )
    return results


def _acknowledge_results(remote_core: WeChatCoreApiClient, results: list[dict[str, object]], logger, *, source: str) -> None:
    if not results:
        return
    failed_count = sum(1 for item in results if not bool(item.get("success")))
    if failed_count > 0:
        logger.warning("%s actions failed to send: %s", source, failed_count)
    remote_core.acknowledge_outbound_actions(results)


def _flush_outbound_actions(platform_api: WeChatPlatformAPI, remote_core: WeChatCoreApiClient, logger) -> int:
    actions = remote_core.fetch_outbound_actions()
    if not actions:
        return 0
    results = _execute_actions(platform_api, actions)
    _acknowledge_results(remote_core, results, logger, source="outbound")
    return len(actions)


def main() -> int:
    config = load_config()
    logging.basicConfig(level=getattr(logging, config.log_level.upper(), logging.INFO), format="%(asctime)s [%(levelname)s] %(message)s")
    logger = logging.getLogger("wechat-adapter")
    exit_code = 0
    try:
        if not config.core_api.enabled():
            raise RuntimeError("WeChat adapter now requires core_api.endpoint and core_api.token")
        remote_core = WeChatCoreApiClient(
            endpoint=config.core_api.endpoint,
            token=config.core_api.token,
            request_timeout_seconds=config.core_api.request_timeout_seconds,
        )
        platform_api = WeChatPlatformAPI(
            listen_chats=config.listen_chats,
            language=config.language,
            runtime_dir=config.runtime_dir,
            config=config,
            logger=logger,
            identity_probe=remote_core.resolve_identity,
        )
        logger.info("WeChat adapter running in remote core mode: %s", config.core_api.endpoint)
        platform_api.ensure_listeners()
        config.listen_chats = list(platform_api.listen_chats)
        save_config(config)
        logger.info("WeChat self identity: nickname=%s wxid=%s", getattr(platform_api, "self_name", ""), getattr(platform_api, "self_wxid", ""))
        logger.info("WeChat adapter started. Listening chats: %s", ", ".join(platform_api.listen_chats))
        inbound_queue = deque()
        inbound_queue_capacity = max(int(getattr(config, "inbound_queue_capacity", 2000)), 1)
        inbound_batch_size = max(int(getattr(config, "inbound_batch_size", 200)), 1)
        while True:
            polled_messages = platform_api.poll_messages()
            if polled_messages:
                inbound_queue.extend(polled_messages)
                overflow = len(inbound_queue) - inbound_queue_capacity
                if overflow > 0:
                    for _ in range(overflow):
                        inbound_queue.popleft()
                    logger.warning("Inbound queue overflowed. Dropped oldest messages: %s", overflow)

            processed = 0
            while inbound_queue and processed < inbound_batch_size:
                message = inbound_queue.popleft()
                try:
                    actions = remote_core.send_envelope(message)
                except Exception:
                    inbound_queue.appendleft(message)
                    logger.warning("Failed to send message to remote core. Will retry next tick.", exc_info=True)
                    break
                results = _execute_actions(platform_api, actions)
                _acknowledge_results(remote_core, results, logger, source="reply")
                processed += 1
            _flush_outbound_actions(platform_api, remote_core, logger)
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

