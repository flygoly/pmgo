"""Build daily standup markdown from `memory/pmgo.db` tasks."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pmgo_common  # type: ignore

_parse_ts = pmgo_common.parse_ts


def _task_title(t: Any) -> str:
  return str(t["title"])


def _bullet(lines: list[str], empty: str) -> str:
  if not lines:
    return empty
  return "\n".join(f"- {x}" for x in lines)


def _date_line(now: datetime, locale: str) -> str:
  d = now.date()
  if locale == "zh-CN":
    return f"{d.year} 年 {d.month} 月 {d.day} 日 (UTC)"
  if locale == "zh-TW":
    return f"{d.year} 年 {d.month} 月 {d.day} 日 (UTC)"
  return f"{d.isoformat()} (UTC)"


ALLOWED_TEMPLATES = ("daily-report", "daily-standup")


def build_daily_markdown(
  *,
  project_id: str,
  locale: str,
  now: datetime | None = None,
  template: str = "daily-report",
) -> str:
  """
  Fill a daily Markdown template from SQLite tasks + open risks.

  Templates live at memory/templates/<template>.<locale>.md
  (default: daily-report — classic daily log sections).
  """
  now = now or datetime.now(timezone.utc)
  tpl_name = (template or "daily-report").strip()
  if tpl_name not in ALLOWED_TEMPLATES:
    raise ValueError(
      f"Unknown template {tpl_name!r}; choose one of: {', '.join(ALLOWED_TEMPLATES)}"
    )
  root = pmgo_common.repo_root()
  tpl_path = root / "memory" / "templates" / f"{tpl_name}.{locale}.md"
  if not tpl_path.is_file():
    raise FileNotFoundError(f"Missing template: {tpl_path}")
  template_text = tpl_path.read_text(encoding="utf-8")
  strings = pmgo_common.load_strings(locale)
  empty = strings.get("standup.empty", "—")

  conn = pmgo_common.connect_db(pmgo_common.db_path())
  try:
    proj = conn.execute(
      "SELECT * FROM projects WHERE id = ?",
      (project_id,),
    ).fetchone()
    if proj is None:
      raise KeyError(f"Unknown project id: {project_id}")
    name = str(proj["name"])
    rows = conn.execute(
      "SELECT * FROM tasks WHERE project_id = ? ORDER BY created_at",
      (project_id,),
    ).fetchall()
    risk_rows = conn.execute(
      """
      SELECT * FROM risks
      WHERE project_id = ? AND status IN ('open', 'watching')
      ORDER BY
        CASE severity
          WHEN 'critical' THEN 0
          WHEN 'high' THEN 1
          WHEN 'medium' THEN 2
          ELSE 3
        END,
        created_at
      """,
      (project_id,),
    ).fetchall()
  finally:
    conn.close()

  cutoff = now - timedelta(hours=24)
  done_24: list[str] = []
  doing: list[str] = []
  todo: list[str] = []
  blocked: list[str] = []

  for t in rows:
    st = t["status"]
    title = _task_title(t)
    if st == "doing":
      doing.append(title)
    elif st == "blocked":
      blocked.append(title)
    elif st == "todo":
      todo.append(title)
    elif st == "done":
      ut = _parse_ts(t["updated_at"])
      if ut is not None and ut >= cutoff:
        done_24.append(title)
    # cancelled: omit

  risks: list[str] = []
  for r in risk_rows:
    risks.append(f"{r['title']} ({r['severity']})")

  ctx = {
    "project_name": name,
    "date_line": _date_line(now, locale),
    "b_done": _bullet(done_24, empty),
    "b_doing": _bullet(doing, empty),
    "b_todo": _bullet(todo, empty),
    "b_blocked": _bullet(blocked, empty),
    "b_risks": _bullet(risks, strings.get("risk.none", empty)),
  }
  out = template_text
  for k, v in ctx.items():
    out = out.replace("{{" + k + "}}", v)
  if "{{" in out:
    raise ValueError("Unfilled placeholders remain in daily template")
  return out.rstrip() + "\n"


def save_daily_markdown(
  markdown: str,
  *,
  project_id: str,
  now: datetime | None = None,
) -> Path:
  """Write report under memory/projects/<slug>/daily-reports/YYYY-MM-DD.md."""
  now = now or datetime.now(timezone.utc)
  conn = pmgo_common.connect_db(pmgo_common.db_path())
  try:
    proj = conn.execute(
      "SELECT slug FROM projects WHERE id = ?",
      (project_id,),
    ).fetchone()
    if proj is None:
      raise KeyError(f"Unknown project id: {project_id}")
    slug = str(proj["slug"] or project_id)
  finally:
    conn.close()

  root = pmgo_common.repo_root()
  out_dir = root / "memory" / "projects" / slug / "daily-reports"
  out_dir.mkdir(parents=True, exist_ok=True)
  path = out_dir / f"{now.date().isoformat()}.md"
  path.write_text(markdown, encoding="utf-8")
  return path
