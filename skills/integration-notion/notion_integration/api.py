"""Minimal Notion API client (users/me smoke)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from .config import NotionConfig

_SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
if str(_SCRIPTS) not in sys.path:
  sys.path.insert(0, str(_SCRIPTS))

from pmgo_http import request_json  # noqa: E402

API = "https://api.notion.com/v1"


def users_me(cfg: NotionConfig) -> dict[str, Any]:
  out, _ = request_json(
    "GET",
    f"{API}/users/me",
    headers={
      "Authorization": f"Bearer {cfg.token}",
      "Notion-Version": cfg.notion_version,
      "User-Agent": cfg.user_agent,
    },
    error_prefix="Notion HTTP",
  )
  if not isinstance(out, dict):
    raise RuntimeError("Unexpected Notion users/me response")
  return out
