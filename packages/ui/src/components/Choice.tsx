import React, { useId } from "react";

import { cx } from "../utils.js";

interface ChoiceOwnProps {
  label: React.ReactNode;
  hint?: React.ReactNode;
  error?: React.ReactNode;
}

function useIds(explicit: string | undefined, hint: unknown, error: unknown) {
  const auto = useId().replace(/:/g, "");
  const id = explicit ?? `nx-choice-${auto}`;
  const hintId = hint ? `${id}-hint` : undefined;
  const errorId = error ? `${id}-error` : undefined;
  return { id, hintId, errorId, describedBy: [hintId, errorId].filter(Boolean).join(" ") || undefined };
}

export type CheckboxProps = Omit<React.InputHTMLAttributes<HTMLInputElement>, "type"> & ChoiceOwnProps;

/** Native checkbox with a label; Space toggles it. */
export const Checkbox = React.forwardRef<HTMLInputElement, CheckboxProps>(function Checkbox(
  { label, hint, error, id, className, ...rest },
  ref,
) {
  const ids = useIds(id, hint, error);
  return (
    <div className={cx("nx-choice", error ? "nx-choice--invalid" : null, className)}>
      <input
        ref={ref}
        type="checkbox"
        id={ids.id}
        className="nx-choice__input nx-choice__input--checkbox"
        aria-invalid={error ? true : undefined}
        aria-describedby={ids.describedBy}
        {...rest}
      />
      <div className="nx-choice__text">
        <label htmlFor={ids.id} className="nx-choice__label">
          {label}
        </label>
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
    </div>
  );
});

export type SwitchProps = Omit<React.InputHTMLAttributes<HTMLInputElement>, "type" | "role"> & ChoiceOwnProps;

/** On/off setting that applies immediately. A checkbox with role="switch": Space toggles it. */
export const Switch = React.forwardRef<HTMLInputElement, SwitchProps>(function Switch(
  { label, hint, error, id, className, ...rest },
  ref,
) {
  const ids = useIds(id, hint, error);
  return (
    <div className={cx("nx-choice", "nx-switch", error ? "nx-choice--invalid" : null, className)}>
      <input
        ref={ref}
        type="checkbox"
        role="switch"
        id={ids.id}
        className="nx-choice__input nx-switch__input"
        aria-invalid={error ? true : undefined}
        aria-describedby={ids.describedBy}
        {...rest}
      />
      <span className="nx-switch__track" aria-hidden="true">
        <span className="nx-switch__thumb" />
      </span>
      <div className="nx-choice__text">
        <label htmlFor={ids.id} className="nx-choice__label">
          {label}
        </label>
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
    </div>
  );
});

export interface RadioOption {
  value: string;
  label: React.ReactNode;
  hint?: React.ReactNode;
  disabled?: boolean;
}

export interface RadioGroupProps {
  /** Group label (rendered as the fieldset legend). */
  label: string;
  name: string;
  options: RadioOption[];
  value?: string;
  defaultValue?: string;
  onChange?: (value: string) => void;
  hint?: React.ReactNode;
  error?: React.ReactNode;
  required?: boolean;
  /** Lay options out in a row on wide screens. */
  inline?: boolean;
  className?: string;
}

/** Native radios in a fieldset: arrow keys move between options. */
export function RadioGroup({
  label,
  name,
  options,
  value,
  defaultValue,
  onChange,
  hint,
  error,
  required,
  inline,
  className,
}: RadioGroupProps) {
  const ids = useIds(undefined, hint, error);
  return (
    <fieldset
      className={cx("nx-radio-group", inline && "nx-radio-group--inline", error ? "nx-choice--invalid" : null, className)}
      aria-describedby={ids.describedBy}
      aria-invalid={error ? true : undefined}
    >
      <legend className="nx-field__label">{label}</legend>
      <div className="nx-radio-group__options">
        {options.map((option, index) => {
          const optionId = `${ids.id}-${index}`;
          return (
            <div key={option.value} className="nx-choice">
              <input
                type="radio"
                id={optionId}
                name={name}
                value={option.value}
                className="nx-choice__input nx-choice__input--radio"
                disabled={option.disabled}
                required={required}
                {...(value !== undefined
                  ? { checked: value === option.value, onChange: () => onChange?.(option.value) }
                  : { defaultChecked: defaultValue === option.value, onChange: () => onChange?.(option.value) })}
              />
              <div className="nx-choice__text">
                <label htmlFor={optionId} className="nx-choice__label">
                  {option.label}
                </label>
                {option.hint ? <p className="nx-field__hint">{option.hint}</p> : null}
              </div>
            </div>
          );
        })}
      </div>
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
    </fieldset>
  );
}
