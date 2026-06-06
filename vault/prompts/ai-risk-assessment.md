---
id: prompt-ai-risk-assessment
title: AI Risk Assessment Scaffolding
use_case: "Produce a first-pass risk assessment for a proposed AI use case"
model_targets: ["sonnet-4-6"]
variables: ["use_case_description", "industry", "data_sensitivity", "autonomy_level"]
version: 1
parent_id: null
---

# AI Risk Assessment Scaffolding

## Prompt

Produce a first-pass risk assessment for this use case: **{{use_case_description}}** in
**{{industry}}**, with data sensitivity **{{data_sensitivity}}** and autonomy level
**{{autonomy_level}}**.

Assess across these dimensions, each rated low/medium/high with a one-line rationale and
a mitigation:

- Data privacy & PII exposure
- Fairness & bias
- Explainability & contestability
- Security (prompt injection, data exfiltration)
- Regulatory exposure (name likely applicable regimes)
- Operational & failure modes (what happens when it's wrong?)

Close with the top 3 risks to address before any pilot, and whether the use case should
stay advisory (human-in-the-loop) to limit exposure.

## Guidance

This is a scaffold for a human reviewer, not a sign-off. Be explicit about uncertainty.
Route the result through the Governance & Risk Checker and Compliance Tracker modules.
