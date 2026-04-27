"""CLI for GitHub Issues (REST) and optional import into pmgo SQLite tasks."""

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


def cmd_smoke(args: argparse.Namespace) -> int:
  if not (os.environ.get("GITHUB_TOKEN") or "").strip():
    print("SKIP: GITHUB_TOKEN not set (GitHub smoke skipped).", file=sys.stderr)
    return 0
  if not (os.environ.get("GITHUB_REPO") or "").strip():
    print("SKIP: GITHUB_REPO not set (GitHub smoke skipped).", file=sys.stderr)
    return 0
  try:
    cfg = load_config()
    rl = api.rate_limit(cfg)
    core = rl.get("resources", {}).get("core", {})
    _print_json(
      {
        "ok": True,
        "rate_limit": {
          "remaining": core.get("remaining"),
          "limit": core.get("limit"),
          "reset": core.get("reset"),
        },
      }
    )
  except OSError as e:
    print(str(e), file=sys.stderr)
    return 1
  except RuntimeError as e:
    print(str(e), file=sys.stderr)
    return 1
  return 0


def cmd_list(args: argparse.Namespace) -> int:
  if args.db:
    os.environ["PMGO_MEMORY_DB"] = args.db
  try:
    cfg = load_config()
    items = api.list_issues(cfg, state=args.state, per_page=args.per_page)
    rows = [
      {
        "number": x.get("number"),
        "id": x.get("id"),
        "title": x.get("title"),
        "state": x.get("state"),
        "html_url": x.get("html_url"),
      }
      for x in items
    ]
    _print_json(rows)
  except (OSError, RuntimeError, ValueError) as e:
    print(str(e), file=sys.stderr)
    return 1
  return 0


def cmd_get(args: argparse.Namespace) -> int:
  if args.db:
    os.environ["PMGO_MEMORY_DB"] = args.db
  try:
    cfg = load_config()
    issue = api.get_issue(cfg, args.number)
    _print_json(_issue_public(issue))
  except (OSError, RuntimeError, ValueError) as e:
    print(str(e), file=sys.stderr)
    return 1
  return 0


def _issue_public(issue: dict[str, Any]) -> dict[str, Any]:
  return {
    "id": issue.get("id"),
    "number": issue.get("number"),
    "title": issue.get("title"),
    "state": issue.get("state"),
    "body": issue.get("body"),
    "html_url": issue.get("html_url"),
    "user": (issue.get("user") or {}).get("login"),
  }


def cmd_create(args: argparse.Namespace) -> int:
  if args.db:
    os.environ["PMGO_MEMORY_DB"] = args.db
  try:
    cfg = load_config()
    out = api.create_issue(cfg, title=args.title, body=args.body or "")
    _print_json(_issue_public(out))
  except (OSError, RuntimeError, ValueError) as e:
    print(str(e), file=sys.stderr)
    return 1
  return 0


def cmd_close(args: argparse.Namespace) -> int:
  if args.db:
    os.environ["PMGO_MEMORY_DB"] = args.db
  try:
    cfg = load_config()
    out = api.update_issue(cfg, args.number, state="closed")
    _print_json(_issue_public(out))
  except (OSError, RuntimeError, ValueError) as e:
    print(str(e), file=sys.stderr)
    return 1
  return 0


def cmd_import_task(args: argparse.Namespace) -> int:
  """Create a local pmgo task from a GitHub issue (dedupe by source + external_id)."""
  if args.db:
    os.environ["PMGO_MEMORY_DB"] = args.db
  root = Path(__file__).resolve().parents[3]
  sys.path[:0] = [str(root / "scripts"), str(root / "skills" / "project-core")]
  from project_core.store import default_task_store  # noqa: WPS433

  try:
    cfg = load_config()
    issue = api.get_issue(cfg, args.number)
  except (OSError, RuntimeError, ValueError) as e:
    print(str(e), file=sys.stderr)
    return 1

  title = str(issue.get("title") or f"Issue #{args.number}")
  body = (issue.get("body") or "").strip()
  url = str(issue.get("html_url") or "")
  if url:
    body = f"{body}\n\nGitHub: {url}".strip() if body else f"GitHub: {url}"
  gh_state = str(issue.get("state") or "open")
  status = "done" if gh_state == "closed" else "todo"
  ext_id = str(issue.get("id") or "")

  store = default_task_store()
  try:
    row = store.create_task(
      args.project_id,
      title=title,
      detail=body or None,
      status=status,
      source="github",
      external_id=ext_id,
    )
  except sqlite3.IntegrityError:
    print(
      "A task with this GitHub id already exists for this project (source=github).",
      file=sys.stderr,
    )
    return 1
  _print_json(row)
  return 0


def build_parser() -> argparse.ArgumentParser:
  p = argparse.ArgumentParser(
    prog="github-issues",
    description="GitHub Issues API helper for pmgo (set GITHUB_TOKEN and GITHUB_REPO=owner/name).",
  )
  p.add_argument(
    "--db",
    type=str,
    default=None,
    metavar="PATH",
    help="PMGO_MEMORY_DB path override for import-task (same as other pmgo scripts).",
  )
  s = p.add_subparsers(dest="command", required=True)

  s.add_parser("smoke", help="Verify token and GITHUB_REPO (or skip if unset)").set_defaults(
    _fn=cmd_smoke
  )

  l = s.add_parser("list", help="List issues (excludes pull requests)")
  l.add_argument("--state", default="all", choices=["open", "closed", "all"])
  l.add_argument("--per-page", type=int, default=30, dest="per_page")
  l.set_defaults(_fn=cmd_list)

  g = s.add_parser("get", help="Get one issue by number")
  g.add_argument("number", type=int)
  g.set_defaults(_fn=cmd_get)

  c = s.add_parser("create", help="Create an issue")
  c.add_argument("--title", required=True)
  c.add_argument("--body", default="")
  c.set_defaults(_fn=cmd_create)

  cl = s.add_parser("close", help="Close an issue by number")
  cl.add_argument("number", type=int)
  cl.set_defaults(_fn=cmd_close)

  it = s.add_parser(
    "import-task",
    help="Create a local pmgo task from an issue (source=github, external_id=GitHub id)",
  )
  it.add_argument("--project-id", required=True, dest="project_id")
  it.add_argument("--number", type=int, required=True, dest="number")
  it.set_defaults(_fn=cmd_import_task)

  return p


def main(argv: list[str] | None = None) -> int:
  parser = build_parser()
  args = parser.parse_args(argv if argv is not None else sys.argv[1:])
  fn = args._fn
  return int(fn(args))


if __name__ == "__main__":
  raise SystemExit(main())
