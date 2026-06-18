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
  from datetime import datetime
  from zoneinfo import ZoneInfo

  from pmgo_policy import gate, quiet_hours_block  # type: ignore[import-not-found]


class TestRepoLayout(unittest.TestCase):
  def test_policy_file_exists(self) -> None:
    p = _ROOT / "policy" / "pmgo.policy.yaml"
    self.assertTrue(p.is_file(), msg=f"Expected {p}")


@unittest.skipIf(yaml is None, "PyYAML not installed (pip install pyyaml)")
class TestPmgoPolicyGate(unittest.TestCase):
  def test_read_allows_without_confirm(self) -> None:
    self.assertIsNone(gate("project_core.read", confirmed=False))
    self.assertIsNone(gate("github.issue.read", confirmed=False))
    self.assertIsNone(gate("linear.issue.read", confirmed=False))
    self.assertIsNone(gate("jira.issue.read", confirmed=False))
    self.assertIsNone(gate("pmgo.report.daily", confirmed=False))
    self.assertIsNone(gate("pmgo.risk.scan", confirmed=False))

  def test_write_requires_confirm(self) -> None:
    self.assertIsNotNone(gate("github.issue.create", confirmed=False))
    self.assertIsNone(gate("github.issue.create", confirmed=True))
    self.assertIsNotNone(gate("linear.issue.import_task", confirmed=False))
    self.assertIsNone(gate("linear.issue.import_task", confirmed=True))
    self.assertIsNotNone(gate("jira.issue.import_task", confirmed=False))
    self.assertIsNone(gate("jira.issue.import_task", confirmed=True))
    self.assertIsNotNone(gate("project_core.task.write", confirmed=False))
    self.assertIsNone(gate("project_core.task.write", confirmed=True))
    self.assertIsNotNone(gate("project_core.milestone.write", confirmed=False))
    self.assertIsNone(gate("project_core.milestone.write", confirmed=True))

  def test_risk_read_allows_without_confirm(self) -> None:
    self.assertIsNone(gate("project_core.risk.read", confirmed=False))

  def test_risk_write_requires_confirm(self) -> None:
    self.assertIsNotNone(gate("project_core.risk.write", confirmed=False))
    self.assertIsNone(gate("project_core.risk.write", confirmed=True))

  def test_decision_read_allows_without_confirm(self) -> None:
    self.assertIsNone(gate("project_core.decision.read", confirmed=False))

  def test_decision_write_requires_confirm(self) -> None:
    self.assertIsNotNone(gate("project_core.decision.write", confirmed=False))
    self.assertIsNone(gate("project_core.decision.write", confirmed=True))

  def test_github_sync_requires_confirm(self) -> None:
    self.assertIsNotNone(gate("github.issue.sync", confirmed=False))
    self.assertIsNone(gate("github.issue.sync", confirmed=True))

  def test_milestone_read_allows_without_confirm(self) -> None:
    self.assertIsNone(gate("project_core.milestone.read", confirmed=False))

  def test_unknown_tool_denied(self) -> None:
    msg = gate("definitely.not.a.real.tool", confirmed=True)
    self.assertIsNotNone(msg)
    self.assertIn("denies", msg or "")


@unittest.skipIf(yaml is None, "PyYAML not installed (pip install pyyaml)")
class TestQuietHours(unittest.TestCase):
  def test_weekend_mutes_non_critical(self) -> None:
    tz = ZoneInfo("Asia/Shanghai")
    sat = datetime(2026, 6, 20, 10, 0, tzinfo=tz)
    msg = quiet_hours_block("pmgo.risk.scan", now=sat)
    self.assertIsNotNone(msg)
    self.assertIn("weekend", msg or "")

  def test_overnight_range_mutes_non_critical(self) -> None:
    tz = ZoneInfo("Asia/Shanghai")
    late = datetime(2026, 6, 16, 23, 0, tzinfo=tz)
    msg = quiet_hours_block("pmgo.report.daily", now=late)
    self.assertIsNotNone(msg)
    self.assertIn("22:00-08:00", msg or "")

  def test_critical_tools_not_muted(self) -> None:
    tz = ZoneInfo("Asia/Shanghai")
    late = datetime(2026, 6, 16, 23, 0, tzinfo=tz)
    self.assertIsNone(quiet_hours_block("project_core.task.write", now=late))


if __name__ == "__main__":
  unittest.main()
