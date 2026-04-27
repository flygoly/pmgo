"""Scan `risks` and `tasks` tables for blocker/risk visibility."""

from __future__ import annotations

from typing import Any

import pmgo_common  # type: ignore


def _row_dict(row: Any) -> dict[str, Any]:
  return {k: row[k] for k in row.keys()}


def scan_project(project_id: str) -> dict[str, Any]:
  """Return open/watching risks and blocked tasks for one project."""
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

  return {
    "project": {
      "id": str(proj["id"]),
      "name": str(proj["name"]),
      "slug": str(proj["slug"]),
    },
    "risks_open": [_row_dict(r) for r in risk_rows],
    "tasks_blocked": [_row_dict(r) for r in blocked_rows],
    "summary": {
      "risk_count": len(risk_rows),
      "blocked_task_count": len(blocked_rows),
      "risks_by_severity": by_sev,
    },
  }
