# @nexus-agent-framework/tokens

Shared design tokens for the Nexus platform apps: CSS custom properties with a light and a dark set per
app theme, Tailwind 3 and Tailwind 4 integration, the same values as typed TypeScript, and WCAG contrast
helpers. Every text and state pair of every theme is tested to AA.

Themes: `base` (neutral), `finhub`, `tandempath`, `predictiveeconomics`, `commandcenter`, `klassesall`.

## Install

```bash
npm install @nexus-agent-framework/tokens
```

The same tarball is also committed in the repository's `releases/` folder and can be installed by URL
from a tag; see `releases/README.md`.

## Use

```css
/* All themes (about 39 KB) */
@import "@nexus-agent-framework/tokens/tokens.css";
/* or one app only (about 14 KB): base plus that theme */
@import "@nexus-agent-framework/tokens/themes/finhub.css";
```

```html
<html data-nx-theme="finhub">
```

Dark mode is on when the element or an ancestor has `data-nx-mode="dark"`, the class `dark`
(Tailwind) or `data-theme="dark"` (FinHub's existing switch). `data-nx-mode="auto"` follows the
operating system; `data-nx-mode="light"` forces light inside a dark page. Themes can also be set on any
element, so one page can show several (the showcase gallery does).

Every value is a custom property: `--nx-color-surface`, `--nx-color-text-muted`, `--nx-color-primary`,
`--nx-color-accent1` ... `--nx-color-accent4` (topic accents), `--nx-space-4`, `--nx-radius-lg`,
`--nx-shadow-card`, `--nx-focus-width`, `--nx-duration-base` (0 ms under reduced motion),
`--nx-control-height` (40 px).

### Tailwind 3

```js
// tailwind.config.js
import nexus from "@nexus-agent-framework/tokens/tailwind";
export default { presets: [nexus], content: ["./index.html", "./src/**/*.{ts,tsx,vue}"] };
```

### Tailwind 4

```css
@import "tailwindcss";
@import "@nexus-agent-framework/tokens/tokens.css";
@import "@nexus-agent-framework/tokens/tailwind4.css";
```

Both add `nx` prefixed utilities only, so they sit next to an app's existing classes:
`bg-nx-surface`, `text-nx-text-muted`, `border-nx-border`, `rounded-nx-lg`, `shadow-nx-card`,
`p-nx-4`, `text-nx-base`, `h-nx-control`. Opacity modifiers are not available for these colours; use
the `*-subtle` roles instead.

### TypeScript

```ts
import { THEMES, themeColors, contrastRatio, checkContrast } from "@nexus-agent-framework/tokens";
const { chartLine, chartFloor } = themeColors("finhub", "dark"); // for canvas charts or emails
```

`checkContrast(roles)` runs the AA pair list (`CONTRAST_PAIRS`) against a colour set, so an app can
test its own overrides the same way.

## Rules

No gradients, glows, blur or remote fonts: font stacks are system fonts (Inter first if the app self
hosts it). Shadows are faint. Colour is never the only signal in the components built on these tokens.

## Versions and release notes

Latest stable: **1.0.1**. 1.0.1 updates this page only; the tokens are the same as 1.0.0.
Every release is listed in the [changelog](https://github.com/sabburi1994/nexus/blob/main/CHANGELOG.md) and on the [GitHub releases](https://github.com/sabburi1994/nexus/releases) page.

The Nexus packages:

| Package | Latest stable |
| :--- | :--- |
| [`@nexus-agent-framework/tokens`](https://www.npmjs.com/package/@nexus-agent-framework/tokens) | 1.0.1 |
| [`@nexus-agent-framework/ui`](https://www.npmjs.com/package/@nexus-agent-framework/ui) | 1.0.2 |
| [`@nexus-agent-framework/contracts`](https://www.npmjs.com/package/@nexus-agent-framework/contracts) | 1.0.4 |
| [`@nexus-agent-framework/middleware`](https://www.npmjs.com/package/@nexus-agent-framework/middleware) | 1.0.3 |
| [`@nexus-agent-framework/scraper`](https://www.npmjs.com/package/@nexus-agent-framework/scraper) | 1.0.3 |
| [`nexus-agent-framework`](https://pypi.org/project/nexus-agent-framework/) (Python, PyPI) | 0.5.1 |
