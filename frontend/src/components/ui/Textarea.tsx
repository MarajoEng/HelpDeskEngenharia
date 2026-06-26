import type { ReactNode, TextareaHTMLAttributes } from "react";

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: ReactNode;
  hint?: ReactNode;
  error?: ReactNode;
  requiredLabel?: boolean;
  containerClassName?: string;
}

export default function Textarea({
  label,
  hint,
  error,
  className = "",
  containerClassName = "",
  required,
  requiredLabel = true,
  id,
  ...props
}: TextareaProps) {
  const textareaId = id ?? (typeof label === "string" ? `textarea-${label.toLowerCase().replace(/\s+/g, "-")}` : undefined);

  return (
    <div className={["flex min-w-0 flex-col gap-1", containerClassName].filter(Boolean).join(" ")}>
      {label ? (
        <label htmlFor={textareaId} className="block text-sm font-semibold text-slate-700">
          {label}
          {required && requiredLabel ? <strong aria-hidden="true" className="text-red-500 ml-0.5"> *</strong> : null}
        </label>
      ) : null}
      <textarea
        id={textareaId}
        className={[
          "block min-w-0 w-full rounded-xl border border-[#d9d1c2] bg-white px-3.5 py-3 text-sm text-slate-900 shadow-[0_1px_0_rgba(17,24,39,0.02)]",
          "placeholder-slate-400 resize-vertical min-h-[100px]",
          "focus:border-[#c9a24a] focus:outline-none focus:ring-2 focus:ring-[#c9a24a]/20",
          "disabled:cursor-not-allowed disabled:bg-slate-50 disabled:text-slate-500",
          error ? "border-red-400 focus:border-red-500 focus:ring-red-500" : "",
          className,
        ]
          .filter(Boolean)
          .join(" ")}
        required={required}
        {...props}
      />
      {hint ? <p className="text-xs text-slate-500">{hint}</p> : null}
      {error ? <p className="text-xs text-red-600 font-medium">{error}</p> : null}
    </div>
  );
}
