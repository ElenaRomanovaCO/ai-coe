---
id: feed-long-context-research
title: Research — long context does not eliminate the need for retrieval
category: research
source_url: "https://example.com/feed/long-context"
published_at: "2026-05-26"
industries: ["cross-industry"]
tags: ["long-context", "rag", "retrieval", "research"]
radar_status: hold
---

# Long context does not eliminate retrieval

New analysis finds that stuffing very long contexts degrades precision and cost
relative to targeted retrieval, even as context windows grow.

## What this means

A recurring client question is "can't we just put everything in the prompt now?"
The evidence says no: retrieval still wins on precision, cost, and latency for large
corpora. Keep RAG as the default and use long context selectively for genuinely small,
self-contained inputs. Radar: **hold** on "long-context replaces RAG" — it doesn't yet.
