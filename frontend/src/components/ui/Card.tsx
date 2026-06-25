import type { HTMLAttributes, ReactNode } from "react";

interface CardProps extends HTMLAttributes<HTMLElement> {
  as?: "article" | "section" | "div";
  children: ReactNode;
  stacked?: boolean;
}

export default function Card({
  as = "section",
  children,
  className = "",
  stacked = false,
  ...props
}: CardProps) {
  const Component = as;
  return (
    <Component
      className={[
        "bg-white rounded-xl border border-slate-200 shadow-sm p-6",
        stacked ? "flex flex-col gap-6" : "",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      {...props}
    >
      {children}
    </Component>
  );
}
