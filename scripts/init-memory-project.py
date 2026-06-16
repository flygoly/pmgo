#!/usr/bin/env python3
"""Initialize memory/projects/<slug>/ with markdown long-term memory files."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "skills" / "project-core"))

from project_core.memory_md import scaffold_project_markdown  # noqa: E402
from project_core.config import slugify  # noqa: E402


def main() -> None:
  parser = argparse.ArgumentParser(
    description="Initialize memory/projects/<slug>/ with markdown long-term memory files."
  )
  parser.add_argument("--name", required=True, help="Project display name.")
  parser.add_argument("--slug", help="Project slug. Defaults to slugified --name.")
  parser.add_argument("--locale", default="en", help="Template locale: en, zh-CN, zh-TW.")
  args = parser.parse_args()

  slug = args.slug or slugify(args.name)
  project_dir = scaffold_project_markdown(
    name=args.name,
    slug=slug,
    locale=args.locale,
  )
  print(f"Initialized project memory directory: {project_dir}")


if __name__ == "__main__":
  main()
