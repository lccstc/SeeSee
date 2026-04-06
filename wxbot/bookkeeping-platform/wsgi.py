from __future__ import annotations

import os

from bookkeeping_web.app import create_app


def _parse_master_users(value: str) -> list[str]:
    users: list[str] = []
    for item in (value or "").split(","):
        text = item.strip()
        if text and text not in users:
            users.append(text)
    return users


DB_DSN = os.environ.get("BOOKKEEPING_DB_DSN", "").strip()
if not DB_DSN:
    raise RuntimeError("BOOKKEEPING_DB_DSN is required")

CORE_TOKEN = os.environ.get("BOOKKEEPING_CORE_TOKEN", "").strip() or None
MASTER_USERS = _parse_master_users(os.environ.get("BOOKKEEPING_MASTER_USERS", ""))

app = create_app(
    DB_DSN,
    core_token=CORE_TOKEN,
    runtime_master_users=MASTER_USERS,
)
