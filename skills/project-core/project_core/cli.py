"""Command-line entry for project-core (dev / smoke tests; future MCP can reuse store)."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from .config import slugify
from .store import default_project_store, default_task_store


def _print_json(data: Any) -> None:
  print(json.dumps(data, indent=2, default=str, ensure_ascii=False))


def build_parser() -> argparse.ArgumentParser:
  p = argparse.ArgumentParser(
    prog="project-core",
    description="List and manage projects and tasks in pmgo local memory (SQLite).",
  )
  p.add_argument(
    "--db",
    type=str,
    default=None,
    metavar="PATH",
    help="Override SQLite path (else PMGO_MEMORY_DB or memory/pmgo.db).",
  )
  sub = p.add_subparsers(dest="command", required=True)

  p_list = sub.add_parser("project-list", help="List projects")
  p_list.set_defaults(_fn=cmd_project_list)

  p_c = sub.add_parser("project-create", help="Create a project")
  p_c.add_argument("--name", required=True)
  p_c.add_argument("--slug", default=None, help="Unique slug; default from name")
  p_c.add_argument("--description", default=None)
  p_c.add_argument("--owner", default=None)
  p_c.set_defaults(_fn=cmd_project_create)

  t_l = sub.add_parser("task-list", help="List tasks for a project")
  t_l.add_argument("--project-id", required=True, dest="project_id")
  t_l.add_argument(
    "--status",
    default=None,
    choices=["todo", "doing", "blocked", "done", "cancelled"],
  )
  t_l.set_defaults(_fn=cmd_task_list)

  t_c = sub.add_parser("task-create", help="Create a task")
  t_c.add_argument("--project-id", required=True, dest="project_id")
  t_c.add_argument("--title", required=True)
  t_c.add_argument("--detail", default=None)
  t_c.add_argument(
    "--status",
    default="todo",
    choices=["todo", "doing", "blocked", "done", "cancelled"],
  )
  t_c.add_argument(
    "--priority",
    default="medium",
    choices=["low", "medium", "high", "critical"],
  )
  t_c.add_argument("--assignee", default=None)
  t_c.add_argument("--due-at", default=None, dest="due_at")
  t_c.add_argument("--milestone-id", default=None, dest="milestone_id")
  t_c.set_defaults(_fn=cmd_task_create)

  t_u = sub.add_parser("task-update", help="Update a task")
  t_u.add_argument("--task-id", required=True, dest="task_id")
  t_u.add_argument("--title", default=None)
  t_u.add_argument("--detail", default=None)
  t_u.add_argument(
    "--status",
    default=None,
    choices=["todo", "doing", "blocked", "done", "cancelled"],
  )
  t_u.add_argument(
    "--priority",
    default=None,
    choices=["low", "medium", "high", "critical"],
  )
  t_u.add_argument("--assignee", default=None)
  t_u.add_argument("--due-at", default=None, dest="due_at")
  t_u.add_argument("--blocked-reason", default=None, dest="blocked_reason")
  t_u.add_argument("--milestone-id", default=None, dest="milestone_id")
  t_u.set_defaults(_fn=cmd_task_update)

  return p


def _apply_db_override(args: argparse.Namespace) -> None:
  if args.db:
    import os
    os.environ["PMGO_MEMORY_DB"] = args.db


def cmd_project_list(args: argparse.Namespace) -> int:
  store = default_project_store()
  _print_json(store.list_projects())
  return 0


def cmd_project_create(args: argparse.Namespace) -> int:
  store = default_project_store()
  slug = args.slug or slugify(args.name)
  row = store.create_project(
    name=args.name,
    slug=slug,
    description=args.description,
    owner=args.owner,
  )
  _print_json(row)
  return 0


def cmd_task_list(args: argparse.Namespace) -> int:
  store = default_task_store()
  _print_json(store.list_tasks(args.project_id, status=args.status))
  return 0


def cmd_task_create(args: argparse.Namespace) -> int:
  store = default_task_store()
  row = store.create_task(
    args.project_id,
    title=args.title,
    detail=args.detail,
    status=args.status,
    priority=args.priority,
    assignee=args.assignee,
    due_at=args.due_at,
    milestone_id=args.milestone_id,
  )
  _print_json(row)
  return 0


def cmd_task_update(args: argparse.Namespace) -> int:
  store = default_task_store()
  try:
    row = store.update_task(
      args.task_id,
      title=args.title,
      detail=args.detail,
      status=args.status,
      priority=args.priority,
      assignee=args.assignee,
      due_at=args.due_at,
      blocked_reason=args.blocked_reason,
      milestone_id=args.milestone_id,
    )
  except KeyError as e:
    print(str(e), file=sys.stderr)
    return 1
  _print_json(row)
  return 0


def main(argv: list[str] | None = None) -> int:
  argv = list(sys.argv[1:] if argv is None else argv)
  parser = build_parser()
  args = parser.parse_args(argv)
  _apply_db_override(args)
  fn = args._fn
  return int(fn(args))


if __name__ == "__main__":
  raise SystemExit(main())
