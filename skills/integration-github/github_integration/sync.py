"""Incremental GitHub Issues ↔ pmgo task sync (import + close-on-done)."""

from __future__ import annotations

import sqlite3
from typing import Any, Optional

from .api import list_issues, update_issue
from .config import GitHubConfig


def _task_fields_from_issue(issue: dict[str, Any]) -> dict[str, Any]:
  number = issue.get("number")
  title = str(issue.get("title") or f"Issue #{number}")
  body = (issue.get("body") or "").strip()
  url = str(issue.get("html_url") or "")
  if url:
    body = f"{body}\n\nGitHub: {url}".strip() if body else f"GitHub: {url}"
  gh_state = str(issue.get("state") or "open")
  status = "done" if gh_state == "closed" else "todo"
  ext_id = str(issue.get("id") or "")
  return {
    "title": title,
    "detail": body or None,
    "status": status,
    "source": "github",
    "external_id": ext_id,
    "number": number,
  }


def import_issue_as_task(
  store: Any,
  project_id: str,
  issue: dict[str, Any],
) -> Optional[dict[str, Any]]:
  """
  Import one GitHub issue as a local task.
  Returns the new task row, or None if skipped (duplicate / invalid id).
  """
  fields = _task_fields_from_issue(issue)
  if not fields["external_id"]:
    return None
  try:
    return store.create_task(
      project_id,
      title=fields["title"],
      detail=fields["detail"],
      status=fields["status"],
      source=fields["source"],
      external_id=fields["external_id"],
    )
  except sqlite3.IntegrityError:
    return None


def sync_issues_to_project(
  cfg: GitHubConfig,
  store: Any,
  project_id: str,
  *,
  state: str = "open",
  per_page: int = 50,
  max_pages: int = 10,
) -> dict[str, Any]:
  """List GitHub issues and import any not yet present locally."""
  issues = list_issues(cfg, state=state, per_page=per_page, max_pages=max_pages)
  imported: list[dict[str, Any]] = []
  skipped: list[int] = []
  invalid: list[int] = []
  for issue in issues:
    number = issue.get("number")
    row = import_issue_as_task(store, project_id, issue)
    if row is not None:
      imported.append(
        {
          "number": number,
          "task_id": row.get("id"),
          "external_id": row.get("external_id"),
          "title": row.get("title"),
        }
      )
    elif not str(issue.get("id") or ""):
      if isinstance(number, int):
        invalid.append(number)
    elif isinstance(number, int):
      skipped.append(number)
  return {
    "project_id": project_id,
    "state": state,
    "scanned": len(issues),
    "imported_count": len(imported),
    "skipped_count": len(skipped),
    "invalid_count": len(invalid),
    "imported": imported,
    "skipped_numbers": skipped,
    "invalid_numbers": invalid,
  }


def push_done_tasks_to_github(
  cfg: GitHubConfig,
  store: Any,
  project_id: str,
  *,
  per_page: int = 50,
  max_pages: int = 10,
) -> dict[str, Any]:
  """
  Close open GitHub issues whose matching local tasks are status=done
  (source=github, matched by GitHub numeric issue id in external_id).
  """
  done_tasks = [
    t
    for t in store.list_tasks(project_id, status="done")
    if str(t.get("source") or "") == "github" and str(t.get("external_id") or "")
  ]
  open_issues = list_issues(cfg, state="open", per_page=per_page, max_pages=max_pages)
  by_ext: dict[str, dict[str, Any]] = {
    str(i.get("id")): i for i in open_issues if i.get("id") is not None
  }
  closed: list[dict[str, Any]] = []
  skipped: list[str] = []
  errors: list[dict[str, Any]] = []
  for task in done_tasks:
    ext = str(task.get("external_id"))
    issue = by_ext.get(ext)
    if issue is None:
      skipped.append(ext)
      continue
    number = issue.get("number")
    if not isinstance(number, int):
      skipped.append(ext)
      continue
    try:
      update_issue(cfg, number, state="closed")
      closed.append(
        {
          "task_id": task.get("id"),
          "external_id": ext,
          "number": number,
          "title": task.get("title"),
        }
      )
    except RuntimeError as e:
      errors.append({"external_id": ext, "number": number, "error": str(e)})
  return {
    "project_id": project_id,
    "done_local": len(done_tasks),
    "closed_count": len(closed),
    "skipped_count": len(skipped),
    "error_count": len(errors),
    "closed": closed,
    "skipped_external_ids": skipped,
    "errors": errors,
  }
