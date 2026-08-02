"""SQLite-backed application service independent from agent runtimes."""

from __future__ import annotations

import re
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK_STATUSES = frozenset({"todo", "doing", "blocked", "done", "cancelled"})
TASK_PRIORITIES = frozenset({"low", "medium", "high", "critical"})
PROJECT_STATUSES = frozenset({"active", "paused", "archived"})
NOTE_FILES = {
  "overview": "project-overview.md",
  "meetings": "meeting-notes.md",
  "decisions": "decision-log.md",
  "weekly": "weekly-report.md",
}


def _now() -> str:
  return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _slugify(value: str) -> str:
  slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
  return slug or "personal-office"


def _required_text(value: Any, field: str) -> str:
  text = str(value or "").strip()
  if not text:
    raise ValueError(f"{field} is required")
  return text


def _choice(value: Any, allowed: frozenset[str], field: str) -> str:
  text = str(value)
  if text not in allowed:
    raise ValueError(f"Invalid {field}: {text}")
  return text


class LocalCore:
  """Owns local persistence and the small desktop-facing query surface."""

  def __init__(self, data_dir: Path):
    self.data_dir = data_dir.expanduser().resolve()
    self.db_file = self.data_dir / "pmgo.db"
    self.projects_dir = self.data_dir / "projects"

  def connect(self) -> sqlite3.Connection:
    conn = sqlite3.connect(self.db_file, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 10000")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn

  def initialize(self, *, project_name: str = "Personal Office", locale: str = "zh-Hans") -> dict[str, Any]:
    self.data_dir.mkdir(parents=True, exist_ok=True)
    schema = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
    with self.connect() as conn:
      conn.executescript(schema)
      project = conn.execute("SELECT * FROM projects ORDER BY created_at LIMIT 1").fetchone()
      if project is None:
        project_id = str(uuid.uuid4())
        slug = _slugify(project_name)
        now = _now()
        conn.execute(
          "INSERT INTO projects (id, slug, name, status, created_at, updated_at) VALUES (?, ?, ?, 'active', ?, ?)",
          (project_id, slug, project_name, now, now),
        )
        conn.commit()
        project = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    assert project is not None
    result = dict(project)
    self._scaffold_markdown(result, locale)
    return result

  def create_project(self, payload: dict[str, Any], *, locale: str = "zh-Hans") -> dict[str, Any]:
    name = _required_text(payload.get("name"), "name")
    project_id = str(uuid.uuid4())
    base_slug = _slugify(str(payload.get("slug") or name))
    slug = f"project-{project_id[:8]}" if base_slug == "personal-office" and name != "Personal Office" else base_slug
    now = _now()
    with self.connect() as conn:
      conn.execute(
        "INSERT INTO projects (id, slug, name, description, status, owner, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, 'active', ?, ?, ?)",
        (project_id, slug, name, payload.get("description"), payload.get("owner"), now, now),
      )
      conn.commit()
      row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    assert row is not None
    project = dict(row)
    self._scaffold_markdown(project, locale)
    return project

  def update_project(self, project_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    if "name" in payload:
      fields["name"] = _required_text(payload["name"], "name")
    for key in ("description", "owner"):
      if key in payload:
        fields[key] = payload[key]
    if "status" in payload:
      fields["status"] = _choice(payload["status"], PROJECT_STATUSES, "status")
    if fields:
      fields["updated_at"] = _now()
      clause = ", ".join(f"{key} = ?" for key in fields)
      with self.connect() as conn:
        cursor = conn.execute(f"UPDATE projects SET {clause} WHERE id = ?", [*fields.values(), project_id])
        if cursor.rowcount == 0:
          raise KeyError(project_id)
        conn.commit()
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    else:
      with self.connect() as conn:
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    if row is None:
      raise KeyError(project_id)
    return dict(row)

  def _scaffold_markdown(self, project: dict[str, Any], locale: str) -> None:
    directory = self.projects_dir / str(project["slug"])
    directory.mkdir(parents=True, exist_ok=True)
    title = str(project["name"])
    headings = {
      "zh-Hans": ("项目概览", "会议记录", "决策日志", "周报"),
      "zh-Hant": ("專案概覽", "會議記錄", "決策日誌", "週報"),
      "en": ("Project overview", "Meeting notes", "Decision log", "Weekly report"),
    }.get(locale, ("Project overview", "Meeting notes", "Decision log", "Weekly report"))
    for filename, heading in zip(
      ("project-overview.md", "meeting-notes.md", "decision-log.md", "weekly-report.md"), headings
    ):
      path = directory / filename
      if not path.exists():
        path.write_text(f"# {heading}: {title}\n\n", encoding="utf-8")

  def dashboard(self, project_id: str | None = None) -> dict[str, Any]:
    with self.connect() as conn:
      projects = [dict(row) for row in conn.execute("SELECT * FROM projects ORDER BY updated_at DESC")]
      selected = project_id or (str(projects[0]["id"]) if projects else None)
      tasks: list[dict[str, Any]] = []
      risks: list[dict[str, Any]] = []
      if selected:
        tasks = [dict(row) for row in conn.execute(
          "SELECT * FROM tasks WHERE project_id = ? ORDER BY due_at IS NULL, due_at, created_at DESC", (selected,)
        )]
        risks = [dict(row) for row in conn.execute(
          "SELECT * FROM risks WHERE project_id = ? AND status != 'closed' ORDER BY score DESC, created_at DESC", (selected,)
        )]
    counts = {status: 0 for status in ("todo", "doing", "blocked", "done")}
    for task in tasks:
      if task["status"] in counts:
        counts[str(task["status"])] += 1
    return {"projects": projects, "project_id": selected, "tasks": tasks, "risks": risks, "counts": counts}

  def create_task(self, payload: dict[str, Any]) -> dict[str, Any]:
    task_id = str(uuid.uuid4())
    now = _now()
    title = _required_text(payload.get("title"), "title")
    status = _choice(payload.get("status", "todo"), TASK_STATUSES, "status")
    priority = _choice(payload.get("priority", "medium"), TASK_PRIORITIES, "priority")
    values = (
      task_id, _required_text(payload.get("project_id"), "project_id"), title, payload.get("detail"),
      status, priority, payload.get("due_at"), now, now,
    )
    with self.connect() as conn:
      conn.execute(
        "INSERT INTO tasks (id, project_id, title, detail, status, priority, due_at, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", values,
      )
      conn.commit()
      row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    assert row is not None
    return dict(row)

  def update_task(self, task_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    allowed = {"title", "detail", "status", "priority", "due_at", "blocked_reason"}
    fields = {key: value for key, value in payload.items() if key in allowed}
    if "title" in fields:
      fields["title"] = _required_text(fields["title"], "title")
    if "status" in fields:
      fields["status"] = _choice(fields["status"], TASK_STATUSES, "status")
    if "priority" in fields:
      fields["priority"] = _choice(fields["priority"], TASK_PRIORITIES, "priority")
    if fields:
      fields["updated_at"] = _now()
      clause = ", ".join(f"{key} = ?" for key in fields)
      with self.connect() as conn:
        cursor = conn.execute(f"UPDATE tasks SET {clause} WHERE id = ?", [*fields.values(), task_id])
        if cursor.rowcount == 0:
          raise KeyError(task_id)
        conn.commit()
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    else:
      with self.connect() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if row is None:
      raise KeyError(task_id)
    return dict(row)

  def delete_task(self, task_id: str) -> None:
    with self.connect() as conn:
      cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
      if cursor.rowcount == 0:
        raise KeyError(task_id)
      conn.commit()

  def _project_slug(self, project_id: str) -> str:
    with self.connect() as conn:
      row = conn.execute("SELECT slug FROM projects WHERE id = ?", (project_id,)).fetchone()
    if row is None:
      raise KeyError(project_id)
    return str(row["slug"])

  def list_notes(self, project_id: str) -> list[dict[str, Any]]:
    directory = self.projects_dir / self._project_slug(project_id)
    return [
      {"id": note_id, "filename": filename, "exists": (directory / filename).is_file()}
      for note_id, filename in NOTE_FILES.items()
    ]

  def read_note(self, project_id: str, note_id: str) -> dict[str, Any]:
    if note_id not in NOTE_FILES:
      raise KeyError(note_id)
    path = self.projects_dir / self._project_slug(project_id) / NOTE_FILES[note_id]
    return {"id": note_id, "filename": path.name, "content": path.read_text(encoding="utf-8") if path.is_file() else ""}

  def write_note(self, project_id: str, note_id: str, content: str) -> dict[str, Any]:
    if note_id not in NOTE_FILES:
      raise KeyError(note_id)
    path = self.projects_dir / self._project_slug(project_id) / NOTE_FILES[note_id]
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".pmgo-tmp")
    temporary.write_text(str(content), encoding="utf-8")
    temporary.replace(path)
    return {"id": note_id, "filename": path.name, "content": str(content)}

  def build_context(self, project_id: str, *, include_notes: bool = True) -> dict[str, Any]:
    state = self.dashboard(project_id)
    project = next((item for item in state["projects"] if item["id"] == project_id), None)
    if project is None:
      raise KeyError(project_id)
    active_tasks = [task for task in state["tasks"] if task["status"] not in {"done", "cancelled"}][:50]
    risks = state["risks"][:20]
    notes: list[dict[str, str]] = []
    if include_notes:
      remaining = 12000
      for note_id in NOTE_FILES:
        note = self.read_note(project_id, note_id)
        content = str(note["content"])[:remaining]
        remaining -= len(content)
        notes.append({"id": note_id, "content": content})
        if remaining <= 0:
          break
    lines = [f"Project: {project['name']}", "", "Active tasks:"]
    lines.extend(f"- [{task['status']}/{task['priority']}] {task['title']}" for task in active_tasks)
    lines.append("\nOpen risks:")
    lines.extend(f"- [{risk['severity']}] {risk['title']}" for risk in risks)
    for note in notes:
      lines.extend((f"\nNote ({note['id']}):", note["content"]))
    text = "\n".join(lines)
    return {
      "project": project,
      "task_count": len(active_tasks),
      "risk_count": len(risks),
      "notes": [note["id"] for note in notes],
      "characters": len(text),
      "text": text,
    }
