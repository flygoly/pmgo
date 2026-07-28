#!/usr/bin/env python3
"""Print OpenClaw or Hermes MCP registration snippets for pmgo."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
  sys.path.insert(0, str(SCRIPT_DIR))

from runtime_manager import compatible_python, runtime_python

ROOT = Path(__file__).resolve().parent.parent
MCP_SCRIPT = ROOT / "scripts" / "pmgo_mcp_server.py"
ENV_EXAMPLE = ROOT / "shared" / "mcp.env.example"

# Fallback if shared/mcp.env.example is missing (keep in sync with that file).
_FALLBACK_ENV_KEYS = (
  "PMGO_WORKSPACE",
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
  "FEISHU_APP_ID",
  "FEISHU_APP_SECRET",
  "FEISHU_TASKLIST_GUID",
  "NOTION_TOKEN",
  "NOTION_DATABASE_ID",
  "DINGTALK_APP_KEY",
  "DINGTALK_APP_SECRET",
)

_ENV_KEY_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")


def _repo_root() -> Path:
  override = os.environ.get("PMGO_ROOT", "").strip()
  if override:
    return Path(override).resolve()
  return ROOT


def _python_cmd(root: Path | None = None) -> str:
  return runtime_python(root or _repo_root())


def mcp_env_keys(example_path: Path | None = None) -> list[str]:
  """
  Keys accepted in the MCP `env` block.

  Source of truth: shared/mcp.env.example (active or commented KEY= lines).
  """
  path = example_path or ENV_EXAMPLE
  if not path.is_file():
    return list(_FALLBACK_ENV_KEYS)

  keys: list[str] = []
  seen: set[str] = set()
  for raw in path.read_text(encoding="utf-8").splitlines():
    line = raw.strip()
    if not line:
      continue
    if line.startswith("#"):
      line = line[1:].strip()
    if not line or "=" not in line:
      continue
    key = line.split("=", 1)[0].strip()
    if not _ENV_KEY_RE.match(key) or key in seen:
      continue
    seen.add(key)
    keys.append(key)
  return keys or list(_FALLBACK_ENV_KEYS)


def _mcp_env(root: Path) -> dict[str, str]:
  """Pass through non-empty process env for keys listed in mcp.env.example."""
  env: dict[str, str] = {"PMGO_WORKSPACE": str(root)}
  for key in mcp_env_keys():
    if key == "PMGO_WORKSPACE":
      continue
    val = os.environ.get(key, "").strip()
    if val:
      env[key] = val
  return env


def render_openclaw(root: Path) -> str:
  payload = {
    "command": _python_cmd(root),
    "args": [str(MCP_SCRIPT)],
    "env": _mcp_env(root),
  }
  lines = [
    "# OpenClaw: register pmgo MCP server",
    f"# Env keys from shared/mcp.env.example (export them before running this).",
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
        "command": _python_cmd(root),
        "args": [str(MCP_SCRIPT)],
        "env": _mcp_env(root),
      }
    }
  }
  lines = [
    "# Hermes: merge into ~/.hermes/config.yaml",
    "# Env keys from shared/mcp.env.example (export them before generating).",
    "# Restart gateway or start a new session after editing.",
    yaml.dump(snippet, default_flow_style=False, sort_keys=False),
  ]
  return "\n".join(lines)


def main() -> int:
  if sys.version_info < (3, 11):
    try:
      python = compatible_python()
    except RuntimeError as exc:
      print(f"ERROR: {exc}", file=sys.stderr)
      return 1
    print(f"# Re-running with supported interpreter: {python}", file=sys.stderr, flush=True)
    os.execv(python, [python, str(Path(__file__).resolve()), *sys.argv[1:]])
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
