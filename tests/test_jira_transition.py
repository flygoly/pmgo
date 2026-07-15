"""Unit tests for Jira transition helpers (mocked HTTP)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "skills" / "integration-jira"))
sys.path.insert(0, str(_ROOT / "scripts"))

from jira_integration.api import list_transitions, transition_issue  # noqa: E402
from jira_integration.config import JiraConfig  # noqa: E402


class TestJiraTransition(unittest.TestCase):
  def setUp(self) -> None:
    self.cfg = JiraConfig(
      base_url="https://example.atlassian.net",
      email="u@example.com",
      api_token="tok",
      user_agent="pmgo-test",
      default_project=None,
    )

  def test_list_transitions(self) -> None:
    payload = {
      "transitions": [
        {"id": "11", "name": "To Do", "to": {"name": "To Do"}},
        {"id": "21", "name": "Done", "to": {"name": "Done"}},
      ]
    }
    with patch("jira_integration.api._request", return_value=payload) as req:
      out = list_transitions(self.cfg, "PROJ-1")
    self.assertEqual(len(out), 2)
    req.assert_called_once()

  def test_transition_issue_posts(self) -> None:
    with patch("jira_integration.api._request", return_value=None) as req:
      transition_issue(self.cfg, "PROJ-1", transition_id="21")
    args, kwargs = req.call_args
    self.assertEqual(args[1], "POST")
    self.assertIn("/transitions", args[2])
    self.assertEqual(kwargs["body"], {"transition": {"id": "21"}})


if __name__ == "__main__":
  unittest.main()
