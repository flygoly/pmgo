"""Shared SQLite helpers for project-core stores."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


def now_utc() -> str:
  return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def connect(path: Path) -> sqlite3.Connection:
  path.parent.mkdir(parents=True, exist_ok=True)
  conn = sqlite3.connect(path)
  conn.row_factory = sqlite3.Row
  conn.execute("PRAGMA foreign_keys = ON")
  return conn


def audit(
  conn: sqlite3.Connection,
  *,
  project_id: Optional[str],
  action: str,
  target_type: str,
  target_id: Optional[str],
  payload: Optional[dict[str, Any]],
) -> None:
  conn.execute(
    """
    INSERT INTO audit_logs (id, project_id, actor, action, target_type, target_id, source, payload, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
    (
      str(uuid.uuid4()),
      project_id,
      "project-core",
      action,
      target_type,
      target_id,
      "project-core",
      json.dumps(payload) if payload is not None else None,
      now_utc(),
    ),
  )


def row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
  return {key: row[key] for key in row.keys()}


# Private aliases keep the moved class implementations byte-for-byte compatible.
_now = now_utc
_connect = connect
_audit = audit
