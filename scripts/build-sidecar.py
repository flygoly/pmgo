#!/usr/bin/env python3
"""Build the Python core as the native sidecar consumed by Electron."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist" / "sidecar" / "bin"


def main() -> int:
  DIST.mkdir(parents=True, exist_ok=True)
  name = "pmgo-api"
  command = [
    sys.executable, "-m", "PyInstaller", "--clean", "--onefile", "--name", name,
    "--distpath", str(DIST), "--workpath", str(ROOT / "build" / "pyinstaller"),
    "--specpath", str(ROOT / "build"), "--add-data", f"pmgo_app/schema.sql{os.pathsep}pmgo_app",
    str(ROOT / "scripts" / "pmgo_api.py"),
  ]
  subprocess.run(command, cwd=ROOT, check=True)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
