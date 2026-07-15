"""Structured stderr logging for MCP and CLIs."""

from __future__ import annotations

import json
import logging
import sys
import time
from typing import Any, Optional


def setup_logging(*, name: str = "pmgo", level: int = logging.INFO) -> logging.Logger:
  logger = logging.getLogger(name)
  if logger.handlers:
    return logger
  handler = logging.StreamHandler(sys.stderr)
  handler.setFormatter(logging.Formatter("%(message)s"))
  logger.addHandler(handler)
  logger.setLevel(level)
  logger.propagate = False
  return logger


def log_event(
  logger: logging.Logger,
  event: str,
  *,
  level: int = logging.INFO,
  **fields: Any,
) -> None:
  payload = {"ts": time.time(), "event": event, **fields}
  logger.log(level, json.dumps(payload, default=str, ensure_ascii=False))


def tool_timer() -> float:
  return time.perf_counter()


def elapsed_ms(started: float) -> int:
  return int((time.perf_counter() - started) * 1000)


def maybe_project_id(value: Optional[str]) -> Optional[str]:
  if value is None:
    return None
  text = str(value).strip()
  return text or None
