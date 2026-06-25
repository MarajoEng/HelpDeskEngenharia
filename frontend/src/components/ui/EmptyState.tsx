import type { ReactNode } from "react";

import Card from "./Card";

interface EmptyStateProps {
  title: string;
  description: ReactNode;
  action?: ReactNode;
}

export default function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <Card className="ui-state ui-state--empty">
      <div className="ui-state__icon" aria-hidden="true">
        0
      </div>
      <div className="ui-state__content">
        <h3>{title}</h3>
        <p>{description}</p>
        {action}
      </div>
    </Card>
  );
}
