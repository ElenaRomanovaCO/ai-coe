---
id: ref-arch-clinical-notes-rag
title: Reference Architecture — Clinical Notes RAG Assistant
type: reference-architecture
industry: healthcare
ai_stage: 2
use_case_type: ["rag", "clinical-documentation", "summarization"]
tags: ["rag", "phi", "bedrock", "vector-search", "healthcare"]
contributor: demo
updated_at: "2026-05-12"
---

# Clinical Notes RAG Assistant

A retrieval-augmented assistant that helps clinicians draft and query unstructured
clinical notes without exposing protected health information (PHI) to the model in
the clear. Suited to organizations at maturity stage 2 (piloting) that have a
document corpus but no production AI.

## Problem

Clinicians spend significant time searching prior encounters and re-summarizing
history. Generic chatbots cannot be pointed at PHI safely, and naive RAG leaks
identifiers into prompts and logs.

## Architecture

1. **Ingestion** — Notes land in an object store. A de-identification step
   redacts direct identifiers (names, MRNs, dates) before embedding.
2. **Chunking & embedding** — Heading-aware chunks (~1000 tokens, 100 overlap)
   are embedded with a managed embedding model and written to a vector index with
   metadata (encounter type, specialty, redaction status).
3. **Retrieval** — Queries embed and retrieve top-k chunks scoped by the
   clinician's access. A guardrail policy blocks any residual PHI and prompt
   injection.
4. **Generation** — A mid-tier model composes a cited answer; every claim links
   to the source chunk.

## Controls

- De-identification before embedding; re-identification only in the trusted UI.
- Per-role retrieval scoping; audit log of every retrieval.
- Human-in-the-loop: the assistant drafts, the clinician signs.

## When to use

Stage 1-3 clients in healthcare with a document-heavy workflow and a hard PHI
boundary. Not for autonomous clinical decisions.
