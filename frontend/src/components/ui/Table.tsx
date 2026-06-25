import type { CSSProperties, HTMLAttributes, TableHTMLAttributes } from "react";

import { cx } from "./cx";

interface TableProps extends TableHTMLAttributes<HTMLTableElement> {
  minWidth?: number | string;
  wrapperClassName?: string;
}

export default function Table({
  className,
  wrapperClassName,
  minWidth = 760,
  style,
  ...props
}: TableProps) {
  const mergedStyle: CSSProperties = {
    minWidth,
    ...style,
  };

  return (
    <div className={cx("ui-table-wrap", wrapperClassName)}>
      <table className={cx("ui-table", className)} style={mergedStyle} {...props} />
    </div>
  );
}

export function TableMeta({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cx("ui-table-meta", className)} {...props} />;
}
