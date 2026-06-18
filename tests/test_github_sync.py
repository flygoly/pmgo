"""Unit tests for GitHub issue → task sync (no live API)."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "skills" / "integration-github"))
sys.path.insert(0, str(_ROOT / "skills" / "project-core"))

from github_integration.sync import import_issue_as_task, sync_issues_to_project  # noqa: E402
from project_core.store import ProjectStore, TaskStore  # noqa: E402

from test_helpers import init_test_db  # noqa: E402


def _issue(number: int, gh_id: int, title: str = "Bug") -> dict:
  return {
    "number": number,
    "id": gh_id,
    "title": title,
    "body": "details",
    "state": "open",
    "html_url": f"https://github.com/o/r/issues/{number}",
  }


class TestGitHubSync(unittest.TestCase):
  def setUp(self) -> None:
    self._tmpdir = tempfile.TemporaryDirectory()
    self.db_path = Path(self._tmpdir.name) / "test.db"
    init_test_db(self.db_path)
    os.environ["PMGO_MEMORY_DB"] = str(self.db_path)
    self.projects = ProjectStore(self.db_path)
    self.tasks = TaskStore(self.db_path)
    project = self.projects.create_project(name="GH Sync", slug="gh-sync")
    self.project_id = project["id"]

  def tearDown(self) -> None:
    os.environ.pop("PMGO_MEMORY_DB", None)
    self._tmpdir.cleanup()

  def test_import_issue_as_task_idempotent(self) -> None:
    issue = _issue(1, 1001)
    row = import_issue_as_task(self.tasks, self.project_id, issue)
    self.assertIsNotNone(row)
    assert row is not None
    self.assertEqual(row["source"], "github")
    self.assertEqual(row["external_id"], "1001")
    again = import_issue_as_task(self.tasks, self.project_id, issue)
    self.assertIsNone(again)

  def test_sync_issues_to_project_counts(self) -> None:
    cfg = MagicMock()
    issues = [_issue(1, 2001), _issue(2, 2002)]
    with unittest.mock.patch(
      "github_integration.sync.list_issues",
      return_value=issues,
    ):
      out = sync_issues_to_project(cfg, self.tasks, self.project_id)
    self.assertEqual(out["scanned"], 2)
    self.assertEqual(out["imported_count"], 2)
    self.assertEqual(out["skipped_count"], 0)
    with unittest.mock.patch(
      "github_integration.sync.list_issues",
      return_value=issues,
    ):
      again = sync_issues_to_project(cfg, self.tasks, self.project_id)
    self.assertEqual(again["imported_count"], 0)
    self.assertEqual(again["skipped_count"], 2)


if __name__ == "__main__":
  unittest.main()
