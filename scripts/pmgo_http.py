"""Minimal stdlib JSON HTTPS helpers shared by integration clients."""

from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Mapping, Optional


def request_json(
  method: str,
  url: str,
  *,
  headers: Optional[Mapping[str, str]] = None,
  body: Optional[dict[str, Any]] = None,
  query: Optional[Mapping[str, str]] = None,
  timeout: float = 60,
  error_prefix: str = "HTTP",
) -> tuple[Any, dict[str, str]]:
  """
  Perform an HTTPS JSON request.

  Returns (parsed_json_or_None, response_headers_lowercased).
  Raises RuntimeError on HTTP errors with a readable message.
  """
  full = url
  if query:
    sep = "&" if "?" in full else "?"
    full = full + sep + urllib.parse.urlencode(dict(query))
  data: Optional[bytes] = None
  hdrs = {str(k): str(v) for k, v in (headers or {}).items()}
  if body is not None:
    data = json.dumps(body).encode("utf-8")
    hdrs.setdefault("Content-Type", "application/json")
  req = urllib.request.Request(full, data=data, headers=hdrs, method=method)
  ctx = ssl.create_default_context()
  try:
    with urllib.request.urlopen(req, context=ctx, timeout=timeout) as resp:  # noqa: S310
      raw = resp.read().decode("utf-8")
      resp_headers = {k.lower(): v for k, v in resp.headers.items()}
      if not raw:
        return None, resp_headers
      return json.loads(raw), resp_headers
  except urllib.error.HTTPError as e:
    err = e.read().decode("utf-8", errors="replace")
    try:
      payload = json.loads(err)
      if isinstance(payload, dict):
        msgs = payload.get("errorMessages")
        if isinstance(msgs, list) and msgs:
          msg = "; ".join(str(m) for m in msgs)
        else:
          msg = str(payload.get("message", err))
      else:
        msg = err or e.reason
    except json.JSONDecodeError:
      msg = err or e.reason
    raise RuntimeError(f"{error_prefix} {e.code} {e.reason}: {msg}") from e
