"""MCP tools for this domain."""

from __future__ import annotations

import sqlite3

from .context import (
  gate,
  issue_public as _issue_public,
  json_text as _j,
  mcp,
  resolve_project_id as _resolve_project_id,
  slugify as _slugify,
)

# --- risk radar (SQLite risks + blocked tasks) ---


@mcp.tool()
def pmgo_risk_scan(
  project_id: str = "",
  auto_escalate: bool = False,
  confirmed: bool = False,
) -> str:
  """List risks and blocked tasks. Set auto_escalate=true (+ confirmed) to create risks for blockers >24h."""
  err = gate("pmgo.risk.scan", confirmed=False)
  if err:
    return err
  from risk_radar import scan as scanmod

  pid = _resolve_project_id(project_id)
  if not pid:
    return "project_id is required (or set PMGO_DEFAULT_PROJECT_ID)."
  try:
    result = scanmod.scan_project(pid)
  except KeyError as e:
    return str(e)
  if auto_escalate:
    werr = gate("project_core.risk.write", confirmed=confirmed)
    if werr:
      return werr
    from project_core.store import default_risk_store
    from risk_radar.escalate import escalate_stale_blockers

    result["escalation"] = escalate_stale_blockers(pid, default_risk_store())
  return _j(result)


@mcp.tool()
def pmgo_risk_list(project_id: str, status: str = "") -> str:
  """List risks for a project. Optional status: open, watching, mitigated, closed."""
  err = gate("project_core.risk.read", confirmed=False)
  if err:
    return err
  from project_core.store import default_risk_store

  pid = project_id.strip() or (_resolve_project_id("") or "")
  if not pid:
    return "project_id is required (or set PMGO_DEFAULT_PROJECT_ID)."
  st = status.strip() or None
  return _j(default_risk_store().list_risks(pid, status=st))


@mcp.tool()
def pmgo_risk_create(
  project_id: str,
  title: str,
  confirmed: bool = False,
  severity: str = "medium",
  risk_status: str = "open",
  owner: str = "",
  evidence: str = "",
  mitigation_plan: str = "",
) -> str:
  """Create a risk (requires confirmed=true for writes)."""
  err = gate("project_core.risk.write", confirmed=confirmed)
  if err:
    return err
  from project_core.store import default_risk_store

  pid = project_id.strip() or (_resolve_project_id("") or "")
  if not pid:
    return "project_id is required (or set PMGO_DEFAULT_PROJECT_ID)."
  return _j(
    default_risk_store().create_risk(
      pid,
      title=title,
      severity=severity,
      status=risk_status,
      owner=owner or None,
      evidence=evidence or None,
      mitigation_plan=mitigation_plan or None,
    )
  )


@mcp.tool()
def pmgo_risk_update(
  risk_id: str,
  confirmed: bool = False,
  title: str = "",
  severity: str = "",
  risk_status: str = "",
  owner: str = "",
  evidence: str = "",
  mitigation_plan: str = "",
) -> str:
  """Update a risk (requires confirmed=true for writes)."""
  err = gate("project_core.risk.write", confirmed=confirmed)
  if err:
    return err
  from project_core.store import default_risk_store

  kwargs: dict[str, object] = {}
  if title.strip():
    kwargs["title"] = title
  if severity.strip():
    kwargs["severity"] = severity
  if risk_status.strip():
    kwargs["status"] = risk_status
  if owner.strip():
    kwargs["owner"] = owner
  if evidence.strip():
    kwargs["evidence"] = evidence
  if mitigation_plan.strip():
    kwargs["mitigation_plan"] = mitigation_plan
  try:
    return _j(default_risk_store().update_risk(risk_id, **kwargs))
  except KeyError as e:
    return str(e)


@mcp.tool()
def pmgo_decision_list(project_id: str, status: str = "") -> str:
  """List decisions (ADR) for a project."""
  err = gate("project_core.decision.read", confirmed=False)
  if err:
    return err
  from project_core.store import default_decision_store

  pid = project_id.strip() or (_resolve_project_id("") or "")
  if not pid:
    return "project_id is required (or set PMGO_DEFAULT_PROJECT_ID)."
  st = status.strip() or None
  return _j(default_decision_store().list_decisions(pid, status=st))


@mcp.tool()
def pmgo_decision_create(
  project_id: str,
  title: str,
  confirmed: bool = False,
  decision_status: str = "proposed",
  rationale: str = "",
  alternatives: str = "",
  evidence: str = "",
  decided_by: str = "",
  decided_at: str = "",
) -> str:
  """Create a decision record (requires confirmed=true for writes)."""
  err = gate("project_core.decision.write", confirmed=confirmed)
  if err:
    return err
  from project_core.store import default_decision_store

  pid = project_id.strip() or (_resolve_project_id("") or "")
  if not pid:
    return "project_id is required (or set PMGO_DEFAULT_PROJECT_ID)."
  return _j(
    default_decision_store().create_decision(
      pid,
      title=title,
      status=decision_status,
      rationale=rationale or None,
      alternatives=alternatives or None,
      evidence=evidence or None,
      decided_by=decided_by or None,
      decided_at=decided_at or None,
    )
  )


@mcp.tool()
def pmgo_decision_update(
  decision_id: str,
  confirmed: bool = False,
  title: str = "",
  decision_status: str = "",
  rationale: str = "",
  alternatives: str = "",
  evidence: str = "",
  decided_by: str = "",
  decided_at: str = "",
) -> str:
  """Update a decision (requires confirmed=true for writes)."""
  err = gate("project_core.decision.write", confirmed=confirmed)
  if err:
    return err
  from project_core.store import default_decision_store

  kwargs: dict[str, object] = {}
  if title.strip():
    kwargs["title"] = title
  if decision_status.strip():
    kwargs["status"] = decision_status
  if rationale.strip():
    kwargs["rationale"] = rationale
  if alternatives.strip():
    kwargs["alternatives"] = alternatives
  if evidence.strip():
    kwargs["evidence"] = evidence
  if decided_by.strip():
    kwargs["decided_by"] = decided_by
  if decided_at.strip():
    kwargs["decided_at"] = decided_at
  try:
    return _j(default_decision_store().update_decision(decision_id, **kwargs))
  except KeyError as e:
    return str(e)


