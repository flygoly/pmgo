#!/usr/bin/env python3
"""Jira Cloud REST CLI (package under skills/integration-jira)."""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "skills" / "integration-jira"))

from jira_integration.cli import main  # noqa: E402

if __name__ == "__main__":
  raise SystemExit(main())
