/**
 * Colour themes: one neutral base plus a theme per platform app, each with a complete light and dark
 * set of semantic roles. Components use the roles (never raw hex), so switching ``data-nx-theme``
 * re-skins everything. Every text and state pair is checked to WCAG AA in ``tests/contrast.test.ts``.
 *
 * Palettes follow each app's current look:
 * - finhub: deep teal ink and navigation on warm white, sage (cash), amber (payments), blue (markets)
 *   and coral (research) topic accents (finhub CLAUDE.md, "UI and UX");
 * - tandempath: blue primary, forest green accent, cool grey page (jobradar repo);
 * - predictiveeconomics: steel blue on cool white, navy ink, coral and lime brand tints;
 * - commandcenter: cobalt accent with its ok, warn and bad status set;
 * - klassesall: indigo primary with a warm amber accent.
 */

export const THEME_NAMES = ["base", "finhub", "tandempath", "predictiveeconomics", "commandcenter", "klassesall"] as const;
export type ThemeName = (typeof THEME_NAMES)[number];
export const MODES = ["light", "dark"] as const;
export type Mode = (typeof MODES)[number];

export interface ColorRoles {
  /** Page canvas. */
  bg: string;
  /** Cards, sheets, dialogs, inputs. */
  surface: string;
  /** Inset wells: table headers, hover rows, skeletons on cards. */
  surfaceSunken: string;
  /** Hairline rules and card borders (decorative, no contrast minimum). */
  border: string;
  /** Firmer dividers. */
  borderStrong: string;
  /** Boundary of form controls: at least 3:1 against surface and bg. */
  control: string;
  text: string;
  textMuted: string;
  primary: string;
  primaryHover: string;
  onPrimary: string;
  primarySubtle: string;
  /** Primary coloured text and links on surface, bg and primarySubtle. */
  primaryText: string;
  danger: string;
  dangerHover: string;
  onDanger: string;
  dangerSubtle: string;
  dangerText: string;
  successSubtle: string;
  successText: string;
  warningSubtle: string;
  warningText: string;
  infoSubtle: string;
  infoText: string;
  /** Focus ring: at least 3:1 against surface and bg. */
  focus: string;
  nav: string;
  navText: string;
  navTextMuted: string;
  navActive: string;
  navActiveText: string;
  skeleton: string;
  chartLine: string;
  chartLineAlt: string;
  chartGrid: string;
  /** Labelled floor line (for example a minimum balance) in charts. */
  chartFloor: string;
  /** Modal scrim. Plain translucent colour, never a blur. */
  overlay: string;
  /** Topic or section accents: strong colour (lines, markers) and readable text on its subtle tint. */
  accent1: string;
  accent1Subtle: string;
  accent1Text: string;
  accent2: string;
  accent2Subtle: string;
  accent2Text: string;
  accent3: string;
  accent3Subtle: string;
  accent3Text: string;
  accent4: string;
  accent4Subtle: string;
  accent4Text: string;
}

export interface ThemeDefinition {
  name: ThemeName;
  label: string;
  /** What the four accents mean in this app (labels for docs and the gallery). */
  accentNames: [string, string, string, string];
  light: ColorRoles;
  dark: ColorRoles;
}

