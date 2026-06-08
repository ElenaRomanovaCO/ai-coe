"""AGENT-01 — the Chat orchestrator (Layer 1 front-door agent).

Runs on Fargate Spot, fronted by an internal ALB and a response-streaming proxy
Lambda. Built on the shared Bedrock Converse tool-loop (see
``vault/decisions/agent-runtime.md``), not Strands.
"""
