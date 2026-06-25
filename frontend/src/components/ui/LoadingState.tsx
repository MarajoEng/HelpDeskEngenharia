import type { ReactNode } from "react";

interface LoadingStateProps {
  title?: string;
  description?: ReactNode;
}

export default function LoadingState({
  title = "Carregando dados",
  description = "Aguarde enquanto as informacoes sao atualizadas.",
}: LoadingStateProps) {
  return (
    <div className="flex items-center gap-4 p-5 rounded-xl border border-slate-200 bg-white">
      <div className="ui-spinner" aria-hidden="true" />
      <div>
        <h3 className="text-sm font-semibold text-slate-900">{title}</h3>
        <p className="text-xs text-slate-500 mt-0.5">{description}</p>
      </div>
    </div>
  );
}
