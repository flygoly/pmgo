"""CLI for DingTalk scaffold."""

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
  if not (os.environ.get("DINGTALK_APP_KEY") or "").strip() or not (
    os.environ.get("DINGTALK_APP_SECRET") or ""
  ).strip():
    print(
      "SKIP: DINGTALK_APP_KEY / DINGTALK_APP_SECRET not set (DingTalk smoke skipped).",
      file=sys.stderr,
    )
    return 0
  try:
    cfg = load_config()
    out = api.get_access_token(cfg)
    _print_json(
      {
        "ok": True,
        "expires_in": out.get("expires_in"),
        "has_token": bool(out.get("access_token")),
      }
    )
  except (OSError, RuntimeError) as e:
    print(str(e), file=sys.stderr)
    return 1
  return 0


def main(argv: list[str] | None = None) -> int:
  p = argparse.ArgumentParser(prog="dingtalk-issues", description="DingTalk scaffold for pmgo.")
  s = p.add_subparsers(dest="command", required=True)
  s.add_parser("smoke", help="Fetch access_token (or skip if unset)").set_defaults(_fn=cmd_smoke)
  args = p.parse_args(argv if argv is not None else sys.argv[1:])
  return int(args._fn(args))


if __name__ == "__main__":
  raise SystemExit(main())
