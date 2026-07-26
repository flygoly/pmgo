#!/usr/bin/env python3
"""Generate OpenClaw / Hermes cron CLI commands from cron/jobs.yaml + shared messages."""

from __future__ import annotations

import argparse
import os
import re
import shlex
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JOBS = ROOT / "cron" / "jobs.yaml"
MESSAGES = ROOT / "shared" / "cron-messages.md"


def _load_messages() -> dict[str, str]:
  text = MESSAGES.read_text(encoding="utf-8")
  # Sections: ## Daily standup / ## Weekly report / ## Blocker scan
  mapping = {
    "morning-briefing": "Daily standup",
    "weekly-report": "Weekly report",
    "blocker-scan": "Blocker scan",
  }
  out: dict[str, str] = {}
  for job_name, heading in mapping.items():
    pat = rf"## {re.escape(heading)}[^\n]*\n+```\n(.*?)```"
    m = re.search(pat, text, flags=re.DOTALL | re.IGNORECASE)
    if m:
      out[job_name] = " ".join(m.group(1).split())
  return out


def _parse_jobs() -> list[dict[str, str]]:
  # Tiny YAML subset parser for our jobs file (avoids requiring PyYAML for openclaw path).
  jobs: list[dict[str, str]] = []
  current: dict[str, str] | None = None
  for raw in JOBS.read_text(encoding="utf-8").splitlines():
    line = raw.strip()
    if not line or line.startswith("#"):
      continue
    if line.startswith("- name:"):
      if current:
        jobs.append(current)
      current = {"name": line.split(":", 1)[1].strip()}
      continue
    if current is None:
      continue
    if ":" in line:
      key, val = line.split(":", 1)
      current[key.strip()] = val.strip().strip('"')
  if current:
    jobs.append(current)
  return jobs


def render_openclaw(jobs: list[dict[str, str]], messages: dict[str, str]) -> str:
  agent = os.environ.get("PMGO_AGENT_ID", "<PMGO_AGENT_ID>")
  to = os.environ.get("TELEGRAM_TO", "<TELEGRAM_TO>")
  lines = [
    "# Generated from cron/jobs.yaml — review before running.",
    f"# export PMGO_AGENT_ID={shlex.quote(agent)}",
    f"# export TELEGRAM_TO={shlex.quote(to)}",
    "",
  ]
  for job in jobs:
    name = job.get("name", "job")
    msg = messages.get(name, "You are pmgo. Run the appropriate MCP report tools.")
    cron = job.get("cron")
    heartbeat = job.get("heartbeat")
    tz = job.get("tz") or "Asia/Shanghai"
    if cron:
      lines.append(
        "openclaw cron add "
        f"--name {shlex.quote('pmgo-' + name)} "
        f"--cron {shlex.quote(cron)} "
        f"--tz {shlex.quote(tz)} "
        "--session isolated "
        f"--agent {shlex.quote(agent)} "
        f"--message {shlex.quote(msg)} "
        f"--announce --channel telegram --to {shlex.quote(to)}"
      )
    elif heartbeat:
      lines.append(
        f"# Heartbeat-style job {name!r} ({heartbeat}): "
        "use OpenClaw heartbeat / a short-interval cron in your gateway; "
        f"suggested message: {shlex.quote(msg)}"
      )
    lines.append("")
  return "\n".join(lines).rstrip() + "\n"


def render_hermes(jobs: list[dict[str, str]], messages: dict[str, str]) -> str:
  """
  Hermes CLI shape (upstream hermes_cli/subcommands/cron.py):

    hermes cron create SCHEDULE [PROMPT] [--name ...] [--deliver ...]

  Schedule and prompt are positional. There is no --cron / --schedule / --message /
  --timezone on create; timezone is global (HERMES_TIMEZONE or config.yaml).
  """
  deliver = os.environ.get("HERMES_CRON_DELIVER", "").strip()
  workdir = os.environ.get("PMGO_WORKSPACE", "").strip()
  cron_jobs = [j for j in jobs if j.get("cron")]
  tz_values = sorted({j.get("tz") or "local" for j in cron_jobs if j.get("cron")})

  lines = [
    "# Generated from cron/jobs.yaml — review before running.",
    "# Hermes CLI: hermes cron create SCHEDULE [PROMPT] [--name ...] [--deliver ...]",
    "# Timezone is gateway-global (HERMES_TIMEZONE or config.yaml timezone), not per-job.",
  ]
  if len(tz_values) > 1:
    lines.append(
      f"# NOTE: jobs.yaml lists multiple tz values ({', '.join(tz_values)}). "
      "Pick one HERMES_TIMEZONE and adjust cron exprs if needed."
    )
  elif tz_values:
    lines.append(f"# Suggested HERMES_TIMEZONE / config timezone: {tz_values[0]}")
  if deliver:
    lines.append(f"# HERMES_CRON_DELIVER={shlex.quote(deliver)}")
  else:
    lines.append(
      "# Optional delivery: export HERMES_CRON_DELIVER=telegram  "
      "# (or discord / feishu chat id — see hermes cron create --help)"
    )
  if workdir:
    lines.append(f"# PMGO_WORKSPACE={shlex.quote(workdir)} (passed as --workdir)")
  lines.append("# See runtimes/hermes/cron.examples.sh")
  lines.append("")

  for job in jobs:
    name = job.get("name", "job")
    msg = messages.get(name, "You are pmgo. Run the appropriate MCP report tools.")
    cron = job.get("cron")
    if not cron:
      lines.append(f"# Skip non-cron job: {name}")
      lines.append("")
      continue
    tz = job.get("tz")
    if tz:
      lines.append(f"# Intent tz from jobs.yaml: {tz}")
    cmd = (
      "hermes cron create "
      f"{shlex.quote(cron)} "
      f"{shlex.quote(msg)} "
      f"--name {shlex.quote('pmgo-' + name)}"
    )
    if deliver:
      cmd += f" --deliver {shlex.quote(deliver)}"
    if workdir:
      cmd += f" --workdir {shlex.quote(workdir)}"
    lines.append(cmd)
    lines.append("")
  return "\n".join(lines).rstrip() + "\n"


def main() -> int:
  parser = argparse.ArgumentParser(description="Render gateway cron commands from cron/jobs.yaml.")
  parser.add_argument("--runtime", choices=["openclaw", "hermes"], required=True)
  args = parser.parse_args()
  if not JOBS.is_file():
    print(f"ERROR: missing {JOBS}", file=sys.stderr)
    return 1
  jobs = _parse_jobs()
  messages = _load_messages()
  if args.runtime == "openclaw":
    print(render_openclaw(jobs, messages), end="")
  else:
    print(render_hermes(jobs, messages), end="")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
