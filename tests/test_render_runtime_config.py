"""Tests for scripts/render-runtime-config.py."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent


class TestRenderRuntimeConfig(unittest.TestCase):
  def test_openclaw_output_contains_mcp_set(self) -> None:
    proc = subprocess.run(
      [
        sys.executable,
        str(_ROOT / "scripts" / "render-runtime-config.py"),
        "--runtime",
        "openclaw",
      ],
      capture_output=True,
      text=True,
      check=False,
      cwd=_ROOT,
    )
    self.assertEqual(proc.returncode, 0, msg=proc.stderr)
    self.assertIn("openclaw mcp set pmgo", proc.stdout)
    self.assertIn("pmgo_mcp_server.py", proc.stdout)

  def test_hermes_output_contains_mcp_servers(self) -> None:
    proc = subprocess.run(
      [
        sys.executable,
        str(_ROOT / "scripts" / "render-runtime-config.py"),
        "--runtime",
        "hermes",
      ],
      capture_output=True,
      text=True,
      check=False,
      cwd=_ROOT,
    )
    if "PyYAML required" in proc.stderr:
      self.skipTest("PyYAML not installed")
    self.assertEqual(proc.returncode, 0, msg=proc.stderr)
    self.assertIn("mcp_servers:", proc.stdout)
    self.assertIn("pmgo:", proc.stdout)


if __name__ == "__main__":
  unittest.main()
