#!/usr/bin/env python3
"""Install, diagnose, and start pmgo on Hermes or OpenClaw."""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
MCP_SCRIPT = ROOT / "scripts" / "pmgo_mcp_server.py"
ENV_EXAMPLE = ROOT / "shared" / "mcp.env.example"
AGENT_DIR = ROOT / "agent"

_FALLBACK_ENV_KEYS = (
  "PMGO_WORKSPACE",
  "PMGO_DEFAULT_PROJECT_ID",
  "PMGO_DEFAULT_LOCALE",
  "PMGO_MEMORY_DB",
  "GITHUB_TOKEN",
  "GITHUB_REPO",
  "LINEAR_API_KEY",
  "JIRA_BASE_URL",
  "JIRA_EMAIL",
  "JIRA_API_TOKEN",
  "JIRA_PROJECT",
  "FEISHU_APP_ID",
  "FEISHU_APP_SECRET",
  "FEISHU_TASKLIST_GUID",
  "NOTION_TOKEN",
  "NOTION_DATABASE_ID",
  "DINGTALK_APP_KEY",
  "DINGTALK_APP_SECRET",
)
_ENV_KEY_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")
_SOUL_BEGIN = "<!-- pmgo:persona:begin -->"
_SOUL_END = "<!-- pmgo:persona:end -->"


class SetupError(RuntimeError):
  """A user-actionable runtime setup failure."""


def _python_supported(command: str) -> bool:
  probe = subprocess.run(
    [command, "-c", "import sys; raise SystemExit(sys.version_info < (3, 11))"],
    capture_output=True,
    check=False,
  )
  return probe.returncode == 0


def compatible_python() -> str:
  """Return a Python >=3.11 interpreter, preferring the current process."""
  if sys.version_info >= (3, 11):
    return sys.executable
  for name in ("python3.13", "python3.12", "python3.11"):
    candidate = shutil.which(name)
    if candidate is None:
      continue
    if _python_supported(candidate):
      return candidate
  raise SetupError(
    f"pmgo requires Python 3.11+; current interpreter is "
    f"{sys.version_info.major}.{sys.version_info.minor}"
  )


def repo_root(override: Path | None = None) -> Path:
  if override is not None:
    return override.expanduser().resolve()
  value = os.environ.get("PMGO_ROOT", "").strip()
  return Path(value).expanduser().resolve() if value else ROOT


def mcp_env_keys(example_path: Path | None = None) -> list[str]:
  """Return supported MCP environment keys from the shared example file."""
  path = example_path or ENV_EXAMPLE
  if not path.is_file():
    return list(_FALLBACK_ENV_KEYS)
  keys: list[str] = []
  seen: set[str] = set()
  for raw in path.read_text(encoding="utf-8").splitlines():
    line = raw.strip()
    if line.startswith("#"):
      line = line[1:].strip()
    if not line or "=" not in line:
      continue
    key = line.split("=", 1)[0].strip()
    if _ENV_KEY_RE.match(key) and key not in seen:
      seen.add(key)
      keys.append(key)
  return keys or list(_FALLBACK_ENV_KEYS)


def _venv_python(root: Path) -> Path:
  if os.name == "nt":
    return root / ".pmgo-venv" / "Scripts" / "python.exe"
  return root / ".pmgo-venv" / "bin" / "python"


def runtime_python(root: Path) -> str:
  venv = _venv_python(root)
  return str(venv) if venv.is_file() else compatible_python()


def build_mcp_payload(root: Path, python_command: str | None = None) -> dict[str, Any]:
  """Build the shared stdio MCP registration payload."""
  env = {"PMGO_WORKSPACE": str(root)}
  for key in mcp_env_keys(root / "shared" / "mcp.env.example"):
    if key == "PMGO_WORKSPACE":
      continue
    value = os.environ.get(key, "").strip()
    if value:
      env[key] = value
  return {
    # Use the same supported interpreter selected by setup.
    "command": python_command or runtime_python(root),
    "args": [str(root / "scripts" / "pmgo_mcp_server.py")],
    "env": env,
  }


