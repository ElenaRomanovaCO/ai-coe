---
name: log-decision
description: >-
  Record a cross-cutting or architectural decision into BOTH the relevant task's
  "Notes & Decisions Log" and a schema-valid vault/decisions/ entry, so future
  tasks (and future sessions) don't re-litigate it. Use whenever a design choice
  is made that will outlive the current task — e.g. picking or deferring a runtime
  or library (Strands vs Bedrock Converse), an architecture pattern, a naming
  convention, a storage choice, or any deviation from the written spec. Invoke with
  /log-decision (optionally followed by the decision in plain words).
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
---

# Log a cross-cutting decision

Capture an architectural/cross-cutting decision in two places so it is both
discoverable by humans (task log) and retrievable by the agents (vault + S3 Vectors).

## 0. Locate the repo root

The repo root is the directory that contains both `vault/` and `ai_docs/tasks/`.
Run all file paths below relative to it. If the current working directory is not the
root, find it (e.g. `Glob` for `vault/modules.json`) and use that parent.

## 1. Gather the decision

From the conversation (and the user's `/log-decision` arguments, if any), assemble:

- **title** — short imperative phrase, e.g. "Standardize agent runtime on Bedrock Converse".
- **decision** — 1-2 sentences stating what was decided.
- **context** — why this came up; the constraint or fork that forced a choice.
- **options** — the alternatives considered, each with a one-line "why not" (or "chosen").
- **consequences** — what this implies downstream, including any spec deviation and the
  follow-ups it creates for later tasks.
- **related task** — the task file this decision arose under (e.g. `02_wave1_chat_orchestrator.md`).
  Infer from context; if several apply, pick the one being worked on.

Only use `AskUserQuestion` if one of **title**, **decision**, or **related task** is
genuinely unclear from context. Otherwise proceed — do not interrogate the user for
details you can infer.

Derive a **slug** from the title: lowercase, hyphenated, no punctuation
(e.g. `standardize-agent-runtime-bedrock-converse`). Use today's date (ISO `YYYY-MM-DD`)
from context for `updated_at`.

## 2. Write the vault decision entry

Create `vault/decisions/<slug>.md`. The frontmatter MUST validate against the decision
schema (`agents/lib/schemas` → `SampleDocFrontmatter`): `id`, `title`, `kind: decision`,
`owner`, `updated_at`. Use this shape:

```markdown
---
id: <slug>
title: <Title>
kind: decision
owner: demo
updated_at: "<YYYY-MM-DD>"
---

# Decision — <Title>

## Decision
<the decision, 1-2 sentences>

## Context
<why this came up; the binding constraint>

## Options considered
| Option | Verdict |
|---|---|
| <option A> | <chosen / why not> |
| <option B> | <why not> |

## Consequences
- <downstream implication>
- <spec deviation, if any, stated plainly>
- <follow-up this creates for a later task>

## Links
- Task: `ai_docs/tasks/<related task file>`
- Related: <other vault paths or decisions, if any>
```

Keep it generic — no company names, no real client data, no secrets (matches the vault
content rules).

## 3. Append to the task's Notes & Decisions Log

Open `ai_docs/tasks/<related task file>`. Under the `## C. Notes & Decisions Log`
section, append one bullet (keep existing entries):

```
- <YYYY-MM-DD>: <Title> — <decision in half a sentence>. See `vault/decisions/<slug>.md`.
```

## 4. Validate

Run the vault validator and confirm it passes:

```
uv run python scripts/validate_vault.py
```

If it fails on the new file, fix the frontmatter and re-run until it exits 0.

## 5. Offer to publish (do not auto-run)

The local files are enough to record the decision. Syncing to S3 makes it retrievable
by the deployed agents (the ReEmbed Lambda indexes it within ~60s). Syncing is an
outward action against AWS, so **ask before doing it** rather than running automatically.
If the user says yes, sync just the decision:

```
aws s3 cp vault/decisions/<slug>.md s3://<vault_bucket>/decisions/<slug>.md
```

The vault bucket name is in MEMORY.md / the foundation build notes (currently
`aicoe-storage-vaultbucket95cbf29a-grqklrktjilv`); confirm it before syncing.

## 6. Report

Summarize in 2-3 lines: the decision, the two files written/updated, validator result,
and whether it was published to S3.
