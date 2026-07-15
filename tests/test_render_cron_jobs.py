"""Tests for scripts/render-cron-jobs.py."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent


class TestRenderCronJobs(unittest.TestCase):
  def test_openclaw_output(self) -> None:
    proc = subprocess.run(
      [
        sys.executable,
        str(_ROOT / "scripts" / "render-cron-jobs.py"),
        "--runtime",
        "openclaw",
      ],
      capture_output=True,
      text=True,
      check=False,
      cwd=_ROOT,
    )
    self.assertEqual(proc.returncode, 0, msg=proc.stderr)
    self.assertIn("openclaw cron add", proc.stdout)
    self.assertIn("pmgo-morning-briefing", proc.stdout)

  def test_hermes_output(self) -> None:
    proc = subprocess.run(
      [
        sys.executable,
        str(_ROOT / "scripts" / "render-cron-jobs.py"),
        "--runtime",
        "hermes",
      ],
      capture_output=True,
      text=True,
      check=False,
      cwd=_ROOT,
    )
    self.assertEqual(proc.returncode, 0, msg=proc.stderr)
    self.assertIn("hermes cron create", proc.stdout)


if __name__ == "__main__":
  unittest.main()
