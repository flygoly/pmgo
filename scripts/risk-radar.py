#!/usr/bin/env python3
"""Launch risk-radar CLI (package under skills/risk-radar)."""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(_ROOT / "scripts"), str(_ROOT / "skills" / "risk-radar")]

from risk_radar.cli import main  # noqa: E402

if __name__ == "__main__":
  raise SystemExit(main())
