"""Integration-style tests for MCP tool functions (requires mcp + pyyaml)."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS = _ROOT / "scripts"
for p in (
  _SCRIPTS,
  _ROOT / "skills" / "project-core",
  _ROOT / "skills" / "daily-standup",
  _ROOT / "skills" / "weekly-report",
  _ROOT / "skills" / "risk-radar",
  _ROOT / "skills" / "integration-github",
  _ROOT / "skills" / "integration-linear",
  _ROOT / "skills" / "integration-jira",
):
  sp = str(p)
  if sp not in sys.path:
    sys.path.insert(0, sp)

try:
  import mcp  # noqa: F401
except ImportError:
  mcp = None
try:
  import yaml  # noqa: F401
except ImportError:
  yaml = None

from test_helpers import init_test_db  # noqa: E402


@unittest.skipIf(mcp is None or yaml is None, "mcp/pyyaml not installed")
class TestPmgoMcpTools(unittest.TestCase):
  def setUp(self) -> None:
    self._tmpdir = tempfile.TemporaryDirectory()
    self.db = Path(self._tmpdir.name) / "test.db"
    init_test_db(self.db)
    self._env = {
      "PMGO_MEMORY_DB": str(self.db),
      "PMGO_WORKSPACE": str(_ROOT),
    }
    self._old = {k: os.environ.get(k) for k in self._env}
    os.environ.update(self._env)
    # Import after env is set so stores see PMGO_MEMORY_DB.
    import pmgo_mcp_server as server  # noqa: WPS433

    self.server = server

  def tearDown(self) -> None:
    for k, v in self._old.items():
      if v is None:
        os.environ.pop(k, None)
      else:
        os.environ[k] = v
    self._tmpdir.cleanup()

  def test_project_list_and_create_respects_confirm(self) -> None:
    denied = self.server.pmgo_project_create(name="No Confirm", confirmed=False)
    self.assertIn("confirmation", denied.lower())

    created = self.server.pmgo_project_create(
      name="MCP Demo",
      confirmed=True,
      slug="mcp-demo",
    )
    row = json.loads(created)
    self.assertEqual(row["slug"], "mcp-demo")

    listed = json.loads(self.server.pmgo_project_list())
    self.assertTrue(any(p["slug"] == "mcp-demo" for p in listed))

  def test_task_create_and_daily_report(self) -> None:
    proj = json.loads(
      self.server.pmgo_project_create(name="Report Proj", confirmed=True, slug="report-proj")
    )
    pid = proj["id"]
    denied = self.server.pmgo_task_create(project_id=pid, title="T1", confirmed=False)
    self.assertIn("confirmation", denied.lower())

    task = json.loads(
      self.server.pmgo_task_create(
        project_id=pid,
        title="Ship MCP tests",
        confirmed=True,
        task_status="doing",
      )
    )
    self.assertEqual(task["title"], "Ship MCP tests")

    os.environ["PMGO_DEFAULT_PROJECT_ID"] = pid
    report = self.server.pmgo_daily_report(project_id=pid, locale="en")
    self.assertIn("Ship MCP tests", report)
    self.assertNotIn("Policy", report)

  def test_gate_denies_unknown_via_wrapper(self) -> None:
    err = self.server.gate("not.a.tool", confirmed=True)
    self.assertIsNotNone(err)
    self.assertIn("denies", err or "")


if __name__ == "__main__":
  unittest.main()

