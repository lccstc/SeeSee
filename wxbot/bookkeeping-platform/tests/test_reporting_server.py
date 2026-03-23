from __future__ import annotations

import unittest
from pathlib import Path

import reporting_server


class ReportingServerTests(unittest.TestCase):
    def test_resolve_db_target_requires_postgres_dsn(self) -> None:
        with self.assertRaisesRegex(ValueError, "PostgreSQL DSN"):
            reporting_server._resolve_db_target("")

    def test_resolve_db_target_accepts_postgres_dsn(self) -> None:
        target = reporting_server._resolve_db_target("postgresql://bookkeeping:test@localhost:5432/bookkeeping")
        self.assertEqual(target, "postgresql://bookkeeping:test@localhost:5432/bookkeeping")

    def test_runtime_token_naming_uses_core(self) -> None:
        source = Path(reporting_server.__file__).read_text(encoding="utf-8")
        self.assertIn("--core-token", source)
        self.assertIn("BOOKKEEPING_CORE_TOKEN", source)


if __name__ == "__main__":
    unittest.main()
