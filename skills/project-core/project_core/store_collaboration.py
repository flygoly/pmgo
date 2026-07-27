"""Domain-specific project-core stores."""

from __future__ import annotations

import sqlite3
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from .store_base import _audit, _connect, _now, row_to_dict

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


