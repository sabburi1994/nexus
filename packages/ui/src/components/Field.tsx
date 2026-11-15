import React, { useId } from "react";

import { cx } from "../utils.js";

interface FieldOwnProps {
  /** Visible label (required: placeholders are not labels). */
  label: string;
  /** Helper text under the control. */
  hint?: React.ReactNode;
  /** Error message; marks the control aria-invalid and is announced through aria-describedby. */
  error?: React.ReactNode;
  /** Hide the label visually but keep it for screen readers (for example in a search bar). */
  hideLabel?: boolean;
}

interface FieldIds {
  id: string;
  hintId: string | undefined;
  errorId: string | undefined;
  describedBy: string | undefined;
}

function useFieldIds(explicitId: string | undefined, hint: unknown, error: unknown, extra?: string): FieldIds {
  const auto = useId();
  const id = explicitId ?? `nx-field-${auto.replace(/:/g, "")}`;
  const hintId = hint ? `${id}-hint` : undefined;
  const errorId = error ? `${id}-error` : undefined;
  const describedBy = [hintId, errorId, extra].filter(Boolean).join(" ") || undefined;
  return { id, hintId, errorId, describedBy };
}

function FieldFrame({
  ids,
  label,
  hint,
  error,
  hideLabel,
  required,
  className,
  children,
}: FieldOwnProps & { ids: FieldIds; required?: boolean; className?: string; children: React.ReactNode }) {
  return (
    <div className={cx("nx-field", error ? "nx-field--invalid" : null, className)}>
      <label htmlFor={ids.id} className={cx("nx-field__label", hideLabel && "nx-visually-hidden")}>
        {label}
        {required ? (
          <span className="nx-field__required" aria-hidden="true">
            {" "}
            *
          </span>
        ) : null}
      </label>
      {children}
      {hint ? (
        <p id={ids.hintId} className="nx-field__hint">
          {hint}
        </p>
      ) : null}
      {error ? (
        <p id={ids.errorId} className="nx-field__error">
          {error}
        </p>
      ) : null}
    </div>
  );
}

export interface InputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "size">, FieldOwnProps {
  /** Right align and use tabular figures (amounts, quantities). */
  numeric?: boolean;
  fieldClassName?: string;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(function Input(
  { label, hint, error, hideLabel, numeric, id, className, fieldClassName, required, ...rest },
  ref,
) {
  const ids = useFieldIds(id, hint, error, rest["aria-describedby"]);
  return (
    <FieldFrame ids={ids} label={label} hint={hint} error={error} hideLabel={hideLabel} required={required} className={fieldClassName}>
      <input
        ref={ref}
        id={ids.id}
        required={required}
        aria-invalid={error ? true : undefined}
        aria-describedby={ids.describedBy}
        className={cx("nx-control", numeric && "nx-control--numeric", className)}
        {...rest}
      />
    </FieldFrame>
  );
});

export interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

export interface SelectProps extends Omit<React.SelectHTMLAttributes<HTMLSelectElement>, "size">, FieldOwnProps {
  options: SelectOption[];
  /** Optional first, empty choice such as "Choose a category". */
  placeholder?: string;
  fieldClassName?: string;
}

/** Native select: full keyboard, screen reader and mobile picker support for free. */
export const Select = React.forwardRef<HTMLSelectElement, SelectProps>(function Select(
  { label, hint, error, hideLabel, options, placeholder, id, className, fieldClassName, required, ...rest },
  ref,
) {
  const ids = useFieldIds(id, hint, error, rest["aria-describedby"]);
  return (
    <FieldFrame ids={ids} label={label} hint={hint} error={error} hideLabel={hideLabel} required={required} className={fieldClassName}>
      <div className="nx-select">
        <select
          ref={ref}
          id={ids.id}
          required={required}
          aria-invalid={error ? true : undefined}
          aria-describedby={ids.describedBy}
          className={cx("nx-control", "nx-select__control", className)}
          {...rest}
        >
          {placeholder !== undefined ? <option value="">{placeholder}</option> : null}
          {options.map((o) => (
            <option key={o.value} value={o.value} disabled={o.disabled}>
              {o.label}
            </option>
          ))}
        </select>
        <svg className="nx-select__chevron" viewBox="0 0 16 16" aria-hidden="true" focusable="false">
          <path d="M4 6l4 4 4-4" />
        </svg>
      </div>
    </FieldFrame>
  );
});

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement>, FieldOwnProps {
  fieldClassName?: string;
}

export const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(function Textarea(
  { label, hint, error, hideLabel, id, className, fieldClassName, required, rows = 4, ...rest },
  ref,
) {
  const ids = useFieldIds(id, hint, error, rest["aria-describedby"]);
  return (
    <FieldFrame ids={ids} label={label} hint={hint} error={error} hideLabel={hideLabel} required={required} className={fieldClassName}>
      <textarea
        ref={ref}
        id={ids.id}
        rows={rows}
        required={required}
        aria-invalid={error ? true : undefined}
        aria-describedby={ids.describedBy}
        className={cx("nx-control", "nx-control--textarea", className)}
        {...rest}
      />
    </FieldFrame>
  );
});
