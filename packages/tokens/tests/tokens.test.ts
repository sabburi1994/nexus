import { describe, expect, it } from "vitest";

import {
  CONTRAST_PAIRS,
  MODES,
  THEMES,
  THEME_NAMES,
  checkContrast,
  colorVar,
  contrastRatio,
  singleThemeCss,
  tailwind4Css,
  tailwindPreset,
  tokensCss,
} from "../src/index.js";

describe("contrast helpers", () => {
  it("matches the WCAG reference values", () => {
    expect(contrastRatio("#000000", "#ffffff")).toBeCloseTo(21, 5);
    expect(contrastRatio("#ffffff", "#ffffff")).toBeCloseTo(1, 5);
    expect(contrastRatio("#767676", "#ffffff")).toBeCloseTo(4.54, 2);
    expect(contrastRatio("#fff", "#000")).toBeCloseTo(21, 5);
  });

  it("rejects non hex colours instead of guessing", () => {
    expect(() => contrastRatio("rgb(0 0 0)", "#fff")).toThrow();
  });
});

describe.each(THEME_NAMES.flatMap((name) => MODES.map((mode) => [name, mode] as const)))(
  "theme %s (%s)",
  (name, mode) => {
    const roles = THEMES[name][mode];

    it("passes AA for every text and state pair", () => {
      const failures = checkContrast(roles)
        .filter((r) => !r.pass)
        .map((r) => `${r.fg} on ${r.bg}: ${r.ratio.toFixed(2)} < ${r.min}`);
      expect(failures).toEqual([]);
    });

    it("defines every role with a solid colour (overlay excepted)", () => {
      for (const [role, value] of Object.entries(roles)) {
        if (role === "overlay") {
          expect(value).toMatch(/^rgb\(/);
        } else {
          expect(value, role).toMatch(/^#[0-9a-f]{6}$/i);
        }
      }
    });
  },
);

describe("contrast pair list", () => {
  it("covers text on every surface and the focus ring", () => {
    const keys = CONTRAST_PAIRS.map((p) => `${p.fg}/${p.bg}`);
    for (const k of ["text/bg", "text/surface", "textMuted/surface", "onPrimary/primary", "focus/surface", "control/surface"]) {
      expect(keys).toContain(k);
    }
  });
});

describe("generated CSS", () => {
  const css = tokensCss();

  it("declares every role for every theme", () => {
    for (const name of THEME_NAMES) {
      if (name !== "base") expect(css).toContain(`[data-nx-theme="${name}"]`);
    }
    for (const role of Object.keys(THEMES.base.light)) {
      expect(css).toContain(`${colorVar(role as keyof typeof THEMES.base.light)}:`);
    }
  });

  it("switches to dark on data-nx-mode, the Tailwind dark class and FinHub's data-theme", () => {
    expect(css).toContain('[data-nx-theme="finhub"]:is([data-nx-mode="dark"], .dark, [data-theme="dark"])');
    expect(css).toContain("@media (prefers-color-scheme: dark)");
    expect(css).toContain('[data-nx-mode="auto"]');
  });

  it("collapses motion for reduced motion users", () => {
    expect(css).toMatch(/@media \(prefers-reduced-motion: reduce\)[\s\S]*--nx-duration-base: 0ms/);
  });

  it("has no gradients, blur or remote fonts", () => {
    expect(css).not.toMatch(/gradient|blur\(|@import|url\(/i);
  });

  it("writes kebab case custom properties", () => {
    expect(colorVar("primaryHover")).toBe("--nx-color-primary-hover");
    expect(colorVar("accent1Subtle")).toBe("--nx-color-accent1-subtle");
  });

  it("single theme files hold the base plus that theme only", () => {
    const one = singleThemeCss("klassesall");
    expect(one).toContain('[data-nx-theme="klassesall"]');
    expect(one).not.toContain('[data-nx-theme="finhub"]');
    expect(one).toContain(":root");
  });
});

describe("Tailwind integration", () => {
  it("Tailwind 3 preset exposes nx prefixed names that point at the variables", () => {
    const preset = tailwindPreset();
    const colors = preset.theme.extend.colors as Record<string, string>;
    expect(colors["nx-surface"]).toBe("var(--nx-color-surface)");
    expect(colors["nx-text-muted"]).toBe("var(--nx-color-text-muted)");
    expect(Object.keys(colors).every((k) => k.startsWith("nx-"))).toBe(true);
    expect((preset.theme.extend.borderRadius as Record<string, string>)["nx-lg"]).toBe("var(--nx-radius-lg)");
  });

  it("Tailwind 4 file is an @theme inline block with the same names", () => {
    const css = tailwind4Css();
    expect(css).toContain("@theme inline {");
    expect(css).toContain("--color-nx-surface: var(--nx-color-surface);");
    expect(css).toContain("--radius-nx-lg: var(--nx-radius-lg);");
    expect(css).toContain("--text-nx-base--line-height: var(--nx-line-height-base);");
  });
});
