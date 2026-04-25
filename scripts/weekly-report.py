#!/usr/bin/env python3
"""Launch weekly-report CLI (package under skills/weekly-report)."""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(_ROOT / "scripts"), str(_ROOT / "skills" / "weekly-report")]

from weekly_report.cli import main  # noqa: E402

if __name__ == "__main__":
  raise SystemExit(main())
