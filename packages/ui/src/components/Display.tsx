import React from "react";

import { cx, type Tone } from "../utils.js";

export interface CardProps extends Omit<React.HTMLAttributes<HTMLElement>, "title"> {
  title?: React.ReactNode;
  /** Short line under the title. */
  description?: React.ReactNode;
  /** Actions shown at the end of the header (a quiet button or a link). */
  actions?: React.ReactNode;
  footer?: React.ReactNode;
  /** Topic accent shown as a thin rule on the start edge. */
  accent?: Extract<Tone, "accent1" | "accent2" | "accent3" | "accent4" | "primary">;
  /** Heading level for the title (default 2). */
  headingLevel?: 2 | 3 | 4;
  /** Remove body padding (for full bleed tables). */
  flush?: boolean;
}

/** White surface with a hairline border and a faint shadow. */
export function Card({
  title,
  description,
  actions,
  footer,
  accent,
  headingLevel = 2,
  flush = false,
  className,
  children,
  ...rest
}: CardProps) {
  const Heading = `h${headingLevel}` as "h2" | "h3" | "h4";
  return (
    <section className={cx("nx-card", accent && `nx-card--${accent}`, className)} {...rest}>
      {title || actions ? (
        <header className="nx-card__header">
          <div className="nx-card__heading">
            {title ? <Heading className="nx-card__title">{title}</Heading> : null}
            {description ? <p className="nx-card__description">{description}</p> : null}
          </div>
          {actions ? <div className="nx-card__actions">{actions}</div> : null}
        </header>
      ) : null}
      <div className={cx("nx-card__body", flush && "nx-card__body--flush")}>{children}</div>
      {footer ? <footer className="nx-card__footer">{footer}</footer> : null}
    </section>
  );
}

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  tone?: Tone;
}

/** Short status label. Colour is never the only signal: keep the text meaningful. */
export function Badge({ tone = "neutral", className, children, ...rest }: BadgeProps) {
  return (
    <span className={cx("nx-badge", `nx-badge--${tone}`, className)} {...rest}>
      {children}
    </span>
  );
}

export interface StatProps extends React.HTMLAttributes<HTMLDivElement> {
  label: string;
  /** The one number, already formatted (for example "1,240.50 EUR"). */
  value: React.ReactNode;
  /** Context under the number (period, comparison, source). */
  hint?: React.ReactNode;
  /** Optional status line, for example "Below floor". */
  status?: { tone: Tone; label: string };
}

/** One number with its label: tabular figures, no decoration. */
export function Stat({ label, value, hint, status, className, ...rest }: StatProps) {
  return (
    <div className={cx("nx-stat", className)} {...rest}>
      <dl className="nx-stat__list">
        <dt className="nx-stat__label">{label}</dt>
        <dd className="nx-stat__value">{value}</dd>
      </dl>
      {status ? <Badge tone={status.tone}>{status.label}</Badge> : null}
      {hint ? <p className="nx-stat__hint">{hint}</p> : null}
    </div>
  );
}

export interface SkeletonRowsProps {
  rows?: number;
  columns?: number;
  /** Announced to screen readers while loading. */
  label?: string;
  className?: string;
}

/** Placeholder rows shown instead of a spinner while data loads. */
export function SkeletonRows({ rows = 3, columns = 3, label = "Loading", className }: SkeletonRowsProps) {
  return (
    <div className={cx("nx-skeleton", className)} role="status" aria-busy="true">
      <span className="nx-visually-hidden">{label}</span>
      {Array.from({ length: rows }, (_, r) => (
        <div className="nx-skeleton__row" key={r} aria-hidden="true">
          {Array.from({ length: columns }, (__, c) => (
            <span key={c} className={cx("nx-skeleton__cell", c === columns - 1 && "nx-skeleton__cell--end")} />
          ))}
        </div>
      ))}
    </div>
  );
}

export interface EmptyStateProps {
  title: string;
  description?: React.ReactNode;
  action?: React.ReactNode;
  /** Optional plain line icon (no illustrations). */
  icon?: React.ReactNode;
  className?: string;
}

/** Nothing to show yet: says why and offers the next step. */
export function EmptyState({ title, description, action, icon, className }: EmptyStateProps) {
  return (
    <div className={cx("nx-state", className)}>
      {icon ? (
        <span className="nx-state__icon" aria-hidden="true">
          {icon}
        </span>
      ) : null}
      <p className="nx-state__title">{title}</p>
      {description ? <p className="nx-state__description">{description}</p> : null}
      {action ? <div className="nx-state__action">{action}</div> : null}
    </div>
  );
}

export interface ErrorStateProps {
  title?: string;
  description?: React.ReactNode;
  onRetry?: () => void;
  retryLabel?: string;
  className?: string;
}

/** A failed load, announced to screen readers, with an optional retry. */
export function ErrorState({
  title = "This could not be loaded",
  description,
  onRetry,
  retryLabel = "Try again",
  className,
}: ErrorStateProps) {
  return (
    <div className={cx("nx-state", "nx-state--error", className)} role="alert">
      <p className="nx-state__title">{title}</p>
      {description ? <p className="nx-state__description">{description}</p> : null}
      {onRetry ? (
        <div className="nx-state__action">
          <button type="button" className="nx-btn nx-btn--secondary" onClick={onRetry}>
            <span className="nx-btn__label">{retryLabel}</span>
          </button>
        </div>
      ) : null}
    </div>
  );
}