def _display(command: list[str]) -> str:
  return shlex.join(command)


def _run(
  command: list[str],
  *,
  cwd: Path,
  dry_run: bool = False,
  capture: bool = False,
  check: bool = True,
) -> subprocess.CompletedProcess[str]:
  print(f"$ {_display(command)}")
  if dry_run:
    return subprocess.CompletedProcess(command, 0, "", "")
  return subprocess.run(
    command,
    cwd=cwd,
    check=check,
    capture_output=capture,
    text=True,
  )


def _dependencies_available(python: str | None = None) -> bool:
  command = python or sys.executable
  probe = subprocess.run(
    [command, "-c", "import mcp, yaml"],
    capture_output=True,
    check=False,
  )
  return probe.returncode == 0


def _ensure_dependencies(root: Path, *, dry_run: bool, skip: bool) -> str:
  target = _venv_python(root)
  if target.is_file() and not _python_supported(str(target)):
    raise SetupError(
      f"Existing pmgo environment uses Python <3.11: {target}. "
      "Move it aside and run setup again."
    )
  if target.is_file() and _dependencies_available(str(target)):
    print(f"[ok] Python MCP dependencies are installed: {target}")
    if not dry_run and Path(sys.executable).absolute() != target.absolute():
      print(f"[setup] Re-running inside pmgo virtual environment: {target}", flush=True)
      os.execv(str(target), [str(target), str(Path(__file__).resolve()), *sys.argv[1:]])
    return str(target)
  if skip:
    raise SetupError('Missing .pmgo-venv MCP dependencies; omit --skip-deps to install them')
  if not target.is_file():
    print(f"[setup] Creating project virtual environment: {target.parent.parent}")
    _run(
      [compatible_python(), "-m", "venv", str(target.parent.parent)],
      cwd=root,
      dry_run=dry_run,
    )
  print(f"[setup] Installing Python MCP dependencies into {target}")
  _run(
    [str(target), "-m", "pip", "install", "-e", ".[mcp]"],
    cwd=root,
    dry_run=dry_run,
  )
  if not dry_run and Path(sys.executable).absolute() != target.absolute():
    print(f"[setup] Re-running inside pmgo virtual environment: {target}", flush=True)
    os.execv(str(target), [str(target), str(Path(__file__).resolve()), *sys.argv[1:]])
  return str(target)


def _backup(path: Path) -> Path:
  stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
  backup = path.with_name(f"{path.name}.pmgo-backup-{stamp}")
  shutil.copy2(path, backup)
  return backup


def _hermes_home(override: Path | None) -> Path:
  if override is not None:
    return override.expanduser().resolve()
  value = os.environ.get("HERMES_HOME", "").strip()
  return Path(value).expanduser().resolve() if value else Path.home() / ".hermes"


def _yaml_module():
  try:
    import yaml  # noqa: WPS433
  except ImportError as exc:
    raise SetupError('PyYAML is required; run: pip install -e ".[mcp]"') from exc
  return yaml


