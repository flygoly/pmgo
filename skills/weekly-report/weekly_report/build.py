"""Fill `memory/templates/weekly-report.<locale>.md` from DB aggregates."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
import pmgo_common  # type: ignore


def _parse_ts(raw: str | None) -> datetime | None:
  if not raw:
    return None
  raw = str(raw).replace("Z", "+00:00")
  try:
    d = datetime.fromisoformat(raw)
  except ValueError:
    return None
  if d.tzinfo is None:
    return d.replace(tzinfo=timezone.utc)
  return d


def _week_bounds_utc(anchor: datetime, week_offset: int) -> tuple[datetime, datetime]:
  """Monday 00:00 UTC start, following Monday 00:00 exclusive end."""
  d = anchor.date()
  if week_offset:
    d = d + timedelta(weeks=week_offset)
  monday = d - timedelta(days=d.weekday())
  start = datetime.combine(monday, datetime.min.time(), tzinfo=timezone.utc)
  end = start + timedelta(days=7)
  return start, end


def _week_range_label(start: datetime, end_excl: datetime, locale: str) -> str:
  last = (end_excl - timedelta(days=1)).date()
  s, e = start.date(), last
  if locale == "zh-CN":
    return f"{s.year}/{s.month:02d}/{s.day:02d} – {e.year}/{e.month:02d}/{e.day:02d} (UTC)"
  if locale == "zh-TW":
    return f"{s.year}/{s.month:02d}/{s.day:02d} – {e.year}/{e.month:02d}/{e.day:02d} (UTC)"
  return f"{s.isoformat()} – {e.isoformat()} (UTC)"


def build_weekly_markdown(
  *,
  project_id: str,
  locale: str,
  now: datetime | None = None,
  week_offset: int = 0,
) -> str:
  now = now or datetime.now(timezone.utc)
  root = pmgo_common.repo_root()
  tpl_path = root / "memory" / "templates" / f"weekly-report.{locale}.md"
  if not tpl_path.is_file():
    raise FileNotFoundError(f"Missing template: {tpl_path}")
  template = tpl_path.read_text(encoding="utf-8")
  em = "—"
  w_start, w_end = _week_bounds_utc(now, week_offset)
  week_range = _week_range_label(w_start, w_end, locale)
  gen_at = now.replace(microsecond=0).isoformat()

  conn = pmgo_common.connect_db(pmgo_common.db_path())
  try:
    proj = conn.execute(
      "SELECT * FROM projects WHERE id = ?",
      (project_id,),
    ).fetchone()
    if proj is None:
      raise KeyError(f"Unknown project id: {project_id}")
    project_name = str(proj["name"])
    owner = str(proj["owner"] or em)
    task_rows = conn.execute(
      "SELECT * FROM tasks WHERE project_id = ?",
      (project_id,),
    ).fetchall()
    ms_rows = conn.execute(
      "SELECT * FROM milestones WHERE project_id = ?",
      (project_id,),
    ).fetchall()
    risk_rows = conn.execute(
      "SELECT * FROM risks WHERE project_id = ? ORDER BY severity, created_at",
      (project_id,),
    ).fetchall()
  finally:
    conn.close()

  by_status: Counter[str] = Counter()
  done_this_week: list[str] = []
  for t in task_rows:
    st = t["status"]
    by_status[st] += 1
    if st == "done":
      ut = _parse_ts(t["updated_at"])
      if ut is not None and w_start <= ut < w_end:
        done_this_week.append(str(t["title"]))

  def pick(seq: list[str], i: int) -> str:
    if len(seq) > i:
      return seq[i]
    return em

  risks_open = [r for r in risk_rows if r["status"] in ("open", "watching")]
  blocked_n = by_status.get("blocked", 0)
  if blocked_n or risks_open:
    overall = "At risk" if locale == "en" else ("有风险" if locale == "zh-CN" else "有風險")
  else:
    overall = "On track" if locale == "en" else ("正常" if locale == "zh-CN" else "正常")

  closed = len(done_this_week)
  if locale == "en":
    goal = f"{closed} tasks closed this week (UTC week)"
  elif locale == "zh-CN":
    goal = f"本周（UTC 周历）完成 {closed} 项"
  else:
    goal = f"本週（UTC 週曆）完成 {closed} 項"

  m_lines: list[str] = []
  for m in ms_rows:
    m_lines.append(f"- {m['title']}: {m['status']}")
  milestone_updates = "\n".join(m_lines) if m_lines else em

  r0 = em
  r1 = em
  if risks_open:
    r0 = f"{risks_open[0]['title']} ({risks_open[0]['status']})"
  if len(risks_open) > 1:
    r1 = f"{risks_open[1]['title']} ({risks_open[1]['status']})"
  else:
    r1 = r0 if r0 != em else em

  todo_tasks = [t for t in task_rows if t["status"] in ("todo", "doing", "blocked")]
  todo_tasks.sort(
    key=lambda t: (t["due_at"] is None, str(t["due_at"] or ""), str(t["title"])),
  )
  na1 = na1o = na1d = em
  na2 = na2o = na2d = em
  if len(todo_tasks) > 0:
    t = todo_tasks[0]
    na1, na1o, na1d = str(t["title"]), str(t["assignee"] or em), str(t["due_at"] or em)
  if len(todo_tasks) > 1:
    t = todo_tasks[1]
    na2, na2o, na2d = str(t["title"]), str(t["assignee"] or em), str(t["due_at"] or em)

  blocked_titles = [str(t["title"]) for t in task_rows if t["status"] == "blocked"]
  esc = em
  if blocked_titles:
    esc = blocked_titles[0]

  ctx: dict[str, str] = {
    "project_name": project_name,
    "week_range": week_range,
    "generated_at": gen_at,
    "owner": owner,
    "overall_status": overall,
    "goal_completion": goal,
    "highlight_1": pick(done_this_week, 0),
    "highlight_2": pick(done_this_week, 1),
    "milestone_updates": milestone_updates,
    "todo_count": str(by_status.get("todo", 0)),
    "doing_count": str(by_status.get("doing", 0)),
    "blocked_count": str(by_status.get("blocked", 0)),
    "done_count": str(by_status.get("done", 0)),
    "deliverable_1": pick(done_this_week, 0),
    "deliverable_2": pick(done_this_week, 1),
    "new_risk_1": r0,
    "active_risk_1": r1,
    "escalation_1": esc,
    "next_action_1": na1,
    "next_action_1_owner": na1o,
    "next_action_1_due": na1d,
    "next_action_2": na2,
    "next_action_2_owner": na2o,
    "next_action_2_due": na2d,
    "evidence_commits_prs": em,
    "evidence_issues": em,
    "evidence_docs": em,
  }
  out = template
  for k, v in ctx.items():
    out = out.replace("{{" + k + "}}", v)
  if "{{" in out:
    raise ValueError("Unfilled placeholders remain in weekly template")
  return out.rstrip() + "\n"
