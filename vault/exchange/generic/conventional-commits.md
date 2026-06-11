---
id: exch-generic-conventional-commits
content_type: exchange
name: "Conventional Commits Plugin"
tool: generic
category: plugin
summary: "A commit-message helper that enforces Conventional Commits and drafts messages from a diff."
tags: [git, commits, plugin, conventions]
install: |
  1. Install the plugin/hook into your repo's git hooks or editor.
  2. Configure the allowed types (feat, fix, chore, docs, …) and scopes.
  3. On commit, it validates the message and can draft one from the staged diff.
source_url: ""
---

# Conventional Commits Plugin

A tool-agnostic helper that keeps commit messages consistent: it validates against the
Conventional Commits spec and can draft a message from the staged diff, so history stays
machine-readable for changelogs and release tooling.

## What it does

- Validates `type(scope): subject` structure on commit.
- Drafts a message from the diff when asked.
- Flags overly large commits that should be split.

## When to use

On any repo that wants clean, automatable history (semantic-release, changelogs).
Pairs with the agent doing the work — it drafts, you confirm.
