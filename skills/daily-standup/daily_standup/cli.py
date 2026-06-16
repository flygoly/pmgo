"""CLI for daily standup / daily report."""

from __future__ import annotations

import argparse
import os
import sys
from typing import Any

import pmgo_common  # type: ignore

from . import build as buildmod


def build_parser() -> argparse.ArgumentParser:
  p = argparse.ArgumentParser(
    prog="daily-standup",
    description="Render a daily project report (Markdown) from local SQLite state.",
  )
  p.add_argument(
    "--db",
    type=str,
    default=None,
    metavar="PATH",
    help="Override SQLite path (else PMGO_MEMORY_DB or memory/pmgo.db).",
  )
  s = p.add_subparsers(dest="command", required=True)
  r = s.add_parser("report", help="Print Markdown report to stdout")
  r.add_argument("--project-id", default=None, dest="project_id")
  r.add_argument(
    "--locale",
    default=None,
    choices=["en", "zh-CN", "zh-TW"],
    help="Report locale (default: PMGO_DEFAULT_LOCALE or en).",
  )
  r.add_argument(
    "--from-first-project",
    action="store_true",
    help="Use the first project in the DB; if none, print a short message and exit 0 (smoke test).",
  )
  r.set_defaults(_fn=cmd_report)
  return p


def cmd_report(args: Any) -> int:
  if args.db:
    os.environ["PMGO_MEMORY_DB"] = args.db
  pid = pmgo_common.resolve_project_id(
    explicit=args.project_id,
    from_first=args.from_first_project,
  )
  if pid is None and args.from_first_project:
    print("No projects in database; skip daily report (smoke OK).", file=sys.stderr)
    return 0
  if not pid:
    print(
      "--project-id is required unless --from-first-project is set or "
      "PMGO_DEFAULT_PROJECT_ID is configured",
      file=sys.stderr,
    )
    return 1
  locale = args.locale or pmgo_common.default_locale()
  try:
    text = buildmod.build_daily_markdown(project_id=pid, locale=locale)
  except (KeyError, FileNotFoundError) as e:
    print(str(e), file=sys.stderr)
    return 1
  print(text, end="")
  return 0


def main(argv: list[str] | None = None) -> int:
  parser = build_parser()
  args = parser.parse_args(argv if argv is not None else sys.argv[1:])
  fn = args._fn
  return int(fn(args))


if __name__ == "__main__":
  raise SystemExit(main())
