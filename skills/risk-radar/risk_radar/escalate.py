"""Auto-create risks for blocked tasks stale beyond 24 hours."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from . import scan as scanmod

TASK_EVIDENCE_PREFIX = "pmgo_task_id:"


def task_evidence_marker(task_id: str) -> str:
  return f"{TASK_EVIDENCE_PREFIX}{task_id}"


def escalate_stale_blockers(
  project_id: str,
  risk_store: Any,
  *,
  now: datetime | None = None,
) -> dict[str, Any]:
  """Create open risks for stale blocked tasks that lack a linked risk row."""
  now = now or datetime.now(timezone.utc)
  scan = scanmod.scan_project(project_id, now=now)
  created: list[dict[str, Any]] = []
  skipped: list[dict[str, str]] = []

  for task in scan.get("tasks_blocked_stale_24h", []):
    tid = str(task["id"])
    marker = task_evidence_marker(tid)
    if risk_store.has_risk_for_task_marker(project_id, marker):
      skipped.append({"task_id": tid, "reason": "risk_exists"})
      continue
    title = f"Stale blocker: {task['title']}"
    reason = task.get("blocked_reason")
    mitigation = str(reason) if reason else None
    row = risk_store.create_risk(
      project_id,
      title=title,
      severity="high",
      status="open",
      evidence=marker,
      mitigation_plan=mitigation,
    )
    created.append(row)

  return {
    "created_count": len(created),
    "skipped_count": len(skipped),
    "created": created,
    "skipped": skipped,
  }
