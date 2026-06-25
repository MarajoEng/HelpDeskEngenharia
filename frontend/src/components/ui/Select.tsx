import type { ReactNode, SelectHTMLAttributes } from "react";

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: ReactNode;
  hint?: ReactNode;
  error?: ReactNode;
  requiredLabel?: boolean;
  containerClassName?: string;
}

export default function Select({
  label,
  hint,
  error,
  className = "",
  containerClassName = "",
  children,
  required,
  requiredLabel = true,
  id,
  ...props
}: SelectProps) {
  const selectId = id ?? (typeof label === "string" ? `select-${label.toLowerCase().replace(/\s+/g, "-")}` : undefined);

  return (
    <div className={["flex flex-col gap-1", containerClassName].filter(Boolean).join(" ")}>
      {label ? (
        <label htmlFor={selectId} className="block text-sm font-medium text-slate-700">
          {label}
          {required && requiredLabel ? <strong aria-hidden="true" className="text-red-500 ml-0.5"> *</strong> : null}
        </label>
      ) : null}
      <select
        id={selectId}
        className={[
          "block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 bg-white",
          "focus:border-teal-500 focus:outline-none focus:ring-1 focus:ring-teal-500",
          "disabled:bg-slate-50 disabled:text-slate-500 disabled:cursor-not-allowed",
          error ? "border-red-400 focus:border-red-500 focus:ring-red-500" : "",
          className,
        ]
          .filter(Boolean)
          .join(" ")}
        required={required}
        {...props}
      >
        {children}
      </select>
      {hint ? <p className="text-xs text-slate-500">{hint}</p> : null}
      {error ? <p className="text-xs text-red-600 font-medium">{error}</p> : null}
    </div>
  );
}
