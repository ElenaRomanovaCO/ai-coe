---
id: vendor-eval-embedding-models
category: llm-provider
vendors_compared: ["Titan Embed v2", "OpenAI text-embedding-3", "Cohere Embed"]
criteria: ["retrieval-quality", "dimensions", "cost", "multilingual", "aws-fit"]
last_verified: "2026-05-20"
vetting:
  data_residency: "US / EU"
  sub_processors_disclosed: false
  encryption_at_rest: true
  encryption_in_transit: true
  soc2_type2: true
  iso27001: false
  hipaa_baa: false
  trains_on_customer_data: false
  data_retention_days: 90
  sso: false
---

# Embedding Model Comparison

Choosing an embedding model for RAG retrieval. Retrieval quality on *your* corpus
matters more than any leaderboard.

## Criteria

| Criterion | Titan Embed v2 | OpenAI 3-large | Cohere Embed |
|---|---|---|---|
| Retrieval quality | Strong | Strong | Strong |
| Dimensions | 1024 (configurable) | up to 3072 | 1024 |
| Cost | Low | Medium | Medium |
| Multilingual | Good | Good | Strong |
| AWS-native fit | Native (Bedrock) | External | Via Bedrock/marketplace |

## Guidance

- **Titan Embed v2** for AWS-native stacks wanting low cost and in-account inference.
- **OpenAI / Cohere** if you need their specific strengths (e.g. dimensionality,
  multilingual) and the integration cost is acceptable.

## Recommendation

Pick one, lock the dimension count, and measure retrieval precision/recall on a
labeled subset of your corpus. Changing embedding models later means re-embedding
everything — decide deliberately.
