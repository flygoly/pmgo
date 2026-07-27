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

# --- project / tasks (project_core) ---


@mcp.tool()
def pmgo_project_list() -> str:
  """List all projects in the local pmgo SQLite database."""
  err = gate("project_core.read", confirmed=False)
  if err:
    return err
  from project_core.store import default_project_store

  return _j(default_project_store().list_projects())


@mcp.tool()
def pmgo_project_create(
  name: str,
  confirmed: bool = False,
  slug: str = "",
  description: str = "",
  owner: str = "",
  scaffold_markdown: bool = False,
  locale: str = "en",
) -> str:
  """Create a project (requires confirmed=true if policy says so). Optionally scaffold markdown memory."""
  err = gate("project_core.project.write", confirmed=confirmed)
  if err:
    return err
  from project_core.memory_md import scaffold_project_markdown
  from project_core.store import default_project_store

  s = (slug or "").strip() or _slugify(name)
  row = default_project_store().create_project(
    name=name,
    slug=s,
    description=description or None,
    owner=owner or None,
  )
  if scaffold_markdown:
    try:
      memory_dir = scaffold_project_markdown(name=name, slug=s, locale=locale)
      row = {**row, "memory_dir": str(memory_dir)}
    except (ValueError, FileNotFoundError) as e:
      return str(e)
  return _j(row)


@mcp.tool()
def pmgo_task_list(project_id: str, status: str = "") -> str:
  """List tasks for a project. Optional status: todo, doing, blocked, done, cancelled."""
  err = gate("project_core.read", confirmed=False)
  if err:
    return err
  from project_core.store import default_task_store

  st = status.strip() or None
  return _j(default_task_store().list_tasks(project_id, status=st))


@mcp.tool()
def pmgo_task_create(
  project_id: str,
  title: str,
  confirmed: bool = False,
  detail: str = "",
  task_status: str = "todo",
  priority: str = "medium",
) -> str:
  """Create a task in a project (requires confirmed=true for writes). task_status: todo|doing|blocked|done|cancelled."""
  err = gate("project_core.task.write", confirmed=confirmed)
  if err:
    return err
  from project_core.store import default_task_store

  try:
    return _j(
      default_task_store().create_task(
        project_id,
        title=title,
        detail=detail or None,
        status=task_status,
        priority=priority,
      )
    )
  except sqlite3.IntegrityError as e:
    return f"Database error (duplicate external id?): {e}"


@mcp.tool()
def pmgo_task_update(
  task_id: str,
  confirmed: bool = False,
  title: str = "",
  detail: str = "",
  task_status: str = "",
  priority: str = "",
  assignee: str = "",
  due_at: str = "",
  blocked_reason: str = "",
  milestone_id: str = "",
) -> str:
  """Update a task (requires confirmed=true for writes). Pass only fields to change."""
  err = gate("project_core.task.write", confirmed=confirmed)
  if err:
    return err
  from project_core.store import default_task_store

  kwargs: dict[str, object] = {}
  if title.strip():
    kwargs["title"] = title
  if detail.strip():
    kwargs["detail"] = detail
  if task_status.strip():
    kwargs["status"] = task_status
  if priority.strip():
    kwargs["priority"] = priority
  if assignee.strip():
    kwargs["assignee"] = assignee
  if due_at.strip():
    kwargs["due_at"] = due_at
  if blocked_reason.strip():
    kwargs["blocked_reason"] = blocked_reason
  if milestone_id.strip():
    kwargs["milestone_id"] = milestone_id
  try:
    return _j(default_task_store().update_task(task_id, **kwargs))
  except KeyError as e:
    return str(e)


