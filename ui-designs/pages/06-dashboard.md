# Page Brief — Dashboard (Personal Home)

> Inherits `../design-system.md`. Route: `/dashboard`. Module 17 (Personal Dashboard).

## Purpose

The personalized landing after login. Orients the consultant: what they were doing,
what's available, and what to do next. For the demo it's the "wow, this is a real
platform" moment — so it should feel alive even with seeded data.

## Who & when

A consultant arriving to start work or to demo the tool. Wants quick entry points and a
sense of momentum.

## Content & data

- **Welcome strip:** "Welcome back, {display_name}" + a one-line nudge.
- **Quick actions / module launchpad:** cards for the live modules (Asset Library, Chat)
  and a few prominent "coming soon" ones, each with icon, name, one-line purpose.
- **Recent activity:** recently viewed assets / chats (seeded for demo).
- **Saved / pinned assets:** a compact list of saved assets (title, type, industry,
  stage indicator).
- **Suggested next steps:** 2–3 contextual suggestions ("Run a maturity assessment",
  "Browse healthcare patterns").
- Optional **at-a-glance stats** (assets available, modules live) — small, tasteful.

## Primary actions

- Jump into a module.
- Open a recent/saved asset.
- Start a chat (or it's already one click away in the dock).

## States

- **Empty/first-visit** — no recent activity yet: lead with the launchpad + a "start
  here" suggestion.
- **Loading** — skeleton cards.
- **Populated** — recent + saved + suggestions filled.

## Layout

A responsive card grid. Top: welcome strip. Then a 2–3 column arrangement: launchpad
(prominent), recent activity, saved assets, suggestions. Breathable, scannable.

## Components

Card (several variants), Badge, the **stage indicator** component, Avatar, Button,
Skeleton, lucide icons per module/content-type.

## Visual direction

Inviting but professional — a calm "command center." Clear visual hierarchy, the
launchpad as the hero. Use content-type accent colors sparingly on cards.

## Design prompt seed

> Design a personalized dashboard / home for an enterprise "AI Center of Excellence"
> platform used by consultants. Top: a "Welcome back, Alex" strip with a short nudge.
> Below, a responsive card layout: (1) a prominent module launchpad — cards for live
> modules "Asset Library" and "Chat Copilot" plus a few muted "coming soon" modules,
> each with a lucide icon, name, and one-line purpose; (2) a "Recent activity" list of
> recently viewed assets; (3) a "Saved assets" list showing title, a content-type badge,
> industry, and a compact 0–5 AI-maturity-stage indicator; (4) a "Suggested next steps"
> panel with 2–3 actions. Calm command-center feel, indigo accent, Inter, rounded-lg
> cards, light + dark. Show populated and empty/first-visit states. Generic demo data,
> no company names.
