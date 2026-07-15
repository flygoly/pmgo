"""Minimal Linear GraphQL client (stdlib only). See https://linear.app/developers/graphql"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Optional

from .config import LinearConfig

_SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
if str(_SCRIPTS) not in sys.path:
  sys.path.insert(0, str(_SCRIPTS))

from pmgo_http import request_json  # noqa: E402

ENDPOINT = "https://api.linear.app/graphql"


def _request(cfg: LinearConfig, query: str, variables: Optional[dict[str, Any]] = None) -> dict[str, Any]:
  out, _ = request_json(
    "POST",
    ENDPOINT,
    headers={
      "Content-Type": "application/json",
      "Authorization": cfg.api_key,
      "User-Agent": cfg.user_agent,
    },
    body={"query": query, "variables": variables or {}},
    error_prefix="Linear HTTP",
  )
  if not isinstance(out, dict):
    raise RuntimeError("Linear GraphQL: unexpected response type")
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


def list_issues(
  cfg: LinearConfig,
  *,
  first: int = 20,
  max_pages: int = 5,
) -> list[dict[str, Any]]:
  """List issues with cursor pagination."""
  q = """
  query IssueList($first: Int!, $after: String) {
    issues(first: $first, after: $after) {
      pageInfo { hasNextPage endCursor }
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
  want = max(1, int(first))
  page_size = min(50, want)
  collected: list[dict[str, Any]] = []
  after: str | None = None
  pages = max(1, int(max_pages))
  for _ in range(pages):
    take = min(page_size, want - len(collected))
    if take <= 0:
      break
    data = _request(cfg, q, {"first": take, "after": after})
    block = data.get("issues") or {}
    nodes = block.get("nodes")
    if not isinstance(nodes, list):
      raise RuntimeError("Unexpected issues list")
    batch = [x for x in nodes if isinstance(x, dict)]
    collected.extend(batch)
    page_info = block.get("pageInfo") or {}
    if not page_info.get("hasNextPage") or len(collected) >= want:
      break
    after = page_info.get("endCursor")
    if not after:
      break
  return collected[:want]


def _parse_team_number(identifier: str) -> tuple[str, float]:
  if identifier.count("-") < 1:
    raise ValueError("expected Linear identifier like TEAM-42 (team key + number)")
  team_key, num_s = identifier.rsplit("-", 1)
  team_key = team_key.strip()
  if not team_key or not num_s.strip():
    raise ValueError("invalid Linear identifier")
  return team_key, float(int(num_s.strip()))


def create_comment(
  cfg: LinearConfig,
  *,
  issue_id: str,
  body: str,
) -> dict[str, Any]:
  """Post a comment on a Linear issue (UUID). Limited write-back for PM notes."""
  issue_uuid = issue_id.strip()
  text = body.strip()
  if not issue_uuid or not text:
    raise ValueError("issue_id and body are required")
  q = """
  mutation CommentCreate($issueId: String!, $body: String!) {
    commentCreate(input: { issueId: $issueId, body: $body }) {
      success
      comment {
        id
        body
        url
      }
    }
  }
  """
  data = _request(cfg, q, {"issueId": issue_uuid, "body": text})
  block = data.get("commentCreate") or {}
  if not block.get("success"):
    raise RuntimeError(f"Linear commentCreate failed: {block}")
  comment = block.get("comment")
  if not isinstance(comment, dict):
    raise RuntimeError("Linear commentCreate missing comment")
  return comment


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
