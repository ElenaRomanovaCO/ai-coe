---
id: runtime-vault-writers
title: Tag and scope runtime-generated vault artifacts
kind: decision
owner: demo
updated_at: "2026-06-11"
---

# Decision — Tag and scope runtime-generated vault artifacts

## Decision

Module agents that write a markdown artifact **into the vault at request time**
(AGENT-02 assessment results, AGENT-05 governance reviews, AGENT-12 ideation exports,
and the upcoming Decision Log / Retrospective / Benchmark writers) MUST tag every
export with frontmatter `content_type: <type>` + `generated: true`, produced via the
shared helper `agents/lambdas/modules/vault_export.export_frontmatter`. The ReEmbed
pipeline propagates `generated: true` into the S3 Vectors metadata, and chat's
`search_knowledge_base` **excludes `generated` vectors by default** (`include_generated`
opts in). Transient state, in-progress JSON, and binary/large deliverables go to the
**sessions** bucket instead — never indexed.

## Context

Runtime exports land in vault folders that the ReEmbed Lambda indexes, so they become
retrievable by chat alongside curated knowledge. Two problems forced a convention:

1. **Mixed-provenance folders.** `assessments/`, `kits/`, and `decisions/` each hold
   *both* seeded curated demo samples (e.g. `sample-assessment-regional-bank`, which
   *should* surface) *and* real user runs (which should not). The ReEmbed pipeline
   derives `content_type` from the **folder name**, so folder/content_type alone cannot
   distinguish curated from generated — a per-file flag is required.
2. **Inconsistent, accidental behavior.** Pre-fix, `assessments/` was mapped in the
   orchestrator's `CONTENT_TYPE_FROM_DIR`, so generated assessments *did* surface in
   chat search (indistinguishable from curated content), while `ideation/` and
   `reviews/governance/` were embedded but silently dropped (their folders weren't
   mapped) — wasted vectors and fragile (one map edit away from leaking). Settling it
   once, before more Wave-5 writers copy the pattern, avoids re-litigation.

## Options considered

| Option | Verdict |
|---|---|
| Per-file `generated: true` flag, excluded in search by default | **Chosen** — the only discriminator that works when curated + generated share a folder; explicit and robust. |
| Rely on folder/`content_type` mapping (omit generated folders from `CONTENT_TYPE_FROM_DIR`) | Rejected — breaks on mixed folders (can't keep the curated assessment sample while dropping user runs); implicit and fragile. |
| Route all generated artifacts to the sessions bucket (never indexed) | Rejected for now — loses the durable, human-readable, linkable markdown and the seam for a future "search my artifacts" view; the user's intent is vault + flagged. |
| Per-user retrieval scoping (multi-tenant) | Deferred — see Consequences. |

## Consequences

- New shared helper `agents/lambdas/modules/vault_export.py`; the three existing
  writers (AGENT-02/05/12) now emit `content_type` + `generated: true`. Future
  runtime vault writers inherit it by calling the same helper.
- ReEmbed (`agents/lambdas/reembed/handler.py`) adds `generated` to vector metadata;
  `search_knowledge_base` filters it out by default (`include_generated=True` opts in).
  The `"generated"` metadata key is a shared literal across those two files and the
  helper (the ReEmbed Lambda stays free of `agents.lib` imports) — change the three
  together.
- **vault-vs-sessions rule (now intentional):** write to **vault** when the artifact is
  durable knowledge a user might resurface (tagged `generated: true`); write to
  **sessions** for transient state, in-progress JSON, and binary/large deliverables
  (e.g. kit-builder zips, which is exactly why kit-builder targets sessions). Rule of
  thumb: searchable markdown knowledge → vault + flag; state/binary/one-off download →
  sessions.
- **Known limitation (deferred): multi-tenant scoping.** Generated artifacts are
  excluded from *everyone's* chat search, not yet filtered per creator — there is no
  "search my own assessments/ideations" view. The `generated` flag + the
  `include_generated` parameter are the seam for that when it lands; cross-user
  isolation (one user must not retrieve another's generated content) is out of scope
  for the demo.
- **Backfill:** artifacts already embedded before this change carry no flag and would
  still surface until re-embedded (re-upload to trigger ReEmbed) or pruned. The seeded
  curated samples are unaffected (they carry no flag and are meant to surface).

## Links
- Task: `ai_docs/tasks/16_wave5_use_case_ideation.md`
- Related: `vault/decisions/worker-pattern.md` (the analogous "generation is the whole
  job" carve-out for WORKER-11), `agents/lambdas/modules/vault_export.py`
