---
id: exch-google-vertex-adk-starter
content_type: exchange
name: "Vertex AI Agent (ADK) Starter"
tool: google
category: plugin
summary: "Scaffold a tool-using agent with Google's Agent Development Kit and run it locally or on Vertex AI Agent Engine."
tags: [google, vertex-ai, adk, agent, gemini]
install: |
  1. `pip install google-adk` (Python 3.10+).
  2. Define an agent in `agent.py` with a Gemini model + your tools (functions or MCP).
  3. Run locally with `adk run` (or `adk web` for the dev UI) to iterate.
  4. Deploy to **Vertex AI Agent Engine** for a managed, scalable runtime when ready.
source_url: "https://google.github.io/adk-docs/"
---

# Vertex AI Agent (ADK) Starter

A starting point for building a production agent on Google's stack with the **Agent
Development Kit (ADK)** — define tools and a Gemini model, iterate locally, then deploy to
Vertex AI Agent Engine.

## What it does

- Scaffolds a tool-using agent (functions and/or MCP tools) around a Gemini model.
- Supports a local dev loop (`adk run` / `adk web`) before a managed Vertex deployment.

## When to use

When an engagement needs a hosted, scalable agent on Google Cloud rather than a local CLI
agent — the Vertex/ADK equivalent of standing up a runtime, parallel to the Bedrock path in
the Tools Repository.
