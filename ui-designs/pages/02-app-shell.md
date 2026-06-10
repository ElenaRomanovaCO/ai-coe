# Page Brief — Authenticated App Shell

> Inherits `../design-system.md`. The persistent frame around every authenticated page.

## Purpose

The shared layout: top header, left sidebar navigation, main content slot, and the
always-present Chat Copilot dock. Establishes wayfinding across the 27 modules and
keeps the copilot one click away everywhere.

## Content & data

- **Header:** product mark (links to dashboard), a global search affordance (optional),
  current user's **display name** + avatar initial, and a logout control.
- **Sidebar nav:** grouped links to modules. Wave 1 modules are live (Dashboard, Asset
  Library); the rest render as **disabled "coming soon"** items (muted, with a small
  lock or wave chip) so the full vision is visible but clearly not yet active.
  - Group by wave or by theme (Assess / Build / Govern / Learn). Show the module's
    `name`; on hover, a tooltip with its one-line `purpose`.
  - Active route highlighted with the indigo accent.
- **Main content slot:** where each page renders.
- **Chat dock:** fixed bottom-right (see `chat-dock.md`).

## Primary actions

- Navigate between modules.
- Collapse/expand the sidebar (icon-only rail when collapsed).
- Logout (clears auth + display name).

## States

- Enabled vs disabled nav items (disabled = not clickable, "coming soon" tooltip).
- Collapsed vs expanded sidebar.
- Responsive: sidebar becomes a slide-over Sheet on narrow screens; header stays.

## Layout

Classic three-zone SaaS shell: fixed top header (~56px), left sidebar (~240px,
collapsible to ~64px), fluid main area with comfortable padding and a max content
width. The dock floats above the bottom-right of the main area.

## Components

Header bar, Sidebar nav (list with icons + labels + wave chips), Avatar, DropdownMenu
(user/logout), Tooltip, Sheet (mobile nav), Separator.

## Visual direction

Quiet and structural — the shell should recede so content leads. Hairline borders
between zones, subtle active-state accent, generous spacing. Lucide icons per module.

## Design prompt seed

> Design the authenticated app shell for an enterprise "AI Center of Excellence"
> platform for consultants. Three zones: a slim top header (generic wordmark left; a
> display-name avatar + logout dropdown right), a left sidebar (~240px) listing modules
> grouped by theme with lucide icons and small "wave N" chips — Dashboard and Asset
> Library are active/highlighted in indigo, the other modules are shown as muted
> "coming soon" disabled items so the full roadmap is visible — and a fluid main content
> area. Include a collapsed icon-only sidebar variant and a mobile slide-over nav. Calm,
> structural, hairline borders, Inter, light + dark. Reserve the bottom-right corner for
> a floating chat dock. No company names.
