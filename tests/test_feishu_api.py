"""Unit tests for Feishu task helpers (mocked HTTP)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "skills" / "integration-feishu"))
sys.path.insert(0, str(_ROOT / "scripts"))

from feishu_integration.api import (  # noqa: E402
  get_task,
  list_tasklist_tasks,
  task_to_public,
)
from feishu_integration.config import FeishuConfig  # noqa: E402


class TestFeishuApi(unittest.TestCase):
  def setUp(self) -> None:
    self.cfg = FeishuConfig(app_id="id", app_secret="secret")

  def test_list_tasklist_tasks(self) -> None:
    resp = {
      "code": 0,
      "data": {
        "items": [{"guid": "g1", "summary": "Do thing"}],
        "has_more": False,
      },
    }
    with patch(
      "feishu_integration.api._ensure_token",
      return_value="tok",
    ), patch(
      "feishu_integration.api.request_json",
      return_value=(resp, {}),
    ):
      data = list_tasklist_tasks(self.cfg, "list-guid")
    self.assertEqual(len(data.get("items") or []), 1)

  def test_get_task_and_public(self) -> None:
    resp = {
      "code": 0,
      "data": {
        "task": {
          "guid": "g1",
          "summary": "Ship",
          "description": "note",
          "completed_at": None,
        }
      },
    }
    with patch(
      "feishu_integration.api._ensure_token",
      return_value="tok",
    ), patch(
      "feishu_integration.api.request_json",
      return_value=(resp, {}),
    ):
      task = get_task(self.cfg, "g1")
    pub = task_to_public(task)
    self.assertEqual(pub["guid"], "g1")
    self.assertEqual(pub["status"], "todo")


if __name__ == "__main__":
  unittest.main()
