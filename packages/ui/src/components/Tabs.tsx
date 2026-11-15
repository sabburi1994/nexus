import React, { useId, useRef, useState } from "react";

import { cx } from "../utils.js";

export interface TabItem {
  id: string;
  label: React.ReactNode;
  content: React.ReactNode;
  disabled?: boolean;
}

export interface TabsProps {
  /** Accessible name of the tab list. */
  label: string;
  items: TabItem[];
  value?: string;
  defaultValue?: string;
  onChange?: (id: string) => void;
  className?: string;
}

/**
 * WAI-ARIA tabs with automatic activation: Left and Right move and select, Home and End jump,
 * only the selected tab is in the tab order.
 */
export function Tabs({ label, items, value, defaultValue, onChange, className }: TabsProps) {
  const base = useId().replace(/:/g, "");
  const enabled = items.filter((i) => !i.disabled);
  const [internal, setInternal] = useState(defaultValue ?? enabled[0]?.id);
  const selected = value ?? internal;
  const tabRefs = useRef(new Map<string, HTMLButtonElement>());

  const select = (id: string, focus = false) => {
    if (value === undefined) setInternal(id);
    onChange?.(id);
    if (focus) tabRefs.current.get(id)?.focus();
  };

  const onKeyDown = (event: React.KeyboardEvent<HTMLButtonElement>, id: string) => {
    const index = enabled.findIndex((i) => i.id === id);
    let next: TabItem | undefined;
    if (event.key === "ArrowRight") next = enabled[(index + 1) % enabled.length];
    else if (event.key === "ArrowLeft") next = enabled[(index - 1 + enabled.length) % enabled.length];
    else if (event.key === "Home") next = enabled[0];
    else if (event.key === "End") next = enabled[enabled.length - 1];
    if (next) {
      event.preventDefault();
      select(next.id, true);
    }
  };

  return (
    <div className={cx("nx-tabs", className)}>
      <div role="tablist" aria-label={label} className="nx-tabs__list">
        {items.map((item) => {
          const isSelected = item.id === selected;
          return (
            <button
              key={item.id}
              ref={(el) => {
                if (el) tabRefs.current.set(item.id, el);
                else tabRefs.current.delete(item.id);
              }}
              type="button"
              role="tab"
              id={`nx-tab-${base}-${item.id}`}
              aria-selected={isSelected}
              aria-controls={`nx-tabpanel-${base}-${item.id}`}
              tabIndex={isSelected ? 0 : -1}
              disabled={item.disabled}
              className={cx("nx-tabs__tab", isSelected && "nx-tabs__tab--selected")}
              onClick={() => select(item.id)}
              onKeyDown={(e) => onKeyDown(e, item.id)}
            >
              {item.label}
            </button>
          );
        })}
      </div>
      {items.map((item) => (
        <div
          key={item.id}
          role="tabpanel"
          id={`nx-tabpanel-${base}-${item.id}`}
          aria-labelledby={`nx-tab-${base}-${item.id}`}
          hidden={item.id !== selected}
          tabIndex={0}
          className="nx-tabs__panel"
        >
          {item.id === selected ? item.content : null}
        </div>
      ))}
    </div>
  );
}
