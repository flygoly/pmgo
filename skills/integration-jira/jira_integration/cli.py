"""CLI for Jira Cloud REST: list / get / import into pmgo SQLite tasks."""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any

from . import api
from .config import JiraConfig, load_config


def _print_json(data: Any) -> None:
  print(json.dumps(data, indent=2, default=str, ensure_ascii=False))


def _adf_to_plain(node: Any) -> str:
  if node is None:
    return ""
  if isinstance(node, str):
    return node
  if not isinstance(node, dict):
    return ""
  if node.get("type") == "text":
    return str(node.get("text") or "")
  parts: list[str] = []
  for child in node.get("content") or []:
    parts.append(_adf_to_plain(child))
  text = "".join(parts)
  if node.get("type") == "paragraph":
    return text + "\n"
  return text


def _issue_public(cfg: JiraConfig, issue: dict[str, Any]) -> dict[str, Any]:
  fields = issue.get("fields") if isinstance(issue.get("fields"), dict) else {}
  status = fields.get("status") if isinstance(fields.get("status"), dict) else {}
  cat = status.get("statusCategory") if isinstance(status.get("statusCategory"), dict) else {}
  key = str(issue.get("key") or "")
  desc_raw = fields.get("description")
  description = _adf_to_plain(desc_raw).strip() if desc_raw is not None else ""
  return {
    "id": issue.get("id"),
    "key": key,
    "title": fields.get("summary"),
    "description": description or None,
    "url": api.browse_url(cfg, key) if key else None,
    "status": status.get("name"),
    "status_category": cat.get("key"),
  }


def _status_category_to_pmgo(category_key: str | None, status_name: str | None) -> str:
  key = (category_key or "").lower()
  name = (status_name or "").lower()
  if key == "done":
    return "done"
  if "cancel" in name:
    return "cancelled"
  if key == "indeterminate":
    return "doing"
  return "todo"


def _jira_credentials_set() -> bool:
  return bool(
    (os.environ.get("JIRA_BASE_URL") or "").strip()
    and (os.environ.get("JIRA_EMAIL") or "").strip()
    and (os.environ.get("JIRA_API_TOKEN") or "").strip()
  )


def cmd_smoke(args: argparse.Namespace) -> int:
  if not _jira_credentials_set():
    print("SKIP: JIRA_BASE_URL / JIRA_EMAIL / JIRA_API_TOKEN not set (Jira smoke skipped).", file=sys.stderr)
    return 0
  try:
    cfg = load_config()
    me = api.myself_smoke(cfg)
    _print_json({"ok": True, "accountId": me.get("accountId"), "displayName": me.get("displayName")})
  except (OSError, RuntimeError) as e:
    print(str(e), file=sys.stderr)
    return 1
  return 0


def cmd_list(args: argparse.Namespace) -> int:
  if args.db:
    os.environ["PMGO_MEMORY_DB"] = args.db
  try:
    cfg = load_config()
    items = api.search_issues(cfg, jql=args.jql, max_results=args.max_results)
    _print_json([_issue_public(cfg, x) for x in items])
  except (OSError, RuntimeError, ValueError) as e:
    print(str(e), file=sys.stderr)
    return 1
  return 0


def cmd_get(args: argparse.Namespace) -> int:
  if args.db:
    os.environ["PMGO_MEMORY_DB"] = args.db
  try:
    cfg = load_config()
    issue = api.get_issue(cfg, args.issue_key)
    _print_json(_issue_public(cfg, issue))
  except (OSError, RuntimeError, ValueError) as e:
    print(str(e), file=sys.stderr)
    return 1
  return 0


def cmd_transitions(args: argparse.Namespace) -> int:
  try:
    cfg = load_config()
    items = api.list_transitions(cfg, args.issue_key)
    slim = [
      {
        "id": t.get("id"),
        "name": t.get("name"),
        "to": ((t.get("to") or {}) if isinstance(t.get("to"), dict) else {}).get("name"),
      }
      for t in items
    ]
    _print_json(slim)
  except (OSError, RuntimeError, ValueError) as e:
    print(str(e), file=sys.stderr)
    return 1
  return 0


