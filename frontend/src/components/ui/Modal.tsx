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
      className="fixed inset-0 z-50 flex items-end justify-center bg-black/55 p-0 backdrop-blur-sm sm:items-center sm:p-4"
      role="presentation"
      onClick={onClose}
    >
      <div
        className={[
          "flex max-h-[100dvh] min-w-0 flex-col overflow-hidden rounded-t-[24px] bg-white shadow-[0_30px_90px_rgba(0,0,0,0.24)] sm:max-h-[calc(100vh-2rem)] sm:rounded-[24px]",
          size === "lg" ? "w-full max-w-3xl" : "w-full max-w-xl",
          className,
        ]
          .filter(Boolean)
          .join(" ")}
        role="dialog"
        aria-modal="true"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-4 border-b border-[#e7dfcf] px-4 py-4 sm:px-6">
          <div className="min-w-0">
            <h3 className="text-lg font-bold text-slate-950">{title}</h3>
            {subtitle ? <p className="text-sm text-slate-500 mt-0.5">{subtitle}</p> : null}
          </div>
          <button
            type="button"
            aria-label={closeLabel}
            className="inline-flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600"
            onClick={onClose}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div className="min-w-0 flex-1 overflow-y-auto p-4 sm:p-6">{children}</div>
        {footer ? (
          <div className="flex flex-wrap justify-end gap-3 border-t border-[#e7dfcf] bg-[#fbfaf7] px-4 py-4 sm:px-6">
            {footer}
          </div>
        ) : null}
      </div>
    </div>
  );
}
