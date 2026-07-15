"""Environment: DINGTALK_APP_KEY, DINGTALK_APP_SECRET."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class DingTalkConfig:
  app_key: str
  app_secret: str
  user_agent: str = "pmgo-integration-dingtalk/0.1"


def load_config(*, require_credentials: bool = True) -> DingTalkConfig:
  app_key = (os.environ.get("DINGTALK_APP_KEY") or "").strip()
  app_secret = (os.environ.get("DINGTALK_APP_SECRET") or "").strip()
  if require_credentials:
    if not app_key:
      raise OSError("DINGTALK_APP_KEY is not set.")
    if not app_secret:
      raise OSError("DINGTALK_APP_SECRET is not set.")
  return DingTalkConfig(app_key=app_key, app_secret=app_secret)
