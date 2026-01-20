#!/usr/bin/env python3
import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent.parent / "data" / "finance.db"


def main() -> int:
    if not DB_PATH.exists():
        print(f"Database not found: {DB_PATH}")
        return 1

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    try:
        row = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='accounts'"
        ).fetchone()
        if not row:
            print("accounts table not found")
            return 1

        if "mortgage" in row["sql"]:
            print("accounts table already allows mortgage")
            return 0

        conn.execute("PRAGMA foreign_keys=OFF")
        conn.execute("BEGIN")
        conn.execute(
            """
            CREATE TABLE accounts_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL,
                account_type VARCHAR(20) NOT NULL CHECK (
                    account_type IN ('checking', 'savings', 'credit_card', 'investment', 'cash', 'mortgage')
                ),
                institution VARCHAR(100),
                last_four VARCHAR(4),
                current_balance REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        conn.execute(
            """
            INSERT INTO accounts_new (
                id, name, account_type, institution, last_four, current_balance, created_at, updated_at
            )
            SELECT
                id, name, account_type, institution, last_four, current_balance, created_at, updated_at
            FROM accounts;
            """
        )
        conn.execute("DROP TABLE accounts")
        conn.execute("ALTER TABLE accounts_new RENAME TO accounts")
        conn.execute("COMMIT")
        print("Updated accounts table to allow mortgage")
        return 0
    except Exception as exc:
        conn.execute("ROLLBACK")
        print(f"Migration failed: {exc}")
        return 1
    finally:
        conn.execute("PRAGMA foreign_keys=ON")
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
