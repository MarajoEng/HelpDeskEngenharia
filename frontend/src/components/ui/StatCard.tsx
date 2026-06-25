import type { ReactNode } from "react";

import Badge from "./Badge";
import type { BadgeTone } from "./statusOptions";

interface StatCardProps {
  label: string;
  value: ReactNode;
  description: ReactNode;
  tone?: BadgeTone;
  meta?: ReactNode;
  className?: string;
}

export default function StatCard({
  label,
  value,
  description,
  tone = "accent",
  meta,
  className = "",
}: StatCardProps) {
  return (
    <div
      className={[
        "bg-white rounded-xl border border-slate-200 p-5 shadow-sm",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <div className="flex items-start justify-between gap-2 mb-3">
        <Badge tone={tone}>{label}</Badge>
        {meta ? <div className="text-xs text-slate-500">{meta}</div> : null}
      </div>
      <p className="text-2xl font-bold text-slate-900 leading-none mb-1">{value}</p>
      <p className="text-sm text-slate-500">{description}</p>
    </div>
  );
}
