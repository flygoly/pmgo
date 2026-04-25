"""Paths and environment for project-core."""

import os
import re
from pathlib import Path


def repo_root() -> Path:
  # skills/project-core/project_core/config.py -> repo root
  return Path(__file__).resolve().parents[3]


def db_path() -> Path:
  """SQLite file used by project-core (same as memory scripts)."""
  override = os.environ.get("PMGO_MEMORY_DB")
  if override:
    return Path(override).expanduser().resolve()
  return repo_root() / "memory" / "pmgo.db"


def slugify(name: str) -> str:
  slug = name.strip().lower()
  slug = re.sub(r"[^a-z0-9]+", "-", slug)
  slug = re.sub(r"-{2,}", "-", slug).strip("-")
  if not slug:
    raise ValueError("Empty slug: use an explicit --slug")
  return slug
