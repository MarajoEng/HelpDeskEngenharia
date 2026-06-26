import type { ReactNode } from "react";
import type { BadgeTone } from "./statusOptions";

interface StatCardProps {
  label: string;
  value: ReactNode;
  description?: ReactNode;
  icon?: ReactNode;
  iconBgColor?: string;
  iconColor?: string;
  trendValue?: string;
  trendDirection?: "up" | "down" | "neutral";
  tone?: BadgeTone;
  className?: string;
}

export default function StatCard({
  label,
  value,
  description,
  icon,
  iconBgColor = "bg-teal-50",
  iconColor = "text-teal-600",
  trendValue,
  trendDirection = "neutral",
  tone,
  className = "",
}: StatCardProps) {
  const toneClasses: Partial<Record<BadgeTone, string>> = {
    danger: "border-red-200 bg-red-50/40",
    warning: "border-amber-200 bg-amber-50/35",
    success: "border-emerald-200 bg-emerald-50/30",
    info: "border-blue-200 bg-blue-50/30",
    accent: "border-teal-200 bg-teal-50/30",
  };

  return (
    <div
      className={[
        "relative flex min-w-0 overflow-hidden items-center gap-4 rounded-[22px] border border-[#e7dfcf] bg-white p-5 shadow-[0_18px_60px_rgba(17,24,39,0.07)]",
        tone ? toneClasses[tone] : "",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {icon && (
        <div
          className={`flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-2xl ${iconBgColor} ${iconColor}`}
        >
          {icon}
        </div>
      )}
      <div className="flex min-w-0 flex-grow flex-col">
        <div className="mb-1 text-[12px] font-bold uppercase leading-tight tracking-[0.12em] text-slate-500">{label}</div>
        <div className="mb-1.5 break-words text-[1.85rem] font-extrabold leading-tight tracking-tight text-slate-950">
          {value}
        </div>
        {(trendValue || description) && (
          <div className="flex min-w-0 flex-wrap items-center gap-1.5 text-xs leading-snug">
            {trendValue && (
              <span
                className={`font-medium flex items-center gap-0.5 ${
                  trendDirection === "up"
                    ? "text-teal-600"
                    : trendDirection === "down"
                    ? "text-red-500"
                    : "text-slate-500"
                }`}
              >
                {trendDirection === "up" && (
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M12 19V5M5 12l7-7 7 7" />
                  </svg>
                )}
                {trendDirection === "down" && (
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M12 5v14M19 12l-7 7-7-7" />
                  </svg>
                )}
                {trendValue}
              </span>
            )}
            {description && <span className="min-w-0 truncate text-slate-500">{description}</span>}
          </div>
        )}
      </div>
    </div>
  );
}
