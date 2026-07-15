"""Unit tests for DingTalk token helper (mocked HTTP)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "skills" / "integration-dingtalk"))
sys.path.insert(0, str(_ROOT / "scripts"))

from dingtalk_integration.api import get_access_token  # noqa: E402
from dingtalk_integration.config import DingTalkConfig  # noqa: E402


class TestDingTalkApi(unittest.TestCase):
  def test_get_access_token(self) -> None:
    cfg = DingTalkConfig(app_key="k", app_secret="s")
    with patch(
      "dingtalk_integration.api.request_json",
      return_value=({"errcode": 0, "access_token": "tok", "expires_in": 7200}, {}),
    ):
      out = get_access_token(cfg)
    self.assertEqual(out["access_token"], "tok")


if __name__ == "__main__":
  unittest.main()
