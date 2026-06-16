"""Scaffold human-readable Markdown under memory/projects/<slug>/."""

from __future__ import annotations

from pathlib import Path

from .config import repo_root, slugify as _slugify


SUPPORTED_LOCALES = frozenset({"en", "zh-CN", "zh-TW"})


def _templates_dir() -> Path:
  return repo_root() / "memory" / "templates"


def _projects_dir() -> Path:
  return repo_root() / "memory" / "projects"


def normalize_locale(locale: str) -> str:
  normalized = locale.strip()
  if normalized not in SUPPORTED_LOCALES:
    raise ValueError("Unsupported locale. Use one of: en, zh-CN, zh-TW.")
  return normalized


def load_template(template_name: str, locale: str) -> str:
  template_file = _templates_dir() / f"{template_name}.{locale}.md"
  if not template_file.is_file():
    raise FileNotFoundError(f"Template missing: {template_file}")
  return template_file.read_text(encoding="utf-8")


def render_template(text: str, *, name: str, slug: str) -> str:
  out = text
  for key, value in (("{{project_name}}", name), ("{{project_slug}}", slug)):
    out = out.replace(key, value)
  return out


def scaffold_project_markdown(
  *,
  name: str,
  slug: str | None = None,
  locale: str = "en",
) -> Path:
  """Create memory/projects/<slug>/ markdown files if missing. Returns project dir."""
  loc = normalize_locale(locale)
  s = slug or _slugify(name)
  project_dir = _projects_dir() / s
  project_dir.mkdir(parents=True, exist_ok=True)

  files = (
    ("project-overview", "project-overview.md"),
    ("weekly-report", "weekly-report.md"),
    ("meeting-notes", "meeting-notes.md"),
    ("decision-log", "decision-log.md"),
  )
  for template_name, filename in files:
    path = project_dir / filename
    if path.exists():
      continue
    raw = load_template(template_name, loc)
    path.write_text(render_template(raw, name=name, slug=s), encoding="utf-8")
  return project_dir
