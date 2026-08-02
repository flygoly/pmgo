"""Tests for the one-command Hermes/OpenClaw runtime manager."""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest import mock


_ROOT = Path(__file__).resolve().parent.parent


def _load_runtime_manager():
  path = _ROOT / "scripts" / "runtime_manager.py"
  spec = importlib.util.spec_from_file_location("runtime_manager", path)
  assert spec and spec.loader
  mod = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(mod)
  return mod


class TestRuntimeManager(unittest.TestCase):
  @classmethod
  def setUpClass(cls) -> None:
    cls.mod = _load_runtime_manager()

  def test_payload_uses_absolute_workspace_and_env(self) -> None:
    with mock.patch.dict(
      os.environ,
      {"PMGO_DEFAULT_LOCALE": "zh-CN", "FEISHU_APP_ID": "cli_test"},
      clear=False,
    ):
      payload = self.mod.build_mcp_payload(_ROOT, "/test/python3.12")
    self.assertEqual(payload["env"]["PMGO_WORKSPACE"], str(_ROOT))
    self.assertEqual(payload["env"]["PMGO_DEFAULT_LOCALE"], "zh-CN")
    self.assertEqual(payload["env"]["FEISHU_APP_ID"], "cli_test")
    self.assertEqual(payload["args"], [str(_ROOT / "scripts" / "pmgo_mcp_server.py")])
    self.assertEqual(payload["command"], "/test/python3.12")

  def test_cli_configured_env_points_runtime_to_shared_database(self) -> None:
    cli_path = _ROOT / "scripts" / "pmgo_cli.py"
    spec = importlib.util.spec_from_file_location("pmgo_cli_test", cli_path)
    assert spec and spec.loader
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    configured = cli._configured_env(
      {"data_dir": "/tmp/pmgo-memory", "default_project_id": "project-1", "locale": "zh-Hans"},
      Path("/tmp/pmgo-config.toml"),
    )
    self.assertEqual(configured["PMGO_MEMORY_DB"], "/tmp/pmgo-memory/pmgo.db")
    self.assertEqual(configured["PMGO_DEFAULT_LOCALE"], "zh-CN")

  def test_persona_merge_is_idempotent_and_preserves_existing_text(self) -> None:
    with tempfile.TemporaryDirectory() as tmp:
      home = Path(tmp)
      soul = home / "SOUL.md"
      soul.write_text("# Existing persona\n", encoding="utf-8")
      changed = self.mod._merge_hermes_persona(_ROOT, home, dry_run=False)
      first = soul.read_text(encoding="utf-8")
      changed_again = self.mod._merge_hermes_persona(_ROOT, home, dry_run=False)
      self.assertTrue(changed)
      self.assertFalse(changed_again)
      self.assertIn("# Existing persona", first)
      self.assertIn("<!-- pmgo:persona:begin -->", first)
      self.assertEqual(first, soul.read_text(encoding="utf-8"))
      self.assertEqual(len(list(home.glob("SOUL.md.pmgo-backup-*"))), 1)

  def test_hermes_setup_dry_run_never_writes_home(self) -> None:
    with tempfile.TemporaryDirectory() as tmp:
      home = Path(tmp) / "hermes"
      proc = subprocess.run(
        [
          sys.executable,
          str(_ROOT / "scripts" / "runtime_manager.py"),
          "setup",
          "--runtime",
          "hermes",
          "--root",
          str(_ROOT),
          "--hermes-home",
          str(home),
          "--dry-run",
        ],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=False,
      )
      self.assertEqual(proc.returncode, 0, msg=proc.stderr)
      self.assertIn("[dry-run]", proc.stdout)
      self.assertFalse(home.exists())

  def test_openclaw_setup_adds_missing_agent(self) -> None:
    args = Namespace(dry_run=False, skip_deps=False)
    calls: list[list[str]] = []

    def fake_run(command, **_kwargs):
      calls.append(command)
      return subprocess.CompletedProcess(command, 0, "", "")

    with (
      mock.patch.object(self.mod.shutil, "which", return_value="/usr/bin/openclaw"),
      mock.patch.object(self.mod, "compatible_python", return_value="/test/python3.12"),
      mock.patch.object(self.mod, "_ensure_dependencies", return_value="/test/python3.12"),
      mock.patch.object(self.mod, "_openclaw_agent", return_value=None),
      mock.patch.object(self.mod, "_run", side_effect=fake_run),
    ):
      self.mod.setup_openclaw(args, _ROOT)
    self.assertTrue(any(command[:4] == ["openclaw", "mcp", "set", "pmgo"] for command in calls))
    self.assertTrue(any(command[:4] == ["openclaw", "agents", "add", "pmgo"] for command in calls))

  def test_openclaw_setup_reuses_matching_agent(self) -> None:
    args = Namespace(dry_run=False, skip_deps=False)
    calls: list[list[str]] = []

    def fake_run(command, **_kwargs):
      calls.append(command)
      return subprocess.CompletedProcess(command, 0, "", "")

    agent = {"id": "pmgo", "workspace": str(_ROOT / "agent")}
    with (
      mock.patch.object(self.mod.shutil, "which", return_value="/usr/bin/openclaw"),
      mock.patch.object(self.mod, "compatible_python", return_value="/test/python3.12"),
      mock.patch.object(self.mod, "_ensure_dependencies", return_value="/test/python3.12"),
      mock.patch.object(self.mod, "_openclaw_agent", return_value=agent),
      mock.patch.object(self.mod, "_run", side_effect=fake_run),
    ):
      self.mod.setup_openclaw(args, _ROOT)
    self.assertFalse(any(command[:3] == ["openclaw", "agents", "add"] for command in calls))

  def test_openclaw_setup_rejects_unverifiable_agent_workspace(self) -> None:
    args = Namespace(dry_run=False, skip_deps=False)
    with (
      mock.patch.object(self.mod.shutil, "which", return_value="/usr/bin/openclaw"),
      mock.patch.object(self.mod, "_ensure_dependencies", return_value="/test/python3.12"),
      mock.patch.object(self.mod, "_openclaw_agent", return_value={"id": "pmgo"}),
      mock.patch.object(
        self.mod,
        "_run",
        return_value=subprocess.CompletedProcess([], 0, "", ""),
      ),
    ):
      with self.assertRaises(self.mod.SetupError):
        self.mod.setup_openclaw(args, _ROOT)

  def test_start_hermes_uses_agent_directory(self) -> None:
    args = Namespace(runtime="hermes", runtime_arg=["--no-open"], dry_run=True)
    with mock.patch.object(self.mod, "_run") as run:
      run.return_value = subprocess.CompletedProcess([], 0, "", "")
      code = self.mod.start_runtime(args, _ROOT)
    self.assertEqual(code, 0)
    run.assert_called_once_with(
      ["hermes", "dashboard", "--no-open"],
      cwd=_ROOT / "agent",
      dry_run=True,
      check=False,
    )

  @unittest.skipUnless(importlib.util.find_spec("yaml"), "PyYAML not installed")
  def test_hermes_uninstall_preserves_unmanaged_config_and_persona(self) -> None:
    import yaml

    with tempfile.TemporaryDirectory() as tmp:
      home = Path(tmp)
      config = home / "config.yaml"
      config.write_text(
        yaml.safe_dump(
          {
            "model": "example/model",
            "mcp_servers": {
              "pmgo": {"command": "python"},
              "other": {"command": "other-server"},
            },
          },
          sort_keys=False,
        ),
        encoding="utf-8",
      )
      soul = home / "SOUL.md"
      soul.write_text(
        "# My persona\n\n"
        "<!-- pmgo:persona:begin -->\n# pmgo\n<!-- pmgo:persona:end -->\n",
        encoding="utf-8",
      )

      self.assertTrue(self.mod._remove_hermes_config(home, dry_run=False))
      self.assertTrue(self.mod._remove_hermes_persona(home, dry_run=False))
      self.assertFalse(self.mod._remove_hermes_config(home, dry_run=False))
      self.assertFalse(self.mod._remove_hermes_persona(home, dry_run=False))

      remaining = yaml.safe_load(config.read_text(encoding="utf-8"))
      self.assertEqual(remaining["model"], "example/model")
      self.assertEqual(remaining["mcp_servers"], {"other": {"command": "other-server"}})
      self.assertEqual(soul.read_text(encoding="utf-8"), "# My persona\n")
      self.assertEqual(len(list(home.glob("config.yaml.pmgo-backup-*"))), 1)
      self.assertEqual(len(list(home.glob("SOUL.md.pmgo-backup-*"))), 1)

  def test_openclaw_uninstall_preserves_agent_workspace(self) -> None:
    args = Namespace(dry_run=False)
    calls: list[list[str]] = []

    def fake_run(command, **_kwargs):
      calls.append(command)
      return subprocess.CompletedProcess(command, 0, "{}", "")

    with (
      mock.patch.object(self.mod.shutil, "which", return_value="/usr/bin/openclaw"),
      mock.patch.object(self.mod, "_run", side_effect=fake_run),
    ):
      self.mod.uninstall_openclaw(args, _ROOT)
    self.assertIn(["openclaw", "mcp", "unset", "pmgo"], calls)
    self.assertFalse(any("agents" in command and "delete" in command for command in calls))


if __name__ == "__main__":
  unittest.main()
