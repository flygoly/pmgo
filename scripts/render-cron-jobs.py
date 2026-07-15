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
    if cron:
      lines.append(
        "openclaw cron add "
        f"--name {shlex.quote('pmgo-' + name)} "
        f"--cron {shlex.quote(cron)} "
        "--tz Asia/Shanghai "
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
  lines = [
    "# Generated from cron/jobs.yaml — adapt channel flags to your Hermes setup.",
    "# See runtimes/hermes/cron.examples.sh",
    "",
  ]
  for job in jobs:
    name = job.get("name", "job")
    msg = messages.get(name, "You are pmgo. Run the appropriate MCP report tools.")
    cron = job.get("cron")
    if not cron:
      lines.append(f"# Skip non-cron job: {name}")
      continue
    lines.append(
      "hermes cron create "
      f"--name {shlex.quote('pmgo-' + name)} "
      f"--cron {shlex.quote(cron)} "
      f"--message {shlex.quote(msg)}"
    )
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
