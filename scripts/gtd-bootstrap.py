#!/usr/bin/env python3
"""One-shot personal GTD bootstrap: DB init + linked SQLite project + markdown memory."""

from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "skills" / "project-core"))

from project_core.config import slugify  # noqa: E402
from project_core.memory_md import scaffold_project_markdown  # noqa: E402
from project_core.store import default_project_store  # noqa: E402


def _run_step(command: list[str], name: str) -> None:
  printable = " ".join(command)
  print(f"[gtd-bootstrap] {name}: {printable}")
  subprocess.run(command, cwd=ROOT, check=True)


def bootstrap_project(
  *,
  name: str,
  slug: str | None = None,
  locale: str = "en",
  owner: str | None = None,
  description: str | None = None,
) -> dict:
  """Ensure SQLite project + markdown memory exist for one slug. Idempotent by slug."""
  s = slug or slugify(name)
  store = default_project_store()
  existing = store.get_project_by_slug(s)
  if existing is None:
    try:
      project = store.create_project(
        name=name,
        slug=s,
        description=description,
        owner=owner,
      )
    except sqlite3.IntegrityError as e:
      raise RuntimeError(f"Failed to create project slug={s!r}: {e}") from e
  else:
    project = existing

  memory_dir = scaffold_project_markdown(name=name, slug=s, locale=locale)
  return {
    **project,
    "memory_dir": str(memory_dir),
    "locale": locale,
    "pmgo_default_project_id": project["id"],
  }


def main() -> None:
  parser = argparse.ArgumentParser(
    description=(
      "Initialize pmgo memory DB and create a linked SQLite + markdown project "
      "for personal GTD."
    )
  )
  parser.add_argument("--name", required=True, help="Project display name.")
  parser.add_argument("--slug", help="Project slug. Defaults to slugified --name.")
  parser.add_argument(
    "--locale",
    default="en",
    choices=["en", "zh-CN", "zh-TW"],
    help="Locale for markdown templates and suggested PMGO_DEFAULT_LOCALE.",
  )
  parser.add_argument("--owner", default=None, help="Optional project owner.")
  parser.add_argument("--description", default=None, help="Optional description.")
  parser.add_argument(
    "--skip-db-init",
    action="store_true",
    help="Skip init/migrate/verify (when DB is already initialized).",
  )
  args = parser.parse_args()

  if not args.skip_db_init:
    _run_step([sys.executable, "scripts/init-memory-db.py"], "init-db")
    _run_step([sys.executable, "scripts/migrate-memory-db.py"], "migrate-db")
    _run_step([sys.executable, "scripts/verify-memory-db.py"], "verify-db")

  result = bootstrap_project(
    name=args.name,
    slug=args.slug,
    locale=args.locale,
    owner=args.owner,
    description=args.description,
  )

  print(json.dumps(result, indent=2, default=str, ensure_ascii=False))
  print(
    "\nNext steps:\n"
    f"  export PMGO_DEFAULT_PROJECT_ID={result['id']}\n"
    f"  export PMGO_DEFAULT_LOCALE={args.locale}\n"
    "  npm run daily-standup -- report\n"
    "  See openclaw/gtd-quickstart.md for Gateway + MCP setup.",
    file=sys.stderr,
  )


if __name__ == "__main__":
  main()
