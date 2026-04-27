#!/usr/bin/env python3
"""
stdio MCP server exposing pmgo CLIs (project-core, reports, GitHub) with policy
checks from `policy/pmgo.policy.yaml`. Run via OpenClaw: `openclaw mcp set pmgo
'{"command":"python3","args":["'$(pwd)'/scripts/pmgo_mcp_server.py"]}'` (use an
absolute path to this script; optional env PMGO_WORKSPACE for clarity).
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from pathlib import Path

# Repository root (this file lives in scripts/)
_ROOT = Path(__file__).resolve().parent.parent
if (ws := (os.environ.get("PMGO_WORKSPACE") or "").strip()):
  _override = Path(ws).resolve()
  if _override.is_dir():
    _ROOT = _override

for _d in (
  _ROOT / "scripts",
  _ROOT / "skills" / "project-core",
  _ROOT / "skills" / "daily-standup",
  _ROOT / "skills" / "weekly-report",
  _ROOT / "skills" / "integration-github",
  _ROOT / "skills" / "risk-radar",
):
  p = str(_d)
  if p not in sys.path:
    sys.path.insert(0, p)

from pmgo_policy import gate  # noqa: E402

try:
  from mcp.server.fastmcp import FastMCP
except ImportError as e:
  print(
    f"ERROR: mcp package not installed. Install with: pip install mcp pyyaml\n{e}",
    file=sys.stderr,
  )
  raise SystemExit(1) from e

mcp = FastMCP("pmgo")


def _j(data: object) -> str:
  return json.dumps(data, indent=2, default=str, ensure_ascii=False)


def _issue_public(issue: dict) -> dict:
  return {
    "id": issue.get("id"),
    "number": issue.get("number"),
    "title": issue.get("title"),
    "state": issue.get("state"),
    "body": issue.get("body"),
    "html_url": issue.get("html_url"),
    "user": (issue.get("user") or {}).get("login"),
  }


def _slugify(name: str) -> str:
  from project_core.config import slugify

  return slugify(name)


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
) -> str:
  """Create a project (requires confirmed=true if policy says so)."""
  err = gate("project_core.project.write", confirmed=confirmed)
  if err:
    return err
  from project_core.store import default_project_store

  s = (slug or "").strip() or _slugify(name)
  return _j(
    default_project_store().create_project(
      name=name,
      slug=s,
      description=description or None,
      owner=owner or None,
    )
  )


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


# --- risk radar (SQLite risks + blocked tasks) ---


@mcp.tool()
def pmgo_risk_scan(project_id: str) -> str:
  """List open/watching risks and blocked tasks for a project (local SQLite)."""
  err = gate("pmgo.risk.scan", confirmed=False)
  if err:
    return err
  from risk_radar import scan as scanmod

  try:
    return _j(scanmod.scan_project(project_id))
  except KeyError as e:
    return str(e)


# --- reports ---


@mcp.tool()
def pmgo_daily_report(project_id: str, locale: str = "en") -> str:
  """Render the Markdown daily standup for a project (UTC 24h window)."""
  err = gate("pmgo.report.daily", confirmed=False)
  if err:
    return err
  from daily_standup.build import build_daily_markdown

  return build_daily_markdown(project_id=project_id, locale=locale)


@mcp.tool()
def pmgo_weekly_report(
  project_id: str,
  locale: str = "en",
  week_offset: int = 0,
) -> str:
  """Render the Markdown weekly report (UTC ISO week; week_offset 0 = current)."""
  err = gate("pmgo.report.weekly", confirmed=False)
  if err:
    return err
  from weekly_report.build import build_weekly_markdown

  return build_weekly_markdown(
    project_id=project_id, locale=locale, week_offset=week_offset
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
  ttitle = str(issue.get("title") or f"Issue #{number}")
  body = (issue.get("body") or "").strip()
  url = str(issue.get("html_url") or "")
  if url:
    body = f"{body}\n\nGitHub: {url}".strip() if body else f"GitHub: {url}"
  gh_state = str(issue.get("state") or "open")
  tstatus = "done" if gh_state == "closed" else "todo"
  ext_id = str(issue.get("id") or "")
  store = default_task_store()
  try:
    return _j(
      store.create_task(
        project_id,
        title=ttitle,
        detail=body or None,
        status=tstatus,
        source="github",
        external_id=ext_id,
      )
    )
  except sqlite3.IntegrityError:
    return "A task for this GitHub issue already exists (same project + source + external_id)."


def main() -> None:
  os.environ.setdefault("PMGO_WORKSPACE", str(_ROOT))
  try:
    os.chdir(_ROOT)
  except OSError:
    pass
  run = getattr(mcp, "run", None)
  if not callable(run):
    raise SystemExit("FastMCP instance has no .run(); install mcp: pip install mcp pyyaml")
  try:
    run(transport="stdio")
  except TypeError:
    run()


if __name__ == "__main__":
  main()
