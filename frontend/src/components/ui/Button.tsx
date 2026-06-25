import type { ButtonHTMLAttributes, ReactNode } from "react";

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";
type ButtonSize = "sm" | "md" | "lg";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  variant?: ButtonVariant;
  size?: ButtonSize;
  block?: boolean;
}

const variantClasses: Record<ButtonVariant, string> = {
  primary:
    "bg-teal-600 text-white hover:bg-teal-700 shadow-sm",
  secondary:
    "bg-white text-slate-700 border border-slate-300 hover:bg-slate-50",
  ghost:
    "bg-transparent text-slate-600 hover:bg-slate-100",
  danger:
    "bg-red-600 text-white hover:bg-red-700 shadow-sm",
};

const sizeClasses: Record<ButtonSize, string> = {
  sm: "px-3 py-1.5 text-xs min-h-[34px]",
  md: "px-4 py-2 text-sm min-h-[38px]",
  lg: "px-5 py-2.5 text-sm min-h-[44px]",
};

export default function Button({
  children,
  className = "",
  variant = "secondary",
  size = "md",
  block = false,
  type = "button",
  disabled,
  ...props
}: ButtonProps) {
  return (
    <button
      className={[
        "inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-colors",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-500 focus-visible:ring-offset-1",
        "disabled:opacity-50 disabled:cursor-not-allowed",
        variantClasses[variant],
        sizeClasses[size],
        block ? "w-full" : "",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      type={type}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  );
}
