"""Paths and environment for project-core."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
if str(_SCRIPTS) not in sys.path:
  sys.path.insert(0, str(_SCRIPTS))


def repo_root() -> Path:
  """Prefer PMGO_WORKSPACE; else derive from this package path."""
  try:
    import pmgo_common

    return pmgo_common.repo_root()
  except ImportError:
    return Path(__file__).resolve().parents[3]


def db_path() -> Path:
  """SQLite file used by project-core (same as memory scripts)."""
  try:
    import pmgo_common

    return pmgo_common.db_path()
  except ImportError:
    override = os.environ.get("PMGO_MEMORY_DB")
    if override:
      return Path(override).expanduser().resolve()
    return Path(__file__).resolve().parents[3] / "memory" / "pmgo.db"


def slugify(name: str) -> str:
  slug = name.strip().lower()
  slug = re.sub(r"[^a-z0-9]+", "-", slug)
  slug = re.sub(r"-{2,}", "-", slug).strip("-")
  if not slug:
    raise ValueError("Empty slug: use an explicit --slug")
  return slug
