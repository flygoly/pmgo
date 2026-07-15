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

  def get_project_by_slug(self, slug: str) -> Optional[dict[str, Any]]:
    with self.connect() as conn:
      row = conn.execute("SELECT * FROM projects WHERE slug = ?", (slug,)).fetchone()
    return row_to_dict(row) if row is not None else None

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


@dataclass
class MilestoneStore:
  db_file: Path

  def connect(self) -> sqlite3.Connection:
    return _connect(self.db_file)

  def list_milestones(self, project_id: str) -> list[dict[str, Any]]:
    with self.connect() as conn:
      rows = conn.execute(
        """
        SELECT * FROM milestones
        WHERE project_id = ?
        ORDER BY due_at IS NULL, due_at, created_at
        """,
        (project_id,),
      ).fetchall()
    return [row_to_dict(r) for r in rows]

  def create_milestone(
    self,
    project_id: str,
    *,
    title: str,
    status: str = "todo",
    owner: Optional[str] = None,
    due_at: Optional[str] = None,
    external_id: Optional[str] = None,
  ) -> dict[str, Any]:
    mid = str(uuid.uuid4())
    ts = _now()
    with self.connect() as conn:
      conn.execute(
        """
        INSERT INTO milestones (
          id, project_id, title, status, owner, due_at, external_id, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (mid, project_id, title, status, owner, due_at, external_id, ts),
      )
      _audit(
        conn,
        project_id=project_id,
        action="milestone.create",
        target_type="milestone",
        target_id=mid,
        payload={"title": title, "status": status},
      )
      conn.commit()
      row = conn.execute("SELECT * FROM milestones WHERE id = ?", (mid,)).fetchone()
    assert row is not None
    return row_to_dict(row)

  def update_milestone(
    self,
    milestone_id: str,
    *,
    title: Optional[str] = None,
    status: Optional[str] = None,
    owner: Optional[str] = None,
    due_at: Optional[str] = None,
  ) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    if title is not None:
      fields["title"] = title
    if status is not None:
      fields["status"] = status
    if owner is not None:
      fields["owner"] = owner
    if due_at is not None:
      fields["due_at"] = due_at
    if not fields:
      with self.connect() as conn:
        row = conn.execute(
          "SELECT * FROM milestones WHERE id = ?", (milestone_id,)
        ).fetchone()
      if row is None:
        raise KeyError(f"Unknown milestone id: {milestone_id}")
      return row_to_dict(row)

    cols = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [milestone_id]
    with self.connect() as conn:
      cur = conn.execute(f"UPDATE milestones SET {cols} WHERE id = ?", values)
      if cur.rowcount == 0:
        raise KeyError(f"Unknown milestone id: {milestone_id}")
      project_id = conn.execute(
        "SELECT project_id FROM milestones WHERE id = ?", (milestone_id,)
      ).fetchone()
      pid = project_id[0] if project_id else None
      _audit(
        conn,
        project_id=pid,
        action="milestone.update",
        target_type="milestone",
        target_id=milestone_id,
        payload=fields,
      )
      conn.commit()
      row = conn.execute(
        "SELECT * FROM milestones WHERE id = ?", (milestone_id,)
      ).fetchone()
    assert row is not None
    return row_to_dict(row)


@dataclass
class RiskStore:
  db_file: Path

  def connect(self) -> sqlite3.Connection:
    return _connect(self.db_file)

  def list_risks(
    self,
    project_id: str,
    *,
    status: Optional[str] = None,
  ) -> list[dict[str, Any]]:
    q = "SELECT * FROM risks WHERE project_id = ?"
    args: list[Any] = [project_id]
    if status is not None:
      q += " AND status = ?"
      args.append(status)
    q += """
      ORDER BY
        CASE severity
          WHEN 'critical' THEN 0
          WHEN 'high' THEN 1
          WHEN 'medium' THEN 2
          ELSE 3
        END,
        created_at
    """
    with self.connect() as conn:
      rows = conn.execute(q, args).fetchall()
    return [row_to_dict(r) for r in rows]

  def has_risk_for_task_marker(self, project_id: str, marker: str) -> bool:
    with self.connect() as conn:
      row = conn.execute(
        """
        SELECT 1 FROM risks
        WHERE project_id = ? AND evidence LIKE ?
        LIMIT 1
        """,
        (project_id, f"%{marker}%"),
      ).fetchone()
    return row is not None

  def create_risk(
    self,
    project_id: str,
    *,
    title: str,
    severity: str = "medium",
    status: str = "open",
    owner: Optional[str] = None,
    evidence: Optional[str] = None,
    mitigation_plan: Optional[str] = None,
    probability: Optional[float] = None,
    impact: Optional[float] = None,
  ) -> dict[str, Any]:
    rid = str(uuid.uuid4())
    ts = _now()
    score: Optional[float] = None
    if probability is not None and impact is not None:
      score = probability * impact
    with self.connect() as conn:
      conn.execute(
        """
        INSERT INTO risks (
          id, project_id, title, severity, probability, impact, score,
          status, owner, evidence, mitigation_plan, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
          rid,
          project_id,
          title,
          severity,
          probability,
          impact,
          score,
          status,
          owner,
          evidence,
          mitigation_plan,
          ts,
          ts,
        ),
      )
      _audit(
        conn,
        project_id=project_id,
        action="risk.create",
        target_type="risk",
        target_id=rid,
        payload={"title": title, "severity": severity, "status": status},
      )
      conn.commit()
      row = conn.execute("SELECT * FROM risks WHERE id = ?", (rid,)).fetchone()
    assert row is not None
    return row_to_dict(row)

  def update_risk(
    self,
    risk_id: str,
    *,
    title: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    owner: Optional[str] = None,
    evidence: Optional[str] = None,
    mitigation_plan: Optional[str] = None,
    probability: Optional[float] = None,
    impact: Optional[float] = None,
  ) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    if title is not None:
      fields["title"] = title
    if severity is not None:
      fields["severity"] = severity
    if status is not None:
      fields["status"] = status
    if owner is not None:
      fields["owner"] = owner
    if evidence is not None:
      fields["evidence"] = evidence
    if mitigation_plan is not None:
      fields["mitigation_plan"] = mitigation_plan
    if probability is not None:
      fields["probability"] = probability
    if impact is not None:
      fields["impact"] = impact
    if probability is not None or impact is not None:
      with self.connect() as conn:
        row = conn.execute("SELECT probability, impact FROM risks WHERE id = ?", (risk_id,)).fetchone()
      if row is not None:
        p = probability if probability is not None else row["probability"]
        i = impact if impact is not None else row["impact"]
        if p is not None and i is not None:
          fields["score"] = float(p) * float(i)
    if not fields:
      with self.connect() as conn:
        row = conn.execute("SELECT * FROM risks WHERE id = ?", (risk_id,)).fetchone()
      if row is None:
        raise KeyError(f"Unknown risk id: {risk_id}")
      return row_to_dict(row)

    fields["updated_at"] = _now()
    cols = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [risk_id]
    with self.connect() as conn:
      cur = conn.execute(f"UPDATE risks SET {cols} WHERE id = ?", values)
      if cur.rowcount == 0:
        raise KeyError(f"Unknown risk id: {risk_id}")
      project_id = conn.execute(
        "SELECT project_id FROM risks WHERE id = ?", (risk_id,)
      ).fetchone()
      pid = project_id[0] if project_id else None
      _audit(
        conn,
        project_id=pid,
        action="risk.update",
        target_type="risk",
        target_id=risk_id,
        payload=fields,
      )
      conn.commit()
      row = conn.execute("SELECT * FROM risks WHERE id = ?", (risk_id,)).fetchone()
    assert row is not None
    return row_to_dict(row)


