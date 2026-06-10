# Task: Wave 1.5 — Wave 1–2 UI Design Alignment (inserted)

> **Phase:** 1.5 (inserted between 06 and 07)
> **Feature group:** Cross-cutting UI polish
> **Covers:** visual consistency — bring all built pages to the Praxis design system + mocks
> **Builds:** no agents (frontend only)
> **Depends on:** 06b (app shell), and the pages from 00/02/03/04/05/06
> **Blocks:** none (but do before the demo so the product looks coherent)
> **Estimated effort:** 1–2 days solo
> **Status:** ◐ Theme pass done (tokens promoted, accent flipped indigo→coral, dock recolored) 2026-06-09 — built + lint/build clean, NOT pushed; awaiting smoke
>
> **🎨 Design references — the source of truth for this task:**
> - Design system: `ui-designs/design-system.md` (wordmark **Praxis**, Hanken Grotesk, indigo, content-type colors, StageIndicator)
> - Page briefs: `ui-designs/pages/01-login.md`, `06-dashboard.md`, `04-asset-library.md`, `05-asset-detail.md`, `07-maturity-assessment.md`, `08-kit-builder.md`, `03-chat-dock.md`
> - Mockups: the matching files in `ui-designs/designs/`

> ⚠️ **Blocker for pixel-matching:** most mock HTMLs reference external CSS/JSX that was
> not uploaded (only `Copilot Dock (offline).html` is self-contained). Until the
> self-contained mocks (or their asset folders) are provided, align pages to the
> **design system**, not pixel-for-pixel. Do a styling pass to exact-match once assets land.

---

## A. TL;DR Checklist

**Goal:** Every built page shares one cohesive visual language (Praxis) — wordmark,
Hanken Grotesk type, indigo accent, consistent cards / badges / `StageIndicator` /
content-type colors — instead of the current mix of styles. No page should look
"old-style" next to the assessment/kit pages.

**Build steps (one consistency pass, not a rebuild):**

1. **Lock the system in code** — load Hanken Grotesk; set the Praxis wordmark; define the
   indigo accent + content-type color/icon tokens as Tailwind theme/CSS variables so all
   pages share them. Promote shared primitives (`StageIndicator`, content-type `Badge`,
   card variants) into `web/components/ui/` if not already.
2. **Per-page alignment** (reconcile each to its brief + mock):
   - `login` → `01-login.md` (+ Login States/Backgrounds mocks)
   - `dashboard` → `06-dashboard.md`
   - `asset-library` + `asset-detail` → `04`/`05`
   - `maturity-assessment` → `07`
   - `kit-builder` → `08`
   - `chat-dock` → `03` (the `(offline)` mock is fully self-contained — pixel-match this one)
3. **Verify the four states** on each page (empty/loading/error/populated) still render
   correctly after restyling.

**Files to edit:** the page/component files under `web/app/(authenticated)/...` and
`web/components/...` for the pages above; shared tokens in the Tailwind/global CSS.

**Done when:**

- [ ] One consistent visual language across all built pages (Praxis wordmark, Hanken
      Grotesk, indigo, shared cards/badges/StageIndicator)
- [ ] No remaining "old-style" page
- [ ] `chat-dock` pixel-matches its self-contained mock; other pages match the design
      system (and their mocks where self-contained assets are available)
- [ ] All four states still render per page; responsive; a11y preserved
- [ ] No company names; demo data only

---

## C. Notes & Decisions Log
- Inserted because tasks 00–06 built UI before the Praxis mocks existed (or built-to-brief
  without pixel-match). This is the consolidation pass — one task, not one-per-page, to
  keep the language consistent. Gated on self-contained design assets for exact matching.
- 2026-06-09: **Theme pass DONE** (frontend-only, lint/build clean, NOT pushed). Extracted real
  tokens from `Copilot Dock (offline).html` and promoted to `web/app/globals.css` `@theme`:
  **accent = coral `#e8633f`** (press `#c35335`), warm cream canvas `#f6f1ec`, white surfaces, warm
  grays. To recolor every page without per-file edits, the Tailwind `indigo-*` scale is remapped to
  coral and `slate-*`/`neutral-*` to a warm-gray ramp → existing utilities inherit the brand.
  `Button` default variant → coral; ChatDock FAB/user-bubble/navigate-button → coral; **Hanken
  Grotesk now actually applies** (removed the system-font override in globals body that was shadowing
  next/font). StageIndicator, dimension bars, sidebar active state, header mark/avatar all inherit.
- 2026-06-09: ⚠️ **DISAGREEMENT FLAGGED (step 4) — RESOLVED to mock:** `design-system.md` prose +
  these task references say **indigo/slate**; the only self-contained mock (`Copilot Dock (offline).html`)
  uses **coral/warm**. Per the user's step-1 ("extract the REAL tokens from the mock and promote them"),
  coral/warm is authoritative — this **flips the 06b shell accent indigo→coral**. design-system.md
  itself calls its palette an "adjustable starting point," so no conflict in intent. Handed off
  un-pushed for smoke; revert is globals.css-centric if the user prefers indigo.
- 2026-06-09: **Pixel-match caveat:** the dock mock is a minified React bundle (+ thumbnail), so the
  dock was matched on tokens (coral accent, Hanken, radii, warm surfaces) rather than exact DOM. Other
  pages aligned to the design system + the live 06b shell (now coral). Content-type per-type badge
  colors (design-system motif) deferred — optional follow-up.

## D. References
- Design system + briefs in `ui-designs/`; mocks in `ui-designs/designs/`
- Per-page design-reference callouts now live in tasks 00/02/03/04/05/06
