"""Unit tests for Live Canvas JSON builders."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))
sys.path.insert(0, str(_ROOT / "skills" / "canvas-data"))
sys.path.insert(0, str(_ROOT / "skills" / "project-core"))

from canvas_data.build import build_burndown, build_gantt, build_snapshot  # noqa: E402
from canvas_data.render import embed_snapshot, render_canvas, template_path  # noqa: E402
from project_core.store import MilestoneStore, ProjectStore, TaskStore  # noqa: E402

from test_helpers import init_test_db  # noqa: E402


class TestCanvasData(unittest.TestCase):
  def setUp(self) -> None:
    self._tmpdir = tempfile.TemporaryDirectory()
    self.db_path = Path(self._tmpdir.name) / "test.db"
    init_test_db(self.db_path)
    os.environ["PMGO_MEMORY_DB"] = str(self.db_path)
    projects = ProjectStore(self.db_path)
    tasks = TaskStore(self.db_path)
    milestones = MilestoneStore(self.db_path)
    self.project = projects.create_project(name="Canvas", slug="canvas")
    milestones.create_milestone(
      self.project["id"],
      title="M1",
      status="doing",
      due_at="2026-07-20T00:00:00+00:00",
    )
    tasks.create_task(
      self.project["id"],
      title="A",
      status="doing",
      due_at="2026-07-18T00:00:00+00:00",
    )
    tasks.create_task(self.project["id"], title="B", status="done")

  def tearDown(self) -> None:
    os.environ.pop("PMGO_MEMORY_DB", None)
    self._tmpdir.cleanup()

  def test_gantt(self) -> None:
    g = build_gantt(self.project["id"])
    self.assertEqual(g["schema"], "pmgo.canvas.gantt/v1")
    self.assertEqual(len(g["milestones"]), 1)
    self.assertEqual(len(g["tasks"]), 2)

  def test_burndown_and_snapshot(self) -> None:
    now = datetime(2026, 7, 15, 12, 0, tzinfo=timezone.utc)
    b = build_burndown(self.project["id"], now=now)
    self.assertEqual(b["schema"], "pmgo.canvas.burndown/v1")
    self.assertEqual(len(b["points"]), 8)
    snap = build_snapshot(self.project["id"], now=now)
    self.assertIn("gantt", snap)
    self.assertIn("burndown", snap)

  def test_render_canvas_writes_html_and_data(self) -> None:
    out = Path(self._tmpdir.name) / "canvas-out"
    result = render_canvas(self.project["id"], out_dir=out, inline=True)
    self.assertTrue(result["ok"])
    index = Path(result["index_html"])
    data = Path(result["data_json"])
    self.assertTrue(index.is_file())
    self.assertTrue(data.is_file())
    html = index.read_text(encoding="utf-8")
    self.assertIn("pmgo.canvas.snapshot/v1", html)
    self.assertIn(self.project["name"], html)
    self.assertIn("window.__PMGO_DATA__", html)
    self.assertNotIn("window.__PMGO_DATA__ = null", html)
    payload = data.read_text(encoding="utf-8")
    self.assertIn("pmgo.canvas.snapshot/v1", payload)
    notes = result.get("runtime_notes") or {}
    self.assertIn("openclaw", notes)
    self.assertIn("hermes", notes)
    self.assertIn("No canvasHost", notes["hermes"])
    self.assertNotIn("present_hint", result)
    self.assertNotIn("openclaw_example", result)

  def test_embed_snapshot_requires_markers(self) -> None:
    with self.assertRaises(ValueError):
      embed_snapshot("<html></html>", {"schema": "pmgo.canvas.snapshot/v1"})

  def test_template_exists(self) -> None:
    self.assertTrue(template_path().is_file())


if __name__ == "__main__":
  unittest.main()
