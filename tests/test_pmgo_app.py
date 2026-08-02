"""Tests for the runtime-independent local application core and API."""

from __future__ import annotations

import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from pmgo_app.api import make_handler
from pmgo_app.core import LocalCore


class TestLocalCore(unittest.TestCase):
  def setUp(self) -> None:
    self.temp = tempfile.TemporaryDirectory()
    self.core = LocalCore(Path(self.temp.name))
    self.project = self.core.initialize(project_name="我的工作", locale="zh-Hans")

  def tearDown(self) -> None:
    self.temp.cleanup()

  def test_initializes_local_database_and_markdown(self) -> None:
    self.assertTrue(self.core.db_file.is_file())
    self.assertTrue((self.core.projects_dir / "personal-office" / "project-overview.md").is_file())
    self.assertEqual(self.core.dashboard()["projects"][0]["name"], "我的工作")

  def test_create_and_update_task(self) -> None:
    task = self.core.create_task({"project_id": self.project["id"], "title": "整理周报"})
    self.assertEqual(task["status"], "todo")
    updated = self.core.update_task(task["id"], {"status": "doing"})
    self.assertEqual(updated["status"], "doing")
    self.assertEqual(self.core.dashboard()["counts"]["doing"], 1)

  def test_projects_notes_and_context(self) -> None:
    project = self.core.create_project({"name": "第二个项目", "description": "移动端准备"})
    self.core.create_task({"project_id": project["id"], "title": "完成桌面端", "priority": "high"})
    note = self.core.write_note(project["id"], "overview", "# 目标\n\n先完成桌面客户端。")
    self.assertIn("桌面客户端", note["content"])
    context = self.core.build_context(project["id"])
    self.assertEqual(context["task_count"], 1)
    self.assertIn("完成桌面端", context["text"])
    self.assertIn("先完成桌面客户端", context["text"])

  def test_task_validation_and_delete(self) -> None:
    with self.assertRaises(ValueError):
      self.core.create_task({"project_id": self.project["id"], "title": "", "status": "unknown"})
    task = self.core.create_task({"project_id": self.project["id"], "title": "临时任务"})
    self.core.delete_task(task["id"])
    self.assertEqual(self.core.dashboard()["tasks"], [])


class TestLocalApi(unittest.TestCase):
  def setUp(self) -> None:
    self.temp = tempfile.TemporaryDirectory()
    core = LocalCore(Path(self.temp.name))
    self.project = core.initialize()
    try:
      self.server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(core, "test-token"))
    except PermissionError:
      self.temp.cleanup()
      self.skipTest("loopback sockets are unavailable in this sandbox")
    self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
    self.thread.start()
    self.base = f"http://127.0.0.1:{self.server.server_address[1]}"

  def tearDown(self) -> None:
    self.server.shutdown()
    self.server.server_close()
    self.thread.join()
    self.temp.cleanup()

  def request(self, route: str, *, method: str = "GET", body: dict | None = None, token: str = "test-token"):
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(
      self.base + route, data=data, method=method,
      headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request) as response:
      return response.status, json.loads(response.read())

  def test_health_is_public_but_dashboard_requires_token(self) -> None:
    status, value = self.request("/health", token="wrong")
    self.assertEqual((status, value), (200, {"ok": True}))
    with self.assertRaises(urllib.error.HTTPError) as error:
      self.request("/api/dashboard", token="wrong")
    self.assertEqual(error.exception.code, 401)

  def test_task_roundtrip(self) -> None:
    status, task = self.request("/api/tasks", method="POST", body={"project_id": self.project["id"], "title": "Local task"})
    self.assertEqual(status, 201)
    _, updated = self.request(f"/api/tasks/{task['id']}", method="PATCH", body={"status": "done"})
    self.assertEqual(updated["status"], "done")
