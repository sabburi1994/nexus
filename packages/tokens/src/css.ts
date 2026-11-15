/**
 * Generates the CSS custom properties.
 *
 * Usage in an app: import ``@nexus-agent-framework/tokens/tokens.css`` once, then set the theme on
 * any element (usually ``<html>``): ``data-nx-theme="finhub"``. Dark mode is on when the element or an
 * ancestor has ``data-nx-mode="dark"``, the class ``dark`` (Tailwind) or ``data-theme="dark"`` (FinHub's
 * existing switch); ``data-nx-mode="auto"`` follows the operating system. ``data-nx-mode="light"``
 * forces light inside a dark page. Without any of these the light set applies.
 */

import { THEMES, THEME_NAMES, type ColorRoles, type Mode, type ThemeName } from "./themes.js";
import { border, focusRing, font, fontWeight, layout, motion, radius, shadow, space, typeScale, zIndex } from "./scales.js";

export const CSS_PREFIX = "--nx";

/** ``primaryHover`` -> ``--nx-color-primary-hover``. */
export function colorVar(role: keyof ColorRoles): string {
  return `${CSS_PREFIX}-color-${role.replace(/([a-z0-9])([A-Z])/g, "$1-$2").toLowerCase()}`;
}

const DARK_SWITCHES = ['[data-nx-mode="dark"]', ".dark", '[data-theme="dark"]'];

function colorDeclarations(roles: ColorRoles, mode: Mode): string[] {
  const lines = (Object.keys(roles) as (keyof ColorRoles)[]).map((role) => `  ${colorVar(role)}: ${roles[role]};`);
  const s = shadow[mode];
  lines.push(`  ${CSS_PREFIX}-shadow-sm: ${s.sm};`);
  lines.push(`  ${CSS_PREFIX}-shadow-card: ${s.card};`);
  lines.push(`  ${CSS_PREFIX}-shadow-overlay: ${s.overlay};`);
  lines.push(`  color-scheme: ${mode};`);
  return lines;
}

function block(selectors: string[], body: string[]): string {
  return `${selectors.join(",\n")} {\n${body.join("\n")}\n}\n`;
}

/**
 * Selectors for one theme and mode. Theme specific rules always out-specify the base rules, and the
 * dark rules out-specify the light ones, so the result never depends on stylesheet order between
 * themes. Covered cases: theme and mode on the same element, a themed element inside a dark (or
 * auto) ancestor, and a dark or ``data-nx-mode="light"`` element nested inside a themed one.
 */
function themeSelectors(name: ThemeName, mode: Mode | "auto"): string[] {
  const switches = `:is(${DARK_SWITCHES.join(", ")})`;
  if (name === "base") {
    if (mode === "light") return [":root", '[data-nx-theme="base"]', '[data-nx-mode="light"]:not([data-nx-theme])'];
    if (mode === "auto") return ['[data-nx-mode="auto"]'];
    return [switches];
  }
  const t = `[data-nx-theme="${name}"]`;
  if (mode === "light") {
    return [t, `${t} [data-nx-mode="light"]:not([data-nx-theme])`];
  }
  if (mode === "auto") {
    return [
      `${t}[data-nx-mode="auto"]`,
      `[data-nx-mode="auto"] ${t}:not([data-nx-mode="light"])`,
      `${t} [data-nx-mode="auto"]:not([data-nx-theme])`,
    ];
  }
  return [
    `${t}${switches}`,
    `${switches} ${t}:not([data-nx-mode="light"])`,
    `${t} ${switches}:not([data-nx-theme])`,
  ];
}

/** Theme independent custom properties (type, spacing, radius, motion, layout). */
export function scaleCss(): string {
  const lines: string[] = [
    `  ${CSS_PREFIX}-font-sans: ${font.sans};`,
    `  ${CSS_PREFIX}-font-mono: ${font.mono};`,
  ];
  for (const [k, v] of Object.entries(typeScale)) {
    lines.push(`  ${CSS_PREFIX}-font-size-${k}: ${v.size};`);
    lines.push(`  ${CSS_PREFIX}-line-height-${k}: ${v.lineHeight};`);
  }
  for (const [k, v] of Object.entries(fontWeight)) lines.push(`  ${CSS_PREFIX}-font-weight-${k}: ${v};`);
  for (const [k, v] of Object.entries(space)) lines.push(`  ${CSS_PREFIX}-space-${k}: ${v};`);
  for (const [k, v] of Object.entries(radius)) lines.push(`  ${CSS_PREFIX}-radius-${k}: ${v};`);
  lines.push(`  ${CSS_PREFIX}-border-hairline: ${border.hairline};`);
  lines.push(`  ${CSS_PREFIX}-border-strong: ${border.strong};`);
  lines.push(`  ${CSS_PREFIX}-focus-width: ${focusRing.width};`);
  lines.push(`  ${CSS_PREFIX}-focus-offset: ${focusRing.offset};`);
  lines.push(`  ${CSS_PREFIX}-duration-fast: ${motion.durationFast};`);
  lines.push(`  ${CSS_PREFIX}-duration-base: ${motion.durationBase};`);
  lines.push(`  ${CSS_PREFIX}-duration-slow: ${motion.durationSlow};`);
  lines.push(`  ${CSS_PREFIX}-ease: ${motion.ease};`);
  lines.push(`  ${CSS_PREFIX}-control-height: ${layout.controlHeight};`);
  lines.push(`  ${CSS_PREFIX}-control-height-sm: ${layout.controlHeightSm};`);
  lines.push(`  ${CSS_PREFIX}-rail-width: ${layout.railWidth};`);
  lines.push(`  ${CSS_PREFIX}-bottom-bar-height: ${layout.bottomBarHeight};`);
  lines.push(`  ${CSS_PREFIX}-content-max-width: ${layout.contentMaxWidth};`);
  for (const [k, v] of Object.entries(zIndex)) lines.push(`  ${CSS_PREFIX}-z-${k}: ${v};`);
  return (
    block([":root"], lines) +
    "@media (prefers-reduced-motion: reduce) {\n" +
    block(
      [":root", "[data-nx-theme]"],
      [
        `  ${CSS_PREFIX}-duration-fast: 0ms;`,
        `  ${CSS_PREFIX}-duration-base: 0ms;`,
        `  ${CSS_PREFIX}-duration-slow: 0ms;`,
      ],
    ) +
    "}\n"
  );
}

/** Light, dark and auto blocks for one theme. */
export function themeCss(name: ThemeName): string {
  const theme = THEMES[name];
  return (
    `/* ${theme.label} */\n` +
    block(themeSelectors(name, "light"), colorDeclarations(theme.light, "light")) +
    block(themeSelectors(name, "dark"), colorDeclarations(theme.dark, "dark")) +
    "@media (prefers-color-scheme: dark) {\n" +
    block(themeSelectors(name, "auto"), colorDeclarations(theme.dark, "dark")) +
    "}\n"
  );
}

const HEADER =
  "/* @nexus-agent-framework/tokens: generated from src/themes.ts and src/scales.ts. Do not edit. */\n";

/** Complete stylesheet: scales plus every theme. */
export function tokensCss(): string {
  return HEADER + scaleCss() + THEME_NAMES.map((name) => themeCss(name)).join("");
}

/** Scales plus a single theme (smaller file for one app). */
export function singleThemeCss(name: ThemeName): string {
  return HEADER + scaleCss() + themeCss("base") + (name === "base" ? "" : themeCss(name));
}
