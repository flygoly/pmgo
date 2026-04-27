"""Load `policy/pmgo.policy.yaml` for MCP tool gating (allow / require_confirm)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def _repo_root() -> Path:
  return Path(__file__).resolve().parent.parent


@lru_cache(maxsize=1)
def _tools_map() -> dict:
  try:
    import yaml
  except ImportError as e:
    raise RuntimeError("PyYAML is required for policy loading (pip install pyyaml)") from e
  path = _repo_root() / "policy" / "pmgo.policy.yaml"
  data = yaml.safe_load(path.read_text(encoding="utf-8"))
  return data.get("tools") or {}


def policy_allows(tool_key: str) -> bool:
  entry = _tools_map().get(tool_key)
  if not isinstance(entry, dict):
    return False
  return bool(entry.get("allow", False))


def policy_require_confirm(tool_key: str) -> bool:
  entry = _tools_map().get(tool_key)
  if not isinstance(entry, dict):
    return True
  return bool(entry.get("require_confirm", False))


def gate(tool_key: str, *, confirmed: bool) -> str | None:
  """
  Returns None if OK, else an error message to return to the agent.
  """
  if not policy_allows(tool_key):
    return f"Policy denies tool {tool_key!r} (allow: false or undefined)."
  if policy_require_confirm(tool_key) and not confirmed:
    return (
      f"Policy requires explicit confirmation for {tool_key!r}. "
      "Re-run with confirmed=true after the user approves in chat."
    )
  return None