def cmd_transition(args: argparse.Namespace) -> int:
  try:
    cfg = load_config()
    api.transition_issue(cfg, args.issue_key, transition_id=args.transition_id)
    _print_json({"ok": True, "issue_key": args.issue_key, "transition_id": args.transition_id})
  except (OSError, RuntimeError, ValueError) as e:
    print(str(e), file=sys.stderr)
    return 1
  return 0


def cmd_import_task(args: argparse.Namespace) -> int:
  if args.db:
    os.environ["PMGO_MEMORY_DB"] = args.db
  root = Path(__file__).resolve().parents[3]
  sys.path[:0] = [str(root / "scripts"), str(root / "skills" / "project-core")]
  from project_core.store import default_task_store  # noqa: WPS433

  try:
    cfg = load_config()
    issue = api.get_issue(cfg, args.issue_key)
  except (OSError, RuntimeError, ValueError) as e:
    print(str(e), file=sys.stderr)
    return 1

  pub = _issue_public(cfg, issue)
  title = str(pub.get("title") or pub.get("key") or "Jira issue")
  body = (pub.get("description") or "").strip() if pub.get("description") else ""
  url = str(pub.get("url") or "")
  if url:
    body = f"{body}\n\nJira: {url}".strip() if body else f"Jira: {url}"
  status = _status_category_to_pmgo(
    str(pub.get("status_category") or ""),
    str(pub.get("status") or ""),
  )
  ext_id = str(pub.get("id") or "")

  store = default_task_store()
  try:
    row = store.create_task(
      args.project_id,
      title=title,
      detail=body or None,
      status=status,
      source="jira",
      external_id=ext_id,
    )
  except sqlite3.IntegrityError:
    print(
      "A task with this Jira id already exists for this project (source=jira).",
      file=sys.stderr,
    )
    return 1
  _print_json(row)
  return 0


def build_parser() -> argparse.ArgumentParser:
  p = argparse.ArgumentParser(
    prog="jira-issues",
    description="Jira Cloud REST helper for pmgo (JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN).",
  )
  p.add_argument(
    "--db",
    type=str,
    default=None,
    metavar="PATH",
    help="PMGO_MEMORY_DB path override for import-task.",
  )
  s = p.add_subparsers(dest="command", required=True)
  s.add_parser("smoke", help="Verify credentials (or skip if unset)").set_defaults(_fn=cmd_smoke)
  l = s.add_parser("list", help="Search issues via JQL")
  l.add_argument("--jql", default=None, help="JQL query (default: project filter or ORDER BY updated)")
  l.add_argument("--max-results", type=int, default=20, dest="max_results")
  l.set_defaults(_fn=cmd_list)
  g = s.add_parser("get", help="Get one issue by key (e.g. PROJ-123)")
  g.add_argument("issue_key", type=str)
  g.set_defaults(_fn=cmd_get)
  it = s.add_parser(
    "import-task",
    help="Create a local task (source=jira, external_id=Jira issue id)",
  )
  it.add_argument("--project-id", required=True, dest="project_id")
  it.add_argument("--issue-key", type=str, required=True, dest="issue_key")
  it.set_defaults(_fn=cmd_import_task)
  tr = s.add_parser("transitions", help="List workflow transitions for an issue")
  tr.add_argument("issue_key", type=str)
  tr.set_defaults(_fn=cmd_transitions)
  tx = s.add_parser("transition", help="Apply a workflow transition (trusted CLI)")
  tx.add_argument("issue_key", type=str)
  tx.add_argument("--transition-id", required=True, dest="transition_id")
  tx.set_defaults(_fn=cmd_transition)
  return p


def main(argv: list[str] | None = None) -> int:
  parser = build_parser()
  args = parser.parse_args(argv if argv is not None else sys.argv[1:])
  return int(args._fn(args))


if __name__ == "__main__":
  raise SystemExit(main())
