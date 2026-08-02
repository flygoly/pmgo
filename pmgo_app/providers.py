"""Pluggable model providers; API keys are accepted per request and never persisted."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ProviderSpec:
  id: str
  name: str
  default_url: str
  default_model: str
  requires_key: bool = True


PROVIDERS = {
  "openai-compatible": ProviderSpec("openai-compatible", "OpenAI compatible", "https://api.openai.com/v1", "gpt-4.1-mini"),
  "ollama": ProviderSpec("ollama", "Ollama (local)", "http://127.0.0.1:11434/v1", "qwen3:8b", False),
}


def list_providers() -> list[dict[str, Any]]:
  return [spec.__dict__ for spec in PROVIDERS.values()]


def chat(payload: dict[str, Any]) -> dict[str, Any]:
  provider_id = str(payload.get("provider", "openai-compatible"))
  if provider_id not in PROVIDERS:
    raise ValueError(f"Unsupported provider: {provider_id}")
  spec = PROVIDERS[provider_id]
  api_key = str(payload.get("api_key", ""))
  if spec.requires_key and not api_key:
    raise ValueError("This provider requires an API key")
  url = str(payload.get("base_url") or spec.default_url).rstrip("/") + "/chat/completions"
  body = json.dumps({
    "model": payload.get("model") or spec.default_model,
    "messages": payload.get("messages") or [{"role": "user", "content": payload.get("prompt", "")}],
    "temperature": payload.get("temperature", 0.2),
  }).encode("utf-8")
  headers = {"Content-Type": "application/json"}
  if api_key:
    headers["Authorization"] = f"Bearer {api_key}"
  request = urllib.request.Request(url, data=body, headers=headers, method="POST")
  try:
    with urllib.request.urlopen(request, timeout=90) as response:  # noqa: S310
      result = json.loads(response.read().decode("utf-8"))
  except urllib.error.HTTPError as exc:
    detail = exc.read().decode("utf-8", errors="replace")
    raise RuntimeError(f"Provider returned HTTP {exc.code}: {detail[:400]}") from exc
  except (urllib.error.URLError, TimeoutError) as exc:
    raise RuntimeError(f"Could not reach model provider: {exc}") from exc
  if not isinstance(result, dict):
    raise RuntimeError("Provider returned an invalid response")
  choices = result.get("choices", []) if isinstance(result, dict) else []
  content = choices[0].get("message", {}).get("content", "") if choices else ""
  return {"content": content, "model": result.get("model"), "usage": result.get("usage")}
