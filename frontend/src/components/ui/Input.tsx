import type { InputHTMLAttributes, ReactNode } from "react";

import { cx } from "./cx";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: ReactNode;
  hint?: ReactNode;
  error?: ReactNode;
  requiredLabel?: boolean;
  containerClassName?: string;
}

export default function Input({
  label,
  hint,
  error,
  className,
  containerClassName,
  required,
  requiredLabel = true,
  ...props
}: InputProps) {
  return (
    <label className={cx("ui-field", containerClassName)}>
      {label ? (
        <span className="ui-field__label">
          {label}
          {required && requiredLabel ? <strong aria-hidden="true"> *</strong> : null}
        </span>
      ) : null}
      <input className={cx("ui-input", className)} required={required} {...props} />
      {hint ? <small className="ui-field__hint">{hint}</small> : null}
      {error ? <small className="ui-field__error">{error}</small> : null}
    </label>
  );
}
