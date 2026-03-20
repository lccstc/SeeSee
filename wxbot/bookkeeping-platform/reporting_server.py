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
    args = parser.parse_args()

    app = create_app(args.db, sync_token=args.sync_token or None)
    with make_server(args.host, args.port, app) as server:
        print(f"Reporting center running at http://{args.host}:{args.port}")
        server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
