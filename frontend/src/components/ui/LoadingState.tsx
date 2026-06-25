import type { ReactNode } from "react";

import Card from "./Card";

interface LoadingStateProps {
  title?: string;
  description?: ReactNode;
}

export default function LoadingState({
  title = "Carregando dados",
  description = "Aguarde enquanto as informacoes sao atualizadas.",
}: LoadingStateProps) {
  return (
    <Card className="ui-state ui-state--loading">
      <div className="ui-state__spinner" aria-hidden="true" />
      <div className="ui-state__content">
        <h3>{title}</h3>
        <p>{description}</p>
      </div>
    </Card>
  );
}
