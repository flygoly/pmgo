"""Shared helpers for pmgo unit tests."""

from __future__ import annotations

import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def init_test_db(path: Path) -> None:
  schema = ROOT / "memory" / "schema.sql"
  path.parent.mkdir(parents=True, exist_ok=True)
  with sqlite3.connect(path) as conn:
    conn.executescript(schema.read_text(encoding="utf-8"))
    conn.commit()
