#!/usr/bin/env python3

import argparse
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MEMORY_PROJECTS_DIR = ROOT / "memory" / "projects"
TEMPLATES_DIR = ROOT / "memory" / "templates"


def slugify(value: str) -> str:
  slug = value.strip().lower()
  slug = re.sub(r"[^a-z0-9]+", "-", slug)
  slug = re.sub(r"-{2,}", "-", slug).strip("-")
  if not slug:
    raise ValueError("Project name generated an empty slug. Use --slug explicitly.")
  return slug


def choose_locale_template_prefix(locale: str) -> str:
  normalized = locale.strip()
  if normalized in {"en", "zh-CN", "zh-TW"}:
    return normalized
  raise ValueError("Unsupported locale. Use one of: en, zh-CN, zh-TW.")


def load_template(template_name: str, locale: str) -> str:
  template_file = TEMPLATES_DIR / f"{template_name}.{locale}.md"
  if not template_file.exists():
    raise FileNotFoundError(f"Template missing: {template_file}")
  return template_file.read_text(encoding="utf-8")


def write_if_missing(path: Path, content: str) -> None:
  if path.exists():
    return
  path.write_text(content, encoding="utf-8")


def main() -> None:
  parser = argparse.ArgumentParser(
    description="Initialize memory/projects/<slug>/ with markdown long-term memory files."
  )
  parser.add_argument("--name", required=True, help="Project display name.")
  parser.add_argument("--slug", help="Project slug. Defaults to slugified --name.")
  parser.add_argument("--locale", default="en", help="Template locale: en, zh-CN, zh-TW.")
  args = parser.parse_args()

  locale = choose_locale_template_prefix(args.locale)
  slug = args.slug or slugify(args.name)

  project_dir = MEMORY_PROJECTS_DIR / slug
  project_dir.mkdir(parents=True, exist_ok=True)

  overview = load_template("project-overview", locale)
  weekly = load_template("weekly-report", locale)
  meeting = load_template("meeting-notes", locale)
  decision = load_template("decision-log", locale)

  placeholder_values = {
    "{{project_name}}": args.name,
    "{{project_slug}}": slug,
  }

  def render(text: str) -> str:
    rendered = text
    for key, value in placeholder_values.items():
      rendered = rendered.replace(key, value)
    return rendered

  write_if_missing(project_dir / "project-overview.md", render(overview))
  write_if_missing(project_dir / "weekly-report.md", render(weekly))
  write_if_missing(project_dir / "meeting-notes.md", render(meeting))
  write_if_missing(project_dir / "decision-log.md", render(decision))

  print(f"Initialized project memory directory: {project_dir}")


if __name__ == "__main__":
  main()
