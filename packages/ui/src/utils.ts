/** Join class names, skipping falsy values. */
export function cx(...parts: Array<string | false | null | undefined>): string {
  return parts.filter(Boolean).join(" ");
}

/** Status and topic tones shared by Badge, Stat, Toast and Card accents. */
export type Tone =
  | "neutral"
  | "primary"
  | "success"
  | "warning"
  | "danger"
  | "info"
  | "accent1"
  | "accent2"
  | "accent3"
  | "accent4";
