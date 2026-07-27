"""Domain-specific project-core stores."""

from __future__ import annotations

import sqlite3
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from .store_base import _audit, _connect, _now, row_to_dict

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


