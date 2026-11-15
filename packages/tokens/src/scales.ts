/**
 * Theme independent scales: type, spacing, radius, borders, shadows, focus ring, motion, layout.
 * Fonts are system stacks: nothing is loaded from a CDN, so pages stay within a strict CSP. An app
 * that self hosts Inter gets it first through the stack.
 */

export const font = {
  sans: '"Inter Variable", Inter, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
  mono: '"JetBrains Mono", "IBM Plex Mono", ui-monospace, SFMono-Regular, Menlo, Consolas, monospace',
} as const;

/** Font size and line height pairs (px). Body copy is 15 px. */
export const typeScale = {
  xs: { size: "0.75rem", lineHeight: "1rem" },
  sm: { size: "0.8125rem", lineHeight: "1.25rem" },
  base: { size: "0.9375rem", lineHeight: "1.5rem" },
  lg: { size: "1.0625rem", lineHeight: "1.625rem" },
  xl: { size: "1.25rem", lineHeight: "1.75rem" },
  "2xl": { size: "1.5rem", lineHeight: "2rem" },
  "3xl": { size: "1.875rem", lineHeight: "2.25rem" },
} as const;

export const fontWeight = { regular: "400", medium: "500", semibold: "600", bold: "700" } as const;

/** 4 px grid. */
export const space = {
  "0": "0",
  "1": "0.25rem",
  "2": "0.5rem",
  "3": "0.75rem",
  "4": "1rem",
  "5": "1.25rem",
  "6": "1.5rem",
  "8": "2rem",
  "10": "2.5rem",
  "12": "3rem",
  "16": "4rem",
} as const;

export const radius = { sm: "6px", md: "10px", lg: "14px", full: "9999px" } as const;

export const border = { hairline: "1px", strong: "2px" } as const;

export const focusRing = { width: "2px", offset: "2px" } as const;

/** Faint, never oversized. Dark mode uses deeper black shadows. */
export const shadow = {
  light: {
    sm: "0 1px 2px 0 rgb(15 23 42 / 0.05)",
    card: "0 1px 3px 0 rgb(15 23 42 / 0.06), 0 1px 2px -1px rgb(15 23 42 / 0.04)",
    overlay: "0 10px 25px -5px rgb(15 23 42 / 0.12), 0 8px 10px -6px rgb(15 23 42 / 0.06)",
  },
  dark: {
    sm: "0 1px 2px 0 rgb(0 0 0 / 0.30)",
    card: "0 1px 3px 0 rgb(0 0 0 / 0.35)",
    overlay: "0 10px 25px -5px rgb(0 0 0 / 0.50)",
  },
} as const;

/** Durations collapse to 0 ms under prefers-reduced-motion (see tokens.css). */
export const motion = {
  durationFast: "120ms",
  durationBase: "180ms",
  durationSlow: "260ms",
  ease: "cubic-bezier(0.2, 0, 0, 1)",
} as const;

export const layout = {
  /** Buttons and form controls. */
  controlHeight: "40px",
  /** Compact controls (icon buttons in dense tables). */
  controlHeightSm: "32px",
  /** Below this width the shell shows the bottom bar, above it the side rail. */
  breakpointMd: "768px",
  railWidth: "232px",
  bottomBarHeight: "64px",
  contentMaxWidth: "1200px",
} as const;

export const zIndex = { nav: "30", sheet: "40", dialog: "50", toast: "60" } as const;
