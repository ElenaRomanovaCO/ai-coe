# UI Design Briefs

Design context for the AI CoE Platform frontend. Each file is a **brief**, not a
spec — enough context to generate a strong UI design (e.g. with Claude design / an
artifact), and to keep every page consistent.

## How to use

1. Open `design-system.md` first — it's the shared visual language (palette, type,
   components, voice). Paste it as context when generating *any* page so the look
   stays cohesive.
2. For the page you're designing, open `pages/<page>.md`. Each ends with a
   **"Design prompt seed"** you can paste (together with the design system) to
   generate a mockup.
3. Save the generated design (image/screenshot/figma export/HTML) next to its brief,
   e.g. `pages/<page>.design.png` or a `pages/<page>/` folder.
4. When the frontend build agent builds that page, point it at both the brief and the
   saved design so the implementation matches.

## Order

Files in `pages/` are **numbered in the order to design them** — just go top to bottom.
The first three are already-live pages (redesign); they lock the visual language. After
that it tracks the build order (Wave 1 → 7). Far-wave briefs derive from each module's
*purpose* (registry + north-star), not its not-yet-written task spec, so reconcile them
against the spec when that wave is actually built.

```
01 login              09 asset-qa            17 intelligence-feed   25 contribute
02 app-shell          10 governance-checker  18 use-case-ideation   26 onboarding
03 chat-dock          11 ethics-checker      19 decision-log        27 certification
04 asset-library      12 compliance-tracker  20 project-health      28 analytics
05 asset-detail       13 tools-repository    21 retrospective       29 code-accelerator
06 dashboard (landing)14 vendor-eval         22 benchmark
07 maturity-assessment15 prompt-studio       23 client-report
08 kit-builder        16 qa                  24 community
```

## Generated designs (`designs/`)

Uploaded mockups live in `designs/`. **Heads-up:** most are entry HTML files that
reference external CSS/JSX (`app-shell/styles.css`, `library/library.jsx`, …) which were
NOT uploaded, so they won't render standalone — treat them as structure references. The
self-contained `*(offline).html` files DO render and carry the real tokens. To make the
others usable, re-export them **offline / self-contained**, or upload the referenced
asset folders alongside.

Each task file in `ai_docs/tasks/` now has a **"🎨 Design references"** block linking the
relevant mockup(s) + brief, so the build agent uses them when building that page.

## Hard rules (apply to every design)

- **No company names, no real client data, no PII** anywhere in copy or mockup data.
- Generic personas only ("a consultant", "a regional bank", "a health system").
- Cite knowledge by file path. Plain English, low jargon.
