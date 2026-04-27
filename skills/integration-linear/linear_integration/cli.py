"""CLI for Linear GraphQL: list / get / import into pmgo SQLite tasks."""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any

from . import api
from .config import load_config


def _print_json(data: Any) -> None:
  print(json.dumps(data, indent=2, default=str, ensure_ascii=False))


def _issue_public(issue: dict[str, Any]) -> dict[str, Any]:
  st = issue.get("state") if isinstance(issue.get("state"), dict) else {}
  return {
    "id": issue.get("id"),
    "identifier": issue.get("identifier"),
    "title": issue.get("title"),
    "description": issue.get("description"),
    "url": issue.get("url"),
    "state": st.get("name"),
    "state_type": st.get("type"),
  }


def _state_type_to_status(state: dict[str, Any] | None) -> str:
  if not isinstance(state, dict):
    return "todo"
  t = str(state.get("type") or "").lower()
  if t == "completed":
    return "done"
  if t in ("canceled", "cancelled"):
    return "cancelled"
  if t == "started":
    return "doing"
  return "todo"


def cmd_smoke(args: argparse.Namespace) -> int:
  if not (os.environ.get("LINEAR_API_KEY") or "").strip():
    print("SKIP: LINEAR_API_KEY not set (Linear smoke skipped).", file=sys.stderr)
    return 0
  try:
    cfg = load_config()
    out = api.viewer_smoke(cfg)
    v = (out or {}).get("viewer") or {}
    _print_json(
      {
        "ok": True,
        "viewer": {"id": v.get("id"), "name": v.get("name")},
      }
    )
  except (OSError, RuntimeError) as e:
    print(str(e), file=sys.stderr)
    return 1
  return 0


def cmd_list(args: argparse.Namespace) -> int:
  if args.db:
    os.environ["PMGO_MEMORY_DB"] = args.db
  try:
    cfg = load_config()
    items = api.list_issues(cfg, first=args.first)
    _print_json([_issue_public(x) for x in items])
  except (OSError, RuntimeError, ValueError) as e:
    print(str(e), file=sys.stderr)
    return 1
  return 0


def cmd_get(args: argparse.Namespace) -> int:
  if args.db:
    os.environ["PMGO_MEMORY_DB"] = args.db
  try:
    cfg = load_config()
    issue = api.get_issue(cfg, args.identifier)
    _print_json(_issue_public(issue))
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
    issue = api.get_issue(cfg, args.identifier)
  except (OSError, RuntimeError, ValueError) as e:
    print(str(e), file=sys.stderr)
    return 1

  title = str(issue.get("title") or "Linear issue")
  body = (issue.get("description") or "").strip()
  url = str(issue.get("url") or "")
  if url:
    body = f"{body}\n\nLinear: {url}".strip() if body else f"Linear: {url}"
  st = issue.get("state") if isinstance(issue.get("state"), dict) else None
  status = _state_type_to_status(st)
  ext_id = str(issue.get("id") or "")

  store = default_task_store()
  try:
    row = store.create_task(
      args.project_id,
      title=title,
      detail=body or None,
      status=status,
      source="linear",
      external_id=ext_id,
    )
  except sqlite3.IntegrityError:
    print(
      "A task with this Linear id already exists for this project (source=linear).",
      file=sys.stderr,
    )
    return 1
  _print_json(row)
  return 0


def build_parser() -> argparse.ArgumentParser:
  p = argparse.ArgumentParser(
    prog="linear-issues",
    description="Linear GraphQL helper for pmgo (set LINEAR_API_KEY).",
  )
  p.add_argument(
    "--db",
    type=str,
    default=None,
    metavar="PATH",
    help="PMGO_MEMORY_DB path override for import-task.",
  )
  s = p.add_subparsers(dest="command", required=True)
  s.add_parser("smoke", help="Verify API key (or skip if unset)").set_defaults(_fn=cmd_smoke)
  l = s.add_parser("list", help="List recent issues")
  l.add_argument("--first", type=int, default=20, help="Page size (default 20)")
  l.set_defaults(_fn=cmd_list)
  g = s.add_parser("get", help="Get one issue by id or identifier (e.g. ENG-42)")
  g.add_argument("identifier", type=str)
  g.set_defaults(_fn=cmd_get)
  it = s.add_parser(
    "import-task",
    help="Create a local task (source=linear, external_id=Linear issue UUID)",
  )
  it.add_argument("--project-id", required=True, dest="project_id")
  it.add_argument("--identifier", type=str, required=True, dest="identifier")
  it.set_defaults(_fn=cmd_import_task)
  return p


def main(argv: list[str] | None = None) -> int:
  parser = build_parser()
  args = parser.parse_args(argv if argv is not None else sys.argv[1:])
  return int(args._fn(args))


if __name__ == "__main__":
  raise SystemExit(main())
