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
    <div
      className={[
        "flex min-w-0 flex-col items-stretch justify-between gap-4 sm:flex-row sm:items-start",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <div className="min-w-0">
        {eyebrow ? (
          <p className="mb-1.5 text-[11px] font-bold uppercase tracking-[0.18em] text-[#c9a24a]">{eyebrow}</p>
        ) : null}
        <h2 className="text-[1.55rem] font-extrabold leading-tight tracking-tight text-slate-950 sm:text-[1.8rem]">{title}</h2>
        {description ? <p className="mt-1.5 max-w-3xl text-sm leading-relaxed text-slate-500">{description}</p> : null}
      </div>
      {actions ? (
        <div className="flex min-w-0 flex-wrap items-center gap-2 sm:flex-shrink-0 sm:justify-end">{actions}</div>
      ) : null}
    </div>
  );
}
