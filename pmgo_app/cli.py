"""Installed console entry point for the repository CLI."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
  script = Path(__file__).resolve().parent.parent / "scripts" / "pmgo_cli.py"
  spec = importlib.util.spec_from_file_location("pmgo_repository_cli", script)
  if spec is None or spec.loader is None:
    raise RuntimeError(f"Cannot load pmgo CLI: {script}")
  module = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(module)
  return int(module.main(argv) or 0)
