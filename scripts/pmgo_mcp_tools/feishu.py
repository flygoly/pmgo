"""MCP tools for this domain."""

from __future__ import annotations

import sqlite3

from .context import (
  gate,
  issue_public as _issue_public,
  json_text as _j,
  mcp,
  resolve_project_id as _resolve_project_id,
  slugify as _slugify,
)

# --- Feishu ---


@mcp.tool()
def pmgo_feishu_task_list(tasklist_guid: str = "", page_size: int = 50) -> str:
  """List Feishu tasks in a tasklist (FEISHU_TASKLIST_GUID or tasklist_guid)."""
  err = gate("feishu.task.read", confirmed=False)
  if err:
    return err
  import os

  from feishu_integration.api import list_tasklist_tasks, task_to_public
  from feishu_integration.config import load_config

  try:
    cfg = load_config()
    guid = (tasklist_guid or os.environ.get("FEISHU_TASKLIST_GUID") or "").strip()
    if not guid:
      return "tasklist_guid is required (or set FEISHU_TASKLIST_GUID)."
    data = list_tasklist_tasks(cfg, guid, page_size=page_size)
    items = data.get("items") or data.get("tasks") or []
    public = [task_to_public(x) for x in items if isinstance(x, dict)]
    return _j(
      {
        "tasklist_guid": guid,
        "items": public,
        "has_more": data.get("has_more"),
        "page_token": data.get("page_token"),
      }
    )
  except (OSError, RuntimeError, ValueError) as e:
    return str(e)


@mcp.tool()
def pmgo_feishu_task_get(task_guid: str) -> str:
  """Get one Feishu task by guid."""
  err = gate("feishu.task.read", confirmed=False)
  if err:
    return err
  from feishu_integration.api import get_task, task_to_public
  from feishu_integration.config import load_config

  try:
    cfg = load_config()
    return _j(task_to_public(get_task(cfg, task_guid)))
  except (OSError, RuntimeError, ValueError) as e:
    return str(e)


@mcp.tool()
def pmgo_feishu_import_task(
  project_id: str,
  task_guid: str,
  confirmed: bool = False,
) -> str:
  """Import a Feishu task as a local task (source=feishu, requires confirmed)."""
  err = gate("feishu.task.import_task", confirmed=confirmed)
  if err:
    return err
  from feishu_integration.api import get_task, task_to_public
  from feishu_integration.config import load_config
  from project_core.store import default_task_store

  try:
    cfg = load_config()
    pub = task_to_public(get_task(cfg, task_guid))
  except (OSError, RuntimeError, ValueError) as e:
    return str(e)
  title = str(pub.get("summary") or pub.get("guid") or "Feishu task")
  body = (pub.get("description") or "").strip() if pub.get("description") else ""
  url = str(pub.get("url") or "")
  if url:
    body = f"{body}\n\nFeishu: {url}".strip() if body else f"Feishu: {url}"
  ext_id = str(pub.get("guid") or "")
  if not ext_id:
    return "Feishu task missing guid"
  try:
    return _j(
      default_task_store().create_task(
        project_id,
        title=title,
        detail=body or None,
        status=str(pub.get("status") or "todo"),
        source="feishu",
        external_id=ext_id,
      )
    )
  except sqlite3.IntegrityError:
    return "A task for this Feishu guid already exists (same project + source + external_id)."


