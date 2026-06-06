---
id: reg-gdpr-ai
name: GDPR — Implications for AI
geo: eu
industry_scope: ["cross-industry"]
status: in-effect
effective_date: "2018-05-25"
risk_tier: null
tags: ["gdpr", "privacy", "automated-decisions", "dpia", "pii"]
---

# GDPR and AI Systems

The GDPR governs processing of personal data of individuals in the EU. AI systems that
process personal data inherit all of its requirements.

## Key implications for AI

- **Lawful basis** — Every processing purpose (training, inference, retrieval) needs a
  lawful basis. Repurposing data for AI may require a fresh basis.
- **Automated decisions (Art. 22)** — Solely automated decisions with legal or similar
  significant effects trigger rights to human review and explanation.
- **DPIA** — High-risk processing requires a Data Protection Impact Assessment.
- **Data minimization & purpose limitation** — Use the least data necessary; don't
  silently repurpose.
- **Right to erasure** — Plan for deletion, including from vector indexes.

## What this means for engagements

Document the lawful basis, run a DPIA for high-risk uses, ensure a human-review path
for significant automated decisions, and design retrieval/embeddings so personal data
can be deleted on request.
