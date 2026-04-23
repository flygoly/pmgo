#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AGENT_DIR="${ROOT_DIR}/agent"

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

pass() {
  echo "OK: $*"
}

require_file() {
  local path="$1"
  [[ -f "${path}" ]] || fail "Missing file: ${path}"
  [[ -s "${path}" ]] || fail "Empty file: ${path}"
  pass "File exists and is non-empty: ${path#${ROOT_DIR}/}"
}

require_json_key() {
  local file="$1"
  local key="$2"
  python3 - "$file" "$key" <<'PY'
import json, sys
path, key = sys.argv[1], sys.argv[2]
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)
if key not in data:
    raise SystemExit(1)
PY
  pass "JSON key '${key}' exists: ${file#${ROOT_DIR}/}"
}

echo "== Static importability checks =="

require_file "${AGENT_DIR}/SOUL.md"
require_file "${AGENT_DIR}/IDENTITY.md"
require_file "${AGENT_DIR}/USER.md"
require_file "${AGENT_DIR}/TOOLS.md"
require_file "${AGENT_DIR}/AGENTS.md"
require_file "${AGENT_DIR}/README.md"

require_file "${AGENT_DIR}/locales/zh-CN/SOUL.md"
require_file "${AGENT_DIR}/locales/zh-TW/SOUL.md"
require_file "${ROOT_DIR}/policy/pmgo.policy.yaml"
require_file "${ROOT_DIR}/cron/jobs.yaml"
require_file "${ROOT_DIR}/skills/project-core/SKILL.md"

require_file "${ROOT_DIR}/locales/en.json"
require_file "${ROOT_DIR}/locales/zh-CN.json"
require_file "${ROOT_DIR}/locales/zh-TW.json"

require_json_key "${ROOT_DIR}/locales/en.json" "agent.greeting"
require_json_key "${ROOT_DIR}/locales/zh-CN.json" "agent.greeting"
require_json_key "${ROOT_DIR}/locales/zh-TW.json" "agent.greeting"

echo
echo "== Optional OpenClaw E2E check =="
if [[ "${OPENCLAW_E2E:-0}" != "1" ]]; then
  echo "SKIP: Set OPENCLAW_E2E=1 to run real OpenClaw import validation."
  echo "Done."
  exit 0
fi

command -v openclaw >/dev/null 2>&1 || fail "openclaw CLI not found in PATH."

tmp_home="$(mktemp -d "${TMPDIR:-/tmp}/pmgo-openclaw-test.XXXXXX")"
cleanup() { rm -rf "${tmp_home}"; }
trap cleanup EXIT

echo "Using isolated HOME for E2E: ${tmp_home}"

if openclaw agents --help >/dev/null 2>&1; then
  echo "Running: openclaw agents add pmgo-e2e --workspace ${ROOT_DIR} --non-interactive --json"
  (
    export HOME="${tmp_home}"
    cd "${ROOT_DIR}"
    openclaw agents add pmgo-e2e --workspace "${ROOT_DIR}" --non-interactive --json
    openclaw agents list >/dev/null
  )
  pass "OpenClaw accepted workspace via 'openclaw agents add ...'."
elif openclaw agent --help >/dev/null 2>&1; then
  echo "ERROR: This OpenClaw version exposes 'agent' but not 'agents'."
  echo "Please provide your CLI version and expected import command."
  exit 1
else
  fail "Could not detect a supported OpenClaw CLI command for import."
fi

echo "Done."
