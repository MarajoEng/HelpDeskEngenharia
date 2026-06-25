import type { ReactNode } from "react";

import Badge from "./Badge";
import Card from "./Card";
import { cx } from "./cx";
import type { BadgeTone } from "./statusOptions";

interface StatCardProps {
  label: string;
  value: ReactNode;
  description: ReactNode;
  tone?: BadgeTone;
  meta?: ReactNode;
  className?: string;
}

export default function StatCard({
  label,
  value,
  description,
  tone = "accent",
  meta,
  className,
}: StatCardProps) {
  return (
    <Card className={cx("ui-stat-card", className)}>
      <div className="ui-stat-card__top">
        <Badge tone={tone}>{label}</Badge>
        {meta}
      </div>
      <strong className="ui-stat-card__value">{value}</strong>
      <p className="ui-stat-card__description">{description}</p>
    </Card>
  );
}
