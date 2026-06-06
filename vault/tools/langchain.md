---
id: tool-langchain
name: LangChain
category: framework
stack: ["python", "javascript"]
ai_stage_fit: [1, 2, 3]
cost_model: open-source
limitations:
  - "Abstraction churn between versions can break pipelines"
  - "Can hide latency and token cost behind convenience wrappers"
  - "Heavier than needed for simple single-call apps"
tags: ["framework", "rag", "orchestration", "prototyping"]
---

# LangChain

A broad framework for composing LLM applications: prompts, chains, retrievers,
memory, and agent loops. Strong for getting a RAG or tool-using prototype standing
quickly.

## Best-fit scenarios

- Early pilots (stage 1-2) where speed of iteration matters more than control.
- Teams that want batteries-included connectors for vector stores and loaders.
- Prototyping retrieval and agent patterns before committing to a hand-rolled stack.

## Stage relevance

Excellent at stage 1-2 for exploration. At stage 3+, teams often replace the heavier
abstractions with thinner, explicit code for latency and cost control while keeping
LangChain for non-critical paths.

## Limitations to plan around

Pin versions and wrap external calls so an upgrade doesn't silently change behavior.
Instrument token usage directly rather than trusting wrapper defaults.
