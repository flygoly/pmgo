"""GitHub list_issues pagination (mocked HTTP)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "skills" / "integration-github"))
sys.path.insert(0, str(_ROOT / "scripts"))

from github_integration.api import list_issues  # noqa: E402
from github_integration.config import GitHubConfig  # noqa: E402


class TestGithubApiPagination(unittest.TestCase):
  def test_list_issues_pages(self) -> None:
    cfg = GitHubConfig(token="t", owner="o", repo="r", user_agent="pmgo-test")
    page1 = [{"id": 1, "number": 1, "title": "a", "state": "open"}]
    page2 = [{"id": 2, "number": 2, "title": "b", "state": "open"}]
    calls: list[str] = []

    def fake_request(_c, _method, _path, *, body=None, query=None):
      calls.append(query.get("page", "1") if query else "1")
      if query and query.get("page") == "1":
        return page1
      if query and query.get("page") == "2":
        return page2
      return []

    with patch("github_integration.api._request", side_effect=fake_request):
      out = list_issues(cfg, per_page=1, max_pages=5)
    self.assertEqual(len(out), 2)
    self.assertEqual(calls[:3], ["1", "2", "3"])


if __name__ == "__main__":
  unittest.main()
