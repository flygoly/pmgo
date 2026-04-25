"""SQLite access for projects and tasks."""

from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .config import db_path


def _now() -> str:
  return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _connect(path: Path) -> sqlite3.Connection:
  path.parent.mkdir(parents=True, exist_ok=True)
  conn = sqlite3.connect(path)
  conn.row_factory = sqlite3.Row
  conn.execute("PRAGMA foreign_keys = ON")
  return conn


def _audit(
  conn: sqlite3.Connection,
  *,
  project_id: Optional[str],
  action: str,
  target_type: str,
  target_id: Optional[str],
  payload: Optional[dict[str, Any]],
) -> None:
  aid = str(uuid.uuid4())
  conn.execute(
    """
    INSERT INTO audit_logs (id, project_id, actor, action, target_type, target_id, source, payload, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
    (
      aid,
      project_id,
      "project-core",
      action,
      target_type,
      target_id,
      "project-core",
      json.dumps(payload) if payload is not None else None,
      _now(),
    ),
  )


def row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
  return {k: row[k] for k in row.keys()}


@dataclass
class ProjectStore:
  db_file: Path

  def connect(self) -> sqlite3.Connection:
    return _connect(self.db_file)

  def list_projects(self) -> list[dict[str, Any]]:
    with self.connect() as conn:
      rows = conn.execute(
        "SELECT * FROM projects ORDER BY updated_at DESC"
      ).fetchall()
    return [row_to_dict(r) for r in rows]

  def create_project(
    self,
    *,
    name: str,
    slug: str,
    description: Optional[str] = None,
    owner: Optional[str] = None,
  ) -> dict[str, Any]:
    pid = str(uuid.uuid4())
    ts = _now()
    with self.connect() as conn:
      conn.execute(
        """
        INSERT INTO projects (id, slug, name, description, status, owner, created_at, updated_at)
        VALUES (?, ?, ?, ?, 'active', ?, ?, ?)
        """,
        (pid, slug, name, description, owner, ts, ts),
      )
      _audit(
        conn,
        project_id=pid,
        action="project.create",
        target_type="project",
        target_id=pid,
        payload={"name": name, "slug": slug},
      )
      conn.commit()
      row = conn.execute("SELECT * FROM projects WHERE id = ?", (pid,)).fetchone()
    assert row is not None
    return row_to_dict(row)


@dataclass
class TaskStore:
  db_file: Path

  def connect(self) -> sqlite3.Connection:
    return _connect(self.db_file)

  def list_tasks(
    self,
    project_id: str,
    *,
    status: Optional[str] = None,
  ) -> list[dict[str, Any]]:
    q = "SELECT * FROM tasks WHERE project_id = ?"
    args: list[Any] = [project_id]
    if status is not None:
      q += " AND status = ?"
      args.append(status)
    q += " ORDER BY due_at IS NULL, due_at, created_at"
    with self.connect() as conn:
      rows = conn.execute(q, args).fetchall()
    return [row_to_dict(r) for r in rows]

  def create_task(
    self,
    project_id: str,
    *,
    title: str,
    detail: Optional[str] = None,
    status: str = "todo",
    priority: str = "medium",
    assignee: Optional[str] = None,
    due_at: Optional[str] = None,
    milestone_id: Optional[str] = None,
    external_id: Optional[str] = None,
    source: Optional[str] = None,
  ) -> dict[str, Any]:
    tid = str(uuid.uuid4())
    ts = _now()
    with self.connect() as conn:
      conn.execute(
        """
        INSERT INTO tasks (
          id, project_id, milestone_id, title, detail, status, priority,
          assignee, due_at, source, external_id, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
          tid,
          project_id,
          milestone_id,
          title,
          detail,
          status,
          priority,
          assignee,
          due_at,
          source,
          external_id,
          ts,
          ts,
        ),
      )
      _audit(
        conn,
        project_id=project_id,
        action="task.create",
        target_type="task",
        target_id=tid,
        payload={"title": title, "status": status},
      )
      conn.commit()
      row = conn.execute("SELECT * FROM tasks WHERE id = ?", (tid,)).fetchone()
    assert row is not None
    return row_to_dict(row)

  def update_task(
    self,
    task_id: str,
    *,
    title: Optional[str] = None,
    detail: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assignee: Optional[str] = None,
    due_at: Optional[str] = None,
    blocked_reason: Optional[str] = None,
    milestone_id: Optional[str] = None,
  ) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    if title is not None:
      fields["title"] = title
    if detail is not None:
      fields["detail"] = detail
    if status is not None:
      fields["status"] = status
    if priority is not None:
      fields["priority"] = priority
    if assignee is not None:
      fields["assignee"] = assignee
    if due_at is not None:
      fields["due_at"] = due_at
    if blocked_reason is not None:
      fields["blocked_reason"] = blocked_reason
    if milestone_id is not None:
      fields["milestone_id"] = milestone_id
    if not fields:
      with self.connect() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
      if row is None:
        raise KeyError(f"Unknown task id: {task_id}")
      return row_to_dict(row)

    ts = _now()
    fields["updated_at"] = ts
    cols = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [task_id]
    with self.connect() as conn:
      cur = conn.execute(f"UPDATE tasks SET {cols} WHERE id = ?", values)
      if cur.rowcount == 0:
        raise KeyError(f"Unknown task id: {task_id}")
      project_id = conn.execute(
        "SELECT project_id FROM tasks WHERE id = ?", (task_id,)
      ).fetchone()
      pid = project_id[0] if project_id else None
      _audit(
        conn,
        project_id=pid,
        action="task.update",
        target_type="task",
        target_id=task_id,
        payload=fields,
      )
      conn.commit()
      row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    assert row is not None
    return row_to_dict(row)


def default_project_store() -> ProjectStore:
  return ProjectStore(db_path())


def default_task_store() -> TaskStore:
  return TaskStore(db_path())
