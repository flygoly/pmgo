"""CLI for Feishu: smoke / list tasklist tasks / get / import-task."""

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


def _default_tasklist() -> str:
  return (os.environ.get("FEISHU_TASKLIST_GUID") or "").strip()


def cmd_smoke(_args: argparse.Namespace) -> int:
  if not (os.environ.get("FEISHU_APP_ID") or "").strip() or not (
    os.environ.get("FEISHU_APP_SECRET") or ""
  ).strip():
    print("SKIP: FEISHU_APP_ID / FEISHU_APP_SECRET not set (Feishu smoke skipped).", file=sys.stderr)
    return 0
  try:
    cfg = load_config()
    out = api.tenant_access_token(cfg)
    _print_json(
      {
        "ok": True,
        "expire": out.get("expire"),
        "has_token": bool(out.get("tenant_access_token")),
      }
    )
  except (OSError, RuntimeError) as e:
    print(str(e), file=sys.stderr)
    return 1
  return 0


def cmd_list(args: argparse.Namespace) -> int:
  try:
    cfg = load_config()
    guid = (args.tasklist_guid or _default_tasklist()).strip()
    if not guid:
      raise OSError("Set FEISHU_TASKLIST_GUID or pass --tasklist-guid")
    data = api.list_tasklist_tasks(cfg, guid, page_size=args.page_size)
    items = data.get("items") or data.get("tasks") or []
    if not isinstance(items, list):
      items = []
    # items may be {guid, summary} stubs or full tasks
    public = []
    for raw in items:
      if not isinstance(raw, dict):
        continue
      if raw.get("summary") or raw.get("description"):
        public.append(api.task_to_public(raw))
      else:
        tg = str(raw.get("guid") or raw.get("id") or "")
        if tg:
          public.append({"guid": tg, "summary": raw.get("summary")})
    _print_json(
      {
        "tasklist_guid": guid,
        "items": public,
        "has_more": data.get("has_more"),
        "page_token": data.get("page_token"),
      }
    )
  except (OSError, RuntimeError, ValueError) as e:
    print(str(e), file=sys.stderr)
    return 1
  return 0


def cmd_get(args: argparse.Namespace) -> int:
  try:
    cfg = load_config()
    task = api.get_task(cfg, args.task_guid)
    _print_json(api.task_to_public(task))
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
    task = api.get_task(cfg, args.task_guid)
  except (OSError, RuntimeError, ValueError) as e:
    print(str(e), file=sys.stderr)
    return 1

  pub = api.task_to_public(task)
  title = str(pub.get("summary") or pub.get("guid") or "Feishu task")
  body = (pub.get("description") or "").strip() if pub.get("description") else ""
  url = str(pub.get("url") or "")
  if url:
    body = f"{body}\n\nFeishu: {url}".strip() if body else f"Feishu: {url}"
  status = str(pub.get("status") or "todo")
  ext_id = str(pub.get("guid") or "")
  if not ext_id:
    print("Feishu task missing guid", file=sys.stderr)
    return 1

  store = default_task_store()
  try:
    row = store.create_task(
      args.project_id,
      title=title,
      detail=body or None,
      status=status,
      source="feishu",
      external_id=ext_id,
    )
  except sqlite3.IntegrityError:
    print(
      "A task with this Feishu guid already exists for this project (source=feishu).",
      file=sys.stderr,
    )
    return 1
  _print_json(row)
  return 0


def main(argv: list[str] | None = None) -> int:
  p = argparse.ArgumentParser(prog="feishu-issues", description="Feishu task helper for pmgo.")
  p.add_argument("--db", type=str, default=None, metavar="PATH")
  s = p.add_subparsers(dest="command", required=True)
  s.add_parser("smoke", help="Fetch tenant_access_token (or skip if unset)").set_defaults(
    _fn=cmd_smoke
  )
  l = s.add_parser("list", help="List tasks in a tasklist (app must be a member)")
  l.add_argument("--tasklist-guid", default=None, dest="tasklist_guid")
  l.add_argument("--page-size", type=int, default=50, dest="page_size")
  l.set_defaults(_fn=cmd_list)
  g = s.add_parser("get", help="Get one task by guid")
  g.add_argument("task_guid", type=str)
  g.set_defaults(_fn=cmd_get)
  it = s.add_parser("import-task", help="Import Feishu task into local SQLite")
  it.add_argument("--project-id", required=True, dest="project_id")
  it.add_argument("--task-guid", required=True, dest="task_guid")
  it.set_defaults(_fn=cmd_import_task)
  args = p.parse_args(argv if argv is not None else sys.argv[1:])
  return int(args._fn(args))


if __name__ == "__main__":
  raise SystemExit(main())
