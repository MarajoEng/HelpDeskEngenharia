import type { ReactNode } from "react";

import Button from "./Button";
import Modal from "./Modal";

interface ConfirmDialogProps {
  title: string;
  description: ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
  tone?: "primary" | "danger";
  isProcessing?: boolean;
  onConfirm: () => void;
  onClose: () => void;
}

export default function ConfirmDialog({
  title,
  description,
  confirmLabel = "Confirmar",
  cancelLabel = "Cancelar",
  tone = "primary",
  isProcessing = false,
  onConfirm,
  onClose,
}: ConfirmDialogProps) {
  return (
    <Modal
      title={title}
      subtitle={description}
      onClose={onClose}
      closeLabel={cancelLabel}
      footer={
        <>
          <Button variant="secondary" onClick={onClose} disabled={isProcessing}>
            {cancelLabel}
          </Button>
          <Button variant={tone === "danger" ? "danger" : "primary"} onClick={onConfirm} disabled={isProcessing}>
            {isProcessing ? "Processando..." : confirmLabel}
          </Button>
        </>
      }
    >
      <div className="p-4 rounded-lg bg-slate-50 text-sm text-slate-600">
        Esta acao altera o estado atual do fluxo. Confirme apenas se as informacoes ja foram validadas.
      </div>
    </Modal>
  );
}
