# Page Brief — Analytics Dashboard

> Inherits `../design-system.md`. Route: `/modules/analytics`. Module 10 (AGENT-10),
> Wave 6. Covers FR-072..073.

## Purpose

Surface usage, adoption, and engagement analytics across the platform — which assets and
modules get used, adoption trends, activity. The "how is the CoE doing?" view.

## Content & data

- **KPIs:** assets available, assessments run, active users, chats — as stat tiles.
- **Charts:** most-used assets/modules (bar), adoption over time (line), activity by
  content type (donut).
- **Tables:** top assets, recent activity.

## Primary actions

Pick a time range · filter by module/content type · drill into a metric · export.

## States

Populated (charts) · loading (skeleton charts) · empty (no data yet) · filtered.

## Layout

A dashboard grid: a row of KPI stat tiles up top, then a 2-column chart area (trend line +
ranked bar), a donut by content type, and a "top assets" table. Time-range control in the
header.

## Design prompt seed

> Design an "Analytics Dashboard" for an enterprise AI-consulting platform. Top: a row of
> KPI stat tiles (Assets available, Assessments run, Active users, Chats this month) each
> with a value and a small trend delta. Below: a chart grid — an adoption-over-time line
> chart, a "most-used assets/modules" horizontal bar chart, a "usage by content type"
> donut, and a "top assets" table. A time-range selector and module/content-type filters
> in the header. Clean analytical dashboard; restrained chart palette anchored on indigo;
> Inter; monospace for numbers; rounded-lg; light + dark. Generic seeded metrics — no
> company names.
