---
id: exch-kiro-steering-config
content_type: exchange
name: "Kiro Steering Config"
tool: kiro
category: config
summary: "Kiro steering files that encode project conventions and guardrails for spec-driven work."
tags: [kiro, config, conventions]
install: |
  1. Copy the steering files into your project's `.kiro/steering/` directory.
  2. Edit them to state your conventions, stack, and hard rules.
  3. Kiro applies the steering context across spec and task sessions.
source_url: ""
---

# Kiro Steering Config

A set of Kiro steering files that give the tool persistent project context: stack and
conventions, directory layout, and the guardrails to honor — so Kiro's spec-driven
output stays aligned with how your team builds.

## What it does

- Persists conventions Kiro applies across spec and task generation.
- Centralizes guardrails (no secrets, scoped permissions, test-first).
- Reduces repeated context-setting in each session.

## When to use

On any project using Kiro's spec/steering workflow. Keep steering concise and current —
stale steering misleads more than it helps.
