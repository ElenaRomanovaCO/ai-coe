---
id: exch-google-gemini-cli-setup
content_type: exchange
name: "Gemini CLI Setup & GEMINI.md"
tool: google
category: config
summary: "Install Google's Gemini CLI and give it project context with a GEMINI.md file at the repo root."
tags: [gemini, gemini-cli, setup, context, google]
install: |
  1. Install the CLI: `npm install -g @google/gemini-cli` (Node 18+).
  2. Run `gemini` in your repo and sign in with your Google account (or set `GEMINI_API_KEY`).
  3. Add a `GEMINI.md` at the repo root describing the stack, conventions, and "do/don't" rules — the CLI loads it as standing context each session (the analogue of `CLAUDE.md`).
  4. Optional: scope extra context with nested `GEMINI.md` files in subfolders.
source_url: "https://github.com/google-gemini/gemini-cli"
---

# Gemini CLI Setup & GEMINI.md

Baseline configuration for Google's **Gemini CLI** — an open-source terminal agent — so it
works against this team's repos with the right standing context.

## What it does

- Installs the CLI and authenticates against Gemini.
- Establishes a `GEMINI.md` context file so every session inherits the project's stack,
  conventions, and guardrails without re-explaining them.

## When to use

When onboarding a repo to the Gemini CLI, or to standardize the context file across the
team so agent behavior is consistent. Pairs with the Gemini MCP server config to give the
agent live tool access.
