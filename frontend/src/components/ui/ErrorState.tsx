import type { ReactNode } from "react";

import Button from "./Button";
import Card from "./Card";

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
    <Card className="ui-state ui-state--error">
      <div className="ui-state__icon" aria-hidden="true">
        !
      </div>
      <div className="ui-state__content">
        <h3>{title}</h3>
        <p>{description}</p>
        {onRetry ? <Button onClick={onRetry}>{actionLabel}</Button> : null}
      </div>
    </Card>
  );
}
