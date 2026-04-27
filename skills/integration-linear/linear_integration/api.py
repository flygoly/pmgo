"""Minimal Linear GraphQL client (stdlib only). See https://linear.app/developers/graphql"""

from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.request
from typing import Any, Optional

from .config import LinearConfig

ENDPOINT = "https://api.linear.app/graphql"


def _request(cfg: LinearConfig, query: str, variables: Optional[dict[str, Any]] = None) -> dict[str, Any]:
  payload = {"query": query, "variables": variables or {}}
  data = json.dumps(payload).encode("utf-8")
  req = urllib.request.Request(
    ENDPOINT,
    data=data,
    headers={
      "Content-Type": "application/json",
      "Authorization": cfg.api_key,
      "User-Agent": cfg.user_agent,
    },
    method="POST",
  )
  ctx = ssl.create_default_context()
  try:
    with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:  # noqa: S310
      raw = resp.read().decode("utf-8")
  except urllib.error.HTTPError as e:
    err = e.read().decode("utf-8", errors="replace")
    raise RuntimeError(f"Linear HTTP {e.code}: {err or e.reason}") from e
  out: dict[str, Any] = json.loads(raw) if raw else {}
  if out.get("errors"):
    parts = [str((e or {}).get("message", e)) for e in out["errors"]]
    raise RuntimeError("Linear GraphQL: " + "; ".join(parts))
  d = out.get("data")
  if d is None:
    raise RuntimeError("Linear GraphQL: empty data and no errors (unexpected).")
  return d if isinstance(d, dict) else {}


def viewer_smoke(cfg: LinearConfig) -> dict[str, Any]:
  q = """
  query ViewerSmoke {
    viewer {
      id
      name
    }
  }
  """
  return _request(cfg, q)


def list_issues(cfg: LinearConfig, *, first: int = 20) -> list[dict[str, Any]]:
  q = """
  query IssueList($first: Int!) {
    issues(first: $first) {
      nodes {
        id
        identifier
        title
        url
        state { name type }
      }
    }
  }
  """
  data = _request(cfg, q, {"first": int(first)})
  issues = (data.get("issues") or {}).get("nodes")
  if not isinstance(issues, list):
    raise RuntimeError("Unexpected issues list")
  return [x for x in issues if isinstance(x, dict)]


def _parse_team_number(identifier: str) -> tuple[str, float]:
  if identifier.count("-") < 1:
    raise ValueError("expected Linear identifier like TEAM-42 (team key + number)")
  team_key, num_s = identifier.rsplit("-", 1)
  team_key = team_key.strip()
  if not team_key or not num_s.strip():
    raise ValueError("invalid Linear identifier")
  return team_key, float(int(num_s.strip()))


def get_issue(cfg: LinearConfig, identifier: str) -> dict[str, Any]:
  """Fetch one issue by UUID, human id (e.g. ENG-42), or team+number filter."""
  ident = identifier.strip()
  if not ident:
    raise ValueError("identifier is empty")
  q_one = """
  query OneIssue($id: String!) {
    issue(id: $id) {
      id
      identifier
      number
      title
      description
      url
      state { name type }
    }
  }
  """
  data = _request(cfg, q_one, {"id": ident})
  iss = data.get("issue")
  if isinstance(iss, dict):
    return iss

  try:
    team_key, num = _parse_team_number(ident)
  except ValueError:
    raise RuntimeError(f"Issue not found: {ident}") from None

  q_filter = """
  query IssueByTeamNumber($teamKey: String!, $num: Float!) {
    issues(
      filter: {
        team: { key: { eq: $teamKey } }
        number: { eq: $num }
      }
      first: 1
    ) {
      nodes {
        id
        identifier
        number
        title
        description
        url
        state { name type }
      }
    }
  }
  """
  data2 = _request(cfg, q_filter, {"teamKey": team_key, "num": num})
  nodes = (data2.get("issues") or {}).get("nodes")
  if isinstance(nodes, list) and nodes and isinstance(nodes[0], dict):
    return nodes[0]
  raise RuntimeError(f"Issue not found: {ident}")
