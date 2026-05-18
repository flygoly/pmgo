"""Environment: JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class JiraConfig:
  base_url: str
  email: str
  api_token: str
  default_project: str | None = None
  user_agent: str = "pmgo-integration-jira/0.1"


def load_config(*, require_credentials: bool = True) -> JiraConfig:
  base = (os.environ.get("JIRA_BASE_URL") or "").strip().rstrip("/")
  email = (os.environ.get("JIRA_EMAIL") or "").strip()
  token = (os.environ.get("JIRA_API_TOKEN") or "").strip()
  project = (os.environ.get("JIRA_PROJECT") or "").strip() or None
  if require_credentials:
    if not base:
      raise OSError("JIRA_BASE_URL is not set (e.g. https://your-domain.atlassian.net).")
    if not email:
      raise OSError("JIRA_EMAIL is not set.")
    if not token:
      raise OSError("JIRA_API_TOKEN is not set.")
  return JiraConfig(base_url=base, email=email, api_token=token, default_project=project)
