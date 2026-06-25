import type { HTMLAttributes, ReactNode } from "react";

import { cx } from "./cx";

interface FilterBarProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  columns?: 2 | 3 | 4 | 5 | 6;
  dense?: boolean;
}

export default function FilterBar({
  children,
  className,
  columns = 4,
  dense = false,
  ...props
}: FilterBarProps) {
  return (
    <div
      className={cx(
        "ui-filter-bar",
        `ui-filter-bar--${columns}`,
        dense && "ui-filter-bar--dense",
        className,
      )}
      {...props}
    >
      {children}
    </div>
  );
}
