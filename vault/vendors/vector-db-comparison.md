---
id: vendor-eval-vector-db
category: vector-db
vendors_compared: ["Pinecone", "pgvector", "Amazon S3 Vectors"]
criteria: ["latency", "scale", "operational-burden", "cost", "data-residency"]
last_verified: "2026-05-19"
---

# Vector Database Comparison

Choosing a vector store for retrieval. The right answer depends heavily on scale,
latency SLO, and whether you already operate Postgres or AWS.

## Criteria

| Criterion | Pinecone | pgvector | S3 Vectors |
|---|---|---|---|
| Latency at scale | High | Medium | Medium |
| Operational burden | Lowest (managed) | Medium (run Postgres) | Low (managed) |
| Cost profile | Usage/pod-based | Cheapest if Postgres exists | Low fixed, usage-based |
| Data residency | Vendor boundary | Your DB | Your AWS account |
| Best at scale | Very large | Small-medium | Large corpus, modest QPS |

## Guidance

- **pgvector** if you already run Postgres and the corpus is small-to-medium.
- **S3 Vectors** for cost-sensitive, AWS-centric internal apps with modest QPS.
- **Pinecone** when latency-critical production serving at large scale justifies the
  managed spend.

## Recommendation

Start with the cheapest option that meets your latency SLO; migrate only when a
measured bottleneck appears. Re-verify as services and pricing evolve.
