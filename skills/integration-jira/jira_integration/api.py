"""Minimal Jira Cloud REST API v3 client (stdlib only)."""

from __future__ import annotations

import base64
import json
import ssl
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Optional

from .config import JiraConfig


def _auth_header(cfg: JiraConfig) -> str:
  raw = f"{cfg.email}:{cfg.api_token}".encode("utf-8")
  return "Basic " + base64.b64encode(raw).decode("ascii")


def _request(
  cfg: JiraConfig,
  method: str,
  path: str,
  *,
  body: Optional[dict[str, Any]] = None,
) -> Any:
  url = cfg.base_url + path
  data: Optional[bytes] = None
  headers = {
    "Accept": "application/json",
    "Authorization": _auth_header(cfg),
    "User-Agent": cfg.user_agent,
  }
  if body is not None:
    data = json.dumps(body).encode("utf-8")
    headers["Content-Type"] = "application/json"
  req = urllib.request.Request(url, data=data, headers=headers, method=method)
  ctx = ssl.create_default_context()
  try:
    with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:  # noqa: S310
      raw = resp.read().decode("utf-8")
      if not raw:
        return None
      return json.loads(raw)
  except urllib.error.HTTPError as e:
    err = e.read().decode("utf-8", errors="replace")
    try:
      payload = json.loads(err)
      msgs = payload.get("errorMessages")
      if isinstance(msgs, list) and msgs:
        msg = "; ".join(str(m) for m in msgs)
      else:
        msg = str(payload.get("message", err))
    except json.JSONDecodeError:
      msg = err or e.reason
    raise RuntimeError(f"Jira HTTP {e.code}: {msg}") from e


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
) -> list[dict[str, Any]]:
  body = {
    "jql": jql or _default_jql(cfg),
    "maxResults": int(max_results),
    "fields": ["summary", "status", "updated"],
  }
  out = _request(cfg, "POST", "/rest/api/3/search", body=body)
  if not isinstance(out, dict):
    raise RuntimeError("Unexpected search response")
  issues = out.get("issues")
  if not isinstance(issues, list):
    raise RuntimeError("Unexpected issues list in search response")
  return [x for x in issues if isinstance(x, dict)]


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


def browse_url(cfg: JiraConfig, issue_key: str) -> str:
  return f"{cfg.base_url}/browse/{issue_key}"
