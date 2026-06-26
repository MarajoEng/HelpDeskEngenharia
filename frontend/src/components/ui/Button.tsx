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
    "border border-transparent bg-slate-950 text-white shadow-sm hover:bg-slate-800",
  secondary:
    "border border-[#e7dfcf] bg-white text-slate-700 shadow-sm hover:bg-[#f3eee2] hover:text-slate-950",
  ghost:
    "border border-transparent bg-transparent text-slate-600 hover:bg-[#f3eee2] hover:text-slate-950",
  danger:
    "border border-transparent bg-red-600 text-white shadow-sm hover:bg-red-700",
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
        "inline-flex max-w-full items-center justify-center gap-2 rounded-xl font-semibold transition duration-200 hover:-translate-y-0.5",
        "whitespace-normal text-center sm:whitespace-nowrap",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#c9a24a] focus-visible:ring-offset-1",
        "disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:translate-y-0",
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
