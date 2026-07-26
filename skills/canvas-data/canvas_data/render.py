"""Render OpenClaw Live Canvas HTML + data.json from a snapshot."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Any

from .build import build_snapshot

_ROOT = Path(__file__).resolve().parents[3]
_TEMPLATE = _ROOT / "runtimes" / "openclaw" / "canvas" / "pmgo" / "index.html"
_DEFAULT_OUT = _ROOT / "reports" / "canvas" / "pmgo"

_DATA_BLOCK = re.compile(
  r"/\* __PMGO_DATA_START__ \*/.*?/\* __PMGO_DATA_END__ \*/",
  re.DOTALL,
)


def template_path() -> Path:
  return _TEMPLATE


def default_out_dir() -> Path:
  return _DEFAULT_OUT


def embed_snapshot(html: str, snapshot: dict[str, Any]) -> str:
  payload = json.dumps(snapshot, ensure_ascii=False, default=str)
  block = (
    "/* __PMGO_DATA_START__ */\n"
    f"    window.__PMGO_DATA__ = {payload};\n"
    "    /* __PMGO_DATA_END__ */"
  )
  if not _DATA_BLOCK.search(html):
    raise ValueError("Canvas template missing __PMGO_DATA__ markers")
  return _DATA_BLOCK.sub(block, html)


def render_canvas(
  project_id: str,
  *,
  out_dir: Path | None = None,
  inline: bool = True,
) -> dict[str, Any]:
  """
  Write OpenClaw-presentable canvas files.

  - `index.html` — template (optionally with inlined snapshot)
  - `data.json` — snapshot for fetch()/live-reload workflows
  """
  if not _TEMPLATE.is_file():
    raise FileNotFoundError(f"Missing canvas template: {_TEMPLATE}")
  dest = (out_dir or _DEFAULT_OUT).expanduser().resolve()
  dest.mkdir(parents=True, exist_ok=True)

  snapshot = build_snapshot(project_id)
  data_path = dest / "data.json"
  data_path.write_text(
    json.dumps(snapshot, indent=2, ensure_ascii=False, default=str) + "\n",
    encoding="utf-8",
  )

  html_src = _TEMPLATE.read_text(encoding="utf-8")
  html_out = embed_snapshot(html_src, snapshot) if inline else html_src
  index_path = dest / "index.html"
  index_path.write_text(html_out, encoding="utf-8")

  # Keep a non-inlined copy of the template assets note for operators.
  readme = dest / "README.txt"
  readme.write_text(
    "pmgo Live Canvas output (HTML artifacts)\n"
    "Runtime-neutral files: index.html + data.json\n"
    "\n"
    "OpenClaw:\n"
    "  1) Point canvasHost.root at this directory (or copy under your canvas root).\n"
    "  2) Present: /__openclaw__/canvas/index.html\n"
    "\n"
    "Hermes (and other gateways):\n"
    "  No Live Canvas host — open index.html locally, or keep using Markdown reports\n"
    "  (npm run daily-standup / weekly-report / pmgo_*_report MCP tools).\n"
    "\n"
    "Refresh: npm run canvas:render -- --project-id <UUID>\n",
    encoding="utf-8",
  )

  return {
    "ok": True,
    "project_id": project_id,
    "out_dir": str(dest),
    "index_html": str(index_path),
    "data_json": str(data_path),
    "inline": inline,
    "runtime_notes": {
      "shared": "Artifacts are HTML + JSON under out_dir; safe to regenerate anytime.",
      "openclaw": (
        "Set canvasHost.root to out_dir, then present "
        "/__openclaw__/canvas/index.html "
        "(example: canvas action:present "
        "target:http://<gateway-host>:18793/__openclaw__/canvas/index.html)."
      ),
      "hermes": (
        "No canvasHost — do not invent /__openclaw__/ URLs. "
        "Open index.html in a browser if useful, otherwise prefer Markdown reports."
      ),
    },
  }


def sync_template_to(out_dir: Path) -> Path:
  """Copy stock template (without project data) into out_dir."""
  out_dir.mkdir(parents=True, exist_ok=True)
  dest = out_dir / "index.html"
  shutil.copyfile(_TEMPLATE, dest)
  return dest
