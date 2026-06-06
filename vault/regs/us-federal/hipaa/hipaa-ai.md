---
id: reg-hipaa-ai
name: HIPAA — AI and Protected Health Information
geo: us-federal
industry_scope: ["healthcare"]
status: in-effect
effective_date: "2003-04-14"
risk_tier: null
tags: ["hipaa", "phi", "healthcare", "privacy", "baa"]
---

# HIPAA and AI Systems

HIPAA governs the use and disclosure of protected health information (PHI). Using AI
over PHI does not change the rules; it raises the stakes for getting them right.

## Key implications for AI

- **Business Associate Agreements (BAAs)** — Any vendor (including model/inference
  providers) that processes PHI must be under a BAA. Confirm coverage before sending
  PHI to any model endpoint.
- **Minimum necessary** — Only the PHI needed for the task should reach the model.
  De-identify where possible; redact before embedding.
- **De-identification** — Properly de-identified data falls outside HIPAA. Safe
  Harbor and Expert Determination are the two paths.
- **Audit & access** — Log access to PHI, including retrieval in a RAG pipeline.

## What this means for engagements

Default to de-identifying before embedding, keep a BAA in place for any PHI-touching
service, and scope retrieval to the requesting user's access. Re-identification, if
needed, happens only in the trusted application layer.
