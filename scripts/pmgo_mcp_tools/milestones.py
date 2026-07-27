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

# --- milestones ---


@mcp.tool()
def pmgo_milestone_list(project_id: str) -> str:
  """List milestones for a project."""
  err = gate("project_core.milestone.read", confirmed=False)
  if err:
    return err
  from project_core.store import default_milestone_store

  return _j(default_milestone_store().list_milestones(project_id))


@mcp.tool()
def pmgo_milestone_create(
  project_id: str,
  title: str,
  confirmed: bool = False,
  milestone_status: str = "todo",
  owner: str = "",
  due_at: str = "",
) -> str:
  """Create a milestone (requires confirmed=true for writes)."""
  err = gate("project_core.milestone.write", confirmed=confirmed)
  if err:
    return err
  from project_core.store import default_milestone_store

  return _j(
    default_milestone_store().create_milestone(
      project_id,
      title=title,
      status=milestone_status,
      owner=owner or None,
      due_at=due_at or None,
    )
  )


@mcp.tool()
def pmgo_milestone_update(
  milestone_id: str,
  confirmed: bool = False,
  title: str = "",
  milestone_status: str = "",
  owner: str = "",
  due_at: str = "",
) -> str:
  """Update a milestone (requires confirmed=true for writes)."""
  err = gate("project_core.milestone.write", confirmed=confirmed)
  if err:
    return err
  from project_core.store import default_milestone_store

  kwargs: dict[str, object] = {}
  if title.strip():
    kwargs["title"] = title
  if milestone_status.strip():
    kwargs["status"] = milestone_status
  if owner.strip():
    kwargs["owner"] = owner
  if due_at.strip():
    kwargs["due_at"] = due_at
  try:
    return _j(default_milestone_store().update_milestone(milestone_id, **kwargs))
  except KeyError as e:
    return str(e)


