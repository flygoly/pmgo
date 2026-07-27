#!/usr/bin/env python3
"""Policy-gated stdio MCP entry point for pmgo domain tools."""

from __future__ import annotations

import os
import sys
from pathlib import Path


_ROOT = Path(__file__).resolve().parent.parent
if workspace := (os.environ.get("PMGO_WORKSPACE") or "").strip():
  override = Path(workspace).resolve()
  if override.is_dir():
    _ROOT = override

for directory in (
  _ROOT / "scripts",
  _ROOT / "skills" / "project-core",
  _ROOT / "skills" / "daily-standup",
  _ROOT / "skills" / "weekly-report",
  _ROOT / "skills" / "integration-github",
  _ROOT / "skills" / "risk-radar",
  _ROOT / "skills" / "integration-linear",
  _ROOT / "skills" / "integration-jira",
  _ROOT / "skills" / "integration-feishu",
  _ROOT / "skills" / "integration-notion",
  _ROOT / "skills" / "canvas-data",
):
  path = str(directory)
  if path not in sys.path:
    sys.path.insert(0, path)

try:
  from pmgo_mcp_tools.context import gate, mcp
except RuntimeError as exc:
  print(f"ERROR: {exc}", file=sys.stderr)
  raise SystemExit(1) from exc

# Importing each module registers its decorated functions on the shared MCP
# instance. Wildcard re-exports preserve the original direct-call API used by
# tests and trusted local callers.
from pmgo_mcp_tools.canvas import *  # noqa: E402,F403
from pmgo_mcp_tools.collaboration import *  # noqa: E402,F403
from pmgo_mcp_tools.core import *  # noqa: E402,F403
from pmgo_mcp_tools.feishu import *  # noqa: E402,F403
from pmgo_mcp_tools.governance import *  # noqa: E402,F403
from pmgo_mcp_tools.github import *  # noqa: E402,F403
from pmgo_mcp_tools.jira import *  # noqa: E402,F403
from pmgo_mcp_tools.linear import *  # noqa: E402,F403
from pmgo_mcp_tools.milestones import *  # noqa: E402,F403
from pmgo_mcp_tools.notion import *  # noqa: E402,F403
from pmgo_mcp_tools.reports import *  # noqa: E402,F403


def main() -> None:
  os.environ.setdefault("PMGO_WORKSPACE", str(_ROOT))
  try:
    os.chdir(_ROOT)
  except OSError:
    pass
  run = getattr(mcp, "run", None)
  if not callable(run):
    raise SystemExit("FastMCP instance has no .run(); install mcp: pip install mcp pyyaml")
  try:
    run(transport="stdio")
  except TypeError:
    run()


if __name__ == "__main__":
  main()
