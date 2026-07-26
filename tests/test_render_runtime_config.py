"""Tests for scripts/render-runtime-config.py."""

from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent


def _load_render_runtime_config():
  path = _ROOT / "scripts" / "render-runtime-config.py"
  spec = importlib.util.spec_from_file_location("render_runtime_config", path)
  assert spec and spec.loader
  mod = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(mod)
  return mod


class TestRenderRuntimeConfig(unittest.TestCase):
  @classmethod
  def setUpClass(cls) -> None:
    cls.mod = _load_render_runtime_config()

  def test_mcp_env_keys_match_example(self) -> None:
    keys = self.mod.mcp_env_keys()
    self.assertIn("PMGO_WORKSPACE", keys)
    self.assertIn("FEISHU_APP_ID", keys)
    self.assertIn("FEISHU_APP_SECRET", keys)
    self.assertIn("FEISHU_TASKLIST_GUID", keys)
    self.assertIn("NOTION_TOKEN", keys)
    self.assertIn("NOTION_DATABASE_ID", keys)
    self.assertIn("DINGTALK_APP_KEY", keys)
    self.assertIn("DINGTALK_APP_SECRET", keys)
    self.assertIn("GITHUB_TOKEN", keys)
    self.assertIn("LINEAR_API_KEY", keys)

  def test_mcp_env_keys_parses_commented_lines(self) -> None:
    with tempfile.TemporaryDirectory() as tmp:
      path = Path(tmp) / "mcp.env.example"
      path.write_text(
        "# comment\nFOO_BAR=\n# BAZ_QUX=value\nnot a key\n",
        encoding="utf-8",
      )
      self.assertEqual(self.mod.mcp_env_keys(path), ["FOO_BAR", "BAZ_QUX"])

  def test_openclaw_output_contains_mcp_set(self) -> None:
    proc = subprocess.run(
      [
        sys.executable,
        str(_ROOT / "scripts" / "render-runtime-config.py"),
        "--runtime",
        "openclaw",
      ],
      capture_output=True,
      text=True,
      check=False,
      cwd=_ROOT,
    )
    self.assertEqual(proc.returncode, 0, msg=proc.stderr)
    self.assertIn("openclaw mcp set pmgo", proc.stdout)
    self.assertIn("pmgo_mcp_server.py", proc.stdout)
    self.assertIn("shared/mcp.env.example", proc.stdout)

  def test_openclaw_passes_feishu_and_notion_env(self) -> None:
    env = os.environ.copy()
    env.update(
      {
        "FEISHU_APP_ID": "cli_test",
        "FEISHU_APP_SECRET": "secret_test",
        "NOTION_TOKEN": "ntn_test",
        "DINGTALK_APP_KEY": "dt_key",
      }
    )
    proc = subprocess.run(
      [
        sys.executable,
        str(_ROOT / "scripts" / "render-runtime-config.py"),
        "--runtime",
        "openclaw",
      ],
      capture_output=True,
      text=True,
      check=False,
      cwd=_ROOT,
      env=env,
    )
    self.assertEqual(proc.returncode, 0, msg=proc.stderr)
    m = re.search(r"openclaw mcp set pmgo ({.*})", proc.stdout)
    self.assertIsNotNone(m)
    payload = json.loads(m.group(1))
    self.assertEqual(payload["env"]["FEISHU_APP_ID"], "cli_test")
    self.assertEqual(payload["env"]["FEISHU_APP_SECRET"], "secret_test")
    self.assertEqual(payload["env"]["NOTION_TOKEN"], "ntn_test")
    self.assertEqual(payload["env"]["DINGTALK_APP_KEY"], "dt_key")

  def test_hermes_output_contains_mcp_servers(self) -> None:
    env = os.environ.copy()
    env["FEISHU_TASKLIST_GUID"] = "tl_guid"
    proc = subprocess.run(
      [
        sys.executable,
        str(_ROOT / "scripts" / "render-runtime-config.py"),
        "--runtime",
        "hermes",
      ],
      capture_output=True,
      text=True,
      check=False,
      cwd=_ROOT,
      env=env,
    )
    if "PyYAML required" in proc.stderr:
      self.skipTest("PyYAML not installed")
    self.assertEqual(proc.returncode, 0, msg=proc.stderr)
    self.assertIn("mcp_servers:", proc.stdout)
    self.assertIn("pmgo:", proc.stdout)
    self.assertIn("FEISHU_TASKLIST_GUID: tl_guid", proc.stdout)
    self.assertIn("shared/mcp.env.example", proc.stdout)


if __name__ == "__main__":
  unittest.main()
