#!/usr/bin/env python3
"""Unified pmgo entrypoint for onboarding, runtime control, and the local UI."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import runtime_manager

from pmgo_app.core import NOTE_FILES, LocalCore
from pmgo_app.paths import default_data_dir


DEFAULT_CONFIG = Path(
  os.environ.get("PMGO_CONFIG", "")
  or Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "pmgo" / "config.toml"
).expanduser()


class CliError(RuntimeError):
  """A user-actionable pmgo CLI failure."""


def _toml_string(value: str) -> str:
  return json.dumps(value, ensure_ascii=False)


def write_config(path: Path, values: dict[str, str]) -> None:
  """Write non-secret pmgo settings as a small TOML document."""
  path.parent.mkdir(parents=True, exist_ok=True)
  if path.is_file():
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    shutil.copy2(path, path.with_name(f"{path.name}.pmgo-backup-{stamp}"))
  lines = ["# Managed by pmgo. Secrets belong in runtime-specific secret stores."]
  for key in ("workspace", "data_dir", "runtime", "default_project_id", "locale", "project_name"):
    value = values.get(key)
    if value:
      lines.append(f"{key} = {_toml_string(value)}")
  path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _print_value(value: Any, *, as_json: bool = False) -> None:
  """Render stable JSON for agents or a compact human-readable view."""
  if as_json:
    print(json.dumps(value, indent=2, ensure_ascii=False))
    return
  rows = value if isinstance(value, list) else [value]
  if not rows:
    print("No results.")
    return
  if all(isinstance(row, dict) for row in rows):
    for row in rows:
      assert isinstance(row, dict)
      identifier = str(row.get("id", ""))
      label = str(row.get("name") or row.get("title") or row.get("filename") or identifier)
      state = str(row.get("status", ""))
      suffix = f" [{state}]" if state else ""
      print(f"{identifier}\t{label}{suffix}".rstrip())
    return
  print(value)


def read_config(path: Path) -> dict[str, Any]:
  if not path.is_file():
    raise CliError(f"pmgo is not onboarded; configuration not found: {path}")
  try:
    import tomllib
  except ImportError as exc:  # pragma: no cover - main re-execs on Python 3.11+
    raise CliError("pmgo requires Python 3.11+") from exc
  with path.open("rb") as handle:
    data = tomllib.load(handle)
  if not isinstance(data, dict):
    raise CliError(f"Invalid pmgo configuration: {path}")
  return data


def _run(
  command: list[str],
  *,
  cwd: Path = ROOT,
  env: dict[str, str] | None = None,
  capture: bool = False,
  dry_run: bool = False,
) -> subprocess.CompletedProcess[str]:
  printable = " ".join(json.dumps(part) if " " in part else part for part in command)
  print(f"$ {printable}")
  if dry_run:
    return subprocess.CompletedProcess(command, 0, "", "")
  return subprocess.run(
    command,
    cwd=cwd,
    env=env,
    check=True,
    capture_output=capture,
    text=True,
  )


def _detect_runtime() -> str:
  found = [name for name in ("hermes", "openclaw") if shutil.which(name)]
  if len(found) == 1:
    return found[0]
  if not found:
    raise CliError("Neither Hermes nor OpenClaw was found; install one or pass --runtime explicitly")
  if sys.stdin.isatty():
    print("Detected both Hermes and OpenClaw:")
    print("  1) hermes")
    print("  2) openclaw")
    choice = input("Select runtime [1]: ").strip() or "1"
    if choice in {"1", "hermes"}:
      return "hermes"
    if choice in {"2", "openclaw"}:
      return "openclaw"
  raise CliError("Both runtimes were found; choose --runtime hermes or --runtime openclaw")


def _parse_bootstrap_json(output: str) -> dict[str, Any]:
  start = output.find("{")
  if start < 0:
    raise CliError("Project bootstrap did not return project metadata")
  try:
    value, _ = json.JSONDecoder().raw_decode(output[start:])
  except json.JSONDecodeError as exc:
    raise CliError("Could not parse project bootstrap output") from exc
  if not isinstance(value, dict) or not value.get("id"):
    raise CliError("Project bootstrap returned incomplete metadata")
  return value


def cmd_onboard(args: argparse.Namespace) -> int:
  runtime = _detect_runtime() if args.runtime == "auto" else args.runtime
  config_path = args.config.expanduser()
  if runtime == "standalone":
    data_dir = args.data_dir.expanduser().resolve()
    if args.dry_run:
      print(f"[dry-run] Would initialize local data in {data_dir}")
      print(f"[dry-run] Would write {config_path}")
      return 0
    project = LocalCore(data_dir).initialize(project_name=args.name, locale=args.locale)
    write_config(config_path, {
      "data_dir": str(data_dir),
      "runtime": "standalone",
      "default_project_id": str(project["id"]),
      "locale": args.locale,
      "project_name": args.name,
    })
    print(f"[ready] Local pmgo data initialized in {data_dir}")
    print(f"[updated] {config_path}")
    print("Next: npm run desktop:dev")
    if args.open:
      return _run(["npm", "run", "desktop:dev"]).returncode
    return 0
  python = runtime_manager.runtime_python(ROOT)
  runtime_locale = {"zh-Hans": "zh-CN", "zh-Hant": "zh-TW"}.get(args.locale, args.locale)
  bootstrap = [
    python,
    str(ROOT / "scripts" / "gtd-bootstrap.py"),
    "--name",
    args.name,
    "--locale",
    runtime_locale,
  ]
  if args.slug:
    bootstrap.extend(["--slug", args.slug])
  if args.dry_run:
    _run(bootstrap, dry_run=True)
    _run(
      [python, str(ROOT / "scripts" / "runtime_manager.py"), "setup", "--runtime", runtime, "--dry-run"],
      dry_run=True,
    )
    print(f"[dry-run] Would write {config_path}")
    return 0

  result = _run(bootstrap, capture=True)
  metadata = _parse_bootstrap_json(result.stdout)
  project_id = str(metadata["id"])
  workspace = str(ROOT.resolve())
  config = {
    "workspace": workspace,
    "data_dir": str((ROOT / "memory").resolve()),
    "runtime": runtime,
    "default_project_id": project_id,
    "locale": args.locale,
    "project_name": args.name,
  }
  write_config(config_path, config)
  print(f"[updated] {config_path}")

  env = os.environ.copy()
  env.update(
    {
      "PMGO_WORKSPACE": workspace,
      "PMGO_DEFAULT_PROJECT_ID": project_id,
      "PMGO_DEFAULT_LOCALE": runtime_locale,
      "PMGO_MEMORY_DB": str((ROOT / "memory" / "pmgo.db").resolve()),
      "PMGO_CONFIG": str(config_path),
    }
  )
  setup = [
    python,
    str(ROOT / "scripts" / "runtime_manager.py"),
    "setup",
    "--runtime",
    runtime,
  ]
  if args.no_persona:
    setup.append("--no-persona")
  _run(setup, env=env)
  _run(
    [python, str(ROOT / "scripts" / "runtime_manager.py"), "doctor", "--runtime", runtime],
    env=env,
  )
  print("[ready] pmgo onboarding completed")
  print("Next: npm run pmgo -- ui")
  if args.open:
    return cmd_open(argparse.Namespace(config=config_path, runtime=None, runtime_arg=[]))
  return 0


def _configured_env(config: dict[str, Any], config_path: Path) -> dict[str, str]:
  env = os.environ.copy()
  locale = {"zh-Hans": "zh-CN", "zh-Hant": "zh-TW"}.get(
    str(config.get("locale") or ""), config.get("locale")
  )
  mapping = {
    "PMGO_WORKSPACE": config.get("workspace"),
    "PMGO_DEFAULT_PROJECT_ID": config.get("default_project_id"),
    "PMGO_DEFAULT_LOCALE": locale,
    "PMGO_CONFIG": str(config_path),
  }
  data_dir = str(config.get("data_dir") or "").strip()
  if data_dir:
    mapping["PMGO_MEMORY_DB"] = str(Path(data_dir).expanduser() / "pmgo.db")
  env.update({key: str(value) for key, value in mapping.items() if value})
  return env


def _core_from_config(config_path: Path) -> tuple[LocalCore, dict[str, Any]]:
  config = read_config(config_path)
  data_dir = str(config.get("data_dir") or "").strip()
  if not data_dir and config.get("workspace"):
    data_dir = str(Path(str(config["workspace"])).expanduser() / "memory")
  if not data_dir:
    raise CliError("No local data directory is configured; run pmgo onboard")
  core = LocalCore(Path(data_dir))
  core.initialize(
    project_name=str(config.get("project_name") or "Personal Office"),
    locale=str(config.get("locale") or "zh-Hans"),
  )
  return core, config


def _project_id(config: dict[str, Any], explicit: str | None) -> str:
  value = str(explicit or config.get("default_project_id") or "").strip()
  if not value:
    raise CliError("No project selected; pass --project or run 'pmgo project use <id>'")
  return value


def cmd_project(args: argparse.Namespace) -> int:
  config_path = args.config.expanduser()
  core, config = _core_from_config(config_path)
  if args.project_command == "list":
    _print_value(core.dashboard()["projects"], as_json=args.json)
    return 0
  if args.project_command == "add":
    project = core.create_project({
      "name": args.name,
      "slug": args.slug,
      "description": args.description,
      "owner": args.owner,
    }, locale=str(config.get("locale") or "zh-Hans"))
    if args.use:
      config["default_project_id"] = project["id"]
      write_config(config_path, {key: str(value) for key, value in config.items() if value is not None})
    _print_value(project, as_json=args.json)
    return 0
  project_id = _project_id(config, args.project_id)
  if args.project_command == "show":
    project = next((row for row in core.dashboard(project_id)["projects"] if row["id"] == project_id), None)
    if project is None:
      raise CliError(f"Project not found: {project_id}")
    _print_value(project, as_json=args.json)
    return 0
  config["default_project_id"] = project_id
  write_config(config_path, {key: str(value) for key, value in config.items() if value is not None})
  print(f"[selected] {project_id}")
  return 0


def cmd_task(args: argparse.Namespace) -> int:
  core, config = _core_from_config(args.config.expanduser())
  if args.task_command == "list":
    tasks = core.dashboard(_project_id(config, args.project))["tasks"]
    if args.status:
      tasks = [task for task in tasks if task["status"] == args.status]
    _print_value(tasks, as_json=args.json)
    return 0
  if args.task_command == "add":
    task = core.create_task({
      "project_id": _project_id(config, args.project),
      "title": args.title,
      "detail": args.detail,
      "status": args.status,
      "priority": args.priority,
      "due_at": args.due,
    })
    _print_value(task, as_json=args.json)
    return 0
  if args.task_command == "delete":
    if not args.yes:
      raise CliError("Task deletion requires --yes")
    core.delete_task(args.task_id)
    print(f"[deleted] {args.task_id}")
    return 0
  payload = {
    key: value for key, value in {
      "title": getattr(args, "title", None),
      "detail": getattr(args, "detail", None),
      "status": "done" if args.task_command == "done" else getattr(args, "status", None),
      "priority": getattr(args, "priority", None),
      "due_at": getattr(args, "due", None),
      "blocked_reason": getattr(args, "blocked_reason", None),
    }.items() if value is not None
  }
  task = core.update_task(args.task_id, payload)
  _print_value(task, as_json=args.json)
  return 0


def cmd_context(args: argparse.Namespace) -> int:
  core, config = _core_from_config(args.config.expanduser())
  context = core.build_context(_project_id(config, args.project), include_notes=not args.no_notes)
  if args.json:
    _print_value(context, as_json=True)
  else:
    print(context["text"])
  return 0


def cmd_note(args: argparse.Namespace) -> int:
  core, config = _core_from_config(args.config.expanduser())
  project_id = _project_id(config, args.project)
  if args.note_command == "list":
    _print_value(core.list_notes(project_id), as_json=args.json)
    return 0
  if args.note_command == "show":
    note = core.read_note(project_id, args.note_id)
    if args.json:
      _print_value(note, as_json=True)
    else:
      print(note["content"], end="" if note["content"].endswith("\n") else "\n")
    return 0
  content = args.content
  if args.file:
    content = args.file.expanduser().read_text(encoding="utf-8")
  if content is None:
    if sys.stdin.isatty():
      raise CliError("Pass --content, --file, or pipe Markdown on stdin")
    content = sys.stdin.read()
  note = core.write_note(project_id, args.note_id, content)
  _print_value({"id": note["id"], "filename": note["filename"]}, as_json=args.json)
  return 0


def cmd_open(args: argparse.Namespace) -> int:
  config_path = args.config.expanduser()
  config = read_config(config_path)
  runtime = args.runtime or str(config.get("runtime", ""))
  if runtime == "standalone":
    return _run(["npm", "run", "desktop:dev"]).returncode
  if runtime not in {"hermes", "openclaw"}:
    raise CliError("No valid runtime configured; run pmgo onboard")
  command = [
    runtime_manager.runtime_python(ROOT),
    str(ROOT / "scripts" / "runtime_manager.py"),
    "start",
    "--runtime",
    runtime,
    *args.runtime_arg,
  ]
  return _run(command, env=_configured_env(config, config_path)).returncode


def cmd_status(args: argparse.Namespace) -> int:
  config_path = args.config.expanduser()
  config = read_config(config_path)
  runtime = args.runtime or str(config.get("runtime", ""))
  if runtime == "standalone":
    data_dir = Path(str(config.get("data_dir") or default_data_dir())).expanduser()
    state = LocalCore(data_dir).dashboard(str(config.get("default_project_id") or "") or None)
    print(json.dumps({
      "mode": "standalone",
      "data_dir": str(data_dir),
      "database": str(data_dir / "pmgo.db"),
      "projects": len(state["projects"]),
      "tasks": len(state["tasks"]),
    }, indent=2, ensure_ascii=False))
    return 0
  command = [
    runtime_manager.runtime_python(ROOT),
    str(ROOT / "scripts" / "runtime_manager.py"),
    "doctor",
    "--runtime",
    runtime,
  ]
  return _run(command, env=_configured_env(config, config_path)).returncode


def cmd_uninstall(args: argparse.Namespace) -> int:
  config_path = args.config.expanduser()
  config = read_config(config_path)
  runtime = args.runtime or str(config.get("runtime", ""))
  if runtime == "standalone":
    if args.dry_run:
      print(f"[dry-run] Would remove configuration {config_path}; local data would be preserved")
      return 0
    config_path.unlink(missing_ok=True)
    print(f"[removed] {config_path}")
    print(f"[preserved] {config.get('data_dir') or default_data_dir()}")
    return 0
  command = [
    runtime_manager.runtime_python(ROOT),
    str(ROOT / "scripts" / "runtime_manager.py"),
    "uninstall",
    "--runtime",
    runtime,
  ]
  if args.dry_run:
    command.append("--dry-run")
  return _run(command, env=_configured_env(config, config_path)).returncode


def cmd_ui(args: argparse.Namespace) -> int:
  read_config(args.config.expanduser())
  return _run(["npm", "run", "desktop:dev"]).returncode


def build_parser() -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser(prog="pmgo", description=__doc__)
  parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG, help="pmgo config.toml path")
  sub = parser.add_subparsers(dest="command", required=True)

  onboard = sub.add_parser("onboard", help="initialize standalone pmgo or connect an optional runtime")
  onboard.add_argument("--runtime", choices=["standalone", "auto", "hermes", "openclaw"], default="standalone")
  onboard.add_argument("--data-dir", type=Path, default=default_data_dir())
  onboard.add_argument("--name", default="Personal Office")
  onboard.add_argument("--slug")
  onboard.add_argument("--locale", choices=["en", "zh-Hans", "zh-Hant", "zh-CN", "zh-TW"], default="zh-Hans")
  onboard.add_argument("--dry-run", action="store_true")
  onboard.add_argument("--no-persona", action="store_true")
  onboard.add_argument("--open", action="store_true", help="open the selected runtime dashboard afterwards")
  onboard.set_defaults(func=cmd_onboard)

  open_cmd = sub.add_parser("open", help="open the configured runtime dashboard")
  open_cmd.add_argument("--runtime", choices=["standalone", "hermes", "openclaw"])
  open_cmd.add_argument("runtime_arg", nargs=argparse.REMAINDER)
  open_cmd.set_defaults(func=cmd_open)

  status = sub.add_parser("status", help="diagnose the configured runtime")
  status.add_argument("--runtime", choices=["standalone", "hermes", "openclaw"])
  status.set_defaults(func=cmd_status)

  ui = sub.add_parser("ui", help="open the standalone local pmgo dashboard")
  ui.add_argument("--host", default="127.0.0.1")
  ui.add_argument("--port", type=int, default=8765)
  ui.add_argument("--no-open", action="store_true")
  ui.set_defaults(func=cmd_ui)

  uninstall = sub.add_parser("uninstall", help="remove runtime registration and preserve project data")
  uninstall.add_argument("--runtime", choices=["hermes", "openclaw"])
  uninstall.add_argument("--dry-run", action="store_true")
  uninstall.set_defaults(func=cmd_uninstall)

  project = sub.add_parser("project", help="manage local projects")
  project_sub = project.add_subparsers(dest="project_command", required=True)
  project_list = project_sub.add_parser("list", help="list projects")
  project_list.add_argument("--json", action="store_true")
  project_list.set_defaults(func=cmd_project)
  project_add = project_sub.add_parser("add", help="create a project")
  project_add.add_argument("name")
  project_add.add_argument("--slug")
  project_add.add_argument("--description")
  project_add.add_argument("--owner")
  project_add.add_argument("--use", action="store_true", help="select the new project")
  project_add.add_argument("--json", action="store_true")
  project_add.set_defaults(func=cmd_project)
  project_show = project_sub.add_parser("show", help="show one project")
  project_show.add_argument("project_id", nargs="?")
  project_show.add_argument("--json", action="store_true")
  project_show.set_defaults(func=cmd_project)
  project_use = project_sub.add_parser("use", help="select the default project")
  project_use.add_argument("project_id")
  project_use.set_defaults(func=cmd_project, json=False)

  task = sub.add_parser("task", help="manage local tasks")
  task_sub = task.add_subparsers(dest="task_command", required=True)
  task_list = task_sub.add_parser("list", help="list tasks")
  task_list.add_argument("--project")
  task_list.add_argument("--status", choices=["todo", "doing", "blocked", "done", "cancelled"])
  task_list.add_argument("--json", action="store_true")
  task_list.set_defaults(func=cmd_task)
  task_add = task_sub.add_parser("add", help="create a task")
  task_add.add_argument("title")
  task_add.add_argument("--project")
  task_add.add_argument("--detail")
  task_add.add_argument("--status", default="todo", choices=["todo", "doing", "blocked", "done", "cancelled"])
  task_add.add_argument("--priority", default="medium", choices=["low", "medium", "high", "critical"])
  task_add.add_argument("--due")
  task_add.add_argument("--json", action="store_true")
  task_add.set_defaults(func=cmd_task)
  task_update = task_sub.add_parser("update", help="update a task")
  task_update.add_argument("task_id")
  task_update.add_argument("--title")
  task_update.add_argument("--detail")
  task_update.add_argument("--status", choices=["todo", "doing", "blocked", "done", "cancelled"])
  task_update.add_argument("--priority", choices=["low", "medium", "high", "critical"])
  task_update.add_argument("--due")
  task_update.add_argument("--blocked-reason")
  task_update.add_argument("--json", action="store_true")
  task_update.set_defaults(func=cmd_task)
  task_done = task_sub.add_parser("done", help="mark a task done")
  task_done.add_argument("task_id")
  task_done.add_argument("--json", action="store_true")
  task_done.set_defaults(func=cmd_task)
  task_delete = task_sub.add_parser("delete", help="delete a task")
  task_delete.add_argument("task_id")
  task_delete.add_argument("--yes", action="store_true")
  task_delete.set_defaults(func=cmd_task, json=False)

  context = sub.add_parser("context", help="build agent-ready project context")
  context.add_argument("--project")
  context.add_argument("--no-notes", action="store_true")
  context.add_argument("--json", action="store_true")
  context.set_defaults(func=cmd_context)

  note = sub.add_parser("note", help="manage project Markdown notes")
  note_sub = note.add_subparsers(dest="note_command", required=True)
  note_list = note_sub.add_parser("list", help="list note files")
  note_list.add_argument("--project")
  note_list.add_argument("--json", action="store_true")
  note_list.set_defaults(func=cmd_note)
  note_show = note_sub.add_parser("show", help="print a note")
  note_show.add_argument("note_id", choices=list(NOTE_FILES))
  note_show.add_argument("--project")
  note_show.add_argument("--json", action="store_true")
  note_show.set_defaults(func=cmd_note)
  note_set = note_sub.add_parser("set", help="replace a Markdown note")
  note_set.add_argument("note_id", choices=["overview", "meetings", "decisions", "weekly"])
  note_set.add_argument("--project")
  note_set.add_argument("--content")
  note_set.add_argument("--file", type=Path)
  note_set.add_argument("--json", action="store_true")
  note_set.set_defaults(func=cmd_note)
  return parser


def main(argv: list[str] | None = None) -> int:
  if sys.version_info < (3, 11):
    python = runtime_manager.compatible_python()
    forwarded = list(argv) if argv is not None else sys.argv[1:]
    os.execv(python, [python, str(Path(__file__).resolve()), *forwarded])
  args = build_parser().parse_args(argv)
  try:
    return int(args.func(args) or 0)
  except (CliError, runtime_manager.SetupError, subprocess.CalledProcessError, OSError, ValueError, KeyError) as exc:
    print(f"ERROR: {exc}", file=sys.stderr)
    return 1


if __name__ == "__main__":
  raise SystemExit(main())
