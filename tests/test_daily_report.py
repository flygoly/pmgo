"""Tests for daily-report template rendering."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))
sys.path.insert(0, str(_ROOT / "skills" / "daily-standup"))
sys.path.insert(0, str(_ROOT / "skills" / "project-core"))

from daily_standup.build import build_daily_markdown, save_daily_markdown  # noqa: E402
from project_core.store import ProjectStore, TaskStore  # noqa: E402

from test_helpers import init_test_db  # noqa: E402


class TestDailyReport(unittest.TestCase):
  def setUp(self) -> None:
    self._tmpdir = tempfile.TemporaryDirectory()
    self.db_path = Path(self._tmpdir.name) / "test.db"
    init_test_db(self.db_path)
    os.environ["PMGO_MEMORY_DB"] = str(self.db_path)
    os.environ["PMGO_WORKSPACE"] = str(_ROOT)
    projects = ProjectStore(self.db_path)
    tasks = TaskStore(self.db_path)
    self.project = projects.create_project(name="日报 Demo", slug="daily-demo")
    tasks.create_task(self.project["id"], title="写日报模板", status="done")
    tasks.create_task(self.project["id"], title="联调 MCP", status="doing")
    tasks.create_task(self.project["id"], title="明天评审", status="todo")

  def tearDown(self) -> None:
    os.environ.pop("PMGO_MEMORY_DB", None)
    os.environ.pop("PMGO_WORKSPACE", None)
    self._tmpdir.cleanup()

  def test_daily_report_zh_cn(self) -> None:
    now = datetime(2026, 7, 26, 12, 0, tzinfo=timezone.utc)
    # Mark done task as updated inside 24h window
    import sqlite3

    conn = sqlite3.connect(self.db_path)
    conn.execute(
      "UPDATE tasks SET updated_at = ? WHERE title = ?",
      ("2026-07-26T10:00:00+00:00", "写日报模板"),
    )
    conn.commit()
    conn.close()

    md = build_daily_markdown(
      project_id=self.project["id"],
      locale="zh-CN",
      now=now,
      template="daily-report",
    )
    self.assertIn("每日日报", md)
    self.assertIn("日报 Demo", md)
    self.assertIn("今日完成", md)
    self.assertIn("明日计划", md)
    self.assertIn("写日报模板", md)
    self.assertIn("联调 MCP", md)
    self.assertIn("明天评审", md)

  def test_save_daily_report(self) -> None:
    now = datetime(2026, 7, 26, 12, 0, tzinfo=timezone.utc)
    md = build_daily_markdown(
      project_id=self.project["id"],
      locale="en",
      now=now,
      template="daily-report",
    )
    # Redirect project folder under tmp by patching repo_root via workspace
    # save uses repo_root()/memory/projects — write into real workspace projects
    # which is gitignored; use unique slug already set.
    path = save_daily_markdown(md, project_id=self.project["id"], now=now)
    self.assertTrue(path.is_file())
    self.assertEqual(path.name, "2026-07-26.md")
    self.assertIn("daily-reports", str(path))
    self.assertIn("Daily report", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
  unittest.main()
