"""Command-line entry for project-core (dev / smoke tests; future MCP can reuse store)."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from .config import slugify
from .memory_md import scaffold_project_markdown
from .store import (
  default_decision_store,
  default_milestone_store,
  default_people_store,
  default_project_store,
  default_retrospective_store,
  default_risk_store,
  default_task_store,
)


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
  p_c.add_argument(
    "--scaffold-markdown",
    action="store_true",
    help="Also create memory/projects/<slug>/ markdown templates.",
  )
  p_c.add_argument(
    "--locale",
    default="en",
    choices=["en", "zh-CN", "zh-TW"],
    help="Locale for markdown scaffold when --scaffold-markdown is set.",
  )
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

  m_l = sub.add_parser("milestone-list", help="List milestones for a project")
  m_l.add_argument("--project-id", required=True, dest="project_id")
  m_l.set_defaults(_fn=cmd_milestone_list)

  m_c = sub.add_parser("milestone-create", help="Create a milestone")
  m_c.add_argument("--project-id", required=True, dest="project_id")
  m_c.add_argument("--title", required=True)
  m_c.add_argument(
    "--status",
    default="todo",
    choices=["todo", "doing", "done", "cancelled"],
  )
  m_c.add_argument("--owner", default=None)
  m_c.add_argument("--due-at", default=None, dest="due_at")
  m_c.set_defaults(_fn=cmd_milestone_create)

  m_u = sub.add_parser("milestone-update", help="Update a milestone")
  m_u.add_argument("--milestone-id", required=True, dest="milestone_id")
  m_u.add_argument("--title", default=None)
  m_u.add_argument(
    "--status",
    default=None,
    choices=["todo", "doing", "done", "cancelled"],
  )
  m_u.add_argument("--owner", default=None)
  m_u.add_argument("--due-at", default=None, dest="due_at")
  m_u.set_defaults(_fn=cmd_milestone_update)

  r_l = sub.add_parser("risk-list", help="List risks for a project")
  r_l.add_argument("--project-id", required=True, dest="project_id")
  r_l.add_argument(
    "--status",
    default=None,
    choices=["open", "watching", "mitigated", "closed"],
  )
  r_l.set_defaults(_fn=cmd_risk_list)

  r_c = sub.add_parser("risk-create", help="Create a risk")
  r_c.add_argument("--project-id", required=True, dest="project_id")
  r_c.add_argument("--title", required=True)
  r_c.add_argument(
    "--severity",
    default="medium",
    choices=["low", "medium", "high", "critical"],
  )
  r_c.add_argument(
    "--status",
    default="open",
    choices=["open", "watching", "mitigated", "closed"],
  )
  r_c.add_argument("--owner", default=None)
  r_c.add_argument("--evidence", default=None)
  r_c.add_argument("--mitigation-plan", default=None, dest="mitigation_plan")
  r_c.set_defaults(_fn=cmd_risk_create)

  r_u = sub.add_parser("risk-update", help="Update a risk")
  r_u.add_argument("--risk-id", required=True, dest="risk_id")
  r_u.add_argument("--title", default=None)
  r_u.add_argument(
    "--severity",
    default=None,
    choices=["low", "medium", "high", "critical"],
  )
  r_u.add_argument(
    "--status",
    default=None,
    choices=["open", "watching", "mitigated", "closed"],
  )
  r_u.add_argument("--owner", default=None)
  r_u.add_argument("--evidence", default=None)
  r_u.add_argument("--mitigation-plan", default=None, dest="mitigation_plan")
  r_u.set_defaults(_fn=cmd_risk_update)

  d_l = sub.add_parser("decision-list", help="List decisions for a project")
  d_l.add_argument("--project-id", required=True, dest="project_id")
  d_l.add_argument(
    "--status",
    default=None,
    choices=["proposed", "accepted", "rejected", "superseded"],
  )
  d_l.set_defaults(_fn=cmd_decision_list)

  d_c = sub.add_parser("decision-create", help="Create a decision (ADR)")
  d_c.add_argument("--project-id", required=True, dest="project_id")
  d_c.add_argument("--title", required=True)
  d_c.add_argument(
    "--status",
    default="proposed",
    choices=["proposed", "accepted", "rejected", "superseded"],
  )
  d_c.add_argument("--rationale", default=None)
  d_c.add_argument("--alternatives", default=None)
  d_c.add_argument("--evidence", default=None)
  d_c.add_argument("--decided-by", default=None, dest="decided_by")
  d_c.add_argument("--decided-at", default=None, dest="decided_at")
  d_c.set_defaults(_fn=cmd_decision_create)

  d_u = sub.add_parser("decision-update", help="Update a decision")
  d_u.add_argument("--decision-id", required=True, dest="decision_id")
  d_u.add_argument("--title", default=None)
  d_u.add_argument(
    "--status",
    default=None,
    choices=["proposed", "accepted", "rejected", "superseded"],
  )
  d_u.add_argument("--rationale", default=None)
  d_u.add_argument("--alternatives", default=None)
  d_u.add_argument("--evidence", default=None)
  d_u.add_argument("--decided-by", default=None, dest="decided_by")
  d_u.add_argument("--decided-at", default=None, dest="decided_at")
  d_u.set_defaults(_fn=cmd_decision_update)

  pe_l = sub.add_parser("people-list", help="List people (roster)")
  pe_l.set_defaults(_fn=cmd_people_list)

  pe_c = sub.add_parser("people-create", help="Create a person")
  pe_c.add_argument("--name", required=True)
  pe_c.add_argument("--role", default=None)
  pe_c.add_argument("--contact", default=None)
  pe_c.set_defaults(_fn=cmd_people_create)

  pe_u = sub.add_parser("people-update", help="Update a person")
  pe_u.add_argument("--person-id", required=True, dest="person_id")
  pe_u.add_argument("--name", default=None)
  pe_u.add_argument("--role", default=None)
  pe_u.add_argument("--contact", default=None)
  pe_u.set_defaults(_fn=cmd_people_update)

  re_l = sub.add_parser("retro-list", help="List retrospectives for a project")
  re_l.add_argument("--project-id", required=True, dest="project_id")
  re_l.set_defaults(_fn=cmd_retro_list)

  re_c = sub.add_parser("retro-create", help="Create a retrospective")
  re_c.add_argument("--project-id", required=True, dest="project_id")
  re_c.add_argument("--period", required=True, help="e.g. 2026-W28 or 2026-Q3")
  re_c.add_argument("--summary", default=None)
  re_c.add_argument("--action-items", default=None, dest="action_items")
  re_c.set_defaults(_fn=cmd_retro_create)

  re_u = sub.add_parser("retro-update", help="Update a retrospective")
  re_u.add_argument("--retrospective-id", required=True, dest="retrospective_id")
  re_u.add_argument("--period", default=None)
  re_u.add_argument("--summary", default=None)
  re_u.add_argument("--action-items", default=None, dest="action_items")
  re_u.set_defaults(_fn=cmd_retro_update)

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
  if args.scaffold_markdown:
    try:
      memory_dir = scaffold_project_markdown(
        name=args.name,
        slug=slug,
        locale=args.locale,
      )
      row = {**row, "memory_dir": str(memory_dir)}
    except (ValueError, FileNotFoundError) as e:
      print(str(e), file=sys.stderr)
      return 1
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


def cmd_milestone_list(args: argparse.Namespace) -> int:
  store = default_milestone_store()
  _print_json(store.list_milestones(args.project_id))
  return 0


def cmd_milestone_create(args: argparse.Namespace) -> int:
  store = default_milestone_store()
  row = store.create_milestone(
    args.project_id,
    title=args.title,
    status=args.status,
    owner=args.owner,
    due_at=args.due_at,
  )
  _print_json(row)
  return 0


def cmd_milestone_update(args: argparse.Namespace) -> int:
  store = default_milestone_store()
  try:
    row = store.update_milestone(
      args.milestone_id,
      title=args.title,
      status=args.status,
      owner=args.owner,
      due_at=args.due_at,
    )
  except KeyError as e:
    print(str(e), file=sys.stderr)
    return 1
  _print_json(row)
  return 0


def cmd_risk_list(args: argparse.Namespace) -> int:
  store = default_risk_store()
  _print_json(store.list_risks(args.project_id, status=args.status))
  return 0


def cmd_risk_create(args: argparse.Namespace) -> int:
  store = default_risk_store()
  row = store.create_risk(
    args.project_id,
    title=args.title,
    severity=args.severity,
    status=args.status,
    owner=args.owner,
    evidence=args.evidence,
    mitigation_plan=args.mitigation_plan,
  )
  _print_json(row)
  return 0


def cmd_risk_update(args: argparse.Namespace) -> int:
  store = default_risk_store()
  try:
    row = store.update_risk(
      args.risk_id,
      title=args.title,
      severity=args.severity,
      status=args.status,
      owner=args.owner,
      evidence=args.evidence,
      mitigation_plan=args.mitigation_plan,
    )
  except KeyError as e:
    print(str(e), file=sys.stderr)
    return 1
  _print_json(row)
  return 0


def cmd_decision_list(args: argparse.Namespace) -> int:
  store = default_decision_store()
  _print_json(store.list_decisions(args.project_id, status=args.status))
  return 0


def cmd_decision_create(args: argparse.Namespace) -> int:
  store = default_decision_store()
  row = store.create_decision(
    args.project_id,
    title=args.title,
    status=args.status,
    rationale=args.rationale,
    alternatives=args.alternatives,
    evidence=args.evidence,
    decided_by=args.decided_by,
    decided_at=args.decided_at,
  )
  _print_json(row)
  return 0


def cmd_decision_update(args: argparse.Namespace) -> int:
  store = default_decision_store()
  try:
    row = store.update_decision(
      args.decision_id,
      title=args.title,
      status=args.status,
      rationale=args.rationale,
      alternatives=args.alternatives,
      evidence=args.evidence,
      decided_by=args.decided_by,
      decided_at=args.decided_at,
    )
  except KeyError as e:
    print(str(e), file=sys.stderr)
    return 1
  _print_json(row)
  return 0


def cmd_people_list(_args: argparse.Namespace) -> int:
  _print_json(default_people_store().list_people())
  return 0


def cmd_people_create(args: argparse.Namespace) -> int:
  row = default_people_store().create_person(
    name=args.name,
    role=args.role,
    contact=args.contact,
  )
  _print_json(row)
  return 0


def cmd_people_update(args: argparse.Namespace) -> int:
  try:
    row = default_people_store().update_person(
      args.person_id,
      name=args.name,
      role=args.role,
      contact=args.contact,
    )
  except KeyError as e:
    print(str(e), file=sys.stderr)
    return 1
  _print_json(row)
  return 0


def cmd_retro_list(args: argparse.Namespace) -> int:
  _print_json(default_retrospective_store().list_retrospectives(args.project_id))
  return 0


def cmd_retro_create(args: argparse.Namespace) -> int:
  row = default_retrospective_store().create_retrospective(
    args.project_id,
    period=args.period,
    summary=args.summary,
    action_items=args.action_items,
  )
  _print_json(row)
  return 0


def cmd_retro_update(args: argparse.Namespace) -> int:
  try:
    row = default_retrospective_store().update_retrospective(
      args.retrospective_id,
      period=args.period,
      summary=args.summary,
      action_items=args.action_items,
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
