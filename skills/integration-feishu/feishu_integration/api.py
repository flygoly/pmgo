"""Feishu open API client: tenant token + tasklist task list/get."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Optional

from .config import FeishuConfig

_SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
if str(_SCRIPTS) not in sys.path:
  sys.path.insert(0, str(_SCRIPTS))

from pmgo_http import request_json  # noqa: E402

TOKEN_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
API = "https://open.feishu.cn/open-apis"


def tenant_access_token(cfg: FeishuConfig) -> dict[str, Any]:
  out, _ = request_json(
    "POST",
    TOKEN_URL,
    headers={"Content-Type": "application/json", "User-Agent": cfg.user_agent},
    body={"app_id": cfg.app_id, "app_secret": cfg.app_secret},
    error_prefix="Feishu HTTP",
  )
  if not isinstance(out, dict):
    raise RuntimeError("Unexpected Feishu token response")
  code = out.get("code")
  if code is not None and code != 0:
    raise RuntimeError(f"Feishu token error: {out.get('msg') or out}")
  if not out.get("tenant_access_token"):
    raise RuntimeError(f"Feishu token missing tenant_access_token: {out}")
  return out


def _auth_headers(cfg: FeishuConfig, token: str) -> dict[str, str]:
  return {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
    "User-Agent": cfg.user_agent,
  }


def _ensure_token(cfg: FeishuConfig, token: Optional[str] = None) -> str:
  if token and token.strip():
    return token.strip()
  return str(tenant_access_token(cfg)["tenant_access_token"])


def list_tasklist_tasks(
  cfg: FeishuConfig,
  tasklist_guid: str,
  *,
  page_size: int = 50,
  page_token: str = "",
  token: Optional[str] = None,
) -> dict[str, Any]:
  """
  List tasks in a tasklist the app can access.

  Requires the app to be a tasklist member (viewer+). Env: FEISHU_TASKLIST_GUID.
  """
  guid = tasklist_guid.strip()
  if not guid:
    raise ValueError("tasklist_guid is empty")
  access = _ensure_token(cfg, token)
  query: dict[str, str] = {"page_size": str(max(1, min(int(page_size), 100)))}
  if page_token.strip():
    query["page_token"] = page_token.strip()
  out, _ = request_json(
    "GET",
    f"{API}/task/v2/tasklists/{guid}/tasks",
    headers=_auth_headers(cfg, access),
    query=query,
    error_prefix="Feishu HTTP",
  )
  if not isinstance(out, dict):
    raise RuntimeError("Unexpected Feishu tasklist tasks response")
  code = out.get("code")
  if code is not None and code != 0:
    raise RuntimeError(f"Feishu tasklist tasks error: {out.get('msg') or out}")
  data = out.get("data") if isinstance(out.get("data"), dict) else out
  return data if isinstance(data, dict) else {}


def get_task(
  cfg: FeishuConfig,
  task_guid: str,
  *,
  token: Optional[str] = None,
) -> dict[str, Any]:
  guid = task_guid.strip()
  if not guid:
    raise ValueError("task_guid is empty")
  access = _ensure_token(cfg, token)
  out, _ = request_json(
    "GET",
    f"{API}/task/v2/tasks/{guid}",
    headers=_auth_headers(cfg, access),
    error_prefix="Feishu HTTP",
  )
  if not isinstance(out, dict):
    raise RuntimeError("Unexpected Feishu get task response")
  code = out.get("code")
  if code is not None and code != 0:
    raise RuntimeError(f"Feishu get task error: {out.get('msg') or out}")
  data = out.get("data") if isinstance(out.get("data"), dict) else {}
  task = data.get("task") if isinstance(data, dict) else None
  if isinstance(task, dict):
    return task
  if isinstance(data, dict) and data.get("guid"):
    return data
  raise RuntimeError(f"Feishu task missing in response: {out}")


def task_to_public(task: dict[str, Any]) -> dict[str, Any]:
  return {
    "guid": task.get("guid") or task.get("id"),
    "summary": task.get("summary") or task.get("title"),
    "description": task.get("description"),
    "completed_at": task.get("completed_at"),
    "status": "done" if task.get("completed_at") else "todo",
    "url": task.get("url") or task.get("share_url"),
  }
