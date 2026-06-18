"""Load `policy/pmgo.policy.yaml` for MCP tool gating (allow / require_confirm / quiet hours)."""

from __future__ import annotations

from datetime import datetime, time
from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo

# Reports and passive scans — muted on weekends / quiet ranges when configured.
NON_CRITICAL_TOOLS = frozenset(
  {
    "pmgo.report.daily",
    "pmgo.report.weekly",
    "pmgo.risk.scan",
  }
)


@lru_cache(maxsize=1)
def _repo_root() -> Path:
  return Path(__file__).resolve().parent.parent


@lru_cache(maxsize=1)
def _policy_data() -> dict:
  try:
    import yaml
  except ImportError as e:
    raise RuntimeError("PyYAML is required for policy loading (pip install pyyaml)") from e
  path = _repo_root() / "policy" / "pmgo.policy.yaml"
  data = yaml.safe_load(path.read_text(encoding="utf-8"))
  return data if isinstance(data, dict) else {}


@lru_cache(maxsize=1)
def _tools_map() -> dict:
  return _policy_data().get("tools") or {}


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


def _parse_hhmm(raw: str) -> time:
  hour, minute = raw.strip().split(":", 1)
  return time(int(hour), int(minute))


def _in_quiet_range(now: datetime, range_str: str) -> bool:
  """True when local `now` falls in a range like '22:00-08:00' (may cross midnight)."""
  part = range_str.strip()
  if "-" not in part:
    return False
  start_s, end_s = part.split("-", 1)
  start_t = _parse_hhmm(start_s)
  end_t = _parse_hhmm(end_s)
  cur = now.time().replace(second=0, microsecond=0)
  if start_t <= end_t:
    return start_t <= cur <= end_t
  return cur >= start_t or cur <= end_t


def quiet_hours_block(tool_key: str, *, now: datetime | None = None) -> str | None:
  """
  Returns a message when `tool_key` should be deferred due to quiet_hours policy.
  Read/write tools not in NON_CRITICAL_TOOLS are not muted by quiet hours.
  """
  cfg = _policy_data().get("quiet_hours")
  if not isinstance(cfg, dict):
    return None
  tz_name = str(cfg.get("timezone") or "UTC")
  try:
    tz = ZoneInfo(tz_name)
  except Exception:
    tz = ZoneInfo("UTC")
  now = now or datetime.now(tz)
  if now.tzinfo is None:
    now = now.replace(tzinfo=tz)
  else:
    now = now.astimezone(tz)

  if tool_key not in NON_CRITICAL_TOOLS:
    return None

  if cfg.get("weekends") == "mute_non_critical" and now.weekday() >= 5:
    return (
      f"Quiet hours: non-critical tool {tool_key!r} is muted on weekends "
      f"({tz_name})."
    )

  for r in cfg.get("ranges") or []:
    if _in_quiet_range(now, str(r)):
      return (
        f"Quiet hours: non-critical tool {tool_key!r} is muted during {r} "
        f"({tz_name})."
      )
  return None


def gate(tool_key: str, *, confirmed: bool) -> str | None:
  """
  Returns None if OK, else an error message to return to the agent.
  """
  if not policy_allows(tool_key):
    return f"Policy denies tool {tool_key!r} (allow: false or undefined)."
  qh = quiet_hours_block(tool_key)
  if qh:
    return qh
  if policy_require_confirm(tool_key) and not confirmed:
    return (
      f"Policy requires explicit confirmation for {tool_key!r}. "
      "Re-run with confirmed=true after the user approves in chat."
    )
  return None
