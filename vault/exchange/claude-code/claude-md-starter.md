---
id: exch-claude-code-claude-md-starter
content_type: exchange
name: "CLAUDE.md Project Starter"
tool: claude-code
category: config
summary: "A starter CLAUDE.md template capturing build/test commands, conventions, and guardrails."
tags: [config, conventions, onboarding]
install: |
  1. Copy the template to `CLAUDE.md` at your repo root.
  2. Fill in the build/test/lint commands and the project's hard rules.
  3. Commit it; Claude Code reads it at the start of every session.
source_url: ""
---

# CLAUDE.md Project Starter

A ready-to-edit `CLAUDE.md` that gives an agent the context it needs up front: how to
build, test, and lint; the directory map; naming and style conventions; and the
non-negotiable guardrails for the codebase.

## What it does

- Documents the commands an agent should use instead of guessing.
- States conventions once so they don't have to be re-derived each session.
- Lists hard rules (no secrets in code, no force-push, etc.).

## When to use

On any repo an agent will work in. A good `CLAUDE.md` is the single highest-leverage
setup step for consistent agent behavior.
