import React from "react";

/** Content for screen readers only (still in the accessibility tree). */
export function VisuallyHidden({ children, as: Tag = "span" }: { children: React.ReactNode; as?: "span" | "div" }) {
  return <Tag className="nx-visually-hidden">{children}</Tag>;
}
