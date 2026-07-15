"""Minimal GitHub REST v3 client (stdlib only)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Optional

from .config import GitHubConfig

_SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
if str(_SCRIPTS) not in sys.path:
  sys.path.insert(0, str(_SCRIPTS))

from pmgo_http import request_json  # noqa: E402

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
  out, _headers = request_json(
    method,
    API + path,
    headers=_ua(cfg),
    body=body,
    query=query,
    error_prefix="GitHub API",
  )
  return out


def rate_limit(cfg: GitHubConfig) -> dict[str, Any]:
  return _request(cfg, "GET", "/rate_limit")  # type: ignore[return-value]


def list_issues(
  cfg: GitHubConfig,
  *,
  state: str = "all",
  per_page: int = 30,
  max_pages: int = 10,
) -> list[dict[str, Any]]:
  """List issues across pages (stops at empty page, short page, or max_pages)."""
  path = f"/repos/{cfg.owner}/{cfg.repo}/issues"
  collected: list[dict[str, Any]] = []
  page = 1
  per = max(1, min(int(per_page), 100))
  pages = max(1, int(max_pages))
  while page <= pages:
    out = _request(
      cfg,
      "GET",
      path,
      query={
        "state": state,
        "per_page": str(per),
        "page": str(page),
      },
    )
    if not isinstance(out, list):
      raise RuntimeError("Unexpected list_issues response type")
    batch = [x for x in out if isinstance(x, dict) and "pull_request" not in x]
    collected.extend(batch)
    if len(out) < per:
      break
    page += 1
  return collected


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
  labels: Optional[list[str]] = None,
  assignees: Optional[list[str]] = None,
) -> dict[str, Any]:
  path = f"/repos/{cfg.owner}/{cfg.repo}/issues"
  payload: dict[str, Any] = {"title": title, "body": body or ""}
  if labels:
    payload["labels"] = labels
  if assignees:
    payload["assignees"] = assignees
  out = _request(cfg, "POST", path, body=payload)
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
  labels: Optional[list[str]] = None,
  assignees: Optional[list[str]] = None,
) -> dict[str, Any]:
  path = f"/repos/{cfg.owner}/{cfg.repo}/issues/{number}"
  payload: dict[str, Any] = {}
  if state is not None:
    payload["state"] = state
  if title is not None:
    payload["title"] = title
  if body is not None:
    payload["body"] = body
  if labels is not None:
    payload["labels"] = labels
  if assignees is not None:
    payload["assignees"] = assignees
  if not payload:
    raise ValueError("No fields to update")
  out = _request(cfg, "PATCH", path, body=payload)
  if not isinstance(out, dict):
    raise RuntimeError("Unexpected update_issue response type")
  return out
