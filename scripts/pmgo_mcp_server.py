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
  _ROOT / "skills" / "integration-feishu",
):
  p = str(_d)
  if p not in sys.path:
    sys.path.insert(0, p)

from pmgo_log import elapsed_ms, log_event, setup_logging, tool_timer  # noqa: E402
from pmgo_policy import gate as _policy_gate  # noqa: E402

_log = setup_logging()


def gate(tool_key: str, *, confirmed: bool) -> str | None:
  """Policy gate with structured stderr logging."""
  started = tool_timer()
  err = _policy_gate(tool_key, confirmed=confirmed)
  log_event(
    _log,
    "mcp.gate",
    tool=tool_key,
    confirmed=confirmed,
    ok=err is None,
    error=err,
    ms=elapsed_ms(started),
  )
  return err


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


# --- Feishu ---


@mcp.tool()
def pmgo_feishu_task_list(tasklist_guid: str = "", page_size: int = 50) -> str:
  """List Feishu tasks in a tasklist (FEISHU_TASKLIST_GUID or tasklist_guid)."""
  err = gate("feishu.task.read", confirmed=False)
  if err:
    return err
  import os

  from feishu_integration.api import list_tasklist_tasks, task_to_public
  from feishu_integration.config import load_config

  try:
    cfg = load_config()
    guid = (tasklist_guid or os.environ.get("FEISHU_TASKLIST_GUID") or "").strip()
    if not guid:
      return "tasklist_guid is required (or set FEISHU_TASKLIST_GUID)."
    data = list_tasklist_tasks(cfg, guid, page_size=page_size)
    items = data.get("items") or data.get("tasks") or []
    public = [task_to_public(x) for x in items if isinstance(x, dict)]
    return _j(
      {
        "tasklist_guid": guid,
        "items": public,
        "has_more": data.get("has_more"),
        "page_token": data.get("page_token"),
      }
    )
  except (OSError, RuntimeError, ValueError) as e:
    return str(e)


@mcp.tool()
def pmgo_feishu_task_get(task_guid: str) -> str:
  """Get one Feishu task by guid."""
  err = gate("feishu.task.read", confirmed=False)
  if err:
    return err
  from feishu_integration.api import get_task, task_to_public
  from feishu_integration.config import load_config

  try:
    cfg = load_config()
    return _j(task_to_public(get_task(cfg, task_guid)))
  except (OSError, RuntimeError, ValueError) as e:
    return str(e)


@mcp.tool()
def pmgo_feishu_import_task(
  project_id: str,
  task_guid: str,
  confirmed: bool = False,
) -> str:
  """Import a Feishu task as a local task (source=feishu, requires confirmed)."""
  err = gate("feishu.task.import_task", confirmed=confirmed)
  if err:
    return err
  from feishu_integration.api import get_task, task_to_public
  from feishu_integration.config import load_config
  from project_core.store import default_task_store

  try:
    cfg = load_config()
    pub = task_to_public(get_task(cfg, task_guid))
  except (OSError, RuntimeError, ValueError) as e:
    return str(e)
  title = str(pub.get("summary") or pub.get("guid") or "Feishu task")
  body = (pub.get("description") or "").strip() if pub.get("description") else ""
  url = str(pub.get("url") or "")
  if url:
    body = f"{body}\n\nFeishu: {url}".strip() if body else f"Feishu: {url}"
  ext_id = str(pub.get("guid") or "")
  if not ext_id:
    return "Feishu task missing guid"
  try:
    return _j(
      default_task_store().create_task(
        project_id,
        title=title,
        detail=body or None,
        status=str(pub.get("status") or "todo"),
        source="feishu",
        external_id=ext_id,
      )
    )
  except sqlite3.IntegrityError:
    return "A task for this Feishu guid already exists (same project + source + external_id)."


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