const baseLight: ColorRoles = {
  bg: "#f8fafc",
  surface: "#ffffff",
  surfaceSunken: "#f1f5f9",
  border: "#e2e8f0",
  borderStrong: "#cbd5e1",
  control: "#64748b",
  text: "#0f172a",
  textMuted: "#475569",
  primary: "#1e293b",
  primaryHover: "#0f172a",
  onPrimary: "#ffffff",
  primarySubtle: "#f1f5f9",
  primaryText: "#1e293b",
  danger: "#be123c",
  dangerHover: "#9f1239",
  onDanger: "#ffffff",
  dangerSubtle: "#fff1f2",
  dangerText: "#be123c",
  successSubtle: "#ecfdf5",
  successText: "#047857",
  warningSubtle: "#fffbeb",
  warningText: "#b45309",
  infoSubtle: "#eff6ff",
  infoText: "#1d4ed8",
  focus: "#2563eb",
  nav: "#ffffff",
  navText: "#0f172a",
  navTextMuted: "#475569",
  navActive: "#f1f5f9",
  navActiveText: "#0f172a",
  skeleton: "#e2e8f0",
  chartLine: "#334155",
  chartLineAlt: "#2563eb",
  chartGrid: "#e2e8f0",
  chartFloor: "#b45309",
  overlay: "rgb(15 23 42 / 0.45)",
  accent1: "#047857",
  accent1Subtle: "#ecfdf5",
  accent1Text: "#065f46",
  accent2: "#b45309",
  accent2Subtle: "#fffbeb",
  accent2Text: "#92400e",
  accent3: "#1d4ed8",
  accent3Subtle: "#eff6ff",
  accent3Text: "#1e40af",
  accent4: "#be123c",
  accent4Subtle: "#fff1f2",
  accent4Text: "#9f1239",
};

const baseDark: ColorRoles = {
  bg: "#0b1220",
  surface: "#111a2b",
  surfaceSunken: "#172236",
  border: "#1f2b40",
  borderStrong: "#2c3a52",
  control: "#7c8aa3",
  text: "#f1f5f9",
  textMuted: "#a3b1c6",
  primary: "#e2e8f0",
  primaryHover: "#f8fafc",
  onPrimary: "#0b1220",
  primarySubtle: "#1e293b",
  primaryText: "#e2e8f0",
  danger: "#fb7185",
  dangerHover: "#fda4af",
  onDanger: "#0b1220",
  dangerSubtle: "#3e1721",
  dangerText: "#fda4af",
  successSubtle: "#0f3328",
  successText: "#6ee7b7",
  warningSubtle: "#3a2a10",
  warningText: "#fcd34d",
  infoSubtle: "#142944",
  infoText: "#93c5fd",
  focus: "#60a5fa",
  nav: "#0f1726",
  navText: "#f1f5f9",
  navTextMuted: "#a3b1c6",
  navActive: "#1e293b",
  navActiveText: "#f8fafc",
  skeleton: "#1f2b40",
  chartLine: "#cbd5e1",
  chartLineAlt: "#60a5fa",
  chartGrid: "#1f2b40",
  chartFloor: "#fbbf24",
  overlay: "rgb(2 6 23 / 0.65)",
  accent1: "#34d399",
  accent1Subtle: "#0f3328",
  accent1Text: "#6ee7b7",
  accent2: "#fbbf24",
  accent2Subtle: "#3a2a10",
  accent2Text: "#fcd34d",
  accent3: "#60a5fa",
  accent3Subtle: "#142944",
  accent3Text: "#93c5fd",
  accent4: "#fb7185",
  accent4Subtle: "#3e1721",
  accent4Text: "#fda4af",
};

