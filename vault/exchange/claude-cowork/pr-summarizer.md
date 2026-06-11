---
id: exch-claude-cowork-pr-summarizer
content_type: exchange
name: "PR Summarizer (Cowork)"
tool: claude-cowork
category: skill
summary: "Summarizes a pull request into reviewer-ready notes: intent, risk areas, and a test checklist."
tags: [pr, review, summary, collaboration]
install: |
  1. Add the skill to your Cowork workspace's shared skills directory.
  2. Grant it read access to the repository and PR metadata.
  3. Trigger it on a PR to post a summary comment draft.
source_url: ""
---

# PR Summarizer (Cowork)

A shared Cowork skill that turns a pull request into concise, reviewer-ready notes:
what changed and why, the riskiest hunks to look at first, and a suggested test
checklist — so reviews start from a shared understanding.

## What it does

- Reads the diff and the PR description.
- Produces a plain-language summary, a risk callout, and a review checklist.
- Drafts a comment the author can edit before posting.

## When to use

On medium-to-large PRs where a cold review is slow. It accelerates the reviewer's
ramp; it does not replace reading the code.
