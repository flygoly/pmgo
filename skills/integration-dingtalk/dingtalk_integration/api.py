"""Minimal DingTalk open API client (access token smoke)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from .config import DingTalkConfig

_SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
if str(_SCRIPTS) not in sys.path:
  sys.path.insert(0, str(_SCRIPTS))

from pmgo_http import request_json  # noqa: E402

TOKEN_URL = "https://oapi.dingtalk.com/gettoken"


def get_access_token(cfg: DingTalkConfig) -> dict[str, Any]:
  out, _ = request_json(
    "GET",
    TOKEN_URL,
    headers={"User-Agent": cfg.user_agent},
    query={"appkey": cfg.app_key, "appsecret": cfg.app_secret},
    error_prefix="DingTalk HTTP",
  )
  if not isinstance(out, dict):
    raise RuntimeError("Unexpected DingTalk token response")
  # DingTalk uses errcode 0 for success
  errcode = out.get("errcode")
  if errcode is not None and errcode != 0:
    raise RuntimeError(f"DingTalk token error: {out.get('errmsg') or out}")
  if not out.get("access_token"):
    raise RuntimeError(f"DingTalk token missing access_token: {out}")
  return out
