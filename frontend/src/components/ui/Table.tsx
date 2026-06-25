import type { HTMLAttributes, TableHTMLAttributes } from "react";

interface TableProps extends TableHTMLAttributes<HTMLTableElement> {
  minWidth?: number | string;
  wrapperClassName?: string;
}

export default function Table({
  className = "",
  wrapperClassName = "",
  minWidth = 760,
  style,
  ...props
}: TableProps) {
  return (
    <div className={["overflow-x-auto", wrapperClassName].filter(Boolean).join(" ")}>
      <table
        className={["min-w-full divide-y divide-slate-200", className].filter(Boolean).join(" ")}
        style={{ minWidth, ...style }}
        {...props}
      />
    </div>
  );
}

export function TableMeta({ className = "", ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={["flex items-center justify-between gap-4", className].filter(Boolean).join(" ")}
      {...props}
    />
  );
}

export function Th({ className = "", ...props }: HTMLAttributes<HTMLTableCellElement>) {
  return (
    <th
      className={[
        "px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider whitespace-nowrap bg-slate-50",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      {...props}
    />
  );
}

export function Td({ className = "", ...props }: HTMLAttributes<HTMLTableCellElement>) {
  return (
    <td
      className={["px-4 py-3 text-sm text-slate-900", className].filter(Boolean).join(" ")}
      {...props}
    />
  );
}
