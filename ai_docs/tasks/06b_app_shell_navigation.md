# Task: Wave 1.5 — App Shell & Navigation (inserted)

> **Phase:** 1.5 (inserted between 06 and 07)
> **Feature group:** Cross-cutting UI substrate
> **Covers:** persistent navigation across all modules (no FR — fills a gap the task suite never built)
> **Builds:** no agents (frontend only)
> **Depends on:** 00, 02, 03, 04 (pages to navigate to exist)
> **Blocks:** 06c (UI alignment slots into this shell); improves every later module page
> **Estimated effort:** 1 day solo
> **Status:** ☑ Done — deployed (Amplify #16) + smoke-verified live 2026-06-09
>
> **🎨 Design references — build to match these (they take precedence over any sketch below):**
> - Design system: `ui-designs/design-system.md` (wordmark **Praxis**, Hanken Grotesk, indigo)
> - Brief: `ui-designs/pages/02-app-shell.md`
> - Mockups: `ui-designs/designs/App Shell (1).html` (note: references external CSS/JSX not uploaded — align to the brief/system; pixel-match once the self-contained asset is provided)

---

## A. TL;DR Checklist

**Goal:** A persistent app shell — header + left sidebar navigation — present on every
authenticated page, so a user can reach any module from anywhere (today you can only
navigate via dashboard Quick Actions + the chat dock). The shell is the frame every page
renders into and establishes the Praxis visual language.

**Build steps:**

1. **Nav model** — derive the module list from `vault/modules.json` (read at build/SSR
   or a small static map): each module's `name`, `wave`, `enabled`, and `ui_route`
   (present on live modules). `enabled: true` → a live link; `enabled: false` → a muted
   "coming soon" item (not clickable, tooltip with `purpose`).
2. **Sidebar component** (`web/components/Sidebar.tsx`) — grouped nav (by theme or wave),
   lucide icon + label + small "wave N" chip per item, active-route highlight (indigo),
   collapsible to an icon-only rail.
3. **Header** — keep the existing `header.tsx` (Praxis wordmark → dashboard; display name
   + logout); align it to the design system.
4. **Mount in the layout** — update `web/app/(authenticated)/layout.tsx` to render
   header + sidebar + content slot, with the chat dock still pinned bottom-right.
5. **Responsive** — sidebar collapses to an icon rail, and to a slide-over `Sheet` on
   narrow screens.

**Files to create/edit:**

- `web/components/Sidebar.tsx` (or `AppNav.tsx`)
- `web/lib/nav.ts` — module → route + group map (or read `modules.json`)
- `web/components/header.tsx` — align to design system
- `web/app/(authenticated)/layout.tsx` — mount header + sidebar + dock

**Done when:**

- [ ] Sidebar nav appears on **every** authenticated page (dashboard, asset library,
      assessment, kit-builder, …)
- [ ] Live modules (Asset Library, Assessment, Kit Builder, Chat) are navigable; disabled
      modules render as muted "coming soon" with a tooltip
- [ ] Active route is highlighted; hover states present
- [ ] Collapsible rail + mobile slide-over both work; chat dock still bottom-right
- [ ] Matches `design-system.md` (Praxis wordmark, Hanken Grotesk, indigo accent)
- [ ] No company names; a11y (keyboard nav, focus rings, labelled links)

---

## C. Notes & Decisions Log
- Inserted because the suite built pages incrementally with only a thin `header.tsx`; no
  task ever built persistent module navigation. Do before 06c so page-polish slots into a
  consistent frame.
- 2026-06-09: **Built (frontend-only; lint/build clean, not pushed).** `web/lib/nav.ts` = curated
  nav model (all 27 modules grouped into Home/Knowledge/Assess&Govern/Build&Deliver/Learn&Community,
  lucide icons + wave chips; live = Dashboard, Asset Library, Maturity Assessment, Kit Builder; rest
  muted "coming soon" with purpose tooltip). Static map (task allows it) since asset-library/dashboard
  routes aren't in modules.json ui_route and grouping/icons aren't in the registry. `Sidebar.tsx`
  (active-route indigo highlight, collapsible icon rail, disabled tooltips), updated `header.tsx`
  (Praxis wordmark + indigo "P" mark, avatar initial, mobile menu button), `AppShell.tsx` (header +
  desktop sidebar + collapse toggle + mobile slide-over drawer), layout renders `<AppShell>` + dock.
  Added **Hanken Grotesk** via next/font in root layout (Praxis typeface). No agent/infra/CDK change.
  **Deploy = `git push` only** (Amplify rebuild); no cdk deploy / modules.json re-sync needed.

## D. References
- Brief: `ui-designs/pages/02-app-shell.md` · Design system: `ui-designs/design-system.md`
- Live modules + routes: `vault/modules.json` (`enabled`, `ui_route`)
