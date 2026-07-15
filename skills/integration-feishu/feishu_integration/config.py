"""Environment: FEISHU_APP_ID, FEISHU_APP_SECRET."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class FeishuConfig:
  app_id: str
  app_secret: str
  user_agent: str = "pmgo-integration-feishu/0.1"


def load_config(*, require_credentials: bool = True) -> FeishuConfig:
  app_id = (os.environ.get("FEISHU_APP_ID") or "").strip()
  app_secret = (os.environ.get("FEISHU_APP_SECRET") or "").strip()
  if require_credentials:
    if not app_id:
      raise OSError("FEISHU_APP_ID is not set.")
    if not app_secret:
      raise OSError("FEISHU_APP_SECRET is not set.")
  return FeishuConfig(app_id=app_id, app_secret=app_secret)
