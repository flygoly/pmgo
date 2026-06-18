"""Unit tests for stale-blocker risk escalation."""

from __future__ import annotations

import os
import sqlite3
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "skills" / "project-core"))
sys.path.insert(0, str(_ROOT / "skills" / "risk-radar"))

from project_core.store import ProjectStore, RiskStore, TaskStore  # noqa: E402
from risk_radar.escalate import escalate_stale_blockers, task_evidence_marker  # noqa: E402

from test_helpers import init_test_db  # noqa: E402


class TestRiskEscalate(unittest.TestCase):
  def setUp(self) -> None:
    self._tmpdir = tempfile.TemporaryDirectory()
    self.db_path = Path(self._tmpdir.name) / "test.db"
    init_test_db(self.db_path)
    os.environ["PMGO_MEMORY_DB"] = str(self.db_path)
    self.projects = ProjectStore(self.db_path)
    self.tasks = TaskStore(self.db_path)
    self.risks = RiskStore(self.db_path)
    project = self.projects.create_project(name="Escalate Demo", slug="esc-demo")
    self.project_id = project["id"]
    self.now = datetime(2026, 6, 16, 12, 0, tzinfo=timezone.utc)

  def tearDown(self) -> None:
    os.environ.pop("PMGO_MEMORY_DB", None)
    self._tmpdir.cleanup()

  def _make_stale_blocked(self, title: str) -> str:
    task = self.tasks.create_task(
      self.project_id,
      title=title,
      status="blocked",
    )
    self.tasks.update_task(task["id"], blocked_reason="vendor delay")
    old_ts = (self.now - timedelta(hours=30)).isoformat()
    with sqlite3.connect(self.db_path) as conn:
      conn.execute(
        "UPDATE tasks SET updated_at = ? WHERE id = ?",
        (old_ts, task["id"]),
      )
      conn.commit()
    return task["id"]

  def test_escalate_creates_risk_for_stale_blocker(self) -> None:
    tid = self._make_stale_blocked("Stuck task")
    out = escalate_stale_blockers(self.project_id, self.risks, now=self.now)
    self.assertEqual(out["created_count"], 1)
    self.assertEqual(out["skipped_count"], 0)
    marker = task_evidence_marker(tid)
    self.assertTrue(self.risks.has_risk_for_task_marker(self.project_id, marker))

  def test_escalate_skips_when_risk_exists(self) -> None:
    tid = self._make_stale_blocked("Already tracked")
    marker = task_evidence_marker(tid)
    self.risks.create_risk(
      self.project_id,
      title="Existing",
      evidence=marker,
    )
    out = escalate_stale_blockers(self.project_id, self.risks, now=self.now)
    self.assertEqual(out["created_count"], 0)
    self.assertEqual(out["skipped_count"], 1)


if __name__ == "__main__":
  unittest.main()
