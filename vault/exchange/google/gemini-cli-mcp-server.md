---
id: exch-google-gemini-cli-mcp
content_type: exchange
name: "Gemini CLI — MCP Server Config"
tool: google
category: mcp-server
summary: "Wire an MCP server (e.g. AWS, GitHub, a vector store) into the Gemini CLI so the agent can call live tools."
tags: [gemini, gemini-cli, mcp, tools, google]
install: |
  1. Open (or create) `~/.gemini/settings.json`.
  2. Add an `mcpServers` block, e.g.:
     `{"mcpServers": {"aws": {"command": "uvx", "args": ["awslabs.aws-api-mcp-server@latest"]}}}`
  3. Restart `gemini`; run `/mcp` to confirm the server and its tools are listed.
  4. Scope risky tools to read-only and set `trust` per server as needed.
source_url: "https://github.com/google-gemini/gemini-cli"
---

# Gemini CLI — MCP Server Config

Gives the Gemini CLI live tool access via the **Model Context Protocol**, the same way the
Claude Code AWS MCP entry does — so the agent can query cloud resources, repos, or a vector
index instead of guessing.

## What it does

- Registers one or more MCP servers in the Gemini CLI settings.
- Exposes their tools to the agent, gated by per-server trust.

## When to use

When the Gemini CLI needs to act on real systems (AWS, GitHub, a knowledge base) during a
session. Start with read-only servers and widen scope deliberately.
