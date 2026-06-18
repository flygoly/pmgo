#!/usr/bin/env python3
"""
stdio MCP server exposing pmgo CLIs (project-core, reports, GitHub, Linear, Jira) with policy
checks from `policy/pmgo.policy.yaml`.

OpenClaw: `openclaw mcp set pmgo '...'` — see `runtimes/openclaw/README.md`
Hermes:   `mcp_servers.pmgo` in config.yaml — see `runtimes/hermes/README.md`
Generate: `npm run runtime:config -- --runtime openclaw|hermes`
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
  _ROOT / "skills" / "integration-linear",
  _ROOT / "skills" / "integration-jira",
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


def _resolve_project_id(project_id: str) -> str | None:
  import pmgo_common  # noqa: WPS433

  return pmgo_common.resolve_project_id(explicit=project_id or None)


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


# --- risk radar (SQLite risks + blocked tasks) ---


@mcp.tool()
def pmgo_risk_scan(project_id: str = "") -> str:
  """List open/watching risks and blocked tasks. Uses PMGO_DEFAULT_PROJECT_ID when empty."""
  err = gate("pmgo.risk.scan", confirmed=False)
  if err:
    return err
  from risk_radar import scan as scanmod

  pid = _resolve_project_id(project_id)
  if not pid:
    return "project_id is required (or set PMGO_DEFAULT_PROJECT_ID)."
  try:
    return _j(scanmod.scan_project(pid))
  except KeyError as e:
    return str(e)


# --- reports ---


@mcp.tool()
def pmgo_daily_report(project_id: str = "", locale: str = "") -> str:
  """Render the Markdown daily standup. Uses PMGO_DEFAULT_PROJECT_ID when project_id is empty."""
  err = gate("pmgo.report.daily", confirmed=False)
  if err:
    return err
  import pmgo_common  # noqa: WPS433
  from daily_standup.build import build_daily_markdown

  pid = _resolve_project_id(project_id)
  if not pid:
    return "project_id is required (or set PMGO_DEFAULT_PROJECT_ID)."
  loc = locale.strip() or pmgo_common.default_locale()
  return build_daily_markdown(project_id=pid, locale=loc)


@mcp.tool()
def pmgo_weekly_report(
  project_id: str = "",
  locale: str = "",
  week_offset: int = 0,
) -> str:
  """Render the Markdown weekly report. Uses PMGO_DEFAULT_PROJECT_ID when project_id is empty."""
  err = gate("pmgo.report.weekly", confirmed=False)
  if err:
    return err
  import pmgo_common  # noqa: WPS433
  from weekly_report.build import build_weekly_markdown

  pid = _resolve_project_id(project_id)
  if not pid:
    return "project_id is required (or set PMGO_DEFAULT_PROJECT_ID)."
  loc = locale.strip() or pmgo_common.default_locale()
  return build_weekly_markdown(
    project_id=pid, locale=loc, week_offset=week_offset
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
