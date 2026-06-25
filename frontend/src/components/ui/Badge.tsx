import type { HTMLAttributes, ReactNode } from "react";

import { cx } from "./cx";
import type { BadgeTone } from "./statusOptions";

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  children: ReactNode;
  tone?: BadgeTone;
}

export default function Badge({
  children,
  className,
  tone = "neutral",
  ...props
}: BadgeProps) {
  return (
    <span
      className={cx("ui-badge", `ui-badge--${tone}`, className)}
      {...props}
    >
      {children}
    </span>
  );
}
