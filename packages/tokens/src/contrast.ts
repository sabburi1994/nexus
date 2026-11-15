/** WCAG 2.x contrast helpers and the role pairs every theme must pass. */

import type { ColorRoles } from "./themes.js";

type Role = keyof ColorRoles;

function channel(value: number): number {
  const c = value / 255;
  return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
}

/** Relative luminance of a ``#rrggbb`` or ``#rgb`` colour. */
export function luminance(hex: string): number {
  let h = hex.trim().replace(/^#/, "");
  if (h.length === 3) {
    h = h
      .split("")
      .map((c) => c + c)
      .join("");
  }
  if (!/^[0-9a-fA-F]{6}$/.test(h)) {
    throw new Error(`Not a #rrggbb colour: ${hex}`);
  }
  const r = parseInt(h.slice(0, 2), 16);
  const g = parseInt(h.slice(2, 4), 16);
  const b = parseInt(h.slice(4, 6), 16);
  return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b);
}

/** Contrast ratio between two colours (1 to 21). */
export function contrastRatio(a: string, b: string): number {
  const la = luminance(a);
  const lb = luminance(b);
  const [hi, lo] = la > lb ? [la, lb] : [lb, la];
  return (hi + 0.05) / (lo + 0.05);
}

export interface ContrastPair {
  fg: Role;
  bg: Role;
  /** 4.5 for text (AA), 3 for UI boundaries, focus rings and graphics (WCAG 1.4.11). */
  min: number;
}

const text = (fg: Role, ...bgs: Role[]): ContrastPair[] => bgs.map((bg) => ({ fg, bg, min: 4.5 }));
const ui = (fg: Role, ...bgs: Role[]): ContrastPair[] => bgs.map((bg) => ({ fg, bg, min: 3 }));

/** Every text and state pair the components use. */
export const CONTRAST_PAIRS: readonly ContrastPair[] = [
  ...text("text", "bg", "surface", "surfaceSunken", "primarySubtle"),
  ...text("textMuted", "bg", "surface", "surfaceSunken"),
  ...text("onPrimary", "primary", "primaryHover"),
  ...text("primaryText", "bg", "surface", "primarySubtle"),
  ...text("onDanger", "danger", "dangerHover"),
  ...text("dangerText", "surface", "dangerSubtle"),
  ...text("successText", "surface", "successSubtle"),
  ...text("warningText", "surface", "warningSubtle"),
  ...text("infoText", "surface", "infoSubtle"),
  ...text("navText", "nav"),
  ...text("navTextMuted", "nav"),
  ...text("navActiveText", "navActive"),
  ...text("accent1Text", "surface", "accent1Subtle"),
  ...text("accent2Text", "surface", "accent2Subtle"),
  ...text("accent3Text", "surface", "accent3Subtle"),
  ...text("accent4Text", "surface", "accent4Subtle"),
  ...ui("control", "bg", "surface"),
  ...ui("focus", "bg", "surface"),
  ...ui("primary", "surface"),
  ...ui("danger", "surface"),
  ...ui("chartLine", "surface"),
  ...ui("chartLineAlt", "surface"),
  ...ui("chartFloor", "surface"),
  ...ui("accent1", "surface"),
  ...ui("accent2", "surface"),
  ...ui("accent3", "surface"),
  ...ui("accent4", "surface"),
];

export interface ContrastResult extends ContrastPair {
  ratio: number;
  pass: boolean;
}

/** Check all ``CONTRAST_PAIRS`` for one colour set. */
export function checkContrast(roles: ColorRoles): ContrastResult[] {
  return CONTRAST_PAIRS.map((pair) => {
    const ratio = contrastRatio(roles[pair.fg], roles[pair.bg]);
    return { ...pair, ratio, pass: ratio >= pair.min };
  });
}
