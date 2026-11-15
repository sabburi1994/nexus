import React from "react";

import { cx } from "../utils.js";

export type ButtonVariant = "primary" | "secondary" | "quiet" | "danger";
export type ButtonSize = "md" | "sm";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /** primary: the one main action; secondary: bordered; quiet: text only; danger: destructive. */
  variant?: ButtonVariant;
  /** md is 40 px high (default), sm is 32 px for dense tables. */
  size?: ButtonSize;
  /** Shows a busy state, disables the button and sets aria-busy. */
  loading?: boolean;
  iconStart?: React.ReactNode;
  iconEnd?: React.ReactNode;
  fullWidth?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  {
    variant = "secondary",
    size = "md",
    loading = false,
    iconStart,
    iconEnd,
    fullWidth = false,
    type = "button",
    disabled,
    className,
    children,
    ...rest
  },
  ref,
) {
  return (
    <button
      ref={ref}
      type={type}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      className={cx(
        "nx-btn",
        `nx-btn--${variant}`,
        size === "sm" && "nx-btn--sm",
        fullWidth && "nx-btn--full",
        loading && "nx-btn--loading",
        className,
      )}
      {...rest}
    >
      {iconStart ? (
        <span className="nx-btn__icon" aria-hidden="true">
          {iconStart}
        </span>
      ) : null}
      <span className="nx-btn__label">{children}</span>
      {iconEnd ? (
        <span className="nx-btn__icon" aria-hidden="true">
          {iconEnd}
        </span>
      ) : null}
    </button>
  );
});

export interface IconButtonProps extends Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, "aria-label" | "children"> {
  /** Accessible name; also shown as the native tooltip. Required: an icon alone has no name. */
  label: string;
  /** The icon (an inline SVG). Hidden from assistive technology. */
  icon: React.ReactNode;
  variant?: ButtonVariant;
  size?: ButtonSize;
}

export const IconButton = React.forwardRef<HTMLButtonElement, IconButtonProps>(function IconButton(
  { label, icon, variant = "quiet", size = "md", type = "button", className, title, ...rest },
  ref,
) {
  return (
    <button
      ref={ref}
      type={type}
      aria-label={label}
      title={title ?? label}
      className={cx("nx-btn", "nx-icon-btn", `nx-btn--${variant}`, size === "sm" && "nx-btn--sm", className)}
      {...rest}
    >
      <span className="nx-btn__icon" aria-hidden="true">
        {icon}
      </span>
    </button>
  );
});
