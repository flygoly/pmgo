"""Environment: LINEAR_API_KEY (Personal API key from Linear → Settings → API)."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class LinearConfig:
  api_key: str
  user_agent: str = "pmgo-integration-linear/0.1"


def load_config(*, require_key: bool = True) -> LinearConfig:
  key = (os.environ.get("LINEAR_API_KEY") or "").strip()
  if require_key and not key:
    raise OSError("LINEAR_API_KEY is not set or empty.")
  return LinearConfig(api_key=key)
