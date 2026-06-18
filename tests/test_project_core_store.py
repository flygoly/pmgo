"""Unit tests for project_core SQLite stores."""

from __future__ import annotations

import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "skills" / "project-core"))

from project_core.memory_md import scaffold_project_markdown  # noqa: E402
from project_core.store import (  # noqa: E402
  DecisionStore,
  MilestoneStore,
  ProjectStore,
  RiskStore,
  TaskStore,
)

from test_helpers import init_test_db  # noqa: E402


class TestProjectCoreStore(unittest.TestCase):
  def setUp(self) -> None:
    self._tmpdir = tempfile.TemporaryDirectory()
    self.db_path = Path(self._tmpdir.name) / "test.db"
    init_test_db(self.db_path)
    os.environ["PMGO_MEMORY_DB"] = str(self.db_path)
    self.projects = ProjectStore(self.db_path)
    self.tasks = TaskStore(self.db_path)
    self.milestones = MilestoneStore(self.db_path)
    self.risks = RiskStore(self.db_path)
    self.decisions = DecisionStore(self.db_path)

  def tearDown(self) -> None:
    os.environ.pop("PMGO_MEMORY_DB", None)
    self._tmpdir.cleanup()

  def test_project_create_and_lookup_by_slug(self) -> None:
    row = self.projects.create_project(name="Demo", slug="demo")
    self.assertEqual(row["slug"], "demo")
    found = self.projects.get_project_by_slug("demo")
    self.assertIsNotNone(found)
    assert found is not None
    self.assertEqual(found["id"], row["id"])

  def test_task_create_and_update(self) -> None:
    project = self.projects.create_project(name="Demo", slug="demo")
    task = self.tasks.create_task(project["id"], title="First task")
    updated = self.tasks.update_task(task["id"], status="doing", priority="high")
    self.assertEqual(updated["status"], "doing")
    self.assertEqual(updated["priority"], "high")

  def test_task_external_id_dedupe(self) -> None:
    project = self.projects.create_project(name="Demo", slug="demo")
    self.tasks.create_task(
      project["id"],
      title="GH-1",
      source="github",
      external_id="999",
    )
    with self.assertRaises(sqlite3.IntegrityError):
      self.tasks.create_task(
        project["id"],
        title="GH-1 duplicate",
        source="github",
        external_id="999",
      )

  def test_milestone_crud(self) -> None:
    project = self.projects.create_project(name="Demo", slug="demo")
    ms = self.milestones.create_milestone(
      project["id"],
      title="M1 release",
      status="todo",
    )
    listed = self.milestones.list_milestones(project["id"])
    self.assertEqual(len(listed), 1)
    updated = self.milestones.update_milestone(ms["id"], status="doing")
    self.assertEqual(updated["status"], "doing")

  def test_risk_crud(self) -> None:
    project = self.projects.create_project(name="Demo", slug="demo-risk")
    risk = self.risks.create_risk(
      project["id"],
      title="Schedule slip",
      severity="high",
    )
    listed = self.risks.list_risks(project["id"])
    self.assertEqual(len(listed), 1)
    updated = self.risks.update_risk(risk["id"], status="watching")
    self.assertEqual(updated["status"], "watching")

  def test_decision_crud(self) -> None:
    project = self.projects.create_project(name="Demo", slug="demo-decision")
    dec = self.decisions.create_decision(
      project["id"],
      title="Use SQLite",
      status="proposed",
      rationale="Local-first",
    )
    listed = self.decisions.list_decisions(project["id"])
    self.assertEqual(len(listed), 1)
    updated = self.decisions.update_decision(
      dec["id"],
      status="accepted",
      decided_by="team",
    )
    self.assertEqual(updated["status"], "accepted")
    self.assertEqual(updated["decided_by"], "team")

  def test_risk_task_marker_dedupe(self) -> None:
    project = self.projects.create_project(name="Demo", slug="demo-marker")
    marker = "pmgo_task_id:abc-123"
    self.assertFalse(self.risks.has_risk_for_task_marker(project["id"], marker))
    self.risks.create_risk(
      project["id"],
      title="Stale blocker",
      evidence=marker,
    )
    self.assertTrue(self.risks.has_risk_for_task_marker(project["id"], marker))

  def test_scaffold_markdown_creates_files(self) -> None:
    slug = "demo-test-scaffold-unit"
    project_dir = scaffold_project_markdown(
      name="Demo",
      slug=slug,
      locale="en",
    )
    try:
      self.assertTrue((project_dir / "project-overview.md").is_file())
      self.assertTrue((project_dir / "decision-log.md").is_file())
      mtime = (project_dir / "project-overview.md").stat().st_mtime
      scaffold_project_markdown(name="Demo", slug=slug, locale="en")
      self.assertEqual(
        (project_dir / "project-overview.md").stat().st_mtime,
        mtime,
      )
    finally:
      import shutil
      if project_dir.is_dir():
        shutil.rmtree(project_dir, ignore_errors=True)


if __name__ == "__main__":
  unittest.main()
