import type { HTMLAttributes, ReactNode } from "react";

import { cx } from "./cx";

interface CardProps extends HTMLAttributes<HTMLElement> {
  as?: "article" | "section" | "div";
  children: ReactNode;
  stacked?: boolean;
}

export default function Card({
  as = "section",
  children,
  className,
  stacked = false,
  ...props
}: CardProps) {
  const Component = as;
  return (
    <Component
      className={cx("ui-card", stacked && "ui-card--stacked", className)}
      {...props}
    >
      {children}
    </Component>
  );
}
