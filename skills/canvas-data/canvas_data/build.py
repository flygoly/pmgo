"""Gantt + burndown JSON for OpenClaw Live Canvas."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any

import pmgo_common  # type: ignore


def _parse_ts(raw: str | None) -> datetime | None:
  return pmgo_common.parse_ts(raw)


def _week_bounds_utc(anchor: datetime) -> tuple[datetime, datetime]:
  d = anchor.date()
  monday = d - timedelta(days=d.weekday())
  start = datetime.combine(monday, datetime.min.time(), tzinfo=timezone.utc)
  end = start + timedelta(days=7)
  return start, end


def build_gantt(project_id: str) -> dict[str, Any]:
  conn = pmgo_common.connect_db(pmgo_common.db_path())
  try:
    proj = conn.execute(
      "SELECT id, name, slug FROM projects WHERE id = ?",
      (project_id,),
    ).fetchone()
    if proj is None:
      raise KeyError(f"Unknown project id: {project_id}")
    milestones = conn.execute(
      """
      SELECT id, title, status, due_at, owner
      FROM milestones WHERE project_id = ?
      ORDER BY due_at IS NULL, due_at, created_at
      """,
      (project_id,),
    ).fetchall()
    tasks = conn.execute(
      """
      SELECT id, title, status, due_at, assignee, milestone_id, priority
      FROM tasks WHERE project_id = ?
      ORDER BY due_at IS NULL, due_at, created_at
      """,
      (project_id,),
    ).fetchall()
  finally:
    conn.close()

  return {
    "schema": "pmgo.canvas.gantt/v1",
    "project": {"id": proj["id"], "name": proj["name"], "slug": proj["slug"]},
    "milestones": [
      {
        "id": m["id"],
        "title": m["title"],
        "status": m["status"],
        "due_at": m["due_at"],
        "owner": m["owner"],
      }
      for m in milestones
    ],
    "tasks": [
      {
        "id": t["id"],
        "title": t["title"],
        "status": t["status"],
        "due_at": t["due_at"],
        "assignee": t["assignee"],
        "milestone_id": t["milestone_id"],
        "priority": t["priority"],
      }
      for t in tasks
    ],
  }


def build_burndown(project_id: str, *, now: datetime | None = None) -> dict[str, Any]:
  now = now or datetime.now(timezone.utc)
  week_start, week_end = _week_bounds_utc(now)
  conn = pmgo_common.connect_db(pmgo_common.db_path())
  try:
    proj = conn.execute(
      "SELECT id, name, slug FROM projects WHERE id = ?",
      (project_id,),
    ).fetchone()
    if proj is None:
      raise KeyError(f"Unknown project id: {project_id}")
    tasks = conn.execute(
      """
      SELECT id, title, status, created_at, updated_at
      FROM tasks WHERE project_id = ?
      """,
      (project_id,),
    ).fetchall()
  finally:
    conn.close()

  by_status = Counter(str(t["status"]) for t in tasks)
  remaining = by_status.get("todo", 0) + by_status.get("doing", 0) + by_status.get("blocked", 0)
  done_total = by_status.get("done", 0)
  done_this_week = 0
  for t in tasks:
    if str(t["status"]) != "done":
      continue
    ut = _parse_ts(t["updated_at"])
    if ut is not None and week_start <= ut < week_end:
      done_this_week += 1

  # Ideal burndown: linear from (remaining+done_this_week) at week start to 0 at week end.
  start_remaining = remaining + done_this_week
  points: list[dict[str, Any]] = []
  for day in range(8):
    day_dt = week_start + timedelta(days=day)
    if day == 7:
      ideal = 0
    else:
      ideal = round(start_remaining * (1 - day / 7), 2)
    # Actual: approximate remaining as of end of day using done timestamps.
    actual_done = 0
    for t in tasks:
      if str(t["status"]) != "done":
        continue
      ut = _parse_ts(t["updated_at"])
      if ut is not None and ut < day_dt + timedelta(days=1) and ut >= week_start:
        actual_done += 1
    # Also count tasks already done before week start as burned.
    pre_done = 0
    for t in tasks:
      if str(t["status"]) != "done":
        continue
      ut = _parse_ts(t["updated_at"])
      if ut is not None and ut < week_start:
        pre_done += 1
    total_scope = remaining + done_total
    actual_remaining = max(0, total_scope - pre_done - actual_done)
    points.append(
      {
        "date": day_dt.date().isoformat(),
        "ideal_remaining": ideal,
        "actual_remaining": actual_remaining if day_dt.date() <= now.date() else None,
      }
    )

  return {
    "schema": "pmgo.canvas.burndown/v1",
    "project": {"id": proj["id"], "name": proj["name"], "slug": proj["slug"]},
    "week_start": week_start.date().isoformat(),
    "week_end": (week_end - timedelta(seconds=1)).date().isoformat(),
    "generated_at": now.isoformat(),
    "summary": {
      "remaining": remaining,
      "done_total": done_total,
      "done_this_week": done_this_week,
      "by_status": dict(by_status),
    },
    "points": points,
  }


def build_snapshot(project_id: str, *, now: datetime | None = None) -> dict[str, Any]:
  return {
    "schema": "pmgo.canvas.snapshot/v1",
    "gantt": build_gantt(project_id),
    "burndown": build_burndown(project_id, now=now),
  }
