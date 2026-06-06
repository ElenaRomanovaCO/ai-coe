---
id: prompt-executive-briefing
title: Executive Briefing Draft
use_case: "Draft a concise executive briefing on an AI topic or recommendation"
model_targets: ["sonnet-4-6"]
variables: ["topic", "audience_role", "decision_needed", "key_facts"]
version: 1
parent_id: null
---

# Executive Briefing Draft

## Prompt

Draft an executive briefing on **{{topic}}** for a **{{audience_role}}**. The decision
needed is: **{{decision_needed}}**. Ground the briefing in these facts: **{{key_facts}}**.

Structure:

1. **Bottom line (2-3 sentences)** — the recommendation and why, up front.
2. **Context** — what's happening and why it matters now.
3. **Options** — 2-3 options with tradeoffs, in a short table.
4. **Recommendation** — the pick, the cost/risk, and the first step.
5. **Ask** — exactly what you need from the executive.

## Guidance

Lead with the answer. Keep it to one page. No hype, no unexplained jargon. Every claim
should trace to a provided fact; if a fact is missing, mark it as an assumption to
confirm rather than inventing it.
