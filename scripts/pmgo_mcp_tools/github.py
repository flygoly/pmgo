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

# --- GitHub ---


@mcp.tool()
def pmgo_github_issue_list(state: str = "all", per_page: int = 20) -> str:
  """List GitHub issues (excludes PRs). Needs GITHUB_TOKEN and GITHUB_REPO=owner/name."""
  err = gate("github.issue.read", confirmed=False)
  if err:
    return err
  from github_integration.api import list_issues
  from github_integration.config import load_config

  try:
    cfg = load_config()
  except OSError as e:
    return str(e)
  return _j(list_issues(cfg, state=state, per_page=per_page))


@mcp.tool()
def pmgo_github_issue_get(number: int) -> str:
  """Get one GitHub issue by number."""
  err = gate("github.issue.read", confirmed=False)
  if err:
    return err
  from github_integration.api import get_issue
  from github_integration.config import load_config

  try:
    cfg = load_config()
    return _j(_issue_public(get_issue(cfg, number)))
  except (OSError, RuntimeError) as e:
    return str(e)


@mcp.tool()
def pmgo_github_issue_create(
  title: str,
  body: str = "",
  confirmed: bool = False,
) -> str:
  """Create a GitHub issue (requires confirmed)."""
  err = gate("github.issue.create", confirmed=confirmed)
  if err:
    return err
  from github_integration.api import create_issue
  from github_integration.config import load_config
  from github_integration.cli import _issue_public

  try:
    cfg = load_config()
    return _j(_issue_public(create_issue(cfg, title=title, body=body)))
  except (OSError, RuntimeError) as e:
    return str(e)


@mcp.tool()
def pmgo_github_issue_close(number: int, confirmed: bool = False) -> str:
  """Close a GitHub issue by number (requires confirmed)."""
  err = gate("github.issue.update", confirmed=confirmed)
  if err:
    return err
  from github_integration.api import update_issue
  from github_integration.config import load_config
  from github_integration.cli import _issue_public

  try:
    cfg = load_config()
    return _j(_issue_public(update_issue(cfg, number, state="closed")))
  except (OSError, RuntimeError) as e:
    return str(e)


@mcp.tool()
def pmgo_github_import_task(
  project_id: str,
  number: int,
  confirmed: bool = False,
) -> str:
  """Import a GitHub issue as a local task (source=github, requires confirmed)."""
  err = gate("github.issue.import_task", confirmed=confirmed)
  if err:
    return err
  from github_integration.api import get_issue
  from github_integration.config import load_config
  from project_core.store import default_task_store

  try:
    cfg = load_config()
    issue = get_issue(cfg, number)
  except (OSError, RuntimeError) as e:
    return str(e)
  store = default_task_store()
  from github_integration.sync import import_issue_as_task

  row = import_issue_as_task(store, project_id, issue)
  if row is not None:
    return _j(row)
  if not str(issue.get("id") or ""):
    return "Issue missing GitHub id; cannot import."
  return "A task for this GitHub issue already exists (same project + source + external_id)."


@mcp.tool()
def pmgo_github_sync_tasks(
  project_id: str,
  confirmed: bool = False,
  state: str = "open",
  per_page: int = 50,
  max_pages: int = 10,
) -> str:
  """Import GitHub issues not yet present as local tasks (idempotent batch sync)."""
  err = gate("github.issue.sync", confirmed=confirmed)
  if err:
    return err
  from github_integration.config import load_config
  from github_integration.sync import sync_issues_to_project
  from project_core.store import default_task_store

  try:
    cfg = load_config()
    store = default_task_store()
    return _j(
      sync_issues_to_project(
        cfg,
        store,
        project_id,
        state=state,
        per_page=per_page,
        max_pages=max_pages,
      )
    )
  except (OSError, RuntimeError) as e:
    return str(e)


@mcp.tool()
def pmgo_github_push_done(
  project_id: str,
  confirmed: bool = False,
  per_page: int = 50,
  max_pages: int = 10,
) -> str:
  """Close open GitHub issues for local done tasks (source=github). Requires confirmed."""
  err = gate("github.issue.update", confirmed=confirmed)
  if err:
    return err
  from github_integration.config import load_config
  from github_integration.sync import push_done_tasks_to_github
  from project_core.store import default_task_store

  try:
    cfg = load_config()
    return _j(
      push_done_tasks_to_github(
        cfg,
        default_task_store(),
        project_id,
        per_page=per_page,
        max_pages=max_pages,
      )
    )
  except (OSError, RuntimeError) as e:
    return str(e)


