---
id: exch-copilot-instructions-python-aws
content_type: exchange
name: "Copilot Instructions — Python/AWS"
tool: copilot
category: config
summary: "A .github/copilot-instructions.md tuned for Python services on AWS (typing, boto3, testing)."
tags: [copilot, python, aws, conventions]
install: |
  1. Copy the file to `.github/copilot-instructions.md` in your repo.
  2. Adjust the stack notes (region, runtime, test framework) to match your project.
  3. Commit; GitHub Copilot picks it up for chat and completions in that repo.
source_url: ""
---

# Copilot Instructions — Python/AWS

A `copilot-instructions.md` that steers GitHub Copilot toward this org's defaults for
Python services on AWS: full type hints, `boto3` client patterns, structured logging,
and pytest conventions — so suggestions land closer to house style.

## What it does

- Sets language/runtime expectations Copilot applies to completions and chat.
- Encodes preferred libraries and the testing approach.
- Calls out anti-patterns to avoid (bare excepts, unscoped IAM, secrets in code).

## When to use

On any Python/AWS repo where the team uses Copilot. Keep it short and specific —
overlong instruction files dilute the signal.
