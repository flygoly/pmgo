"""Unit tests for Notion page helpers (mocked HTTP)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "skills" / "integration-notion"))
sys.path.insert(0, str(_ROOT / "scripts"))

from notion_integration.api import (  # noqa: E402
  list_database_pages,
  page_public,
  page_status,
  page_title,
)
from notion_integration.config import NotionConfig  # noqa: E402


class TestNotionApi(unittest.TestCase):
  def setUp(self) -> None:
    self.cfg = NotionConfig(token="secret")

  def test_page_title_and_status(self) -> None:
    page = {
      "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
      "url": "https://notion.so/x",
      "properties": {
        "Name": {
          "type": "title",
          "title": [{"plain_text": "Ship Notion"}],
        },
        "Status": {
          "type": "status",
          "status": {"name": "In progress"},
        },
      },
    }
    self.assertEqual(page_title(page), "Ship Notion")
    self.assertEqual(page_status(page), "doing")
    pub = page_public(page)
    self.assertEqual(pub["title"], "Ship Notion")

  def test_list_database_pages_paginates(self) -> None:
    page1 = {
      "results": [{"object": "page", "id": "1", "properties": {}}],
      "has_more": True,
      "next_cursor": "c2",
    }
    page2 = {
      "results": [{"object": "page", "id": "2", "properties": {}}],
      "has_more": False,
      "next_cursor": None,
    }
    with patch(
      "notion_integration.api.query_database",
      side_effect=[page1, page2],
    ):
      out = list_database_pages(self.cfg, "db", page_size=1, max_pages=5)
    self.assertEqual(len(out), 2)


if __name__ == "__main__":
  unittest.main()
