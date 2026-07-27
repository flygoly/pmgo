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

# --- Linear ---


@mcp.tool()
def pmgo_linear_issue_list(first: int = 20) -> str:
  """List Linear issues (newest). Needs LINEAR_API_KEY."""
  err = gate("linear.issue.read", confirmed=False)
  if err:
    return err
  from linear_integration.api import list_issues
  from linear_integration.cli import _issue_public
  from linear_integration.config import load_config

  try:
    cfg = load_config()
  except OSError as e:
    return str(e)
  try:
    items = list_issues(cfg, first=first)
    return _j([_issue_public(x) for x in items])
  except RuntimeError as e:
    return str(e)


@mcp.tool()
def pmgo_linear_issue_get(identifier: str) -> str:
  """Get one Linear issue by id or identifier (e.g. ENG-42)."""
  err = gate("linear.issue.read", confirmed=False)
  if err:
    return err
  from linear_integration.api import get_issue
  from linear_integration.cli import _issue_public
  from linear_integration.config import load_config

  try:
    cfg = load_config()
    return _j(_issue_public(get_issue(cfg, identifier)))
  except (OSError, RuntimeError, ValueError) as e:
    return str(e)


@mcp.tool()
def pmgo_linear_import_task(
  project_id: str,
  identifier: str,
  confirmed: bool = False,
) -> str:
  """Import a Linear issue as a local task (source=linear, requires confirmed)."""
  err = gate("linear.issue.import_task", confirmed=confirmed)
  if err:
    return err
  from linear_integration.api import get_issue
  from linear_integration.cli import _state_type_to_status
  from linear_integration.config import load_config
  from project_core.store import default_task_store

  try:
    cfg = load_config()
    issue = get_issue(cfg, identifier)
  except (OSError, RuntimeError, ValueError) as e:
    return str(e)
  ttitle = str(issue.get("title") or "Linear issue")
  body = (issue.get("description") or "").strip()
  url = str(issue.get("url") or "")
  if url:
    body = f"{body}\n\nLinear: {url}".strip() if body else f"Linear: {url}"
  st = issue.get("state") if isinstance(issue.get("state"), dict) else None
  tstatus = _state_type_to_status(st)
  ext_id = str(issue.get("id") or "")
  store = default_task_store()
  try:
    return _j(
      store.create_task(
        project_id,
        title=ttitle,
        detail=body or None,
        status=tstatus,
        source="linear",
        external_id=ext_id,
      )
    )
  except sqlite3.IntegrityError:
    return "A task for this Linear issue already exists (same project + source + external_id)."


@mcp.tool()
def pmgo_linear_comment(
  identifier: str,
  body: str,
  confirmed: bool = False,
) -> str:
  """Post a comment on a Linear issue (requires confirmed=true)."""
  err = gate("linear.issue.comment", confirmed=confirmed)
  if err:
    return err
  from linear_integration.api import create_comment, get_issue
  from linear_integration.cli import _issue_public
  from linear_integration.config import load_config

  try:
    cfg = load_config()
    issue = get_issue(cfg, identifier)
    issue_id = str(issue.get("id") or "")
    if not issue_id:
      return "Issue has no id"
    comment = create_comment(cfg, issue_id=issue_id, body=body)
    return _j({"ok": True, "issue": _issue_public(issue), "comment": comment})
  except (OSError, RuntimeError, ValueError) as e:
    return str(e)


