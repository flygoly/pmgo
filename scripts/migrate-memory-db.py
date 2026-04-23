#!/usr/bin/env python3

import re
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MEMORY_DIR = ROOT / "memory"
DB_FILE = MEMORY_DIR / "pmgo.db"
MIGRATIONS_DIR = MEMORY_DIR / "migrations"

MIGRATION_PATTERN = re.compile(r"^(\d+)_.*\.sql$")


def ensure_migration_table(conn: sqlite3.Connection) -> None:
  conn.execute(
    """
    CREATE TABLE IF NOT EXISTS schema_migrations (
      version TEXT PRIMARY KEY,
      applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """
  )
  conn.commit()


def list_migration_files() -> list[Path]:
  if not MIGRATIONS_DIR.exists():
    return []

  files: list[Path] = []
  for file_path in MIGRATIONS_DIR.iterdir():
    if not file_path.is_file():
      continue
    if MIGRATION_PATTERN.match(file_path.name):
      files.append(file_path)
  return sorted(files, key=lambda p: p.name)


def extract_version(file_path: Path) -> str:
  match = MIGRATION_PATTERN.match(file_path.name)
  if not match:
    raise ValueError(f"Invalid migration filename: {file_path.name}")
  return match.group(1)


def apply_migrations() -> None:
  MEMORY_DIR.mkdir(parents=True, exist_ok=True)

  with sqlite3.connect(DB_FILE) as conn:
    ensure_migration_table(conn)

    applied = {
      row[0]
      for row in conn.execute("SELECT version FROM schema_migrations").fetchall()
    }

    migration_files = list_migration_files()
    if not migration_files:
      print("No migration files found.")
      return

    applied_count = 0
    for migration_file in migration_files:
      version = extract_version(migration_file)
      if version in applied:
        continue

      sql = migration_file.read_text(encoding="utf-8")
      conn.executescript(sql)
      conn.execute(
        "INSERT OR IGNORE INTO schema_migrations(version) VALUES (?)",
        (version,),
      )
      conn.commit()
      applied_count += 1
      print(f"Applied migration {version}: {migration_file.name}")

    if applied_count == 0:
      print("No pending migrations.")
    else:
      print(f"Applied {applied_count} migration(s).")


if __name__ == "__main__":
  apply_migrations()
