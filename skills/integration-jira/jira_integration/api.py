"""Minimal Jira Cloud REST API v3 client (stdlib only)."""

from __future__ import annotations

import base64
import sys
import urllib.parse
from pathlib import Path
from typing import Any, Optional

from .config import JiraConfig

_SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
if str(_SCRIPTS) not in sys.path:
  sys.path.insert(0, str(_SCRIPTS))

from pmgo_http import request_json  # noqa: E402


def _auth_header(cfg: JiraConfig) -> str:
  raw = f"{cfg.email}:{cfg.api_token}".encode("utf-8")
  return "Basic " + base64.b64encode(raw).decode("ascii")


def _headers(cfg: JiraConfig) -> dict[str, str]:
  return {
    "Accept": "application/json",
    "Authorization": _auth_header(cfg),
    "User-Agent": cfg.user_agent,
  }


def _request(
  cfg: JiraConfig,
  method: str,
  path: str,
  *,
  body: Optional[dict[str, Any]] = None,
) -> Any:
  out, _ = request_json(
    method,
    cfg.base_url + path,
    headers=_headers(cfg),
    body=body,
    error_prefix="Jira HTTP",
  )
  return out


def myself_smoke(cfg: JiraConfig) -> dict[str, Any]:
  out = _request(cfg, "GET", "/rest/api/3/myself")
  if not isinstance(out, dict):
    raise RuntimeError("Unexpected myself response")
  return out


def _default_jql(cfg: JiraConfig) -> str:
  if cfg.default_project:
    return f'project = "{cfg.default_project}" ORDER BY updated DESC'
  return "ORDER BY updated DESC"


def search_issues(
  cfg: JiraConfig,
  *,
  jql: str | None = None,
  max_results: int = 20,
  page_size: int = 50,
) -> list[dict[str, Any]]:
  """Search issues with startAt pagination until max_results is reached."""
  want = max(1, int(max_results))
  size = max(1, min(int(page_size), 100))
  collected: list[dict[str, Any]] = []
  start_at = 0
  query_jql = jql or _default_jql(cfg)
  while len(collected) < want:
    take = min(size, want - len(collected))
    body = {
      "jql": query_jql,
      "startAt": start_at,
      "maxResults": take,
      "fields": ["summary", "status", "updated"],
    }
    out = _request(cfg, "POST", "/rest/api/3/search", body=body)
    if not isinstance(out, dict):
      raise RuntimeError("Unexpected search response")
    issues = out.get("issues")
    if not isinstance(issues, list):
      raise RuntimeError("Unexpected issues list in search response")
    batch = [x for x in issues if isinstance(x, dict)]
    if not batch:
      break
    collected.extend(batch)
    total = out.get("total")
    start_at += len(batch)
    if isinstance(total, int) and start_at >= total:
      break
    if len(batch) < take:
      break
  return collected[:want]


def get_issue(cfg: JiraConfig, issue_key: str) -> dict[str, Any]:
  key = issue_key.strip()
  if not key:
    raise ValueError("issue key is empty")
  out = _request(
    cfg,
    "GET",
    f"/rest/api/3/issue/{urllib.parse.quote(key, safe='')}",
  )
  if not isinstance(out, dict):
    raise RuntimeError("Unexpected issue response")
  return out


def list_transitions(cfg: JiraConfig, issue_key: str) -> list[dict[str, Any]]:
  key = issue_key.strip()
  if not key:
    raise ValueError("issue key is empty")
  out = _request(
    cfg,
    "GET",
    f"/rest/api/3/issue/{urllib.parse.quote(key, safe='')}/transitions",
  )
  if not isinstance(out, dict):
    raise RuntimeError("Unexpected transitions response")
  transitions = out.get("transitions")
  if not isinstance(transitions, list):
    raise RuntimeError("Unexpected transitions list")
  return [x for x in transitions if isinstance(x, dict)]


def transition_issue(
  cfg: JiraConfig,
  issue_key: str,
  *,
  transition_id: str,
) -> None:
  key = issue_key.strip()
  tid = str(transition_id).strip()
  if not key or not tid:
    raise ValueError("issue key and transition_id are required")
  _request(
    cfg,
    "POST",
    f"/rest/api/3/issue/{urllib.parse.quote(key, safe='')}/transitions",
    body={"transition": {"id": tid}},
  )


def browse_url(cfg: JiraConfig, issue_key: str) -> str:
  return f"{cfg.base_url}/browse/{issue_key}"
