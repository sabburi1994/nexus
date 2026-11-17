`@nexus-agent-framework/ui` 1.0.1 and `@nexus-agent-framework/tokens` 1.0.0, the first npm release of
the shared UI foundation for the platform apps.

```bash
npm install @nexus-agent-framework/tokens@1.0.0 @nexus-agent-framework/ui@1.0.1
```

## tokens 1.0.0

* CSS custom properties for colour roles, type, spacing, radius, shadows, focus ring, motion and layout.
* A light and a dark theme per platform app; Tailwind 3 and 4 presets; typed values; WCAG AA contrast
  helpers, with every theme tested.

## ui 1.0.1

* The React kit (React 18): Button, form fields, Card, Table, Sheet, Dialog, Tabs, AppShell, Toast,
  SkeletonRows, EmptyState, ErrorState, Badge, Stat, LineChart. Plain CSS that works under a strict
  Content Security Policy.
* Fix in 1.0.1: `LineChart` no longer widens the page on phones (its screen reader table is clipped
  inside a visually hidden wrapper; `.nx-chart` is `position: relative`).
* The showcase components live in `@nexus-agent-framework/ui/showcase`.

The tarballs in `releases/` at this tag are the exact files published to npm.
