"""Environment: NOTION_TOKEN."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class NotionConfig:
  token: str
  user_agent: str = "pmgo-integration-notion/0.1"
  notion_version: str = "2022-06-28"


def load_config(*, require_token: bool = True) -> NotionConfig:
  token = (os.environ.get("NOTION_TOKEN") or "").strip()
  if require_token and not token:
    raise OSError("NOTION_TOKEN is not set.")
  return NotionConfig(token=token)
