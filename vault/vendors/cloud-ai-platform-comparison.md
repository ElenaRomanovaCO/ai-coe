---
id: vendor-eval-cloud-ai-platform
category: cloud-ai-platform
vendors_compared: ["AWS Bedrock", "Azure AI Foundry", "Google Vertex AI"]
criteria: ["model-choice", "governance", "ecosystem-fit", "cost", "guardrails"]
last_verified: "2026-05-23"
---

# Cloud AI Platform Comparison

Choosing a managed platform to host foundation-model workloads. The dominant factor
is usually which cloud the organization already runs on.

## Criteria

| Criterion | AWS Bedrock | Azure AI Foundry | Google Vertex AI |
|---|---|---|---|
| Breadth of model choice | High | High | High |
| Native governance / IAM | Strong | Strong | Strong |
| Ecosystem fit | AWS | Microsoft | Google |
| Built-in guardrails | Yes | Yes | Yes |
| Cost model | Usage-based | Usage-based | Usage-based |

## Guidance

Lead with the platform that matches the client's existing cloud and data gravity —
the integration and governance savings usually outweigh small per-token differences.
Validate the specific models you need are available in the required region.

## Recommendation

Default to the incumbent cloud's AI platform unless a specific model or capability is
only available elsewhere. Re-verify model availability and pricing each quarter.
