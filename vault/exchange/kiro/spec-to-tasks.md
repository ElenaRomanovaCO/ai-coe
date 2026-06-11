---
id: exch-kiro-spec-to-tasks
content_type: exchange
name: "Kiro Spec-to-Tasks"
tool: kiro
category: skill
summary: "Turns a Kiro spec into an ordered, dependency-aware task list ready to execute."
tags: [kiro, planning, specs]
install: |
  1. Add the skill to your Kiro workspace.
  2. Point it at an approved spec document.
  3. Run it to produce a `tasks.md` with ordered, checkable steps.
source_url: ""
---

# Kiro Spec-to-Tasks

A Kiro skill that decomposes an approved spec into a concrete, ordered task list —
each task scoped, dependency-aware, and small enough to verify — so implementation can
start without re-planning.

## What it does

- Reads the spec and derives discrete tasks.
- Orders them by dependency and flags the critical path.
- Emits a checkable `tasks.md` you refine before executing.

## When to use

After a spec is approved and before implementation. Review the generated tasks — the
skill proposes a plan; you own the sequencing decisions.
