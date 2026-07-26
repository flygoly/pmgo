#!/usr/bin/env python3
"""Render pmgo Live Canvas HTML for OpenClaw canvasHost.root."""

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
from canvas_data.render import default_out_dir, render_canvas  # noqa: E402


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(
    description="Build OpenClaw Live Canvas HTML + data.json from pmgo SQLite.",
  )
  parser.add_argument("--project-id", default=None, dest="project_id")
  parser.add_argument("--from-first-project", action="store_true")
  parser.add_argument(
    "--out",
    type=Path,
    default=None,
    help=f"Output directory (default: {default_out_dir()})",
  )
  parser.add_argument(
    "--no-inline",
    action="store_true",
    help="Do not embed snapshot into index.html (load data.json only).",
  )
  args = parser.parse_args(argv if argv is not None else sys.argv[1:])

  pid = pmgo_common.resolve_project_id(
    explicit=args.project_id,
    from_first=args.from_first_project,
  )
  if not pid:
    if args.from_first_project:
      print("No projects in database; skip canvas render (smoke OK).", file=sys.stderr)
      return 0
    print(
      "project_id required (or PMGO_DEFAULT_PROJECT_ID / --from-first-project)",
      file=sys.stderr,
    )
    return 1

  try:
    result = render_canvas(
      pid,
      out_dir=args.out,
      inline=not args.no_inline,
    )
  except (FileNotFoundError, KeyError, ValueError) as e:
    print(str(e), file=sys.stderr)
    return 1

  print(json.dumps(result, indent=2, ensure_ascii=False))
  notes = result.get("runtime_notes") or {}
  print("\nNext steps by runtime:", file=sys.stderr)
  if notes.get("openclaw"):
    print(f"  OpenClaw: {notes['openclaw']}", file=sys.stderr)
  if notes.get("hermes"):
    print(f"  Hermes:   {notes['hermes']}", file=sys.stderr)
  print(f"  Docs:     docs/LIVE_CANVAS.md · out_dir={result.get('out_dir')}\n", file=sys.stderr)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
