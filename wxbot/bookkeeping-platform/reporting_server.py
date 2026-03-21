from __future__ import annotations

import argparse
import os
from pathlib import Path
from wsgiref.simple_server import make_server

from bookkeeping_web.app import create_app


def main() -> int:
    parser = argparse.ArgumentParser(description="启动总账中心 Web 页面")
    parser.add_argument("--db", default=str(Path(__file__).resolve().parent / "data" / "bookkeeping.db"))
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--sync-token", default=os.environ.get("BOOKKEEPING_SYNC_TOKEN", ""))
    parser.add_argument("--master-user", action="append", dest="master_users", default=None)
    args = parser.parse_args()

    app = create_app(
        args.db,
        sync_token=args.sync_token or None,
        runtime_master_users=_parse_master_users(
            os.environ.get("BOOKKEEPING_MASTER_USERS", ""),
            args.master_users,
        ),
    )
    with make_server(args.host, args.port, app) as server:
        print(f"Reporting center running at http://{args.host}:{args.port}")
        server.serve_forever()
    return 0


def _parse_master_users(env_value: str, cli_values: list[str] | None) -> list[str]:
    result: list[str] = []
    for item in str(env_value or "").split(","):
        text = item.strip()
        if text and text not in result:
            result.append(text)
    for item in cli_values or []:
        text = str(item).strip()
        if text and text not in result:
            result.append(text)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
