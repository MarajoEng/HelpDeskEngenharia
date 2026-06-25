import type { ReactNode } from "react";

interface PageHeaderProps {
  eyebrow?: string;
  title: ReactNode;
  description?: ReactNode;
  actions?: ReactNode;
  className?: string;
}

export default function PageHeader({
  eyebrow,
  title,
  description,
  actions,
  className = "",
}: PageHeaderProps) {
  return (
    <div className={["flex items-start justify-between gap-4", className].filter(Boolean).join(" ")}>
      <div>
        {eyebrow ? (
          <p className="text-xs font-semibold text-teal-600 uppercase tracking-wider mb-1">{eyebrow}</p>
        ) : null}
        <h2 className="text-2xl font-bold text-slate-900 leading-tight">{title}</h2>
        {description ? <p className="text-sm text-slate-500 mt-1">{description}</p> : null}
      </div>
      {actions ? <div className="flex items-center gap-3 flex-shrink-0">{actions}</div> : null}
    </div>
  );
}
