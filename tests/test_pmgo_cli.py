"""End-to-end tests for the user-facing pmgo command."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CLI = ROOT / "scripts" / "pmgo_cli.py"


class TestPmgoCli(unittest.TestCase):
  def setUp(self) -> None:
    self.temp = tempfile.TemporaryDirectory()
    self.directory = Path(self.temp.name)
    self.config = self.directory / "config.toml"
    self.data = self.directory / "data"
    onboard = self.run_cli(
      "onboard", "--runtime", "standalone", "--data-dir", str(self.data),
      "--name", "CLI Project", "--locale", "en",
    )
    self.assertEqual(onboard.returncode, 0, onboard.stderr)

  def tearDown(self) -> None:
    self.temp.cleanup()

  def run_cli(self, *args: str, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
      [sys.executable, "-B", str(CLI), "--config", str(self.config), *args],
      cwd=ROOT,
      input=input_text,
      capture_output=True,
      text=True,
      check=False,
    )

  def test_project_task_and_context_workflow(self) -> None:
    projects = self.run_cli("project", "list", "--json")
    self.assertEqual(projects.returncode, 0, projects.stderr)
    project_id = json.loads(projects.stdout)[0]["id"]

    created = self.run_cli("task", "add", "Ship CLI", "--priority", "high", "--json")
    self.assertEqual(created.returncode, 0, created.stderr)
    task_id = json.loads(created.stdout)["id"]

    done = self.run_cli("task", "done", task_id, "--json")
    self.assertEqual(json.loads(done.stdout)["status"], "done")
    context = self.run_cli("context", "--project", project_id, "--json")
    self.assertEqual(context.returncode, 0, context.stderr)
    self.assertEqual(json.loads(context.stdout)["task_count"], 0)

  def test_project_selection_and_markdown_notes(self) -> None:
    created = self.run_cli("project", "add", "Second Project", "--use", "--json")
    self.assertEqual(created.returncode, 0, created.stderr)
    project_id = json.loads(created.stdout)["id"]
    self.assertIn(project_id, self.config.read_text(encoding="utf-8"))

    saved = self.run_cli("note", "set", "overview", input_text="# Goal\n\nBuild pmgo.\n")
    self.assertEqual(saved.returncode, 0, saved.stderr)
    shown = self.run_cli("note", "show", "overview")
    self.assertEqual(shown.stdout, "# Goal\n\nBuild pmgo.\n")

  def test_task_delete_requires_confirmation(self) -> None:
    created = self.run_cli("task", "add", "Temporary", "--json")
    task_id = json.loads(created.stdout)["id"]
    refused = self.run_cli("task", "delete", task_id)
    self.assertNotEqual(refused.returncode, 0)
    self.assertIn("requires --yes", refused.stderr)
    deleted = self.run_cli("task", "delete", task_id, "--yes")
    self.assertEqual(deleted.returncode, 0, deleted.stderr)


if __name__ == "__main__":
  unittest.main()
