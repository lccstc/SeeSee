from __future__ import annotations

import os
import tempfile
import unittest
import uuid
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


DEFAULT_TEST_DSN_ENV = "BOOKKEEPING_TEST_DSN"


class PostgresTestCase(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.tempdir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.tempdir.name)
        self._base_dsn = str(os.environ.get(DEFAULT_TEST_DSN_ENV, "")).strip()
        if not self._base_dsn:
            raise RuntimeError(f"{DEFAULT_TEST_DSN_ENV} is required for PostgreSQL integration tests")
        self._schema_dsns: dict[str, str] = {}

    def tearDown(self) -> None:
        self._drop_created_schemas()
        self.tempdir.cleanup()
        super().tearDown()

    def make_dsn(self, name: str = "bookkeeping") -> str:
        existing = self._schema_dsns.get(name)
        if existing is not None:
            return existing

        schema_name = self._schema_name(name)
        self._create_schema(schema_name)
        self._apply_schema(schema_name)
        dsn = self._dsn_with_search_path(schema_name)
        self._schema_dsns[name] = dsn
        return dsn

    def make_db(self, name: str = "bookkeeping"):
        from bookkeeping_core.database import BookkeepingDB

        return BookkeepingDB(self.make_dsn(name))

    def _schema_name(self, name: str) -> str:
        normalized = "".join(ch if ch.isalnum() else "_" for ch in name.lower())
        return f"bk_test_{normalized}_{uuid.uuid4().hex[:12]}"

    def _create_schema(self, schema_name: str) -> None:
        import psycopg

        with psycopg.connect(self._base_dsn, autocommit=True) as conn:
            with conn.cursor() as cursor:
                cursor.execute(f'CREATE SCHEMA "{schema_name}"')

    def _apply_schema(self, schema_name: str) -> None:
        import psycopg

        schema_path = Path(__file__).resolve().parents[2] / "sql" / "postgres_schema.sql"
        statements = [item.strip() for item in schema_path.read_text(encoding="utf-8-sig").split(";") if item.strip()]

        with psycopg.connect(self._dsn_with_search_path(schema_name), autocommit=True) as conn:
            with conn.cursor() as cursor:
                for statement in statements:
                    cursor.execute(statement)
                cursor.execute(
                    """
                    INSERT INTO settings (key, value, updated_at)
                    VALUES ('ngn_rate', '', CURRENT_TIMESTAMP)
                    ON CONFLICT(key) DO NOTHING
                    """
                )

    def _drop_created_schemas(self) -> None:
        if not self._schema_dsns:
            return

        import psycopg

        with psycopg.connect(self._base_dsn, autocommit=True) as conn:
            with conn.cursor() as cursor:
                for dsn in self._schema_dsns.values():
                    schema_name = self._extract_search_path_schema(dsn)
                    if schema_name:
                        cursor.execute(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE')

    def _dsn_with_search_path(self, schema_name: str) -> str:
        parts = urlsplit(self._base_dsn)
        query_items = parse_qsl(parts.query, keep_blank_values=True)
        next_items: list[tuple[str, str]] = []
        injected = False
        for key, value in query_items:
            if key == "options":
                merged = f"{value} -csearch_path={schema_name}".strip()
                next_items.append((key, merged))
                injected = True
            else:
                next_items.append((key, value))
        if not injected:
            next_items.append(("options", f"-csearch_path={schema_name}"))
        return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(next_items), parts.fragment))

    @staticmethod
    def _extract_search_path_schema(dsn: str) -> str:
        for key, value in parse_qsl(urlsplit(dsn).query, keep_blank_values=True):
            if key != "options":
                continue
            marker = "-csearch_path="
            if marker not in value:
                continue
            return value.split(marker, 1)[1].split(" ", 1)[0].strip()
        return ""
