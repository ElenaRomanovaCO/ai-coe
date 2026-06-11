---
id: exch-claude-code-aws-mcp
content_type: exchange
name: "AWS Read-Only MCP Server"
tool: claude-code
category: mcp-server
summary: "MCP server exposing read-only AWS tools (list/describe) so an agent can inspect cloud state safely."
tags: [aws, mcp, cloud, read-only]
install: |
  1. Add the server to `.mcp.json` (or your client's MCP config) with the command and args.
  2. Provide AWS credentials via the standard environment (no keys in config).
  3. Restart the client; the `list_*` / `describe_*` tools appear under the server.
source_url: ""
---

# AWS Read-Only MCP Server

An MCP server that surfaces a curated set of **read-only** AWS operations (list buckets,
describe instances, get stack outputs, tail logs) so an agent can reason about live cloud
state without any mutating access.

## What it does

- Wraps the AWS SDK behind a small, allow-listed tool surface.
- Returns structured JSON the agent can cite.
- Refuses any create/update/delete call by construction.

## When to use

During incident triage, infra Q&A, or when an agent needs grounding in real account
state. Keep it read-only; pair with human-run changes for anything mutating.
