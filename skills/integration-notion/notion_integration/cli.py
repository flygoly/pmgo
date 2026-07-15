"""CLI for Notion scaffold."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

from . import api
from .config import load_config


def _print_json(data: Any) -> None:
  print(json.dumps(data, indent=2, default=str, ensure_ascii=False))


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


def main(argv: list[str] | None = None) -> int:
  p = argparse.ArgumentParser(prog="notion-issues", description="Notion scaffold for pmgo.")
  s = p.add_subparsers(dest="command", required=True)
  s.add_parser("smoke", help="GET /v1/users/me (or skip if unset)").set_defaults(_fn=cmd_smoke)
  args = p.parse_args(argv if argv is not None else sys.argv[1:])
  return int(args._fn(args))


if __name__ == "__main__":
  raise SystemExit(main())
