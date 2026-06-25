import type { ReactNode } from "react";

import Button from "./Button";
import { cx } from "./cx";

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
  className,
}: ModalProps) {
  return (
    <div className="ui-modal-backdrop" role="presentation" onClick={onClose}>
      <div
        className={cx("ui-modal", `ui-modal--${size}`, className)}
        role="dialog"
        aria-modal="true"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="ui-modal__header">
          <div>
            <h3 className="ui-modal__title">{title}</h3>
            {subtitle ? <p className="ui-modal__subtitle">{subtitle}</p> : null}
          </div>
          <Button aria-label={closeLabel} variant="ghost" onClick={onClose}>
            {closeLabel}
          </Button>
        </div>
        <div className="ui-modal__body">{children}</div>
        {footer ? <div className="ui-modal__footer">{footer}</div> : null}
      </div>
    </div>
  );
}