def _merge_hermes_config(
  root: Path,
  home: Path,
  *,
  dry_run: bool,
  python_command: str | None = None,
) -> bool:
  config_path = home / "config.yaml"
  if dry_run and not _dependencies_available():
    print(f"[dry-run] Would merge mcp_servers.pmgo into {config_path}")
    return True
  yaml = _yaml_module()
  existing_text = config_path.read_text(encoding="utf-8") if config_path.is_file() else ""
  try:
    config = yaml.safe_load(existing_text) if existing_text.strip() else {}
  except yaml.YAMLError as exc:
    raise SetupError(f"Cannot parse Hermes config {config_path}: {exc}") from exc
  if config is None:
    config = {}
  if not isinstance(config, dict):
    raise SetupError(f"Hermes config must contain a YAML mapping: {config_path}")

  servers = config.setdefault("mcp_servers", {})
  if not isinstance(servers, dict):
    raise SetupError("Hermes config key 'mcp_servers' must be a mapping")
  desired = build_mcp_payload(root, python_command)
  if servers.get("pmgo") == desired:
    print(f"[ok] Hermes MCP registration already current: {config_path}")
    return False
  servers["pmgo"] = desired
  rendered = yaml.safe_dump(config, default_flow_style=False, sort_keys=False, allow_unicode=True)
  if dry_run:
    print(f"[dry-run] Would update {config_path}")
    return True
  home.mkdir(parents=True, exist_ok=True)
  if config_path.is_file():
    print(f"[backup] {_backup(config_path)}")
  config_path.write_text(rendered, encoding="utf-8")
  print(f"[updated] {config_path}")
  return True


def _persona_block(root: Path) -> str:
  soul_path = root / "agent" / "SOUL.md"
  if not soul_path.is_file():
    raise SetupError(f"pmgo persona not found: {soul_path}")
  return f"{_SOUL_BEGIN}\n{soul_path.read_text(encoding='utf-8').rstrip()}\n{_SOUL_END}"


def _merge_hermes_persona(root: Path, home: Path, *, dry_run: bool) -> bool:
  soul_path = home / "SOUL.md"
  existing = soul_path.read_text(encoding="utf-8") if soul_path.is_file() else ""
  block = _persona_block(root)
  pattern = re.compile(
    re.escape(_SOUL_BEGIN) + r".*?" + re.escape(_SOUL_END),
    flags=re.DOTALL,
  )
  if pattern.search(existing):
    updated = pattern.sub(block, existing).rstrip() + "\n"
  elif existing.strip():
    updated = existing.rstrip() + "\n\n" + block + "\n"
  else:
    updated = block + "\n"
  if updated == existing:
    print(f"[ok] Hermes pmgo persona already current: {soul_path}")
    return False
  if dry_run:
    print(f"[dry-run] Would merge pmgo persona into {soul_path}")
    return True
  home.mkdir(parents=True, exist_ok=True)
  if soul_path.is_file():
    print(f"[backup] {_backup(soul_path)}")
  soul_path.write_text(updated, encoding="utf-8")
  print(f"[updated] {soul_path}")
  return True


def _remove_hermes_config(home: Path, *, dry_run: bool) -> bool:
  config_path = home / "config.yaml"
  if not config_path.is_file():
    print(f"[ok] Hermes config does not exist: {config_path}")
    return False
  yaml = _yaml_module()
  try:
    config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
  except yaml.YAMLError as exc:
    raise SetupError(f"Cannot parse Hermes config {config_path}: {exc}") from exc
  if not isinstance(config, dict):
    raise SetupError(f"Hermes config must contain a YAML mapping: {config_path}")
  servers = config.get("mcp_servers")
  if not isinstance(servers, dict) or "pmgo" not in servers:
    print(f"[ok] Hermes pmgo MCP registration is already absent: {config_path}")
    return False
  del servers["pmgo"]
  if not servers:
    config.pop("mcp_servers", None)
  if dry_run:
    print(f"[dry-run] Would remove mcp_servers.pmgo from {config_path}")
    return True
  print(f"[backup] {_backup(config_path)}")
  config_path.write_text(
    yaml.safe_dump(config, default_flow_style=False, sort_keys=False, allow_unicode=True),
    encoding="utf-8",
  )
  print(f"[updated] {config_path}")
  return True


