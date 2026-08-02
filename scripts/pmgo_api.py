#!/usr/bin/env python3
"""Source-tree launcher for the standalone pmgo API."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pmgo_app.api import main  # noqa: E402

raise SystemExit(main())
