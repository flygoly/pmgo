"""Unit tests for Linear create_comment (mocked GraphQL)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "skills" / "integration-linear"))
sys.path.insert(0, str(_ROOT / "scripts"))

from linear_integration.api import create_comment  # noqa: E402
from linear_integration.config import LinearConfig  # noqa: E402


class TestLinearComment(unittest.TestCase):
  def test_create_comment_mutation(self) -> None:
    cfg = LinearConfig(api_key="k", user_agent="t")
    payload = {
      "commentCreate": {
        "success": True,
        "comment": {"id": "c1", "body": "hi", "url": "https://linear.app/c1"},
      }
    }
    with patch("linear_integration.api._request", return_value=payload) as req:
      out = create_comment(cfg, issue_id="issue-uuid", body="hi")
    self.assertEqual(out["id"], "c1")
    args, _kwargs = req.call_args
    self.assertIn("commentCreate", args[1])
    self.assertEqual(args[2], {"issueId": "issue-uuid", "body": "hi"})


if __name__ == "__main__":
  unittest.main()
