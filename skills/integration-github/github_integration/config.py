"""Environment: GITHUB_TOKEN, GITHUB_REPO=owner/name."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GitHubConfig:
  token: str
  owner: str
  repo: str
  user_agent: str = "pmgo-integration-github/0.1"


def _split_repo(raw: str) -> tuple[str, str]:
  raw = raw.strip()
  if raw.count("/") != 1:
    raise ValueError("GITHUB_REPO must be 'owner/name' (exactly one slash).")
  owner, name = raw.split("/", 1)
  owner, name = owner.strip(), name.strip()
  if not owner or not name:
    raise ValueError("GITHUB_REPO owner and name must be non-empty.")
  return owner, name


def load_config(*, require_token: bool = True) -> GitHubConfig:
  token = (os.environ.get("GITHUB_TOKEN") or "").strip()
  if require_token and not token:
    raise OSError("GITHUB_TOKEN is not set or empty.")
  raw_repo = (os.environ.get("GITHUB_REPO") or "").strip()
  if not raw_repo:
    raise OSError("GITHUB_REPO is not set (expected 'owner/name').")
  owner, name = _split_repo(raw_repo)
  return GitHubConfig(token=token, owner=owner, repo=name)
