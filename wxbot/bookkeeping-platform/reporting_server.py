from __future__ import annotations

import argparse
import os
from socketserver import ThreadingMixIn
from pathlib import Path
from wsgiref.handlers import SimpleHandler
from wsgiref.simple_server import ServerHandler, WSGIRequestHandler, WSGIServer, make_server

from bookkeeping_core.database import require_postgres_dsn
from bookkeeping_web.app import create_app


class _ReportingServerHandler(ServerHandler):
    def close(self):
        try:
            if not self._should_skip_access_log():
                self.request_handler.log_request(self.status.split(" ", 1)[0], self.bytes_sent)
        finally:
            SimpleHandler.close(self)

    def _should_skip_access_log(self) -> bool:
        if self.environ is None or self.headers is None or self.status is None:
            return False
        return (
            str(self.environ.get("PATH_INFO") or "") == "/api/core/actions"
            and str(self.status).startswith("200")
            and str(self.headers.get("X-Outbound-Action-Count") or "") == "0"
        )


class _ReportingRequestHandler(WSGIRequestHandler):
    def handle(self):
        self.raw_requestline = self.rfile.readline(65537)
        if len(self.raw_requestline) > 65536:
            self.requestline = ""
            self.request_version = ""
            self.command = ""
            self.send_error(414)
            return

        if not self.parse_request():
            return

        handler = _ReportingServerHandler(
            self.rfile,
            self.wfile,
            self.get_stderr(),
            self.get_environ(),
            multithread=True,
        )
        handler.request_handler = self
        handler.run(self.server.get_app())


class _ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
    daemon_threads = True


def main() -> int:
    parser = argparse.ArgumentParser(description="启动总账中心 Web 页面")
    parser.add_argument(
        "--db",
        default=os.environ.get("BOOKKEEPING_DB_DSN", ""),
        help="正式总账 PostgreSQL DSN，可用 BOOKKEEPING_DB_DSN 提供默认值",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--core-token", default=os.environ.get("BOOKKEEPING_CORE_TOKEN", ""))
    parser.add_argument("--master-user", action="append", dest="master_users", default=None)
    args = parser.parse_args()
    db_target = _resolve_db_target(args.db)

    app = create_app(
        db_target,
        core_token=args.core_token or None,
        runtime_master_users=_parse_master_users(
            os.environ.get("BOOKKEEPING_MASTER_USERS", ""),
            args.master_users,
        ),
    )
    with make_server(
        args.host,
        args.port,
        app,
        server_class=_ThreadingWSGIServer,
        handler_class=_ReportingRequestHandler,
    ) as server:
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


def _resolve_db_target(raw_db_target: str | Path) -> str:
    return require_postgres_dsn(raw_db_target, context="Core runtime database")


if __name__ == "__main__":
    raise SystemExit(main())
