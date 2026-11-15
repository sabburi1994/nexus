/**
 * @nexus-agent-framework/tokens: shared design tokens for the platform apps.
 *
 * - ``tokens.css``: custom properties for every theme (light, dark, auto) and the scales.
 * - ``themes/<name>.css``: scales plus one theme, for a single app.
 * - ``tailwind`` (Tailwind 3 preset) and ``tailwind4.css`` (Tailwind 4 ``@theme``).
 * - This module: the same values as typed objects, plus WCAG contrast helpers.
 */

export { THEMES, THEME_NAMES, MODES } from "./themes.js";
export type { ColorRoles, Mode, ThemeDefinition, ThemeName } from "./themes.js";
export { border, focusRing, font, fontWeight, layout, motion, radius, shadow, space, typeScale, zIndex } from "./scales.js";
export { checkContrast, contrastRatio, luminance, CONTRAST_PAIRS } from "./contrast.js";
export type { ContrastPair, ContrastResult } from "./contrast.js";
export { colorVar, CSS_PREFIX, singleThemeCss, tokensCss } from "./css.js";
export { tailwind4Css, tailwindPreset } from "./tailwind.js";
export type { TailwindPreset } from "./tailwind.js";

import { THEMES, type Mode, type ThemeName } from "./themes.js";

/** Read one theme's resolved colour values (for canvas charts, emails, native code). */
export function themeColors(name: ThemeName, mode: Mode = "light") {
  return THEMES[name][mode];
}
