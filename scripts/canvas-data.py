#!/usr/bin/env python3
"""CLI for Live Canvas JSON snapshots."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for d in (ROOT / "scripts", ROOT / "skills" / "canvas-data"):
  p = str(d)
  if p not in sys.path:
    sys.path.insert(0, p)

import pmgo_common  # noqa: E402
from canvas_data.build import build_burndown, build_gantt, build_snapshot  # noqa: E402


def _print(data: object) -> None:
  print(json.dumps(data, indent=2, default=str, ensure_ascii=False))


def _resolve(args: argparse.Namespace) -> str | None:
  return pmgo_common.resolve_project_id(
    explicit=getattr(args, "project_id", None),
    from_first=bool(getattr(args, "from_first_project", False)),
  )


def _run_build(args: argparse.Namespace, builder) -> int:
  pid = _resolve(args)
  if not pid:
    if getattr(args, "from_first_project", False):
      print("No projects in database; skip canvas export (smoke OK).", file=sys.stderr)
      return 0
    print(
      "project_id required (or PMGO_DEFAULT_PROJECT_ID / --from-first-project)",
      file=sys.stderr,
    )
    return 1
  try:
    _print(builder(pid))
  except KeyError as e:
    print(str(e), file=sys.stderr)
    return 1
  return 0


def main(argv: list[str] | None = None) -> int:
  p = argparse.ArgumentParser(prog="canvas-data", description="pmgo Live Canvas JSON export")
  s = p.add_subparsers(dest="command", required=True)

  def add_project(sp: argparse.ArgumentParser) -> None:
    sp.add_argument("--project-id", default=None, dest="project_id")
    sp.add_argument("--from-first-project", action="store_true")

  g = s.add_parser("gantt")
  add_project(g)
  g.set_defaults(_fn=lambda a: _run_build(a, build_gantt))

  b = s.add_parser("burndown")
  add_project(b)
  b.set_defaults(_fn=lambda a: _run_build(a, build_burndown))

  snap = s.add_parser("snapshot")
  add_project(snap)
  snap.set_defaults(_fn=lambda a: _run_build(a, build_snapshot))

  args = p.parse_args(argv if argv is not None else sys.argv[1:])
  return int(args._fn(args))


if __name__ == "__main__":
  raise SystemExit(main())