def _remove_hermes_persona(home: Path, *, dry_run: bool) -> bool:
  soul_path = home / "SOUL.md"
  if not soul_path.is_file():
    print(f"[ok] Hermes SOUL does not exist: {soul_path}")
    return False
  existing = soul_path.read_text(encoding="utf-8")
  pattern = re.compile(
    r"\n*" + re.escape(_SOUL_BEGIN) + r".*?" + re.escape(_SOUL_END) + r"\n*",
    flags=re.DOTALL,
  )
  if not pattern.search(existing):
    print(f"[ok] Hermes pmgo persona is already absent: {soul_path}")
    return False
  updated = pattern.sub("\n", existing).strip()
  updated = updated + "\n" if updated else ""
  if dry_run:
    print(f"[dry-run] Would remove pmgo persona block from {soul_path}")
    return True
  print(f"[backup] {_backup(soul_path)}")
  soul_path.write_text(updated, encoding="utf-8")
  print(f"[updated] {soul_path}")
  return True


def _find_openclaw_agent(value: Any) -> dict[str, Any] | None:
  if isinstance(value, dict):
    if value.get("id") == "pmgo" or value.get("name") == "pmgo":
      return value
    for child in value.values():
      found = _find_openclaw_agent(child)
      if found:
        return found
  elif isinstance(value, list):
    for child in value:
      found = _find_openclaw_agent(child)
      if found:
        return found
  return None


def _openclaw_agent(root: Path) -> dict[str, Any] | None:
  result = _run(
    ["openclaw", "agents", "list", "--json"],
    cwd=root,
    capture=True,
    check=False,
  )
  if result.returncode != 0:
    raise SetupError(result.stderr.strip() or "Unable to list OpenClaw agents")
  try:
    return _find_openclaw_agent(json.loads(result.stdout))
  except json.JSONDecodeError as exc:
    raise SetupError("OpenClaw returned invalid JSON from 'agents list'") from exc


def setup_hermes(args: argparse.Namespace, root: Path) -> None:
  if shutil.which("hermes") is None and not args.dry_run:
    raise SetupError("Hermes CLI not found in PATH")
  python = _ensure_dependencies(root, dry_run=args.dry_run, skip=args.skip_deps)
  home = _hermes_home(args.hermes_home)
  _merge_hermes_config(root, home, dry_run=args.dry_run, python_command=python)
  if not args.no_persona:
    _merge_hermes_persona(root, home, dry_run=args.dry_run)
  print("[ready] Start with: npm run start -- --runtime hermes")


def setup_openclaw(args: argparse.Namespace, root: Path) -> None:
  if shutil.which("openclaw") is None and not args.dry_run:
    raise SetupError("OpenClaw CLI not found in PATH")
  python = _ensure_dependencies(root, dry_run=args.dry_run, skip=args.skip_deps)
  payload = json.dumps(build_mcp_payload(root, python), ensure_ascii=False)
  _run(
    ["openclaw", "mcp", "set", "pmgo", payload],
    cwd=root,
    dry_run=args.dry_run,
  )
  if args.dry_run:
    _run(
      [
        "openclaw", "agents", "add", "pmgo", "--workspace", str(root / "agent"),
        "--non-interactive", "--json",
      ],
      cwd=root,
      dry_run=True,
    )
  else:
    agent = _openclaw_agent(root)
    if agent is None:
      _run(
        [
          "openclaw", "agents", "add", "pmgo", "--workspace", str(root / "agent"),
          "--non-interactive", "--json",
        ],
        cwd=root,
      )
    else:
      workspace = str(agent.get("workspace", ""))
      expected = str((root / "agent").resolve())
      if not workspace:
        raise SetupError(
          "OpenClaw agent 'pmgo' exists but its workspace could not be verified. "
          "Run 'openclaw agents list --json' and resolve the conflict manually."
        )
      if str(Path(workspace).expanduser().resolve()) != expected:
        raise SetupError(
          f"OpenClaw agent 'pmgo' already uses {workspace}; expected {expected}. "
          "Remove or rename that agent before retrying."
        )
      print("[ok] OpenClaw agent 'pmgo' already exists")
  print("[ready] Start with: npm run start -- --runtime openclaw")


