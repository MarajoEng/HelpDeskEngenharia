import type { ReactNode, SelectHTMLAttributes } from "react";

import { cx } from "./cx";

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: ReactNode;
  hint?: ReactNode;
  error?: ReactNode;
  requiredLabel?: boolean;
  containerClassName?: string;
}

export default function Select({
  label,
  hint,
  error,
  className,
  containerClassName,
  children,
  required,
  requiredLabel = true,
  ...props
}: SelectProps) {
  return (
    <label className={cx("ui-field", containerClassName)}>
      {label ? (
        <span className="ui-field__label">
          {label}
          {required && requiredLabel ? <strong aria-hidden="true"> *</strong> : null}
        </span>
      ) : null}
      <select className={cx("ui-input", className)} required={required} {...props}>
        {children}
      </select>
      {hint ? <small className="ui-field__hint">{hint}</small> : null}
      {error ? <small className="ui-field__error">{error}</small> : null}
    </label>
  );
}
