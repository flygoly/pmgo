"""Shared helpers for pmgo Python skills (DB path, locale JSON)."""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path


def repo_root() -> Path:
  return Path(__file__).resolve().parent.parent


def db_path() -> Path:
  override = os.environ.get("PMGO_MEMORY_DB")
  if override:
    return Path(override).expanduser().resolve()
  return repo_root() / "memory" / "pmgo.db"


def connect_db(path: Path) -> sqlite3.Connection:
  path.parent.mkdir(parents=True, exist_ok=True)
  conn = sqlite3.connect(path)
  conn.row_factory = sqlite3.Row
  conn.execute("PRAGMA foreign_keys = ON")
  return conn


def load_strings(locale: str) -> dict[str, str]:
  root = repo_root()
  p = root / "locales" / f"{locale}.json"
  with open(p, encoding="utf-8") as f:
    return json.load(f)
