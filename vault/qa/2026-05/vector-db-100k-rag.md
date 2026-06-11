---
id: qa-vector-db-100k-rag
question: What is the right vector database for a 100k-document RAG pilot?
tags: ["rag", "vector-db", "retrieval", "pilot"]
posted_by: demo
posted_at: "2026-05-18T11:05:00Z"
answers:
  - id: ans-1
    text: "At 100k documents (likely a few hundred thousand chunks) almost any vector store is fine on raw scale, so optimize for operational fit, not benchmarks. If you are AWS-native, S3 Vectors keeps everything in-account with no servers to run and is the cheapest at low query volume. Reach for a managed store like Pinecone only when you need very high QPS or advanced filtering."
    posted_by: demo
    posted_at: "2026-05-18T13:30:00Z"
---

# What is the right vector database for a 100k-document RAG pilot?

Choosing a vector store for a mid-sized RAG pilot. The corpus is ~100k documents.

## Answers

**demo** — At 100k documents (likely a few hundred thousand chunks) almost any vector store
is fine on raw scale, so optimize for operational fit, not benchmarks. If you are AWS-native,
S3 Vectors keeps everything in-account with no servers to run and is the cheapest at low
query volume. Reach for a managed store like Pinecone only when you need very high QPS or
advanced metadata filtering. Measure retrieval precision on a labeled subset before locking
the choice in — changing later means re-embedding everything.
