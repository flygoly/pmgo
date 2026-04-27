#!/usr/bin/env python3
"""Check that stdio MCP server dependencies import (for CI; skips if mcp is absent)."""

import sys

try:
  import mcp  # noqa: F401
  import yaml  # noqa: F401
except ImportError as e:
  print(f"SKIP: pip install mcp pyyaml (or pip install -e \".[mcp]\" from repo root). {e}", file=sys.stderr)
  sys.exit(0)

print("MCP preflight: mcp and PyYAML import OK", file=sys.stderr)
sys.exit(0)
