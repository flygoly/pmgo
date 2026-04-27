#!/usr/bin/env python3
"""GitHub Issues CLI (package under skills/integration-github)."""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "skills" / "integration-github"))

from github_integration.cli import main  # noqa: E402

if __name__ == "__main__":
  raise SystemExit(main())
