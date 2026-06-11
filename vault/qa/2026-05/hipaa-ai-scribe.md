---
id: qa-hipaa-ai-scribe
question: What does HIPAA require before we send clinical notes to an AI scribe?
tags: ["hipaa", "healthcare", "phi", "compliance"]
posted_by: demo
posted_at: "2026-05-24T16:45:00Z"
answers:
  - id: ans-1
    text: "Get a Business Associate Agreement (BAA) in place with any vendor that touches PHI, including the model/inference provider, before a single note is sent. Then apply minimum-necessary: de-identify where you can and only send the PHI the task actually needs."
    posted_by: demo
    posted_at: "2026-05-24T17:20:00Z"
  - id: ans-2
    text: "Log access to PHI including retrieval in the RAG pipeline, and scope retrieval to the requesting clinician's access. Re-identification, if needed, should happen only in the trusted application layer, never in the prompt."
    posted_by: demo
    posted_at: "2026-05-25T08:10:00Z"
---

# What does HIPAA require before we send clinical notes to an AI scribe?

A healthcare engagement wants to use an AI scribe over clinical notes. What are the HIPAA
must-dos before sending protected health information (PHI) to a model?

## Answers

**demo** — Get a Business Associate Agreement (BAA) in place with any vendor that touches
PHI, including the model/inference provider, before a single note is sent. Then apply
minimum-necessary: de-identify where you can and only send the PHI the task actually needs.

**demo** — Log access to PHI including retrieval in the RAG pipeline, and scope retrieval to
the requesting clinician's access. Re-identification, if needed, should happen only in the
trusted application layer, never in the prompt.
