---
id: tool-llamaindex
name: LlamaIndex
category: framework
stack: ["python", "typescript"]
ai_stage_fit: [1, 2, 3]
cost_model: open-source
limitations:
  - "Indexing abstractions can obscure what is actually retrieved"
  - "Defaults favor convenience over retrieval precision tuning"
  - "Overlaps with general frameworks; avoid stacking too many"
tags: ["framework", "rag", "indexing", "retrieval"]
---

# LlamaIndex

A data-framework focused on connecting LLMs to private data: ingestion, indexing,
and retrieval primitives. Particularly strong on the retrieval half of RAG.

## Best-fit scenarios

- Document-heavy RAG where chunking, indexing, and query strategies need to be
  experimented with quickly.
- Teams that want structured retrieval (summaries, hierarchical indices) out of the box.
- Stage 1-2 pilots validating whether retrieval quality is good enough.

## Stage relevance

Most valuable at stage 1-2 for rapid retrieval experiments. At stage 3, keep the
retrieval ideas but make the actual retrieval path explicit and measured.

## Limitations to plan around

Log the exact chunks retrieved per query so you can evaluate precision/recall, rather
than trusting index defaults. Don't combine with a second heavyweight framework
unless there's a clear reason.
