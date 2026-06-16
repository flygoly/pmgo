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


def first_project_id() -> str | None:
  conn = connect_db(db_path())
  try:
    row = conn.execute("SELECT id FROM projects ORDER BY created_at LIMIT 1").fetchone()
  finally:
    conn.close()
  if row is None:
    return None
  return str(row[0])


def default_project_id() -> str | None:
  override = os.environ.get("PMGO_DEFAULT_PROJECT_ID", "").strip()
  return override or None


def default_locale() -> str:
  loc = os.environ.get("PMGO_DEFAULT_LOCALE", "").strip()
  if loc in {"en", "zh-CN", "zh-TW"}:
    return loc
  return "en"


def resolve_project_id(
  *,
  explicit: str | None = None,
  from_first: bool = False,
) -> str | None:
  if explicit and str(explicit).strip():
    return str(explicit).strip()
  default = default_project_id()
  if default:
    return default
  if from_first:
    return first_project_id()
  return None
