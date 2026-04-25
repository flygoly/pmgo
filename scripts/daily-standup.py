#!/usr/bin/env python3
"""Launch daily-standup CLI (package under skills/daily-standup)."""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(_ROOT / "scripts"), str(_ROOT / "skills" / "daily-standup")]

from daily_standup.cli import main  # noqa: E402

if __name__ == "__main__":
  raise SystemExit(main())
