"""Unit tests for daily / weekly report builders."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "skills" / "project-core"))
sys.path.insert(0, str(_ROOT / "skills" / "daily-standup"))
sys.path.insert(0, str(_ROOT / "skills" / "weekly-report"))
sys.path.insert(0, str(_ROOT / "scripts"))

from daily_standup.build import build_daily_markdown  # noqa: E402
from project_core.store import ProjectStore, TaskStore  # noqa: E402
from weekly_report.build import build_weekly_markdown  # noqa: E402

import pmgo_common  # noqa: E402

from test_helpers import init_test_db  # noqa: E402


class TestReportBuild(unittest.TestCase):
  def setUp(self) -> None:
    self._tmpdir = tempfile.TemporaryDirectory()
    self.db_path = Path(self._tmpdir.name) / "test.db"
    init_test_db(self.db_path)
    os.environ["PMGO_MEMORY_DB"] = str(self.db_path)
    self.projects = ProjectStore(self.db_path)
    self.tasks = TaskStore(self.db_path)
    project = self.projects.create_project(name="Report Demo", slug="report-demo")
    self.project_id = project["id"]
    self.tasks.create_task(self.project_id, title="In progress item", status="doing")
    self.tasks.create_task(self.project_id, title="Blocked item", status="blocked")
    self.tasks.create_task(self.project_id, title="Todo item", status="todo")
    from project_core.store import RiskStore  # noqa: E402
    risks = RiskStore(self.db_path)
    risks.create_risk(self.project_id, title="Vendor delay", severity="high")

  def tearDown(self) -> None:
    os.environ.pop("PMGO_DEFAULT_PROJECT_ID", None)
    os.environ.pop("PMGO_MEMORY_DB", None)
    self._tmpdir.cleanup()

  def test_daily_report_contains_sections(self) -> None:
    now = datetime(2026, 6, 16, 12, 0, tzinfo=timezone.utc)
    text = build_daily_markdown(
      project_id=self.project_id,
      locale="en",
      now=now,
    )
    self.assertIn("# Daily — Report Demo", text)
    self.assertIn("In progress item", text)
    self.assertIn("Blocked item", text)
    self.assertIn("Vendor delay", text)
    self.assertIn("Active risks", text)
    self.assertIn("Todo item", text)
    self.assertNotIn("{{", text)

  def test_weekly_report_on_track(self) -> None:
    now = datetime(2026, 6, 16, 12, 0, tzinfo=timezone.utc)
    text = build_weekly_markdown(
      project_id=self.project_id,
      locale="en",
      now=now,
    )
    self.assertIn("# Weekly Report - Report Demo", text)
    self.assertIn("At risk", text)  # blocked task present
    self.assertNotIn("{{", text)

  def test_resolve_project_id_prefers_explicit(self) -> None:
    os.environ["PMGO_DEFAULT_PROJECT_ID"] = "other-id"
    resolved = pmgo_common.resolve_project_id(explicit=self.project_id)
    self.assertEqual(resolved, self.project_id)

  def test_resolve_project_id_uses_env_default(self) -> None:
    os.environ["PMGO_DEFAULT_PROJECT_ID"] = self.project_id
    resolved = pmgo_common.resolve_project_id()
    self.assertEqual(resolved, self.project_id)


if __name__ == "__main__":
  unittest.main()
