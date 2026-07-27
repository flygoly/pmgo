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

# --- Jira ---


@mcp.tool()
def pmgo_jira_issue_list(jql: str = "", max_results: int = 20) -> str:
  """Search Jira issues via JQL (empty jql uses default). Needs Jira env vars."""
  err = gate("jira.issue.read", confirmed=False)
  if err:
    return err
  from jira_integration.api import search_issues
  from jira_integration.cli import _issue_public
  from jira_integration.config import load_config

  try:
    cfg = load_config()
  except OSError as e:
    return str(e)
  try:
    items = search_issues(cfg, jql=jql or None, max_results=max_results)
    return _j([_issue_public(cfg, x) for x in items])
  except RuntimeError as e:
    return str(e)


@mcp.tool()
def pmgo_jira_issue_get(issue_key: str) -> str:
  """Get one Jira issue by key (e.g. PROJ-123)."""
  err = gate("jira.issue.read", confirmed=False)
  if err:
    return err
  from jira_integration.api import get_issue
  from jira_integration.cli import _issue_public
  from jira_integration.config import load_config

  try:
    cfg = load_config()
    return _j(_issue_public(cfg, get_issue(cfg, issue_key)))
  except (OSError, RuntimeError, ValueError) as e:
    return str(e)


@mcp.tool()
def pmgo_jira_import_task(
  project_id: str,
  issue_key: str,
  confirmed: bool = False,
) -> str:
  """Import a Jira issue as a local task (source=jira, requires confirmed)."""
  err = gate("jira.issue.import_task", confirmed=confirmed)
  if err:
    return err
  from jira_integration.api import get_issue
  from jira_integration.cli import _issue_public, _status_category_to_pmgo
  from jira_integration.config import load_config
  from project_core.store import default_task_store

  try:
    cfg = load_config()
    issue = get_issue(cfg, issue_key)
  except (OSError, RuntimeError, ValueError) as e:
    return str(e)
  pub = _issue_public(cfg, issue)
  ttitle = str(pub.get("title") or pub.get("key") or "Jira issue")
  body = (pub.get("description") or "").strip() if pub.get("description") else ""
  url = str(pub.get("url") or "")
  if url:
    body = f"{body}\n\nJira: {url}".strip() if body else f"Jira: {url}"
  tstatus = _status_category_to_pmgo(
    str(pub.get("status_category") or ""),
    str(pub.get("status") or ""),
  )
  ext_id = str(pub.get("id") or "")
  store = default_task_store()
  try:
    return _j(
      store.create_task(
        project_id,
        title=ttitle,
        detail=body or None,
        status=tstatus,
        source="jira",
        external_id=ext_id,
      )
    )
  except sqlite3.IntegrityError:
    return "A task for this Jira issue already exists (same project + source + external_id)."


@mcp.tool()
def pmgo_jira_list_transitions(issue_key: str) -> str:
  """List available Jira transitions for an issue key."""
  err = gate("jira.issue.read", confirmed=False)
  if err:
    return err
  from jira_integration.api import list_transitions
  from jira_integration.config import load_config

  try:
    cfg = load_config()
    transitions = list_transitions(cfg, issue_key)
    slim = [
      {
        "id": t.get("id"),
        "name": t.get("name"),
        "to": ((t.get("to") or {}) if isinstance(t.get("to"), dict) else {}).get("name"),
      }
      for t in transitions
    ]
    return _j(slim)
  except (OSError, RuntimeError, ValueError) as e:
    return str(e)


@mcp.tool()
def pmgo_jira_transition_issue(
  issue_key: str,
  transition_id: str,
  confirmed: bool = False,
) -> str:
  """Apply a Jira workflow transition (requires confirmed=true)."""
  err = gate("jira.transition_issue", confirmed=confirmed)
  if err:
    return err
  from jira_integration.api import transition_issue
  from jira_integration.config import load_config

  try:
    cfg = load_config()
    transition_issue(cfg, issue_key, transition_id=transition_id)
    return _j({"ok": True, "issue_key": issue_key, "transition_id": transition_id})
  except (OSError, RuntimeError, ValueError) as e:
    return str(e)


