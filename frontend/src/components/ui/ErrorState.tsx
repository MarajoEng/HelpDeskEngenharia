import type { ReactNode } from "react";

import Button from "./Button";

interface ErrorStateProps {
  title?: string;
  description: ReactNode;
  actionLabel?: string;
  onRetry?: () => void;
}

export default function ErrorState({
  title = "Falha ao carregar",
  description,
  actionLabel = "Tentar novamente",
  onRetry,
}: ErrorStateProps) {
  return (
    <div className="flex items-start gap-3 p-4 rounded-xl border border-red-200 bg-red-50">
      <div
        className="w-8 h-8 rounded-lg bg-red-100 flex items-center justify-center text-red-600 font-bold text-sm flex-shrink-0"
        aria-hidden="true"
      >
        !
      </div>
      <div className="min-w-0">
        <h3 className="text-sm font-semibold text-red-900">{title}</h3>
        <p className="text-sm text-red-700 mt-0.5">{description}</p>
        {onRetry ? (
          <div className="mt-3">
            <Button variant="danger" size="sm" onClick={onRetry}>
              {actionLabel}
            </Button>
          </div>
        ) : null}
      </div>
    </div>
  );
}
