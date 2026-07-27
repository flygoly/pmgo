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

# --- Notion ---


@mcp.tool()
def pmgo_notion_page_list(database_id: str = "", page_size: int = 50) -> str:
  """List pages in a Notion database (NOTION_DATABASE_ID or database_id)."""
  err = gate("notion.page.read", confirmed=False)
  if err:
    return err
  import os

  from notion_integration.api import list_database_pages, page_public
  from notion_integration.config import load_config

  try:
    cfg = load_config()
    db = (database_id or os.environ.get("NOTION_DATABASE_ID") or "").strip()
    if not db:
      return "database_id is required (or set NOTION_DATABASE_ID)."
    pages = list_database_pages(cfg, db, page_size=page_size)
    return _j([page_public(p) for p in pages])
  except (OSError, RuntimeError, ValueError) as e:
    return str(e)


@mcp.tool()
def pmgo_notion_page_get(page_id: str) -> str:
  """Get one Notion page by id."""
  err = gate("notion.page.read", confirmed=False)
  if err:
    return err
  from notion_integration.api import get_page, page_public
  from notion_integration.config import load_config

  try:
    cfg = load_config()
    return _j(page_public(get_page(cfg, page_id)))
  except (OSError, RuntimeError, ValueError) as e:
    return str(e)


@mcp.tool()
def pmgo_notion_import_task(
  project_id: str,
  page_id: str,
  confirmed: bool = False,
) -> str:
  """Import a Notion page as a local task (source=notion, requires confirmed)."""
  err = gate("notion.page.import_task", confirmed=confirmed)
  if err:
    return err
  from notion_integration.api import get_page, page_public
  from notion_integration.config import load_config
  from project_core.store import default_task_store

  try:
    cfg = load_config()
    pub = page_public(get_page(cfg, page_id))
  except (OSError, RuntimeError, ValueError) as e:
    return str(e)
  title = str(pub.get("title") or "Notion page")
  url = str(pub.get("url") or "")
  body = f"Notion: {url}" if url else None
  ext_id = str(pub.get("id") or "").replace("-", "")
  if not ext_id:
    return "Notion page missing id"
  try:
    return _j(
      default_task_store().create_task(
        project_id,
        title=title,
        detail=body,
        status=str(pub.get("status") or "todo"),
        source="notion",
        external_id=ext_id,
      )
    )
  except sqlite3.IntegrityError:
    return "A task for this Notion page already exists (same project + source + external_id)."


