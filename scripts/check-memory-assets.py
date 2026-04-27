#!/usr/bin/env python3

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MEMORY_DIR = ROOT / "memory"
MIGRATIONS_DIR = MEMORY_DIR / "migrations"
TEMPLATES_DIR = MEMORY_DIR / "templates"
SCRIPTS_DIR = ROOT / "scripts"

MIGRATION_PATTERN = re.compile(r"^\d+_.*\.sql$")
REQUIRED_TEMPLATE_BASENAMES = {
  "project-overview",
  "meeting-notes",
  "decision-log",
  "weekly-report",
  "daily-standup",
}
REQUIRED_LOCALES = {"en", "zh-CN", "zh-TW"}
REQUIRED_SCRIPT_FILES = {
  "init-memory-db.py",
  "migrate-memory-db.py",
  "verify-memory-db.py",
  "init-memory-project.py",
  "scaffold-memory.py",
  "project-core.py",
  "pmgo_common.py",
  "daily-standup.py",
  "weekly-report.py",
  "github-issues.py",
  "pmgo_mcp_server.py",
  "pmgo_policy.py",
  "pmgo_mcp_preflight.py",
}


def assert_exists(path: Path, label: str) -> None:
  if not path.exists():
    raise FileNotFoundError(f"Missing {label}: {path}")


def check_migrations() -> None:
  assert_exists(MIGRATIONS_DIR, "migrations directory")
  migration_files = [p.name for p in MIGRATIONS_DIR.iterdir() if p.is_file() and MIGRATION_PATTERN.match(p.name)]
  if not migration_files:
    raise RuntimeError("No migration files found in memory/migrations.")


def check_templates() -> None:
  assert_exists(TEMPLATES_DIR, "templates directory")
  existing = {p.name for p in TEMPLATES_DIR.iterdir() if p.is_file() and p.suffix == ".md"}
  missing = []
  for base in sorted(REQUIRED_TEMPLATE_BASENAMES):
    for locale in sorted(REQUIRED_LOCALES):
      name = f"{base}.{locale}.md"
      if name not in existing:
        missing.append(name)
  if missing:
    raise RuntimeError(f"Missing template files: {', '.join(missing)}")


def check_scripts() -> None:
  assert_exists(SCRIPTS_DIR, "scripts directory")
  missing = [name for name in sorted(REQUIRED_SCRIPT_FILES) if not (SCRIPTS_DIR / name).exists()]
  if missing:
    raise RuntimeError(f"Missing required script files: {', '.join(missing)}")


def main() -> None:
  assert_exists(MEMORY_DIR, "memory directory")
  assert_exists(MEMORY_DIR / "schema.sql", "memory schema")
  check_migrations()
  check_templates()
  check_scripts()
  print("Memory assets check passed.")


if __name__ == "__main__":
  main()