def uninstall_hermes(args: argparse.Namespace, _root: Path) -> None:
  home = _hermes_home(args.hermes_home)
  _remove_hermes_config(home, dry_run=args.dry_run)
  if not args.no_persona:
    _remove_hermes_persona(home, dry_run=args.dry_run)
  print("[done] pmgo Hermes registration removed; project data was preserved")


def uninstall_openclaw(args: argparse.Namespace, root: Path) -> None:
  if shutil.which("openclaw") is None and not args.dry_run:
    raise SetupError("OpenClaw CLI not found in PATH")
  if args.dry_run:
    _run(["openclaw", "mcp", "unset", "pmgo"], cwd=root, dry_run=True)
  else:
    show = _run(
      ["openclaw", "mcp", "show", "pmgo", "--json"],
      cwd=root,
      capture=True,
      check=False,
    )
    if show.returncode == 0:
      _run(["openclaw", "mcp", "unset", "pmgo"], cwd=root)
    else:
      print("[ok] OpenClaw pmgo MCP registration is already absent")
  print(
    "[preserved] OpenClaw agent 'pmgo' and its workspace were not deleted; "
    "'openclaw agents delete' may move workspace files to Trash"
  )


def _check(label: str, ok: bool, detail: str) -> bool:
  print(f"[{'ok' if ok else 'fail'}] {label}: {detail}")
  return ok


def doctor_hermes(args: argparse.Namespace, root: Path) -> bool:
  good = _check("Hermes CLI", shutil.which("hermes") is not None, shutil.which("hermes") or "not found")
  good &= _check("MCP dependencies", _dependencies_available(), "mcp + PyYAML")
  config_path = _hermes_home(args.hermes_home) / "config.yaml"
  if not config_path.is_file():
    return _check("Hermes config", False, f"missing {config_path}") and good
  try:
    config = _yaml_module().safe_load(config_path.read_text(encoding="utf-8")) or {}
    pmgo = config.get("mcp_servers", {}).get("pmgo", {})
    expected = build_mcp_payload(root)
    good &= _check("Hermes pmgo MCP", pmgo == expected, str(config_path))
  except Exception as exc:  # Diagnostic command must report malformed YAML cleanly.
    good &= _check("Hermes config", False, str(exc))
  soul = _hermes_home(args.hermes_home) / "SOUL.md"
  persona_ok = args.no_persona or (
    soul.is_file() and _SOUL_BEGIN in soul.read_text(encoding="utf-8")
  )
  good &= _check("Hermes pmgo persona", persona_ok, str(soul))
  return good


def doctor_openclaw(_args: argparse.Namespace, root: Path) -> bool:
  binary = shutil.which("openclaw")
  good = _check("OpenClaw CLI", binary is not None, binary or "not found")
  good &= _check("MCP dependencies", _dependencies_available(), "mcp + PyYAML")
  if binary is None:
    return False
  mcp = _run(
    ["openclaw", "mcp", "show", "pmgo", "--json"],
    cwd=root,
    capture=True,
    check=False,
  )
  expected_script = str(root / "scripts" / "pmgo_mcp_server.py")
  expected_workspace = str(root)
  mcp_ok = (
    mcp.returncode == 0
    and expected_script in mcp.stdout
    and expected_workspace in mcp.stdout
  )
  good &= _check(
    "OpenClaw pmgo MCP",
    mcp_ok,
    "registered with expected paths" if mcp_ok else (mcp.stderr.strip() or "missing or stale"),
  )
  try:
    agent = _openclaw_agent(root)
    expected_agent_workspace = str((root / "agent").resolve())
    actual_workspace = str(agent.get("workspace", "")) if agent else ""
    agent_ok = bool(
      agent
      and actual_workspace
      and str(Path(actual_workspace).expanduser().resolve()) == expected_agent_workspace
    )
    good &= _check(
      "OpenClaw pmgo agent",
      agent_ok,
      "workspace registered" if agent_ok else "missing or points to another workspace",
    )
  except SetupError as exc:
    good &= _check("OpenClaw pmgo agent", False, str(exc))
  return good


