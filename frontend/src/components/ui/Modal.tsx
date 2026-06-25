import type { ReactNode } from "react";

import Button from "./Button";

interface ModalProps {
  title: ReactNode;
  subtitle?: ReactNode;
  children: ReactNode;
  onClose: () => void;
  closeLabel?: string;
  size?: "md" | "lg";
  footer?: ReactNode;
  className?: string;
}

export default function Modal({
  title,
  subtitle,
  children,
  onClose,
  closeLabel = "Fechar",
  size = "md",
  footer,
  className = "",
}: ModalProps) {
  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50"
      role="presentation"
      onClick={onClose}
    >
      <div
        className={[
          "bg-white rounded-2xl shadow-2xl flex flex-col max-h-[calc(100vh-2rem)] overflow-hidden",
          size === "lg" ? "w-full max-w-3xl" : "w-full max-w-xl",
          className,
        ]
          .filter(Boolean)
          .join(" ")}
        role="dialog"
        aria-modal="true"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-4 px-6 py-4 border-b border-slate-200">
          <div>
            <h3 className="text-lg font-semibold text-slate-900">{title}</h3>
            {subtitle ? <p className="text-sm text-slate-500 mt-0.5">{subtitle}</p> : null}
          </div>
          <button
            type="button"
            aria-label={closeLabel}
            className="p-1 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition-colors"
            onClick={onClose}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div className="overflow-y-auto flex-1 p-6">{children}</div>
        {footer ? (
          <div className="flex justify-end gap-3 px-6 py-4 border-t border-slate-200 flex-wrap">
            {footer}
          </div>
        ) : null}
      </div>
    </div>
  );
}
