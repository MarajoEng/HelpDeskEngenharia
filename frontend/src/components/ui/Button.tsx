import type { ButtonHTMLAttributes, ReactNode } from "react";

import { cx } from "./cx";

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";
type ButtonSize = "sm" | "md" | "lg";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  variant?: ButtonVariant;
  size?: ButtonSize;
  block?: boolean;
}

export default function Button({
  children,
  className,
  variant = "secondary",
  size = "md",
  block = false,
  type = "button",
  ...props
}: ButtonProps) {
  return (
    <button
      className={cx(
        "ui-button",
        `ui-button--${variant}`,
        `ui-button--${size}`,
        block && "ui-button--block",
        className,
      )}
      type={type}
      {...props}
    >
      {children}
    </button>
  );
}