def start_runtime(args: argparse.Namespace, root: Path) -> int:
  if args.runtime == "hermes":
    command = ["hermes", "dashboard", *args.runtime_arg]
    cwd = root / "agent"
  else:
    command = ["openclaw", "dashboard", *args.runtime_arg]
    cwd = root
  if shutil.which(command[0]) is None and not args.dry_run:
    raise SetupError(f"{command[0]} CLI not found in PATH")
  result = _run(command, cwd=cwd, dry_run=args.dry_run, check=False)
  return result.returncode


def build_parser() -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser(description=__doc__)
  sub = parser.add_subparsers(dest="command", required=True)

  def common(target: argparse.ArgumentParser) -> None:
    target.add_argument("--runtime", required=True, choices=["hermes", "openclaw"])
    target.add_argument("--root", type=Path, help="pmgo repository root")
    target.add_argument("--hermes-home", type=Path, help="override HERMES_HOME")
    target.add_argument("--no-persona", action="store_true", help="do not install/check the Hermes persona")

  setup = sub.add_parser("setup", help="install pmgo into a runtime")
  common(setup)
  setup.add_argument("--dry-run", action="store_true", help="print actions without changing anything")
  setup.add_argument("--skip-deps", action="store_true", help="do not install missing Python dependencies")

  doctor = sub.add_parser("doctor", help="diagnose a runtime installation")
  common(doctor)

  uninstall = sub.add_parser("uninstall", help="remove runtime registration while preserving project data")
  common(uninstall)
  uninstall.add_argument("--dry-run", action="store_true", help="print actions without changing anything")

  start = sub.add_parser("start", help="start the selected runtime dashboard")
  common(start)
  start.add_argument("--dry-run", action="store_true", help="print the launch command only")
  start.add_argument("runtime_arg", nargs=argparse.REMAINDER, help="arguments passed to the dashboard")
  return parser


def main(argv: list[str] | None = None) -> int:
  if sys.version_info < (3, 11):
    try:
      python = compatible_python()
    except SetupError as exc:
      print(f"ERROR: {exc}", file=sys.stderr)
      return 1
    forwarded = list(argv) if argv is not None else sys.argv[1:]
    print(f"[setup] Re-running with supported interpreter: {python}", flush=True)
    os.execv(python, [python, str(Path(__file__).resolve()), *forwarded])
  args = build_parser().parse_args(argv)
  root = repo_root(args.root)
  if not (root / "agent" / "AGENTS.md").is_file() or not (root / "scripts" / "pmgo_mcp_server.py").is_file():
    print(f"ERROR: not a pmgo repository: {root}", file=sys.stderr)
    return 1
  venv = _venv_python(root)
  if (
    args.command in {"doctor", "uninstall"}
    and venv.is_file()
    and Path(sys.executable).absolute() != venv.absolute()
  ):
    print(f"[{args.command}] Re-running inside pmgo virtual environment: {venv}", flush=True)
    os.execv(str(venv), [str(venv), str(Path(__file__).resolve()), *sys.argv[1:]])
  try:
    if args.command == "setup":
      if args.runtime == "hermes":
        setup_hermes(args, root)
      else:
        setup_openclaw(args, root)
      return 0
    if args.command == "doctor":
      ok = doctor_hermes(args, root) if args.runtime == "hermes" else doctor_openclaw(args, root)
      return 0 if ok else 1
    if args.command == "uninstall":
      if args.runtime == "hermes":
        uninstall_hermes(args, root)
      else:
        uninstall_openclaw(args, root)
      return 0
    return start_runtime(args, root)
  except (SetupError, subprocess.CalledProcessError, OSError) as exc:
    print(f"ERROR: {exc}", file=sys.stderr)
    return 1


if __name__ == "__main__":
  raise SystemExit(main())
