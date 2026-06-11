---
id: exch-claude-code-security-review
content_type: exchange
name: "Security Review Skill"
tool: claude-code
category: skill
summary: "Reviews pending changes for security issues (injection, secrets, authz gaps) and proposes fixes."
tags: [security, review, sast, secrets]
install: |
  1. Copy the skill folder to `.claude/skills/security-review/` in your repo.
  2. Ensure `SKILL.md` declares the read-only tools it needs (Grep, Read, Bash for `git diff`).
  3. Run `/security-review` on a branch with pending changes.
source_url: ""
---

# Security Review Skill

A Claude Code skill that runs a focused security pass over the current diff: it flags
injection-prone string building, missing authorization checks, hard-coded secrets, and
unsafe deserialization, then proposes concrete fixes grounded in the changed lines.

## What it does

- Collects the pending diff and reads the touched files for context.
- Checks against a checklist of common web/cloud weaknesses.
- Returns findings ranked by severity, each with a file/line and a suggested patch.

## When to use

Before opening a PR, or as a pre-merge gate on changes that touch auth, input handling,
or infrastructure. Pairs well with a deterministic linter — this catches the
context-dependent issues a linter can't.
