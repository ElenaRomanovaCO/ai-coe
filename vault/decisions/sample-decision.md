---
id: sample-decision-vector-store
title: Sample Decision — Default Vector Store for Internal Tools
kind: decision
owner: demo
updated_at: "2026-05-06"
---

# Sample Decision — Default Vector Store for Internal Tools

A demo decision-log entry for continuity. Generic context; no real client data.

## Decision

Use **Amazon S3 Vectors** as the default vector store for internal and demo-grade RAG
tools, rather than a managed third-party vector database.

## Context

We needed a default retrieval store for internal applications with large corpora but
modest query volume, where cost predictability and keeping data in-account matter more
than ultra-low latency.

## Options considered

| Option | Why not (for this default) |
|---|---|
| Pinecone | Strong at scale, but managed-vendor cost and data-boundary overhead aren't justified for internal/modest-QPS tools |
| pgvector | Great if we already ran Postgres; we don't want to operate a DB for this |
| **S3 Vectors** | **Chosen** — low fixed cost, in-account, adequate latency for internal use |

## Consequences

- No CloudFormation support → provision the index out-of-band via a script.
- Re-evaluate for any latency-critical, high-QPS, user-facing workload.

See `vendors/vector-db-comparison.md` for the full comparison.
