---
name: design-brief
description: >-
  Create or expand UI design briefs for the AI CoE platform — one markdown brief per
  page, saved into ui-designs/pages/ with a two-digit priority prefix (NN-name.md) in
  build order, following the house template and inheriting ui-designs/design-system.md.
  Use when the user asks to add a brief for a new/changed page, brief a whole feature,
  re-enumerate the priority order, or stand up briefs for an upcoming wave. Each brief
  ends with a paste-ready "Design prompt seed". Briefs are design CONTEXT, not specs.
allowed-tools: Read, Grep, Glob, Bash, Write, Edit, AskUserQuestion
---

# Author UI design briefs

Produce design briefs that a designer (or Claude design) turns into mockups, and that
the frontend build agent later implements against. Location: `ui-designs/pages/`. The
shared visual language lives in `ui-designs/design-system.md` — read it first and assume
every brief inherits it.

## 1. Locate & orient

- Repo root contains `ui-designs/` (and `vault/`, `ai_docs/`). Find it if not in cwd.
- Read `ui-designs/design-system.md` (the anchor) and `ui-designs/README.md` (the
  numbered index) before writing, so new briefs match the house style and numbering.
- Pull **real data shapes** for the page from the code/registry, not invented fields:
  asset frontmatter (`agents/lib/schemas`), the module registry (`vault/modules.json`),
  citation/response models (`agents/orchestrator/models.py`). Designs should reflect
  real field names; example *copy* is illustrative placeholder only.

## 2. Numbering (priority = build order)

Files are `NN-<page>.md`, two digits, sorted so the folder *is* the priority order.
Order = the three already-live anchors first (login, app-shell, chat-dock — they lock
the visual language), then strict task/wave build order. When adding a page, slot it at
its build position and renumber following files if needed (use `git mv`/`mv`; they're
not code, renaming is safe). Keep `README.md`'s index in sync.

## 3. House template (every brief)

```markdown
# Page Brief — <Name>

> Inherits `../design-system.md`. Route: `<route>`. Module N (AGENT-XX), Wave W.
> Covers FR-...

## Purpose
<1-2 lines: what the user accomplishes here>

## Who & when
<the user and the moment they're on this page>

## Content & data
<bullets using REAL field names / data shapes>

## Primary actions
<the key interactions>

## States
<empty / loading / error / populated — be specific to this page>

## Layout
<regions and structure in 1-3 lines>

## Components
<shadcn/ui + lucide pieces to compose from>

## Visual direction
<the page's specific tone within the design system>

## Design prompt seed
> <a ready-to-paste paragraph that, with design-system.md, generates a strong mockup —
> concrete about layout, the states to show, real-ish demo data, and "light + dark">
```

## 4. Hard rules (enforce in every brief and seed)

- **No company names, no PII, no real client data.** Generic personas only.
- Map to the locked stack: Next.js 16 App Router · Tailwind v4 · shadcn/ui · lucide.
- Design every page for all four states (empty/loading/error/populated).
- Accessibility (WCAG AA) and the always-present chat dock (bottom-right) are givens.
- Far-wave briefs derive from a module's *purpose* (registry + north-star), not its
  not-yet-written task spec — say so, so they're reconciled at build time.

## 5. Saving generated designs

Tell the user to save each generated design next to its brief with the same prefix
(e.g. `pages/02-app-shell.design.html`, or a `pages/02-app-shell/` folder for variants),
so the build agent reads the brief + the design together.

## 6. Report

List the files created/renamed with their numbers, and remind the user to settle
`design-system.md` before generating (every page inherits it) and to `git add ui-designs/`
when ready to version.
