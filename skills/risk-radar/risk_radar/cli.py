"""CLI for risk-radar scan (JSON to stdout)."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

import pmgo_common  # type: ignore

from . import scan as scanmod


def _j(data: object) -> str:
  return json.dumps(data, indent=2, default=str, ensure_ascii=False)


def _first_project_id() -> str | None:
  conn = pmgo_common.connect_db(pmgo_common.db_path())
  try:
    row = conn.execute("SELECT id FROM projects ORDER BY created_at LIMIT 1").fetchone()
  finally:
    conn.close()
  if row is None:
    return None
  return str(row[0])


def cmd_report(args: Any) -> int:
  if args.db:
    os.environ["PMGO_MEMORY_DB"] = args.db
  pid: str | None = args.project_id
  if args.from_first_project:
    pid = _first_project_id()
    if pid is None:
      print("No projects in database; skip risk scan (smoke OK).", file=sys.stderr)
      return 0
  if not pid:
    print("--project-id is required unless --from-first-project is set", file=sys.stderr)
    return 1
  try:
    out = scanmod.scan_project(pid)
  except KeyError as e:
    print(str(e), file=sys.stderr)
    return 1
  print(_j(out), end="")
  return 0


def build_parser() -> argparse.ArgumentParser:
  p = argparse.ArgumentParser(
    prog="risk-radar",
    description="List open/watching risks and blocked tasks for a project (local SQLite).",
  )
  p.add_argument(
    "--db",
    type=str,
    default=None,
    metavar="PATH",
    help="Override SQLite path (else PMGO_MEMORY_DB or memory/pmgo.db).",
  )
  s = p.add_subparsers(dest="command", required=True)
  r = s.add_parser("report", help="Print JSON scan to stdout")
  r.add_argument("--project-id", default=None, dest="project_id")
  r.add_argument(
    "--from-first-project",
    action="store_true",
    help="Use the first project; if none, exit 0 (smoke).",
  )
  r.set_defaults(_fn=cmd_report)
  return p


def main(argv: list[str] | None = None) -> int:
  parser = build_parser()
  args = parser.parse_args(argv if argv is not None else sys.argv[1:])
  return int(args._fn(args))


if __name__ == "__main__":
  raise SystemExit(main())
