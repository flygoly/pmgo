"""Tests for shared HTTP helper."""

from __future__ import annotations

import json
import sys
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

_SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
if str(_SCRIPTS) not in sys.path:
  sys.path.insert(0, str(_SCRIPTS))

from pmgo_http import request_json  # noqa: E402


class TestPmgoHttp(unittest.TestCase):
  def test_success_json(self) -> None:
    resp = MagicMock()
    resp.read.return_value = b'{"ok": true}'
    resp.headers = {"Content-Type": "application/json"}
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)

    with patch("pmgo_http.urllib.request.urlopen", return_value=resp):
      data, headers = request_json("GET", "https://example.com/x")
    self.assertEqual(data, {"ok": True})
    self.assertEqual(headers.get("content-type"), "application/json")

  def test_http_error_message(self) -> None:
    err_body = json.dumps({"message": "nope"}).encode("utf-8")
    http_err = HTTPError(
      "https://example.com/x",
      404,
      "Not Found",
      hdrs=None,
      fp=BytesIO(err_body),
    )
    with patch("pmgo_http.urllib.request.urlopen", side_effect=http_err):
      with self.assertRaises(RuntimeError) as ctx:
        request_json("GET", "https://example.com/x", error_prefix="GitHub API")
    self.assertIn("404", str(ctx.exception))
    self.assertIn("nope", str(ctx.exception))


if __name__ == "__main__":
  unittest.main()
