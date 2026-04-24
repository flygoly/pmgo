#!/usr/bin/env python3

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def run_step(command: list[str], name: str) -> None:
  printable = " ".join(command)
  print(f"[memory:scaffold] {name}: {printable}")
  subprocess.run(command, cwd=ROOT, check=True)


def main() -> None:
  parser = argparse.ArgumentParser(
    description=(
      "Run memory init/migrate/verify in order, and optionally scaffold "
      "memory/projects/<slug>/ markdown files."
    )
  )
  parser.add_argument("--project-name", help="Optional project display name.")
  parser.add_argument("--project-slug", help="Optional project slug.")
  parser.add_argument(
    "--locale",
    default="en",
    help="Project template locale when --project-name is provided: en, zh-CN, zh-TW.",
  )
  args = parser.parse_args()

  run_step([sys.executable, "scripts/init-memory-db.py"], "init-db")
  run_step([sys.executable, "scripts/migrate-memory-db.py"], "migrate-db")
  run_step([sys.executable, "scripts/verify-memory-db.py"], "verify-db")

  if args.project_name:
    command = [
      sys.executable,
      "scripts/init-memory-project.py",
      "--name",
      args.project_name,
      "--locale",
      args.locale,
    ]
    if args.project_slug:
      command.extend(["--slug", args.project_slug])
    run_step(command, "init-project-memory")
  elif args.project_slug:
    raise ValueError("--project-slug requires --project-name.")

  print("[memory:scaffold] Completed.")


if __name__ == "__main__":
  main()
