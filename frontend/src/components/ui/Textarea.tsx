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
    <div className={["flex flex-col gap-1", containerClassName].filter(Boolean).join(" ")}>
      {label ? (
        <label htmlFor={textareaId} className="block text-sm font-medium text-slate-700">
          {label}
          {required && requiredLabel ? <strong aria-hidden="true" className="text-red-500 ml-0.5"> *</strong> : null}
        </label>
      ) : null}
      <textarea
        id={textareaId}
        className={[
          "block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 bg-white",
          "placeholder-slate-400 resize-vertical min-h-[100px]",
          "focus:border-teal-500 focus:outline-none focus:ring-1 focus:ring-teal-500",
          "disabled:bg-slate-50 disabled:text-slate-500 disabled:cursor-not-allowed",
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
