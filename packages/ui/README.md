# @nexus-agent-framework/ui

The shared React kit for the Nexus platform apps (React 18). Accessible, mobile first at 390 px, themed
by `@nexus-agent-framework/tokens`, styled with one plain CSS file: no runtime scripts or fonts from a
CDN, no inline style attributes, so it works under each app's strict Content Security Policy.

The gallery at `nexus.abburi.info/#gallery` shows every component in every app theme, light and dark.

## Install

Distributed as tarballs at a git tag (see `releases/README.md` in the repository):

```bash
npm install https://raw.githubusercontent.com/sabburi1994/nexus/ui-v1.0.1/releases/nexus-agent-framework-tokens-1.0.0.tgz https://raw.githubusercontent.com/sabburi1994/nexus/ui-v1.0.1/releases/nexus-agent-framework-ui-1.0.1.tgz
```

```tsx
import "@nexus-agent-framework/tokens/themes/finhub.css"; // or tokens.css for all themes
import "@nexus-agent-framework/ui/styles.css";
import { AppShell, Button, Card, Stat, Table, ToastProvider } from "@nexus-agent-framework/ui";
```

```html
<html data-nx-theme="finhub">
```

## Components

| Component | Notes |
| :--- | :--- |
| `Button` | `primary`, `secondary`, `quiet`, `danger`; 40 px (`size="sm"` 32 px); `loading` sets aria-busy |
| `IconButton` | `label` is required and becomes the accessible name |
| `Input`, `Select`, `Textarea` | visible label, `hint`, `error` (aria-invalid and aria-describedby); `numeric` inputs right align |
| `Checkbox`, `RadioGroup`, `Switch` | native inputs; radios in a fieldset with a legend; the switch has role="switch" |
| `Card` | hairline border, faint shadow; optional topic `accent`, `actions`, `footer`, `flush` body for tables |
| `Table` | typed columns, right aligned tabular numbers, sticky header, focusable scroll region, skeleton loading, empty row, keyboard row activation |
| `Sheet` | side panel on wide screens, bottom sheet on phones (native dialog) |
| `Dialog` | modal decision; Escape and backdrop close; focus returns to the trigger |
| `Tabs` | WAI-ARIA tabs: arrows, Home, End; one tab in the tab order |
| `AppShell` | side rail from 768 px, bottom bar of up to five spaces on phones, skip link, aria-current |
| `ToastProvider`, `useToast` | polite and assertive live regions; pauses on hover and focus; danger stays until dismissed |
| `SkeletonRows` | placeholder rows instead of spinners |
| `EmptyState`, `ErrorState` | the error state is announced and offers a retry |
| `Badge` | status and topic tones; keep the text meaningful (colour is never the only signal) |
| `Stat` | one number with its label, tabular figures |
| `LineChart` | thin SVG line, optional comparison series and a labelled floor line, screen reader data table |

## Showcase components

`AiBadge`, `TraceViewer`, `NexusHeader`, `HealingLoopPanel`, `BlastRadiusCard`, `RoiScorecard`,
`CommandBlock` and `StatCard` (the Nexus showcase's own look) moved to a separate entry point so apps do
not pull them in:

```tsx
import { TraceViewer } from "@nexus-agent-framework/ui/showcase";
```

They still need Tailwind in the consuming app, as before.

## Rules the kit follows

No gradients, glows, glassmorphism or backdrop blur, sparkle icons or emoji. Visible focus on every
control. Reduced motion turns animations and transitions off. Tests: Vitest and Testing Library for
behaviour and keyboard, axe-core (offline) for accessibility, and policy checks for the rules above.

## Changelog

* **1.0.1**: `LineChart` no longer widens the page on phones. Its screen reader data table is now clipped inside a visually hidden `div` (a `<table>` cannot shrink to 1 px, so at a 390 px viewport the page scrolled to about 428 px), and `.nx-chart` is `position: relative`. Apps that worked around it with `.nx-chart { position: relative; overflow: hidden }` can drop the workaround.
* **1.0.0**: first release of the kit.