@dataclass
class DecisionStore:
  db_file: Path

  def connect(self) -> sqlite3.Connection:
    return _connect(self.db_file)

  def list_decisions(
    self,
    project_id: str,
    *,
    status: Optional[str] = None,
  ) -> list[dict[str, Any]]:
    q = "SELECT * FROM decisions WHERE project_id = ?"
    args: list[Any] = [project_id]
    if status is not None:
      q += " AND status = ?"
      args.append(status)
    q += " ORDER BY created_at DESC"
    with self.connect() as conn:
      rows = conn.execute(q, args).fetchall()
    return [row_to_dict(r) for r in rows]

  def create_decision(
    self,
    project_id: str,
    *,
    title: str,
    status: str = "proposed",
    rationale: Optional[str] = None,
    alternatives: Optional[str] = None,
    evidence: Optional[str] = None,
    decided_by: Optional[str] = None,
    decided_at: Optional[str] = None,
  ) -> dict[str, Any]:
    did = str(uuid.uuid4())
    ts = _now()
    with self.connect() as conn:
      conn.execute(
        """
        INSERT INTO decisions (
          id, project_id, title, status, rationale, alternatives,
          evidence, decided_by, decided_at, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
          did,
          project_id,
          title,
          status,
          rationale,
          alternatives,
          evidence,
          decided_by,
          decided_at,
          ts,
        ),
      )
      _audit(
        conn,
        project_id=project_id,
        action="decision.create",
        target_type="decision",
        target_id=did,
        payload={"title": title, "status": status},
      )
      conn.commit()
      row = conn.execute("SELECT * FROM decisions WHERE id = ?", (did,)).fetchone()
    assert row is not None
    return row_to_dict(row)

  def update_decision(
    self,
    decision_id: str,
    *,
    title: Optional[str] = None,
    status: Optional[str] = None,
    rationale: Optional[str] = None,
    alternatives: Optional[str] = None,
    evidence: Optional[str] = None,
    decided_by: Optional[str] = None,
    decided_at: Optional[str] = None,
  ) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    if title is not None:
      fields["title"] = title
    if status is not None:
      fields["status"] = status
    if rationale is not None:
      fields["rationale"] = rationale
    if alternatives is not None:
      fields["alternatives"] = alternatives
    if evidence is not None:
      fields["evidence"] = evidence
    if decided_by is not None:
      fields["decided_by"] = decided_by
    if decided_at is not None:
      fields["decided_at"] = decided_at
    if not fields:
      with self.connect() as conn:
        row = conn.execute(
          "SELECT * FROM decisions WHERE id = ?", (decision_id,)
        ).fetchone()
      if row is None:
        raise KeyError(f"Unknown decision id: {decision_id}")
      return row_to_dict(row)

    cols = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [decision_id]
    with self.connect() as conn:
      cur = conn.execute(f"UPDATE decisions SET {cols} WHERE id = ?", values)
      if cur.rowcount == 0:
        raise KeyError(f"Unknown decision id: {decision_id}")
      project_id = conn.execute(
        "SELECT project_id FROM decisions WHERE id = ?", (decision_id,)
      ).fetchone()
      pid = project_id[0] if project_id else None
      _audit(
        conn,
        project_id=pid,
        action="decision.update",
        target_type="decision",
        target_id=decision_id,
        payload=fields,
      )
      conn.commit()
      row = conn.execute(
        "SELECT * FROM decisions WHERE id = ?", (decision_id,)
      ).fetchone()
    assert row is not None
    return row_to_dict(row)


@dataclass
class PeopleStore:
  db_file: Path

  def connect(self) -> sqlite3.Connection:
    return _connect(self.db_file)

  def list_people(self) -> list[dict[str, Any]]:
    with self.connect() as conn:
      rows = conn.execute(
        "SELECT * FROM people ORDER BY created_at DESC"
      ).fetchall()
    return [row_to_dict(r) for r in rows]

  def create_person(
    self,
    *,
    name: str,
    role: Optional[str] = None,
    contact: Optional[str] = None,
  ) -> dict[str, Any]:
    pid = str(uuid.uuid4())
    ts = _now()
    with self.connect() as conn:
      conn.execute(
        """
        INSERT INTO people (id, name, role, contact, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (pid, name, role, contact, ts),
      )
      _audit(
        conn,
        project_id=None,
        action="person.create",
        target_type="person",
        target_id=pid,
        payload={"name": name, "role": role},
      )
      conn.commit()
      row = conn.execute("SELECT * FROM people WHERE id = ?", (pid,)).fetchone()
    assert row is not None
    return row_to_dict(row)

  def update_person(
    self,
    person_id: str,
    *,
    name: Optional[str] = None,
    role: Optional[str] = None,
    contact: Optional[str] = None,
  ) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    if name is not None:
      fields["name"] = name
    if role is not None:
      fields["role"] = role
    if contact is not None:
      fields["contact"] = contact
    if not fields:
      with self.connect() as conn:
        row = conn.execute("SELECT * FROM people WHERE id = ?", (person_id,)).fetchone()
      if row is None:
        raise KeyError(f"Unknown person id: {person_id}")
      return row_to_dict(row)

    cols = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [person_id]
    with self.connect() as conn:
      cur = conn.execute(f"UPDATE people SET {cols} WHERE id = ?", values)
      if cur.rowcount == 0:
        raise KeyError(f"Unknown person id: {person_id}")
      _audit(
        conn,
        project_id=None,
        action="person.update",
        target_type="person",
        target_id=person_id,
        payload=fields,
      )
      conn.commit()
      row = conn.execute("SELECT * FROM people WHERE id = ?", (person_id,)).fetchone()
    assert row is not None
    return row_to_dict(row)


@dataclass
class RetrospectiveStore:
  db_file: Path

  def connect(self) -> sqlite3.Connection:
    return _connect(self.db_file)

  def list_retrospectives(self, project_id: str) -> list[dict[str, Any]]:
    with self.connect() as conn:
      rows = conn.execute(
        """
        SELECT * FROM retrospectives
        WHERE project_id = ?
        ORDER BY created_at DESC
        """,
        (project_id,),
      ).fetchall()
    return [row_to_dict(r) for r in rows]

  def create_retrospective(
    self,
    project_id: str,
    *,
    period: str,
    summary: Optional[str] = None,
    action_items: Optional[str] = None,
  ) -> dict[str, Any]:
    rid = str(uuid.uuid4())
    ts = _now()
    with self.connect() as conn:
      conn.execute(
        """
        INSERT INTO retrospectives (
          id, project_id, period, summary, action_items, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (rid, project_id, period, summary, action_items, ts),
      )
      _audit(
        conn,
        project_id=project_id,
        action="retrospective.create",
        target_type="retrospective",
        target_id=rid,
        payload={"period": period},
      )
      conn.commit()
      row = conn.execute(
        "SELECT * FROM retrospectives WHERE id = ?", (rid,)
      ).fetchone()
    assert row is not None
    return row_to_dict(row)

  def update_retrospective(
    self,
    retrospective_id: str,
    *,
    period: Optional[str] = None,
    summary: Optional[str] = None,
    action_items: Optional[str] = None,
  ) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    if period is not None:
      fields["period"] = period
    if summary is not None:
      fields["summary"] = summary
    if action_items is not None:
      fields["action_items"] = action_items
    if not fields:
      with self.connect() as conn:
        row = conn.execute(
          "SELECT * FROM retrospectives WHERE id = ?",
          (retrospective_id,),
        ).fetchone()
      if row is None:
        raise KeyError(f"Unknown retrospective id: {retrospective_id}")
      return row_to_dict(row)

    cols = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [retrospective_id]
    with self.connect() as conn:
      cur = conn.execute(
        f"UPDATE retrospectives SET {cols} WHERE id = ?", values
      )
      if cur.rowcount == 0:
        raise KeyError(f"Unknown retrospective id: {retrospective_id}")
      project_id = conn.execute(
        "SELECT project_id FROM retrospectives WHERE id = ?",
        (retrospective_id,),
      ).fetchone()
      pid = project_id[0] if project_id else None
      _audit(
        conn,
        project_id=pid,
        action="retrospective.update",
        target_type="retrospective",
        target_id=retrospective_id,
        payload=fields,
      )
      conn.commit()
      row = conn.execute(
        "SELECT * FROM retrospectives WHERE id = ?",
        (retrospective_id,),
      ).fetchone()
    assert row is not None
    return row_to_dict(row)


def default_project_store() -> ProjectStore:
  return ProjectStore(db_path())


def default_task_store() -> TaskStore:
  return TaskStore(db_path())


def default_milestone_store() -> MilestoneStore:
  return MilestoneStore(db_path())


def default_risk_store() -> RiskStore:
  return RiskStore(db_path())


def default_decision_store() -> DecisionStore:
  return DecisionStore(db_path())


def default_people_store() -> PeopleStore:
  return PeopleStore(db_path())


def default_retrospective_store() -> RetrospectiveStore:
  return RetrospectiveStore(db_path())
