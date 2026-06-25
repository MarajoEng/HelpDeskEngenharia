import type { HTMLAttributes, ReactNode } from "react";

import type { BadgeTone } from "./statusOptions";

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  children: ReactNode;
  tone?: BadgeTone;
}

const toneClasses: Record<BadgeTone, string> = {
  info: "bg-blue-100 text-blue-800",
  success: "bg-emerald-100 text-emerald-800",
  warning: "bg-amber-100 text-amber-800",
  danger: "bg-red-100 text-red-800",
  neutral: "bg-slate-100 text-slate-700",
  accent: "bg-teal-100 text-teal-800",
};

export default function Badge({
  children,
  className = "",
  tone = "neutral",
  ...props
}: BadgeProps) {
  return (
    <span
      className={[
        "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold whitespace-nowrap",
        toneClasses[tone],
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      {...props}
    >
      {children}
    </span>
  );
}
