# Page Brief — Vendor & Model Evaluation Center

> Inherits `../design-system.md`. Route: `/modules/vendor-eval`. Module 13 (AGENT-13),
> Wave 4. Covers FR-034..035.

## Purpose

Compare LLM providers, vector DBs, and platforms side-by-side against weighted criteria,
and recommend a fit for a workload/budget. The "decision matrix" surface.

## Content & data (real vendor-eval fields)

Eval entries: `category` (llm-provider / vector-db / cloud-ai-platform /
orchestration-framework), `vendors_compared[]`, `criteria[]`, `last_verified`. Body has
a comparison matrix + recommendation. (Seed: Claude/GPT/Gemini; Pinecone/pgvector/S3
Vectors; etc.)

## Primary actions

- Pick a category / eval → see the **side-by-side matrix** (vendors × criteria, with
  weights and a recommendation).
- Adjust criteria weights (light) → re-rank.
- Open an existing published eval; export the comparison.

## States

List of evals · matrix view · empty · loading.

## Layout

A comparison **table/matrix**: rows = criteria (weighted), columns = vendors, cells =
ratings; a recommendation callout below; a "last verified" date prominent (these go stale).

## Design prompt seed

> Design a "Vendor & Model Evaluation Center" comparison page for an enterprise
> AI-consulting platform. The centerpiece is a side-by-side comparison matrix: columns are
> the vendors being compared (e.g. Claude Sonnet, GPT-4o, Gemini), rows are weighted
> criteria (accuracy, long-context, cost, latency, safety) with the weight shown, and
> cells show ratings (e.g. High/Med/Low or scores) with subtle color. Below the matrix: a
> recommendation callout and a prominent "last verified" date (with a note that rankings
> shift). Include a category switcher (LLM providers / vector DBs / cloud AI platforms)
> and a way to nudge criteria weights to re-rank, plus an "export comparison" button.
> Crisp, analytical, decision-support feel; indigo accent; Inter; monospace for scores;
> rounded-lg; light + dark. No company names.
