"""Minimal GitHub REST v3 client (stdlib only)."""

from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Optional

from .config import GitHubConfig

API = "https://api.github.com"


def _ua(cfg: GitHubConfig) -> dict[str, str]:
  return {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": cfg.user_agent,
    "Authorization": f"Bearer {cfg.token}",
  }


def _request(
  cfg: GitHubConfig,
  method: str,
  path: str,
  *,
  body: Optional[dict[str, Any]] = None,
  query: Optional[dict[str, str]] = None,
) -> Any:
  url = API + path
  if query:
    url = url + "?" + urllib.parse.urlencode(query)
  data: Optional[bytes] = None
  headers = _ua(cfg)
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
      msg = payload.get("message", err)
    except json.JSONDecodeError:
      msg = err or e.reason
    raise RuntimeError(f"GitHub API {e.code} {e.reason}: {msg}") from e


def rate_limit(cfg: GitHubConfig) -> dict[str, Any]:
  return _request(cfg, "GET", "/rate_limit")  # type: ignore[return-value]


def list_issues(
  cfg: GitHubConfig,
  *,
  state: str = "all",
  per_page: int = 30,
) -> list[dict[str, Any]]:
  path = f"/repos/{cfg.owner}/{cfg.repo}/issues"
  out = _request(
    cfg,
    "GET",
    path,
    query={"state": state, "per_page": str(per_page)},
  )
  if not isinstance(out, list):
    raise RuntimeError("Unexpected list_issues response type")
  return [x for x in out if isinstance(x, dict) and "pull_request" not in x]


def get_issue(cfg: GitHubConfig, number: int) -> dict[str, Any]:
  path = f"/repos/{cfg.owner}/{cfg.repo}/issues/{number}"
  out = _request(cfg, "GET", path)
  if not isinstance(out, dict):
    raise RuntimeError("Unexpected get_issue response type")
  if out.get("pull_request"):
    raise RuntimeError(f"#{number} is a pull request, not a plain issue")
  return out


def create_issue(
  cfg: GitHubConfig,
  *,
  title: str,
  body: str = "",
) -> dict[str, Any]:
  path = f"/repos/{cfg.owner}/{cfg.repo}/issues"
  out = _request(cfg, "POST", path, body={"title": title, "body": body or ""})
  if not isinstance(out, dict):
    raise RuntimeError("Unexpected create_issue response type")
  return out


def update_issue(
  cfg: GitHubConfig,
  number: int,
  *,
  state: Optional[str] = None,
  title: Optional[str] = None,
  body: Optional[str] = None,
) -> dict[str, Any]:
  path = f"/repos/{cfg.owner}/{cfg.repo}/issues/{number}"
  payload: dict[str, str] = {}
  if state is not None:
    payload["state"] = state
  if title is not None:
    payload["title"] = title
  if body is not None:
    payload["body"] = body
  if not payload:
    raise ValueError("No fields to update")
  out = _request(cfg, "PATCH", path, body=payload)
  if not isinstance(out, dict):
    raise RuntimeError("Unexpected update_issue response type")
  return out
