from __future__ import annotations

import argparse
from pathlib import Path

from bookkeeping_core.database import BookkeepingDB
from bookkeeping_core.importers import import_whatsapp_legacy_db


def main() -> int:
    parser = argparse.ArgumentParser(description="导入旧 WhatsApp 账单库到统一总库")
    parser.add_argument("legacy_db", help="旧 WhatsApp bookkeeping.db 路径")
    parser.add_argument("--target-db", default=str(Path(__file__).resolve().parent / "data" / "bookkeeping.db"))
    args = parser.parse_args()

    db = BookkeepingDB(args.target_db)
    try:
        result = import_whatsapp_legacy_db(args.legacy_db, db)
    finally:
        db.close()

    print("Import complete")
    print(f"Groups: {result['groups']}")
    print(f"Transactions: {result['transactions']}")
    print(f"Settlements: {result['settlements']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
