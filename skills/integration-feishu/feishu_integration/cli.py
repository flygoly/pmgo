"""CLI for Feishu scaffold."""

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


def main(argv: list[str] | None = None) -> int:
  p = argparse.ArgumentParser(prog="feishu-issues", description="Feishu scaffold for pmgo.")
  s = p.add_subparsers(dest="command", required=True)
  s.add_parser("smoke", help="Fetch tenant_access_token (or skip if unset)").set_defaults(
    _fn=cmd_smoke
  )
  args = p.parse_args(argv if argv is not None else sys.argv[1:])
  return int(args._fn(args))


if __name__ == "__main__":
  raise SystemExit(main())
