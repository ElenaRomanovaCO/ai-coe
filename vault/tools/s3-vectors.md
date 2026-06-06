---
id: tool-s3-vectors
name: Amazon S3 Vectors
category: vector-db
stack: ["aws", "managed-service", "boto3"]
ai_stage_fit: [1, 2, 3]
cost_model: usage-based
limitations:
  - "Newer service; SDK surface and limits still maturing"
  - "Not designed for ultra-low-latency, high-QPS serving paths"
  - "No CloudFormation support yet — provision out-of-band"
tags: ["vector-db", "aws", "cost-effective", "serverless"]
---

# Amazon S3 Vectors

Native vector storage and similarity search on top of S3-class economics. Attractive
when data already lives in AWS and cost predictability matters more than raw QPS.

## Best-fit scenarios

- Cost-sensitive RAG (stage 1-3) where corpora are large but query volume is modest.
- AWS-centric stacks that want to keep data within the account boundary.
- Demos and internal tools where simplicity and low fixed cost win.

## Stage relevance

Great default for stage 1-3 internal applications. For high-QPS, latency-critical
production serving, evaluate a purpose-built store alongside it.

## Limitations to plan around

Provision the bucket and index out-of-band (no CloudFormation) and pin the SDK
calls, since the service is still evolving. Benchmark latency against your SLO before
putting it on a user-facing hot path.
