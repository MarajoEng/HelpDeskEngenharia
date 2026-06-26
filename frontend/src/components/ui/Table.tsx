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
    <div
      className={["max-w-full overflow-x-auto overscroll-x-contain rounded-[18px]", wrapperClassName].filter(Boolean).join(" ")}
      tabIndex={0}
      role="region"
      aria-label="Tabela com rolagem horizontal"
    >
      <table
        className={["min-w-full divide-y divide-[#eadfce]", className].filter(Boolean).join(" ")}
        style={{ minWidth, ...style }}
        {...props}
      />
    </div>
  );
}

export function TableMeta({ className = "", ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={["flex flex-wrap items-center justify-between gap-4", className].filter(Boolean).join(" ")}
      {...props}
    />
  );
}

export function Th({ className = "", ...props }: HTMLAttributes<HTMLTableCellElement>) {
  return (
    <th
      className={[
        "sticky top-0 z-10 bg-[#f7f2e8] px-4 py-3 text-left text-[11px] font-bold uppercase tracking-[0.14em] text-slate-500 shadow-[0_1px_0_#eadfce] whitespace-nowrap",
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
      className={["px-4 py-3.5 text-sm text-slate-900 align-top", className].filter(Boolean).join(" ")}
      {...props}
    />
  );
}
