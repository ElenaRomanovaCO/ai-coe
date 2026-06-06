---
id: feed-agentic-rag-research
title: Research — agentic retrieval beats single-shot RAG on multi-hop questions
category: research
source_url: "https://example.com/feed/agentic-rag"
published_at: "2026-04-19"
industries: ["cross-industry"]
tags: ["rag", "agents", "research", "retrieval"]
radar_status: assess
---

# Agentic retrieval outperforms single-shot RAG on multi-hop questions

A study finds that letting a model plan and issue multiple retrieval steps improves
answer quality on multi-hop questions, at the cost of more tokens and latency.

## What this means

For complex Q&A where answers span several documents, an iterative retrieve-reason
loop can lift quality — but it raises cost and latency, so reserve it for hard
queries and keep single-shot RAG for simple ones. Radar: **assess** — prototype on a
known multi-hop workload and measure the quality-vs-cost tradeoff before adopting.
