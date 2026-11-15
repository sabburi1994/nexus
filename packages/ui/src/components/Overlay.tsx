import React, { useEffect, useId, useRef } from "react";

import { cx } from "../utils.js";
import { IconButton } from "./Button.js";

const FOCUSABLE_PARTS = [
  "a[href]",
  "button:not([disabled])",
  'input:not([disabled]):not([type="hidden"])',
  "select:not([disabled])",
  "textarea:not([disabled])",
  '[tabindex]:not([tabindex="-1"])',
];
const FOCUSABLE = FOCUSABLE_PARTS.join(", ");
// First choice for initial focus: something inside the body, not the header's Close button.
const BODY_FOCUSABLE = FOCUSABLE_PARTS.map((s) => `.nx-overlay__body ${s}`).join(", ");

function CloseIcon() {
  return (
    <svg viewBox="0 0 16 16" width="16" height="16" focusable="false">
      <path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" fill="none" />
    </svg>
  );
}

/**
 * Drives a native ``<dialog>`` from React state: ``showModal`` when open (focus is trapped and the page
 * behind is inert), Escape and backdrop clicks call ``onClose``, focus returns to the trigger on close.
 */
function useModal(open: boolean, onClose: () => void) {
  const ref = useRef<HTMLDialogElement>(null);
  const returnFocus = useRef<HTMLElement | null>(null);
  const onCloseRef = useRef(onClose);
  useEffect(() => {
    onCloseRef.current = onClose;
  });

  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (open && !dialog.open) {
      returnFocus.current = document.activeElement instanceof HTMLElement ? document.activeElement : null;
      if (typeof dialog.showModal === "function") dialog.showModal();
      else dialog.setAttribute("open", "");
      const preferred =
        dialog.querySelector<HTMLElement>("[data-autofocus]") ??
        dialog.querySelector<HTMLElement>(BODY_FOCUSABLE) ??
        dialog.querySelector<HTMLElement>(FOCUSABLE);
      preferred?.focus();
    } else if (!open && dialog.open) {
      if (typeof dialog.close === "function") dialog.close();
      else dialog.removeAttribute("open");
      returnFocus.current?.focus();
      returnFocus.current = null;
    }
  }, [open]);

  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    const onCancel = (event: Event) => {
      // Escape: keep React in charge of the open state.
      event.preventDefault();
      onCloseRef.current();
    };
    dialog.addEventListener("cancel", onCancel);
    return () => dialog.removeEventListener("cancel", onCancel);
  }, []);

  useEffect(
    () => () => {
      // Unmounted while open: give focus back.
      if (ref.current?.open) returnFocus.current?.focus();
    },
    [],
  );

  return ref;
}

interface OverlayProps {
  open: boolean;
  onClose: () => void;
  title: string;
  description?: React.ReactNode;
  children?: React.ReactNode;
  /** Buttons at the bottom (primary action last). */
  footer?: React.ReactNode;
  /** Close when the backdrop is clicked (default true). */
  closeOnBackdrop?: boolean;
  closeLabel?: string;
  className?: string;
}

function OverlayFrame({
  kind,
  side,
  open,
  onClose,
  title,
  description,
  children,
  footer,
  closeOnBackdrop = true,
  closeLabel = "Close",
  className,
}: OverlayProps & { kind: "dialog" | "sheet"; side?: "end" | "start" }) {
  const ref = useModal(open, onClose);
  const id = useId().replace(/:/g, "");
  const titleId = `nx-${kind}-${id}-title`;
  const descId = description ? `nx-${kind}-${id}-desc` : undefined;

  return (
    // The dialog element handles keyboard (Escape) natively; the click handler only covers the backdrop.
    // eslint-disable-next-line jsx-a11y/click-events-have-key-events, jsx-a11y/no-noninteractive-element-interactions
    <dialog
      ref={ref}
      className={cx("nx-overlay", `nx-${kind}`, side && `nx-sheet--${side}`, className)}
      aria-labelledby={titleId}
      aria-describedby={descId}
      onClick={(event) => {
        if (closeOnBackdrop && event.target === event.currentTarget) onClose();
      }}
    >
      {open ? (
        <div className="nx-overlay__panel">
          <header className="nx-overlay__header">
            <div>
              <h2 id={titleId} className="nx-overlay__title">
                {title}
              </h2>
              {description ? (
                <p id={descId} className="nx-overlay__description">
                  {description}
                </p>
              ) : null}
            </div>
            <IconButton label={closeLabel} icon={<CloseIcon />} onClick={onClose} className="nx-overlay__close" />
          </header>
          <div className="nx-overlay__body">{children}</div>
          {footer ? <footer className="nx-overlay__footer">{footer}</footer> : null}
        </div>
      ) : null}
    </dialog>
  );
}

export type DialogProps = OverlayProps;

/** Centered modal for a decision or a short form. */
export function Dialog(props: DialogProps) {
  return <OverlayFrame kind="dialog" {...props} />;
}

export interface SheetProps extends OverlayProps {
  /** Edge it slides from on wide screens (default end). On phones it is a bottom sheet. */
  side?: "end" | "start";
}

/** Side panel for details on the same page (a bottom sheet on phones). */
export function Sheet({ side = "end", ...props }: SheetProps) {
  return <OverlayFrame kind="sheet" side={side} {...props} />;
}
