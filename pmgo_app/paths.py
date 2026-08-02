"""Cross-platform local data and configuration paths."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def default_data_dir() -> Path:
  override = os.environ.get("PMGO_DATA_DIR", "").strip()
  if override:
    return Path(override).expanduser().resolve()
  if sys.platform == "darwin":
    return Path.home() / "Library" / "Application Support" / "pmgo"
  if os.name == "nt":
    base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
    return base / "pmgo"
  base = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
  return base / "pmgo"


def database_path(data_dir: Path | None = None) -> Path:
  return (data_dir or default_data_dir()) / "pmgo.db"
