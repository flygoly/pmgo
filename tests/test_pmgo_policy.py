"""Unit tests for `scripts/pmgo_policy` (requires PyYAML: pip install pyyaml)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS = _ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
  sys.path.insert(0, str(_SCRIPTS))

try:
  import yaml  # noqa: F401
except ImportError:
  yaml = None

if yaml is not None:
  from pmgo_policy import gate  # type: ignore[import-not-found]


class TestRepoLayout(unittest.TestCase):
  def test_policy_file_exists(self) -> None:
    p = _ROOT / "policy" / "pmgo.policy.yaml"
    self.assertTrue(p.is_file(), msg=f"Expected {p}")


@unittest.skipIf(yaml is None, "PyYAML not installed (pip install pyyaml)")
class TestPmgoPolicyGate(unittest.TestCase):
  def test_read_allows_without_confirm(self) -> None:
    self.assertIsNone(gate("project_core.read", confirmed=False))
    self.assertIsNone(gate("github.issue.read", confirmed=False))
    self.assertIsNone(gate("pmgo.report.daily", confirmed=False))

  def test_write_requires_confirm(self) -> None:
    self.assertIsNotNone(gate("github.issue.create", confirmed=False))
    self.assertIsNone(gate("github.issue.create", confirmed=True))
    self.assertIsNotNone(gate("project_core.task.write", confirmed=False))
    self.assertIsNone(gate("project_core.task.write", confirmed=True))

  def test_unknown_tool_denied(self) -> None:
    msg = gate("definitely.not.a.real.tool", confirmed=True)
    self.assertIsNotNone(msg)
    self.assertIn("denies", msg or "")


if __name__ == "__main__":
  unittest.main()
