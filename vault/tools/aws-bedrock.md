---
id: tool-aws-bedrock
name: AWS Bedrock
category: llm-provider
stack: ["aws", "managed-service", "boto3"]
ai_stage_fit: [1, 2, 3, 4]
cost_model: usage-based
limitations:
  - "Model availability and IDs vary by region"
  - "On-demand vs provisioned throughput tradeoffs need planning"
  - "Guardrails and features differ across model families"
tags: ["llm-provider", "aws", "managed", "guardrails", "embeddings"]
---

# AWS Bedrock

A managed gateway to multiple foundation models (text, embeddings) with IAM-native
access, guardrails, and no servers to run. Keeps inference inside the AWS boundary.

## Best-fit scenarios

- AWS-centric organizations that want multiple model families behind one API.
- Workloads needing built-in guardrails (PII, prompt-attack) and IAM scoping.
- Any stage where avoiding key management and self-hosting is a priority.

## Stage relevance

Useful across stages 1-4: cheap models for high-volume classification, mid-tier for
reasoning, and embeddings for retrieval. Pair model choice with the workload.

## Limitations to plan around

Confirm model IDs and on-demand availability per region before committing. Decide
on-demand vs provisioned throughput based on traffic, and apply a guardrail policy to
user-facing flows from day one.
