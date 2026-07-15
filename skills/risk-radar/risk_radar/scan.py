"""Scan `risks` and `tasks` tables for blocker/risk visibility."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import pmgo_common  # type: ignore

_parse_ts = pmgo_common.parse_ts


def _row_dict(row: Any) -> dict[str, Any]:
  return {k: row[k] for k in row.keys()}


def scan_project(project_id: str, *, now: datetime | None = None) -> dict[str, Any]:
  """Return open/watching risks, blocked tasks, and stale blockers (>24h)."""
  now = now or datetime.now(timezone.utc)
  stale_cutoff = now - timedelta(hours=24)
  conn = pmgo_common.connect_db(pmgo_common.db_path())
  try:
    proj = conn.execute(
      "SELECT id, name, slug FROM projects WHERE id = ?",
      (project_id,),
    ).fetchone()
    if proj is None:
      raise KeyError(f"Unknown project id: {project_id}")
    risk_rows = conn.execute(
      """
      SELECT * FROM risks
      WHERE project_id = ? AND status IN ('open', 'watching')
      ORDER BY
        CASE severity
          WHEN 'critical' THEN 0
          WHEN 'high' THEN 1
          WHEN 'medium' THEN 2
          ELSE 3
        END,
        created_at
      """,
      (project_id,),
    ).fetchall()
    blocked_rows = conn.execute(
      """
      SELECT * FROM tasks
      WHERE project_id = ? AND status = 'blocked'
      ORDER BY updated_at DESC
      """,
      (project_id,),
    ).fetchall()
  finally:
    conn.close()

  by_sev: dict[str, int] = {}
  for r in risk_rows:
    s = str(r["severity"])
    by_sev[s] = by_sev.get(s, 0) + 1

  blocked = [_row_dict(r) for r in blocked_rows]
  stale_blocked: list[dict[str, Any]] = []
  for t in blocked:
    ut = _parse_ts(t.get("updated_at"))
    if ut is not None and ut < stale_cutoff:
      stale_blocked.append(t)

  return {
    "project": {
      "id": str(proj["id"]),
      "name": str(proj["name"]),
      "slug": str(proj["slug"]),
    },
    "risks_open": [_row_dict(r) for r in risk_rows],
    "tasks_blocked": blocked,
    "tasks_blocked_stale_24h": stale_blocked,
    "summary": {
      "risk_count": len(risk_rows),
      "blocked_task_count": len(blocked_rows),
      "stale_blocked_count": len(stale_blocked),
      "risks_by_severity": by_sev,
    },
  }
