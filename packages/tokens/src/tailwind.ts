/**
 * Tailwind integration. Both variants only add ``nx`` prefixed names, so an app can adopt them next to
 * its existing classes (``bg-nx-surface``, ``text-nx-text-muted``, ``rounded-nx-lg``, ``shadow-nx-card``).
 *
 * - Tailwind 3: ``presets: [require("@nexus-agent-framework/tokens/tailwind")]`` (or the ESM import).
 * - Tailwind 4: ``@import "@nexus-agent-framework/tokens/tailwind4.css";`` after ``@import "tailwindcss";``.
 *
 * Colours are ``var(--nx-color-*)`` references, so themes and dark mode switch at runtime. Opacity
 * modifiers (``bg-nx-primary/50``) are not supported for these colours; use the ``*-subtle`` roles.
 */

import { colorVar, CSS_PREFIX } from "./css.js";
import { space, typeScale } from "./scales.js";
import { THEMES, type ColorRoles } from "./themes.js";

const ROLES = Object.keys(THEMES.base.light) as (keyof ColorRoles)[];

function kebab(role: string): string {
  return role.replace(/([a-z0-9])([A-Z])/g, "$1-$2").toLowerCase();
}

export interface TailwindPreset {
  theme: { extend: Record<string, Record<string, unknown>> };
}

/** Tailwind 3 preset (``presets: [preset]``). */
export function tailwindPreset(): TailwindPreset {
  const colors: Record<string, string> = {};
  for (const role of ROLES) colors[`nx-${kebab(role)}`] = `var(${colorVar(role)})`;
  const spacing: Record<string, string> = {};
  for (const k of Object.keys(space)) spacing[`nx-${k}`] = `var(${CSS_PREFIX}-space-${k})`;
  const fontSize: Record<string, [string, { lineHeight: string }]> = {};
  for (const k of Object.keys(typeScale)) {
    fontSize[`nx-${k}`] = [`var(${CSS_PREFIX}-font-size-${k})`, { lineHeight: `var(${CSS_PREFIX}-line-height-${k})` }];
  }
  return {
    theme: {
      extend: {
        colors,
        spacing,
        fontSize,
        fontFamily: {
          "nx-sans": [`var(${CSS_PREFIX}-font-sans)`],
          "nx-mono": [`var(${CSS_PREFIX}-font-mono)`],
        },
        borderRadius: {
          "nx-sm": `var(${CSS_PREFIX}-radius-sm)`,
          "nx-md": `var(${CSS_PREFIX}-radius-md)`,
          "nx-lg": `var(${CSS_PREFIX}-radius-lg)`,
          "nx-full": `var(${CSS_PREFIX}-radius-full)`,
        },
        boxShadow: {
          "nx-sm": `var(${CSS_PREFIX}-shadow-sm)`,
          "nx-card": `var(${CSS_PREFIX}-shadow-card)`,
          "nx-overlay": `var(${CSS_PREFIX}-shadow-overlay)`,
        },
        height: { "nx-control": `var(${CSS_PREFIX}-control-height)` },
        minHeight: { "nx-control": `var(${CSS_PREFIX}-control-height)` },
        transitionDuration: {
          "nx-fast": `var(${CSS_PREFIX}-duration-fast)`,
          "nx-base": `var(${CSS_PREFIX}-duration-base)`,
          "nx-slow": `var(${CSS_PREFIX}-duration-slow)`,
        },
        transitionTimingFunction: { nx: `var(${CSS_PREFIX}-ease)` },
      },
    },
  };
}

/** Tailwind 4 ``@theme inline`` block exposing the same names. */
export function tailwind4Css(): string {
  const lines: string[] = [];
  for (const role of ROLES) lines.push(`  --color-nx-${kebab(role)}: var(${colorVar(role)});`);
  for (const k of Object.keys(space)) lines.push(`  --spacing-nx-${k}: var(${CSS_PREFIX}-space-${k});`);
  // Sizes (h-, w-, min-h-) use the spacing namespace in Tailwind 4.
  lines.push(`  --spacing-nx-control: var(${CSS_PREFIX}-control-height);`);
  for (const k of Object.keys(typeScale)) {
    lines.push(`  --text-nx-${k}: var(${CSS_PREFIX}-font-size-${k});`);
    lines.push(`  --text-nx-${k}--line-height: var(${CSS_PREFIX}-line-height-${k});`);
  }
  lines.push(`  --font-nx-sans: var(${CSS_PREFIX}-font-sans);`);
  lines.push(`  --font-nx-mono: var(${CSS_PREFIX}-font-mono);`);
  for (const k of ["sm", "md", "lg", "full"]) lines.push(`  --radius-nx-${k}: var(${CSS_PREFIX}-radius-${k});`);
  for (const k of ["sm", "card", "overlay"]) lines.push(`  --shadow-nx-${k}: var(${CSS_PREFIX}-shadow-${k});`);
  lines.push(`  --ease-nx: var(${CSS_PREFIX}-ease);`);
  return (
    "/* @nexus-agent-framework/tokens for Tailwind 4: import after tailwindcss and tokens.css. Generated. */\n" +
    `@theme inline {\n${lines.join("\n")}\n}\n`
  );
}
