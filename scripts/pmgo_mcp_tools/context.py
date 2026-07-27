"""Shared MCP instance, policy gate, and serialization helpers."""

from __future__ import annotations

import json

from pmgo_log import elapsed_ms, log_event, setup_logging, tool_timer
from pmgo_policy import gate as _policy_gate

try:
  from mcp.server.fastmcp import FastMCP
except ImportError as exc:
  raise RuntimeError(
    "mcp package not installed. Install with: pip install mcp pyyaml"
  ) from exc


_log = setup_logging()
mcp = FastMCP("pmgo")


def gate(tool_key: str, *, confirmed: bool) -> str | None:
  """Apply the policy gate and emit a structured timing event."""
  started = tool_timer()
  err = _policy_gate(tool_key, confirmed=confirmed)
  log_event(
    _log,
    "mcp.gate",
    tool=tool_key,
    confirmed=confirmed,
    ok=err is None,
    error=err,
    ms=elapsed_ms(started),
  )
  return err


def json_text(data: object) -> str:
  return json.dumps(data, indent=2, default=str, ensure_ascii=False)


def issue_public(issue: dict) -> dict:
  return {
    "id": issue.get("id"),
    "number": issue.get("number"),
    "title": issue.get("title"),
    "state": issue.get("state"),
    "body": issue.get("body"),
    "html_url": issue.get("html_url"),
    "user": (issue.get("user") or {}).get("login"),
  }


def slugify(name: str) -> str:
  from project_core.config import slugify as project_slugify

  return project_slugify(name)


def resolve_project_id(project_id: str) -> str | None:
  import pmgo_common

  return pmgo_common.resolve_project_id(explicit=project_id or None)
