#!/usr/bin/env python3
"""Linear GraphQL CLI (package under skills/integration-linear)."""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "skills" / "integration-linear"))

from linear_integration.cli import main  # noqa: E402

if __name__ == "__main__":
  raise SystemExit(main())
