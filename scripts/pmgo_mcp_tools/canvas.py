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

# --- Live Canvas ---


@mcp.tool()
def pmgo_canvas_gantt(project_id: str = "") -> str:
  """Export Gantt JSON (milestones + tasks) for OpenClaw Live Canvas."""
  err = gate("pmgo.canvas.read", confirmed=False)
  if err:
    return err
  from canvas_data.build import build_gantt

  pid = project_id.strip() or (_resolve_project_id("") or "")
  if not pid:
    return "project_id is required (or set PMGO_DEFAULT_PROJECT_ID)."
  try:
    return _j(build_gantt(pid))
  except KeyError as e:
    return str(e)


@mcp.tool()
def pmgo_canvas_burndown(project_id: str = "") -> str:
  """Export UTC-week burndown JSON for OpenClaw Live Canvas."""
  err = gate("pmgo.canvas.read", confirmed=False)
  if err:
    return err
  from canvas_data.build import build_burndown

  pid = project_id.strip() or (_resolve_project_id("") or "")
  if not pid:
    return "project_id is required (or set PMGO_DEFAULT_PROJECT_ID)."
  try:
    return _j(build_burndown(pid))
  except KeyError as e:
    return str(e)


@mcp.tool()
def pmgo_canvas_snapshot(project_id: str = "") -> str:
  """Export combined Gantt + burndown snapshot for Live Canvas."""
  err = gate("pmgo.canvas.read", confirmed=False)
  if err:
    return err
  from canvas_data.build import build_snapshot

  pid = project_id.strip() or (_resolve_project_id("") or "")
  if not pid:
    return "project_id is required (or set PMGO_DEFAULT_PROJECT_ID)."
  try:
    return _j(build_snapshot(pid))
  except KeyError as e:
    return str(e)


@mcp.tool()
def pmgo_canvas_render(project_id: str = "", inline: bool = True) -> str:
  """
  Render Live Canvas HTML + data.json under reports/canvas/pmgo.

  Returns out_dir / index_html / data_json plus runtime_notes.
  OpenClaw: point canvasHost.root at out_dir and present the canvas URL.
  Hermes: no canvas host — use the files locally or stick to Markdown reports.
  """
  err = gate("pmgo.canvas.read", confirmed=False)
  if err:
    return err
  from canvas_data.render import default_out_dir, render_canvas

  pid = project_id.strip() or (_resolve_project_id("") or "")
  if not pid:
    return "project_id is required (or set PMGO_DEFAULT_PROJECT_ID)."
  try:
    return _j(
      render_canvas(
        pid,
        out_dir=default_out_dir(),
        inline=bool(inline),
      )
    )
  except (FileNotFoundError, KeyError, ValueError) as e:
    return str(e)

