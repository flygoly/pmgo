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

# --- reports ---


@mcp.tool()
def pmgo_daily_report(project_id: str = "", locale: str = "") -> str:
  """Render the Markdown daily report (daily-report template). Uses PMGO_DEFAULT_PROJECT_ID when empty."""
  err = gate("pmgo.report.daily", confirmed=False)
  if err:
    return err
  import pmgo_common  # noqa: WPS433
  from daily_standup.build import build_daily_markdown

  pid = _resolve_project_id(project_id)
  if not pid:
    return "project_id is required (or set PMGO_DEFAULT_PROJECT_ID)."
  loc = locale.strip() or pmgo_common.default_locale()
  return build_daily_markdown(project_id=pid, locale=loc, template="daily-report")


@mcp.tool()
def pmgo_weekly_report(
  project_id: str = "",
  locale: str = "",
  week_offset: int = 0,
) -> str:
  """Render the Markdown weekly report. Uses PMGO_DEFAULT_PROJECT_ID when project_id is empty."""
  err = gate("pmgo.report.weekly", confirmed=False)
  if err:
    return err
  import pmgo_common  # noqa: WPS433
  from weekly_report.build import build_weekly_markdown

  pid = _resolve_project_id(project_id)
  if not pid:
    return "project_id is required (or set PMGO_DEFAULT_PROJECT_ID)."
  loc = locale.strip() or pmgo_common.default_locale()
  return build_weekly_markdown(
    project_id=pid, locale=loc, week_offset=week_offset
  )


