from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = BASE_DIR / "config.wechat.json"


@dataclass(slots=True)
class CoreApiConfig:
    endpoint: str = ""
    token: str = ""
    request_timeout_seconds: float = 5.0

    def enabled(self) -> bool:
        return bool(self.endpoint.strip() and self.token.strip())


@dataclass(slots=True)
class WeChatConfig:
    listen_chats: list[str]
    master_users: list[str]
    poll_interval_seconds: float
    log_level: str
    language: str
    db_path: str
    export_dir: str
    runtime_dir: str
    core_api: CoreApiConfig = field(default_factory=CoreApiConfig)


def _clean_chat_names(items) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for item in items or []:
        if item is None:
            continue
        name = str(item).strip()
        if not name:
            continue
        if "\n" in name or "\r" in name:
            continue
        if len(name) > 80:
            continue
        if name in seen:
            continue
        seen.add(name)
        cleaned.append(name)
    return cleaned


def load_config() -> WeChatConfig:
    defaults = {
        "listen_chats": ["文件传输助手"],
        "master_users": [],
        "poll_interval_seconds": 1.0,
        "log_level": "INFO",
        "language": "cn",
        "db_path": str(BASE_DIR / "data" / "bookkeeping.db"),
        "export_dir": str(BASE_DIR / "exports"),
        "runtime_dir": str(BASE_DIR / "runtime"),
        "core_api": {
            "endpoint": "",
            "token": "",
            "request_timeout_seconds": 5.0,
        },
    }
    if CONFIG_PATH.exists():
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8-sig"))
        defaults.update(data)
    defaults["listen_chats"] = _clean_chat_names(defaults.get("listen_chats")) or ["文件传输助手"]
    defaults["master_users"] = [str(item).strip() for item in defaults.get("master_users", []) if str(item).strip()]
    core_api_raw = defaults.get("core_api") or {}
    defaults["core_api"] = CoreApiConfig(
        endpoint=str(core_api_raw.get("endpoint") or "").strip(),
        token=str(core_api_raw.get("token") or "").strip(),
        request_timeout_seconds=float(core_api_raw.get("request_timeout_seconds") or 5.0),
    )
    if not CONFIG_PATH.exists():
        serializable_defaults = dict(defaults)
        serializable_defaults["core_api"] = asdict(defaults["core_api"])
        CONFIG_PATH.write_text(json.dumps(serializable_defaults, ensure_ascii=False, indent=2), encoding="utf-8")
    return WeChatConfig(**defaults)


def save_config(config: WeChatConfig) -> None:
    data = asdict(config)
    data["listen_chats"] = _clean_chat_names(data.get("listen_chats"))
    CONFIG_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
