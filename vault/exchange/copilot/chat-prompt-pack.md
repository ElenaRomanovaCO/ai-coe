---
id: exch-copilot-chat-prompt-pack
content_type: exchange
name: "Copilot Chat Prompt Pack"
tool: copilot
category: prompt-pack
summary: "Reusable Copilot Chat prompts for refactors, test backfill, and code explanation."
tags: [copilot, prompts, refactor]
install: |
  1. Save the prompts to a shared note or `.github/prompts/` (Copilot prompt files).
  2. Paste a prompt into Copilot Chat, filling the {placeholders}.
  3. Iterate; tune the wording to your codebase.
source_url: ""
---

# Copilot Chat Prompt Pack

A small pack of battle-tested Copilot Chat prompts for recurring tasks: structured
refactors, backfilling tests for an untested module, explaining unfamiliar code, and
tightening error handling.

## What it does

- Gives consistent, well-scoped prompts instead of ad-hoc phrasing.
- Uses `{placeholders}` so each prompt is quick to adapt.
- Encodes "show a plan first" patterns to keep large changes reviewable.

## When to use

When the team wants repeatable results from Copilot Chat rather than one-off prompting.
Works alongside the Copilot instructions file.