export const THEMES: Record<ThemeName, ThemeDefinition> = {
  base: {
    name: "base",
    label: "Nexus neutral",
    accentNames: ["Green", "Amber", "Blue", "Rose"],
    light: baseLight,
    dark: baseDark,
  },
  finhub: {
    name: "finhub",
    label: "FinHub",
    accentNames: ["Cash", "Payments", "Markets", "Research"],
    light: {
      ...baseLight,
      primary: "#0f766e",
      primaryHover: "#115e59",
      primarySubtle: "#f0fdfa",
      primaryText: "#0f766e",
      focus: "#0284c7",
      nav: "#08282b",
      navText: "#ffffff",
      navTextMuted: "#99f6e4",
      navActive: "#134e4a",
      navActiveText: "#ffffff",
      chartLine: "#0f766e",
      chartLineAlt: "#0284c7",
      accent1: "#047857",
      accent1Subtle: "#ecfdf5",
      accent1Text: "#065f46",
      accent2: "#c2410c",
      accent2Subtle: "#fff7ed",
      accent2Text: "#9a3412",
      accent3: "#1d4ed8",
      accent3Subtle: "#eff6ff",
      accent3Text: "#1e40af",
      accent4: "#e11d48",
      accent4Subtle: "#fff1f2",
      accent4Text: "#9f1239",
    },
    dark: {
      ...baseDark,
      bg: "#090e17",
      surface: "#0f172a",
      surfaceSunken: "#162036",
      border: "#1e293b",
      borderStrong: "#334155",
      primary: "#2dd4bf",
      primaryHover: "#5eead4",
      onPrimary: "#042f2e",
      primarySubtle: "#0d3532",
      primaryText: "#5eead4",
      focus: "#38bdf8",
      nav: "#05181a",
      navText: "#f8fafc",
      navTextMuted: "#99f6e4",
      navActive: "#134e4a",
      navActiveText: "#ffffff",
      chartLine: "#2dd4bf",
      chartLineAlt: "#38bdf8",
      chartGrid: "#1e293b",
      accent1: "#34d399",
      accent1Subtle: "#13382c",
      accent1Text: "#6ee7b7",
      accent2: "#fbbf24",
      accent2Subtle: "#3d2b12",
      accent2Text: "#fcd34d",
      accent3: "#60a5fa",
      accent3Subtle: "#142944",
      accent3Text: "#93c5fd",
      accent4: "#fb7185",
      accent4Subtle: "#3e1721",
      accent4Text: "#fda4af",
    },
  },
  tandempath: {
    name: "tandempath",
    label: "TandemPath",
    accentNames: ["Applied", "Interview", "Offer", "Closed"],
    light: {
      ...baseLight,
      bg: "#f6f8fb",
      surfaceSunken: "#f8fafc",
      primary: "#2563eb",
      primaryHover: "#1d4ed8",
      primarySubtle: "#eff6ff",
      primaryText: "#1d4ed8",
      focus: "#276552",
      navActive: "#eff6ff",
      navActiveText: "#1d4ed8",
      chartLine: "#2563eb",
      chartLineAlt: "#276552",
      accent1: "#2563eb",
      accent1Subtle: "#eff6ff",
      accent1Text: "#1d4ed8",
      accent2: "#276552",
      accent2Subtle: "#ecfdf5",
      accent2Text: "#276552",
      accent3: "#b45309",
      accent3Subtle: "#fffbeb",
      accent3Text: "#92400e",
      accent4: "#64748b",
      accent4Subtle: "#f1f5f9",
      accent4Text: "#334155",
    },
    dark: {
      ...baseDark,
      primary: "#60a5fa",
      primaryHover: "#93c5fd",
      onPrimary: "#0b1220",
      primarySubtle: "#142944",
      primaryText: "#93c5fd",
      focus: "#4ade80",
      navActive: "#142944",
      navActiveText: "#bfdbfe",
      chartLine: "#60a5fa",
      chartLineAlt: "#4ade80",
      accent1: "#60a5fa",
      accent1Subtle: "#142944",
      accent1Text: "#93c5fd",
      accent2: "#4ade80",
      accent2Subtle: "#10301f",
      accent2Text: "#86efac",
      accent3: "#fbbf24",
      accent3Subtle: "#3a2a10",
      accent3Text: "#fcd34d",
      accent4: "#94a3b8",
      accent4Subtle: "#1e293b",
      accent4Text: "#cbd5e1",
    },
  },
  predictiveeconomics: {
    name: "predictiveeconomics",
    label: "PredictiveEconomics",
    accentNames: ["Bullish", "Watch", "Markets", "Stress"],
    light: {
      ...baseLight,
      bg: "#f8fbfd",
      text: "#0d2340",
      textMuted: "#4a6078",
      primary: "#276b98",
      primaryHover: "#1f5679",
      primarySubtle: "#edf7fc",
      primaryText: "#1f5679",
      focus: "#2f78a8",
      nav: "#1f5679",
      navText: "#ffffff",
      navTextMuted: "#e1f1fa",
      navActive: "#16405c",
      navActiveText: "#ffffff",
      chartLine: "#2f78a8",
      chartLineAlt: "#c2410c",
      accent1: "#047857",
      accent1Subtle: "#ecfdf5",
      accent1Text: "#065f46",
      accent2: "#a16207",
      accent2Subtle: "#fff0ba",
      accent2Text: "#713f12",
      accent3: "#2f78a8",
      accent3Subtle: "#edf7fc",
      accent3Text: "#1f5679",
      accent4: "#c2410c",
      accent4Subtle: "#ffe8d6",
      accent4Text: "#9a3412",
    },
    dark: {
      ...baseDark,
      bg: "#08192c",
      surface: "#0d2236",
      surfaceSunken: "#132c45",
      border: "#1b3653",
      borderStrong: "#27445f",
      control: "#7f98b0",
      text: "#e8f3ff",
      textMuted: "#a9c0d5",
      primary: "#68abd0",
      primaryHover: "#8cc1de",
      onPrimary: "#08192c",
      primarySubtle: "#12324d",
      primaryText: "#8cc1de",
      focus: "#7cc4ec",
      nav: "#0a2037",
      navText: "#e8f3ff",
      navTextMuted: "#a9c0d5",
      navActive: "#16405c",
      navActiveText: "#ffffff",
      skeleton: "#1b3653",
      chartLine: "#68abd0",
      chartLineAlt: "#ffb477",
      chartGrid: "#1b3653",
      accent1: "#34d399",
      accent1Subtle: "#0f3328",
      accent1Text: "#6ee7b7",
      accent2: "#fde68a",
      accent2Subtle: "#3a3010",
      accent2Text: "#fde68a",
      accent3: "#68abd0",
      accent3Subtle: "#12324d",
      accent3Text: "#a5d2ea",
      accent4: "#ffb477",
      accent4Subtle: "#3d2412",
      accent4Text: "#fdc597",
    },
  },
  commandcenter: {
    name: "commandcenter",
    label: "CommandCenter",
    accentNames: ["OK", "Warn", "Info", "Bad"],
    light: {
      ...baseLight,
      bg: "#f6f7f9",
      surfaceSunken: "#f2f4f7",
      border: "#e4e7ec",
      borderStrong: "#d0d5dd",
      control: "#667085",
      text: "#1c2430",
      textMuted: "#535d6e",
      primary: "#2557d6",
      primaryHover: "#1d46b0",
      primarySubtle: "#eef3ff",
      primaryText: "#2048b8",
      focus: "#2557d6",
      navActive: "#eef3ff",
      navActiveText: "#2048b8",
      successSubtle: "#e3f4e8",
      successText: "#136d33",
      warningSubtle: "#fdf1d6",
      warningText: "#8a5a00",
      dangerSubtle: "#fde7e5",
      dangerText: "#b42318",
      danger: "#b42318",
      dangerHover: "#912018",
      chartLine: "#2557d6",
      accent1: "#157f3b",
      accent1Subtle: "#e3f4e8",
      accent1Text: "#136d33",
      accent2: "#8a5a00",
      accent2Subtle: "#fdf1d6",
      accent2Text: "#8a5a00",
      accent3: "#2557d6",
      accent3Subtle: "#eef3ff",
      accent3Text: "#2048b8",
      accent4: "#b42318",
      accent4Subtle: "#fde7e5",
      accent4Text: "#b42318",
    },
    dark: {
      ...baseDark,
      bg: "#0f141b",
      surface: "#171e27",
      surfaceSunken: "#1d2531",
      border: "#2a3441",
      borderStrong: "#36414f",
      control: "#8590a2",
      text: "#e6eaf0",
      textMuted: "#a2abba",
      primary: "#8fb0ff",
      primaryHover: "#b3c9ff",
      onPrimary: "#0f141b",
      primarySubtle: "#1b2945",
      primaryText: "#a9c1ff",
      focus: "#8fb0ff",
      navActive: "#1b2945",
      navActiveText: "#c7d7ff",
      successSubtle: "#12301d",
      successText: "#6fd391",
      warningSubtle: "#352a0e",
      warningText: "#f1c25b",
      dangerSubtle: "#3a1614",
      dangerText: "#ff8a80",
      danger: "#ff8a80",
      dangerHover: "#ffaba3",
      onDanger: "#0f141b",
      chartLine: "#8fb0ff",
      chartGrid: "#2a3441",
      accent1: "#6fd391",
      accent1Subtle: "#12301d",
      accent1Text: "#6fd391",
      accent2: "#f1c25b",
      accent2Subtle: "#352a0e",
      accent2Text: "#f1c25b",
      accent3: "#8fb0ff",
      accent3Subtle: "#1b2945",
      accent3Text: "#a9c1ff",
      accent4: "#ff8a80",
      accent4Subtle: "#3a1614",
      accent4Text: "#ff8a80",
    },
  },
  klassesall: {
    name: "klassesall",
    label: "klassesall",
    accentNames: ["Lesson", "Streak", "Listening", "Review"],
    light: {
      ...baseLight,
      bg: "#f6f7f9",
      surfaceSunken: "#f1f3f6",
      border: "#e6e9ee",
      borderStrong: "#d4d9e0",
      control: "#6b7686",
      text: "#0b1220",
      textMuted: "#5f6b7c",
      primary: "#5b53e6",
      primaryHover: "#4b43cf",
      primarySubtle: "#eef0fe",
      primaryText: "#4b43cf",
      focus: "#5b53e6",
      navActive: "#eef0fe",
      navActiveText: "#3f38b8",
      successSubtle: "#e6f6ef",
      successText: "#0b7a56",
      warningSubtle: "#fbf3e2",
      warningText: "#8f5d10",
      danger: "#c41d3c",
      dangerHover: "#a3172f",
      dangerSubtle: "#fdeaee",
      dangerText: "#c41d3c",
      chartLine: "#5b53e6",
      chartLineAlt: "#c47f0e",
      accent1: "#5b53e6",
      accent1Subtle: "#eef0fe",
      accent1Text: "#3f38b8",
      accent2: "#c47f0e",
      accent2Subtle: "#fdf1de",
      accent2Text: "#8a5a12",
      accent3: "#0b7a56",
      accent3Subtle: "#e6f6ef",
      accent3Text: "#0b7a56",
      accent4: "#c41d3c",
      accent4Subtle: "#fdeaee",
      accent4Text: "#a3172f",
    },
    dark: {
      ...baseDark,
      bg: "#0d0f1a",
      surface: "#151829",
      surfaceSunken: "#1c2036",
      border: "#252a44",
      borderStrong: "#323858",
      control: "#8a90b4",
      text: "#eef0fb",
      textMuted: "#a8adc8",
      primary: "#a5a0f2",
      primaryHover: "#c2befa",
      onPrimary: "#0d0f1a",
      primarySubtle: "#24224a",
      primaryText: "#c2befa",
      focus: "#a5a0f2",
      nav: "#11131f",
      navActive: "#24224a",
      navActiveText: "#d9d6ff",
      chartLine: "#a5a0f2",
      chartLineAlt: "#f5a623",
      chartGrid: "#252a44",
      accent1: "#a5a0f2",
      accent1Subtle: "#24224a",
      accent1Text: "#c2befa",
      accent2: "#f5a623",
      accent2Subtle: "#3a2a10",
      accent2Text: "#fcd34d",
      accent3: "#34d399",
      accent3Subtle: "#0f3328",
      accent3Text: "#6ee7b7",
      accent4: "#fb7185",
      accent4Subtle: "#3e1721",
      accent4Text: "#fda4af",
    },
  },
};
