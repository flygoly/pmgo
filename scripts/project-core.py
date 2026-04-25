#!/usr/bin/env python3
"""Launch project-core CLI (package lives under skills/project-core)."""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "skills" / "project-core"))

from project_core.cli import main  # noqa: E402

if __name__ == "__main__":
  raise SystemExit(main())
