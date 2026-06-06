---
id: tool-strands-agents
name: Strands Agents
category: orchestration
stack: ["python", "aws"]
ai_stage_fit: [2, 3, 4]
cost_model: open-source
limitations:
  - "Younger ecosystem than general-purpose frameworks"
  - "Best leverage is within an AWS-centric deployment"
  - "Multi-agent routing needs deliberate design to stay debuggable"
tags: ["orchestration", "agents", "aws", "multi-agent"]
---

# Strands Agents

An agent framework for building tool-using and multi-agent systems, with a clean fit
for AWS deployments (Lambda, Fargate, Bedrock). Favors explicit tools and structured
control over hidden magic.

## Best-fit scenarios

- Multi-agent systems (stage 2-4) where an orchestrator routes across specialized agents.
- AWS-native deployments wanting agents that map naturally to Lambda/Fargate.
- Teams that value explicit instrumentation around every tool call.

## Stage relevance

Best at stage 2-4 when moving beyond a single prompt into routed, tool-using
workflows. For a one-shot prompt, a framework is overkill.

## Limitations to plan around

Design the routing and agent boundaries deliberately and instrument every tool call
(logs, metrics, cost) so multi-agent flows stay debuggable. Keep the agent hierarchy
shallow until the use case demands depth.
