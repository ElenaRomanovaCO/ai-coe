---
id: exch-google-gemini-security-review
content_type: exchange
name: "Gemini CLI Security Review Command"
tool: google
category: skill
summary: "A custom Gemini CLI command that reviews the pending diff for security issues and proposes fixes."
tags: [gemini, gemini-cli, security, review, google]
install: |
  1. Create `.gemini/commands/security-review.toml` in your repo.
  2. Set its `prompt` to: collect `git diff`, read the touched files, and flag injection,
     missing authz, hard-coded secrets, and unsafe deserialization — returning findings
     ranked by severity with file/line and a suggested patch.
  3. In a `gemini` session run `/security-review` on a branch with pending changes.
source_url: "https://github.com/google-gemini/gemini-cli"
---

# Gemini CLI Security Review Command

The Gemini-CLI counterpart to the Claude Code security-review skill: a custom slash command
that runs a focused security pass over the current diff and proposes concrete fixes.

## What it does

- Collects the pending diff and reads the touched files for context.
- Checks against a checklist of common web/cloud weaknesses.
- Returns findings ranked by severity, each with a file/line and a suggested patch.

## When to use

Before opening a PR, or as a pre-merge gate on changes touching auth, input handling, or
infrastructure — for teams standardized on the Gemini CLI.
