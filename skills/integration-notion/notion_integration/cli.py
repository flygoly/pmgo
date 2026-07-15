"""CLI for Notion: smoke / list database / get page / import-task."""

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


def _default_database() -> str:
  return (os.environ.get("NOTION_DATABASE_ID") or "").strip()


def cmd_smoke(_args: argparse.Namespace) -> int:
  if not (os.environ.get("NOTION_TOKEN") or "").strip():
    print("SKIP: NOTION_TOKEN not set (Notion smoke skipped).", file=sys.stderr)
    return 0
  try:
    cfg = load_config()
    me = api.users_me(cfg)
    _print_json({"ok": True, "id": me.get("id"), "type": me.get("type"), "name": me.get("name")})
  except (OSError, RuntimeError) as e:
    print(str(e), file=sys.stderr)
    return 1
  return 0


def cmd_list(args: argparse.Namespace) -> int:
  try:
    cfg = load_config()
    db = (args.database_id or _default_database()).strip()
    if not db:
      raise OSError("Set NOTION_DATABASE_ID or pass --database-id")
    pages = api.list_database_pages(cfg, db, page_size=args.page_size)
    _print_json([api.page_public(p) for p in pages])
  except (OSError, RuntimeError, ValueError) as e:
    print(str(e), file=sys.stderr)
    return 1
  return 0


def cmd_get(args: argparse.Namespace) -> int:
  try:
    cfg = load_config()
    page = api.get_page(cfg, args.page_id)
    _print_json(api.page_public(page))
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
    page = api.get_page(cfg, args.page_id)
  except (OSError, RuntimeError, ValueError) as e:
    print(str(e), file=sys.stderr)
    return 1

  pub = api.page_public(page)
  title = str(pub.get("title") or "Notion page")
  url = str(pub.get("url") or "")
  body = f"Notion: {url}" if url else None
  ext_id = str(pub.get("id") or "").replace("-", "")
  if not ext_id:
    print("Notion page missing id", file=sys.stderr)
    return 1

  store = default_task_store()
  try:
    row = store.create_task(
      args.project_id,
      title=title,
      detail=body,
      status=str(pub.get("status") or "todo"),
      source="notion",
      external_id=ext_id,
    )
  except sqlite3.IntegrityError:
    print(
      "A task with this Notion page id already exists for this project (source=notion).",
      file=sys.stderr,
    )
    return 1
  _print_json(row)
  return 0


def main(argv: list[str] | None = None) -> int:
  p = argparse.ArgumentParser(prog="notion-issues", description="Notion helper for pmgo.")
  p.add_argument("--db", type=str, default=None, metavar="PATH")
  s = p.add_subparsers(dest="command", required=True)
  s.add_parser("smoke", help="GET /v1/users/me (or skip if unset)").set_defaults(_fn=cmd_smoke)
  l = s.add_parser("list", help="Query pages in a database")
  l.add_argument("--database-id", default=None, dest="database_id")
  l.add_argument("--page-size", type=int, default=50, dest="page_size")
  l.set_defaults(_fn=cmd_list)
  g = s.add_parser("get", help="Get one page by id")
  g.add_argument("page_id", type=str)
  g.set_defaults(_fn=cmd_get)
  it = s.add_parser("import-task", help="Import Notion page into local SQLite")
  it.add_argument("--project-id", required=True, dest="project_id")
  it.add_argument("--page-id", required=True, dest="page_id")
  it.set_defaults(_fn=cmd_import_task)
  args = p.parse_args(argv if argv is not None else sys.argv[1:])
  return int(args._fn(args))


if __name__ == "__main__":
  raise SystemExit(main())
