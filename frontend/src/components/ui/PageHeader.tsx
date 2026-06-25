import type { ReactNode } from "react";

import { cx } from "./cx";

interface PageHeaderProps {
  eyebrow?: string;
  title: ReactNode;
  description?: ReactNode;
  actions?: ReactNode;
  className?: string;
}

export default function PageHeader({
  eyebrow,
  title,
  description,
  actions,
  className,
}: PageHeaderProps) {
  return (
    <div className={cx("ui-page-header", className)}>
      <div className="ui-page-header__copy">
        {eyebrow ? <p className="eyebrow">{eyebrow}</p> : null}
        <h2 className="page__title">{title}</h2>
        {description ? <p className="page__description">{description}</p> : null}
      </div>
      {actions ? <div className="ui-page-header__actions">{actions}</div> : null}
    </div>
  );
}
