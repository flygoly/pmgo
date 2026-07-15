"""Tests for shared pmgo_common helpers."""

from __future__ import annotations

import sys
import unittest
from datetime import timezone
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
if str(_SCRIPTS) not in sys.path:
  sys.path.insert(0, str(_SCRIPTS))

from pmgo_common import parse_ts  # noqa: E402


class TestParseTs(unittest.TestCase):
  def test_zulu(self) -> None:
    d = parse_ts("2024-01-02T03:04:05Z")
    self.assertIsNotNone(d)
    assert d is not None
    self.assertEqual(d.tzinfo, timezone.utc)

  def test_naive_becomes_utc(self) -> None:
    d = parse_ts("2024-01-02T03:04:05")
    self.assertIsNotNone(d)
    assert d is not None
    self.assertEqual(d.tzinfo, timezone.utc)

  def test_invalid(self) -> None:
    self.assertIsNone(parse_ts("not-a-date"))
    self.assertIsNone(parse_ts(None))


if __name__ == "__main__":
  unittest.main()
