import type { ReactNode, TextareaHTMLAttributes } from "react";

import { cx } from "./cx";

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: ReactNode;
  hint?: ReactNode;
  error?: ReactNode;
  requiredLabel?: boolean;
  containerClassName?: string;
}

export default function Textarea({
  label,
  hint,
  error,
  className,
  containerClassName,
  required,
  requiredLabel = true,
  ...props
}: TextareaProps) {
  return (
    <label className={cx("ui-field", containerClassName)}>
      {label ? (
        <span className="ui-field__label">
          {label}
          {required && requiredLabel ? <strong aria-hidden="true"> *</strong> : null}
        </span>
      ) : null}
      <textarea className={cx("ui-input", "ui-textarea", className)} required={required} {...props} />
      {hint ? <small className="ui-field__hint">{hint}</small> : null}
      {error ? <small className="ui-field__error">{error}</small> : null}
    </label>
  );
}
