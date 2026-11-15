import React, { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";

import { cx } from "../utils.js";
import { IconButton } from "./Button.js";

export type ToastTone = "neutral" | "success" | "warning" | "danger" | "info";

export interface ToastOptions {
  title: string;
  description?: React.ReactNode;
  tone?: ToastTone;
  /** Milliseconds before it closes on its own; 0 keeps it until dismissed. Danger toasts default to 0. */
  duration?: number;
  action?: { label: string; onClick: () => void };
}

interface ToastEntry extends ToastOptions {
  id: number;
}

interface ToastApi {
  toast: (options: ToastOptions) => number;
  dismiss: (id: number) => void;
}

const ToastContext = createContext<ToastApi | null>(null);

/** Access ``toast()`` and ``dismiss()``. Must be used inside ``ToastProvider``. */
export function useToast(): ToastApi {
  const api = useContext(ToastContext);
  if (!api) throw new Error("useToast must be used inside <ToastProvider>");
  return api;
}

function DismissIcon() {
  return (
    <svg viewBox="0 0 16 16" width="14" height="14" focusable="false">
      <path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" fill="none" />
    </svg>
  );
}

function ToastItem({ entry, onDismiss, dismissLabel }: { entry: ToastEntry; onDismiss: () => void; dismissLabel: string }) {
  const duration = entry.duration ?? (entry.tone === "danger" ? 0 : 6000);
  const [paused, setPaused] = useState(false);
  const dismissRef = useRef(onDismiss);
  useEffect(() => {
    dismissRef.current = onDismiss;
  });

  useEffect(() => {
    if (duration <= 0 || paused) return;
    const timer = setTimeout(() => dismissRef.current(), duration);
    return () => clearTimeout(timer);
  }, [duration, paused]);

  return (
    <div
      className={cx("nx-toast", `nx-toast--${entry.tone ?? "neutral"}`)}
      // Hovering or focusing a toast pauses its timer (WCAG 2.2.1, timing adjustable).
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
      onFocus={() => setPaused(true)}
      onBlur={() => setPaused(false)}
    >
      <div className="nx-toast__content">
        <p className="nx-toast__title">{entry.title}</p>
        {entry.description ? <p className="nx-toast__description">{entry.description}</p> : null}
      </div>
      {entry.action ? (
        <button
          type="button"
          className="nx-btn nx-btn--quiet nx-btn--sm"
          onClick={() => {
            entry.action?.onClick();
            onDismiss();
          }}
        >
          <span className="nx-btn__label">{entry.action.label}</span>
        </button>
      ) : null}
      <IconButton label={dismissLabel} icon={<DismissIcon />} size="sm" onClick={onDismiss} />
    </div>
  );
}

export interface ToastProviderProps {
  children: React.ReactNode;
  /** Label of each toast's close button. */
  dismissLabel?: string;
  /** Name of the notification region. */
  regionLabel?: string;
}

/**
 * Renders two live regions that exist before any toast appears (so screen readers announce them):
 * a polite one for ordinary messages and an assertive one for danger.
 */
export function ToastProvider({ children, dismissLabel = "Dismiss notification", regionLabel = "Notifications" }: ToastProviderProps) {
  const [toasts, setToasts] = useState<ToastEntry[]>([]);
  const nextId = useRef(1);

  const dismiss = useCallback((id: number) => setToasts((list) => list.filter((t) => t.id !== id)), []);
  const toast = useCallback((options: ToastOptions) => {
    const id = nextId.current++;
    setToasts((list) => [...list, { ...options, id }]);
    return id;
  }, []);
  const api = useMemo(() => ({ toast, dismiss }), [toast, dismiss]);

  const render = (urgent: boolean) =>
    toasts
      .filter((t) => (t.tone === "danger") === urgent)
      .map((t) => <ToastItem key={t.id} entry={t} onDismiss={() => dismiss(t.id)} dismissLabel={dismissLabel} />);

  return (
    <ToastContext.Provider value={api}>
      {children}
      <section className="nx-toast-region" aria-label={regionLabel}>
        <div role="status" aria-live="polite" className="nx-toast-region__list">
          {render(false)}
        </div>
        <div role="alert" aria-live="assertive" className="nx-toast-region__list">
          {render(true)}
        </div>
      </section>
    </ToastContext.Provider>
  );
}
