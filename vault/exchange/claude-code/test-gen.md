---
id: exch-claude-code-test-gen
content_type: exchange
name: "/test-gen — Test Generator"
tool: claude-code
category: slash-command
summary: "Slash command that scaffolds unit tests for the file or function under discussion."
tags: [testing, tdd, coverage]
install: |
  1. Save the command to `.claude/commands/test-gen.md`.
  2. Adjust the prompt body to point at your test framework (pytest, vitest, etc.).
  3. Invoke `/test-gen <path-or-symbol>` in a session.
source_url: ""
---

# /test-gen — Test Generator

A slash command that generates a focused test file for a given module or function,
matching the project's existing test conventions (framework, naming, fixtures).

## What it does

- Reads the target file and a sibling test for style.
- Produces happy-path, edge-case, and error-path tests.
- Leaves clear TODOs where it needs a fixture or a value it cannot infer.

## When to use

When adding tests to legacy code, or to bootstrap a test file before hand-refining.
Keep the generated tests under review — they encode assumptions you should verify.
