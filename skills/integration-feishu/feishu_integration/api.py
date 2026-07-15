"""Minimal Feishu open API client (tenant token smoke)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from .config import FeishuConfig

_SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
if str(_SCRIPTS) not in sys.path:
  sys.path.insert(0, str(_SCRIPTS))

from pmgo_http import request_json  # noqa: E402

TOKEN_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"


def tenant_access_token(cfg: FeishuConfig) -> dict[str, Any]:
  out, _ = request_json(
    "POST",
    TOKEN_URL,
    headers={"Content-Type": "application/json", "User-Agent": cfg.user_agent},
    body={"app_id": cfg.app_id, "app_secret": cfg.app_secret},
    error_prefix="Feishu HTTP",
  )
  if not isinstance(out, dict):
    raise RuntimeError("Unexpected Feishu token response")
  code = out.get("code")
  if code is not None and code != 0:
    raise RuntimeError(f"Feishu token error: {out.get('msg') or out}")
  if not out.get("tenant_access_token"):
    raise RuntimeError(f"Feishu token missing tenant_access_token: {out}")
  return out
