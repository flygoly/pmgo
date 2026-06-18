"""Unit tests for risk-radar scan."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "skills" / "project-core"))
sys.path.insert(0, str(_ROOT / "skills" / "risk-radar"))

from project_core.store import ProjectStore, TaskStore  # noqa: E402
from risk_radar.scan import scan_project  # noqa: E402

from test_helpers import init_test_db  # noqa: E402


class TestRiskRadarScan(unittest.TestCase):
  def setUp(self) -> None:
    self._tmpdir = tempfile.TemporaryDirectory()
    self.db_path = Path(self._tmpdir.name) / "test.db"
    init_test_db(self.db_path)
    os.environ["PMGO_MEMORY_DB"] = str(self.db_path)
    self.projects = ProjectStore(self.db_path)
    self.tasks = TaskStore(self.db_path)
    project = self.projects.create_project(name="Scan Demo", slug="scan-demo")
    self.project_id = project["id"]

  def tearDown(self) -> None:
    os.environ.pop("PMGO_MEMORY_DB", None)
    self._tmpdir.cleanup()

  def test_stale_blocked_detection(self) -> None:
    now = datetime(2026, 6, 16, 12, 0, tzinfo=timezone.utc)
    task = self.tasks.create_task(
      self.project_id,
      title="Stuck task",
      status="blocked",
    )
    old_ts = (now - timedelta(hours=30)).isoformat()
    self.tasks.update_task(task["id"], blocked_reason="waiting on vendor")
    import sqlite3
    with sqlite3.connect(self.db_path) as conn:
      conn.execute(
        "UPDATE tasks SET updated_at = ? WHERE id = ?",
        (old_ts, task["id"]),
      )
      conn.commit()

    out = scan_project(self.project_id, now=now)
    self.assertEqual(out["summary"]["stale_blocked_count"], 1)
    self.assertEqual(len(out["tasks_blocked_stale_24h"]), 1)
    self.assertEqual(out["tasks_blocked_stale_24h"][0]["title"], "Stuck task")


if __name__ == "__main__":
  unittest.main()
