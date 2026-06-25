import type { HTMLAttributes, ReactNode } from "react";

interface FilterBarProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  columns?: 2 | 3 | 4 | 5 | 6;
  dense?: boolean;
}

const columnsClasses: Record<number, string> = {
  2: "grid-cols-1 sm:grid-cols-2",
  3: "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3",
  4: "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4",
  5: "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5",
  6: "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-6",
};

export default function FilterBar({
  children,
  className = "",
  columns = 4,
  dense = false,
  ...props
}: FilterBarProps) {
  return (
    <div
      className={[
        "grid",
        columnsClasses[columns] ?? columnsClasses[4],
        dense ? "gap-3" : "gap-4",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      {...props}
    >
      {children}
    </div>
  );
}
