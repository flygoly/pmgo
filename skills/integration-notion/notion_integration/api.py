"""Notion API client: users/me, database query, page helpers."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Optional

from .config import NotionConfig

_SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
if str(_SCRIPTS) not in sys.path:
  sys.path.insert(0, str(_SCRIPTS))

from pmgo_http import request_json  # noqa: E402

API = "https://api.notion.com/v1"


def _headers(cfg: NotionConfig) -> dict[str, str]:
  return {
    "Authorization": f"Bearer {cfg.token}",
    "Notion-Version": cfg.notion_version,
    "User-Agent": cfg.user_agent,
  }


def users_me(cfg: NotionConfig) -> dict[str, Any]:
  out, _ = request_json(
    "GET",
    f"{API}/users/me",
    headers=_headers(cfg),
    error_prefix="Notion HTTP",
  )
  if not isinstance(out, dict):
    raise RuntimeError("Unexpected Notion users/me response")
  return out


def query_database(
  cfg: NotionConfig,
  database_id: str,
  *,
  page_size: int = 50,
  start_cursor: str = "",
) -> dict[str, Any]:
  """POST /v1/databases/{id}/query — database must be shared with the integration."""
  db = database_id.replace("-", "").strip()
  if len(db) < 32:
    # allow dashed UUIDs; Notion accepts both
    db = database_id.strip()
  if not db:
    raise ValueError("database_id is empty")
  body: dict[str, Any] = {"page_size": max(1, min(int(page_size), 100))}
  if start_cursor.strip():
    body["start_cursor"] = start_cursor.strip()
  out, _ = request_json(
    "POST",
    f"{API}/databases/{database_id.strip()}/query",
    headers=_headers(cfg),
    body=body,
    error_prefix="Notion HTTP",
  )
  if not isinstance(out, dict):
    raise RuntimeError("Unexpected Notion database query response")
  return out


def get_page(cfg: NotionConfig, page_id: str) -> dict[str, Any]:
  pid = page_id.strip()
  if not pid:
    raise ValueError("page_id is empty")
  out, _ = request_json(
    "GET",
    f"{API}/pages/{pid}",
    headers=_headers(cfg),
    error_prefix="Notion HTTP",
  )
  if not isinstance(out, dict):
    raise RuntimeError("Unexpected Notion page response")
  return out


def _plain_from_rich_text(items: Any) -> str:
  if not isinstance(items, list):
    return ""
  parts: list[str] = []
  for item in items:
    if isinstance(item, dict):
      parts.append(str(item.get("plain_text") or ""))
  return "".join(parts).strip()


def page_title(page: dict[str, Any]) -> str:
  props = page.get("properties") if isinstance(page.get("properties"), dict) else {}
  for _name, prop in props.items():
    if not isinstance(prop, dict):
      continue
    if prop.get("type") == "title":
      title = _plain_from_rich_text(prop.get("title"))
      if title:
        return title
  return str(page.get("id") or "Notion page")


def page_status(page: dict[str, Any]) -> str:
  """Best-effort map Status/Select/Checkbox → pmgo task status."""
  props = page.get("properties") if isinstance(page.get("properties"), dict) else {}
  for _name, prop in props.items():
    if not isinstance(prop, dict):
      continue
    ptype = prop.get("type")
    if ptype == "status":
      st = prop.get("status") if isinstance(prop.get("status"), dict) else {}
      name = str(st.get("name") or "").lower()
      if "done" in name or "complete" in name:
        return "done"
      if "progress" in name or "doing" in name:
        return "doing"
      if "block" in name:
        return "blocked"
      return "todo"
    if ptype == "select":
      sel = prop.get("select") if isinstance(prop.get("select"), dict) else {}
      name = str(sel.get("name") or "").lower()
      if "done" in name or "complete" in name:
        return "done"
      if "progress" in name or "doing" in name:
        return "doing"
      return "todo"
    if ptype == "checkbox" and prop.get("checkbox") is True:
      return "done"
  if page.get("archived"):
    return "cancelled"
  return "todo"


def page_public(page: dict[str, Any]) -> dict[str, Any]:
  pid = str(page.get("id") or "")
  return {
    "id": pid,
    "title": page_title(page),
    "url": page.get("url"),
    "status": page_status(page),
    "archived": bool(page.get("archived")),
  }


def list_database_pages(
  cfg: NotionConfig,
  database_id: str,
  *,
  page_size: int = 50,
  max_pages: int = 5,
) -> list[dict[str, Any]]:
  collected: list[dict[str, Any]] = []
  cursor = ""
  for _ in range(max(1, int(max_pages))):
    out = query_database(
      cfg,
      database_id,
      page_size=page_size,
      start_cursor=cursor,
    )
    results = out.get("results")
    if not isinstance(results, list):
      break
    for row in results:
      if isinstance(row, dict) and row.get("object") == "page":
        collected.append(row)
    if not out.get("has_more"):
      break
    cursor = str(out.get("next_cursor") or "")
    if not cursor:
      break
  return collected
