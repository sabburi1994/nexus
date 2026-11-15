import React from "react";

import { cx } from "../utils.js";

export interface NavItem {
  id: string;
  label: string;
  /** Plain line icon (inline SVG), hidden from assistive technology. */
  icon?: React.ReactNode;
  /** Link target. Without href the item is a button calling onSelect. */
  href?: string;
  current?: boolean;
}

export interface AppShellProps {
  /** App name or logo at the top of the rail and the header. */
  brand: React.ReactNode;
  nav: NavItem[];
  onNavigate?: (id: string) => void;
  /** Header actions (theme switch, account, search). */
  actions?: React.ReactNode;
  /** Page title shown in the header. */
  title?: React.ReactNode;
  navLabel?: string;
  skipLinkLabel?: string;
  /** id of the main element (skip link target). */
  mainId?: string;
  children: React.ReactNode;
  className?: string;
}

/**
 * Navigation shell, mobile first: on phones a bottom bar with the spaces (up to five), from the md
 * breakpoint a side rail. One nav landmark either way, a skip link to the main content, and
 * aria-current on the active item.
 */
export function AppShell({
  brand,
  nav,
  onNavigate,
  actions,
  title,
  navLabel = "Main",
  skipLinkLabel = "Skip to content",
  mainId = "nx-main",
  children,
  className,
}: AppShellProps) {
  return (
    <div className={cx("nx-shell", className)}>
      <a className="nx-skip-link" href={`#${mainId}`}>
        {skipLinkLabel}
      </a>
      <nav className="nx-shell__nav" aria-label={navLabel}>
        <div className="nx-shell__brand">{brand}</div>
        <ul className="nx-shell__nav-list">
          {nav.map((item) => {
            const content = (
              <>
                {item.icon ? (
                  <span className="nx-shell__nav-icon" aria-hidden="true">
                    {item.icon}
                  </span>
                ) : null}
                <span className="nx-shell__nav-label">{item.label}</span>
              </>
            );
            const itemClass = cx("nx-shell__nav-item", item.current && "nx-shell__nav-item--current");
            return (
              <li key={item.id}>
                {item.href ? (
                  <a
                    href={item.href}
                    className={itemClass}
                    aria-current={item.current ? "page" : undefined}
                    onClick={onNavigate ? () => onNavigate(item.id) : undefined}
                  >
                    {content}
                  </a>
                ) : (
                  <button
                    type="button"
                    className={itemClass}
                    aria-current={item.current ? "page" : undefined}
                    onClick={() => onNavigate?.(item.id)}
                  >
                    {content}
                  </button>
                )}
              </li>
            );
          })}
        </ul>
      </nav>
      <div className="nx-shell__frame">
        {title || actions ? (
          <header className="nx-shell__header">
            <div className="nx-shell__header-brand">{brand}</div>
            {title ? <h1 className="nx-shell__title">{title}</h1> : null}
            {actions ? <div className="nx-shell__actions">{actions}</div> : null}
          </header>
        ) : null}
        <main id={mainId} className="nx-shell__main" tabIndex={-1}>
          {children}
        </main>
      </div>
    </div>
  );
}
