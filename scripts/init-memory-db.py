#!/usr/bin/env python3

import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MEMORY_DIR = ROOT / "memory"
SCHEMA_FILE = MEMORY_DIR / "schema.sql"
DB_FILE = MEMORY_DIR / "pmgo.db"


def main() -> None:
  if not SCHEMA_FILE.exists():
    raise FileNotFoundError(f"Schema file missing: {SCHEMA_FILE}")

  MEMORY_DIR.mkdir(parents=True, exist_ok=True)
  schema_sql = SCHEMA_FILE.read_text(encoding="utf-8")

  with sqlite3.connect(DB_FILE) as conn:
    conn.executescript(schema_sql)
    conn.commit()

  print(f"Initialized memory database: {DB_FILE}")


if __name__ == "__main__":
  main()
