"""Tests for scripts/render-cron-jobs.py."""

from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent


class TestRenderCronJobs(unittest.TestCase):
  def _run(self, runtime: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    full_env = os.environ.copy()
    if env:
      full_env.update(env)
    return subprocess.run(
      [
        sys.executable,
        str(_ROOT / "scripts" / "render-cron-jobs.py"),
        "--runtime",
        runtime,
      ],
      capture_output=True,
      text=True,
      check=False,
      cwd=_ROOT,
      env=full_env,
    )

  def test_openclaw_output(self) -> None:
    proc = self._run("openclaw")
    self.assertEqual(proc.returncode, 0, msg=proc.stderr)
    self.assertIn("openclaw cron add", proc.stdout)
    self.assertIn("pmgo-morning-briefing", proc.stdout)
    self.assertIn("--tz Asia/Shanghai", proc.stdout)
    self.assertIn("--tz UTC", proc.stdout)

  def test_hermes_output_positional_cli(self) -> None:
    proc = self._run(
      "hermes",
      env={
        "HERMES_CRON_DELIVER": "telegram",
        "PMGO_WORKSPACE": "/tmp/pmgo-ws",
      },
    )
    self.assertEqual(proc.returncode, 0, msg=proc.stderr)
    self.assertIn("hermes cron create", proc.stdout)
    # Positional schedule + prompt (not --cron / --schedule / --message)
    self.assertIn("hermes cron create '0 9 * * 1-5'", proc.stdout)
    self.assertNotIn("--cron ", proc.stdout)
    self.assertNotIn("--schedule ", proc.stdout)
    self.assertNotIn("--message ", proc.stdout)
    self.assertNotIn("--timezone ", proc.stdout)
    self.assertIn("--name pmgo-morning-briefing", proc.stdout)
    self.assertIn("--deliver telegram", proc.stdout)
    self.assertIn("--workdir /tmp/pmgo-ws", proc.stdout)
    self.assertIn("multiple tz values", proc.stdout)


if __name__ == "__main__":
  unittest.main()
