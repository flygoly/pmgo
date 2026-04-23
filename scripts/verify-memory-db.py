#!/usr/bin/env python3

import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DB_FILE = ROOT / "memory" / "pmgo.db"

REQUIRED_TABLES = {
  "projects",
  "milestones",
  "tasks",
  "people",
  "risks",
  "decisions",
  "retrospectives",
  "schema_migrations",
}


def main() -> None:
  if not DB_FILE.exists():
    raise FileNotFoundError(f"Database file missing: {DB_FILE}")

  with sqlite3.connect(DB_FILE) as conn:
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    existing = {row[0] for row in rows}

  missing = sorted(REQUIRED_TABLES - existing)
  if missing:
    raise RuntimeError(f"Missing required tables: {', '.join(missing)}")

  print("Memory database verification passed.")


if __name__ == "__main__":
  main()
