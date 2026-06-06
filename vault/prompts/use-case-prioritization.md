---
id: prompt-use-case-prioritization
title: Use Case Prioritization Workshop
use_case: "Score and rank candidate AI use cases by value and feasibility"
model_targets: ["sonnet-4-6"]
variables: ["use_case_list", "client_constraints", "time_horizon"]
version: 1
parent_id: null
---

# Use Case Prioritization Workshop

## Prompt

Given this list of candidate AI use cases: **{{use_case_list}}**, and these client
constraints: **{{client_constraints}}**, over a **{{time_horizon}}** horizon, help the
team prioritize.

For each use case, estimate (low / expected / high) on:

- **Value** — labor saved, quality/error reduction, revenue or risk impact.
- **Feasibility** — data readiness, technical effort, change/governance overhead.

Then:

1. Plot each on a value-vs-effort grid (describe the quadrant).
2. Recommend a top 3 to pursue and 1-2 to explicitly defer, with one-line rationale.
3. Flag the single assumption each top pick is most sensitive to.

## Guidance

Keep estimates ranged, not falsely precise. Where data is missing, state the
assumption rather than guessing silently. Output a ranked table.
