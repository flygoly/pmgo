#!/usr/bin/env python3
"""Print OpenClaw or Hermes MCP registration snippets for pmgo."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MCP_SCRIPT = ROOT / "scripts" / "pmgo_mcp_server.py"


def _repo_root() -> Path:
  override = os.environ.get("PMGO_ROOT", "").strip()
  if override:
    return Path(override).resolve()
  return ROOT


def _python_cmd() -> str:
  return shutil.which("python3") or "python3"


def _mcp_env(root: Path) -> dict[str, str]:
  env: dict[str, str] = {"PMGO_WORKSPACE": str(root)}
  for key in (
    "PMGO_DEFAULT_PROJECT_ID",
    "PMGO_DEFAULT_LOCALE",
    "PMGO_MEMORY_DB",
    "GITHUB_TOKEN",
    "GITHUB_REPO",
    "LINEAR_API_KEY",
    "JIRA_BASE_URL",
    "JIRA_EMAIL",
    "JIRA_API_TOKEN",
    "JIRA_PROJECT",
  ):
    val = os.environ.get(key, "").strip()
    if val:
      env[key] = val
  return env


def render_openclaw(root: Path) -> str:
  payload = {
    "command": _python_cmd(),
    "args": [str(MCP_SCRIPT)],
    "env": _mcp_env(root),
  }
  lines = [
    "# OpenClaw: register pmgo MCP server",
    f"export PMGO_ROOT={root}",
    f'openclaw mcp set pmgo {json.dumps(payload)}',
    "openclaw mcp show pmgo --json",
  ]
  return "\n".join(lines) + "\n"


def render_hermes(root: Path) -> str:
  import yaml  # noqa: WPS433 — optional dep; same as MCP stack

  snippet = {
    "mcp_servers": {
      "pmgo": {
        "command": _python_cmd(),
        "args": [str(MCP_SCRIPT)],
        "env": _mcp_env(root),
      }
    }
  }
  lines = [
    "# Hermes: merge into ~/.hermes/config.yaml",
    "# Restart gateway or start a new session after editing.",
    yaml.dump(snippet, default_flow_style=False, sort_keys=False),
  ]
  return "\n".join(lines)


def main() -> int:
  parser = argparse.ArgumentParser(
    description="Print MCP registration snippets for OpenClaw or Hermes.",
  )
  parser.add_argument(
    "--runtime",
    choices=["openclaw", "hermes"],
    required=True,
    help="Target gateway runtime.",
  )
  parser.add_argument(
    "--root",
    type=Path,
    default=None,
    help="pmgo repo root (default: repo containing this script or PMGO_ROOT).",
  )
  args = parser.parse_args()
  root = (args.root or _repo_root()).resolve()
  if not MCP_SCRIPT.is_file():
    print(f"ERROR: MCP script not found: {MCP_SCRIPT}", file=sys.stderr)
    return 1

  if args.runtime == "openclaw":
    print(render_openclaw(root), end="")
    return 0

  try:
    import yaml  # noqa: F401
  except ImportError:
    print(
      "ERROR: PyYAML required for Hermes output (pip install pyyaml)",
      file=sys.stderr,
    )
    return 1
  print(render_hermes(root), end="")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
