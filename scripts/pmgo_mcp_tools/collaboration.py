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

@mcp.tool()
def pmgo_people_list() -> str:
  """List people in the roster (assignees / contacts)."""
  err = gate("project_core.people.read", confirmed=False)
  if err:
    return err
  from project_core.store import default_people_store

  return _j(default_people_store().list_people())


@mcp.tool()
def pmgo_people_create(
  name: str,
  confirmed: bool = False,
  role: str = "",
  contact: str = "",
) -> str:
  """Create a person in the roster (requires confirmed=true for writes)."""
  err = gate("project_core.people.write", confirmed=confirmed)
  if err:
    return err
  from project_core.store import default_people_store

  return _j(
    default_people_store().create_person(
      name=name,
      role=role or None,
      contact=contact or None,
    )
  )


@mcp.tool()
def pmgo_people_update(
  person_id: str,
  confirmed: bool = False,
  name: str = "",
  role: str = "",
  contact: str = "",
) -> str:
  """Update a person (requires confirmed=true for writes)."""
  err = gate("project_core.people.write", confirmed=confirmed)
  if err:
    return err
  from project_core.store import default_people_store

  kwargs: dict[str, object] = {}
  if name.strip():
    kwargs["name"] = name
  if role.strip():
    kwargs["role"] = role
  if contact.strip():
    kwargs["contact"] = contact
  try:
    return _j(default_people_store().update_person(person_id, **kwargs))
  except KeyError as e:
    return str(e)


@mcp.tool()
def pmgo_retrospective_list(project_id: str = "") -> str:
  """List retrospectives for a project."""
  err = gate("project_core.retrospective.read", confirmed=False)
  if err:
    return err
  from project_core.store import default_retrospective_store

  pid = project_id.strip() or (_resolve_project_id("") or "")
  if not pid:
    return "project_id is required (or set PMGO_DEFAULT_PROJECT_ID)."
  return _j(default_retrospective_store().list_retrospectives(pid))


@mcp.tool()
def pmgo_retrospective_create(
  project_id: str,
  period: str,
  confirmed: bool = False,
  summary: str = "",
  action_items: str = "",
) -> str:
  """Create a retrospective (requires confirmed=true for writes)."""
  err = gate("project_core.retrospective.write", confirmed=confirmed)
  if err:
    return err
  from project_core.store import default_retrospective_store

  pid = project_id.strip() or (_resolve_project_id("") or "")
  if not pid:
    return "project_id is required (or set PMGO_DEFAULT_PROJECT_ID)."
  return _j(
    default_retrospective_store().create_retrospective(
      pid,
      period=period,
      summary=summary or None,
      action_items=action_items or None,
    )
  )


@mcp.tool()
def pmgo_retrospective_update(
  retrospective_id: str,
  confirmed: bool = False,
  period: str = "",
  summary: str = "",
  action_items: str = "",
) -> str:
  """Update a retrospective (requires confirmed=true for writes)."""
  err = gate("project_core.retrospective.write", confirmed=confirmed)
  if err:
    return err
  from project_core.store import default_retrospective_store

  kwargs: dict[str, object] = {}
  if period.strip():
    kwargs["period"] = period
  if summary.strip():
    kwargs["summary"] = summary
  if action_items.strip():
    kwargs["action_items"] = action_items
  try:
    return _j(
      default_retrospective_store().update_retrospective(retrospective_id, **kwargs)
    )
  except KeyError as e:
    return str(e)


