import { type FormEvent, useState } from "react";

import { ApiError } from "../../api/http";
import { decideTicketApproval } from "../../api/ticketApi";
import type { TicketApproval, TicketDetail } from "../../types/ticket";
import { ROLE_LABELS } from "./ticketUi";

interface ApprovalDecisionModalProps {
  ticket: TicketDetail;
  approval: TicketApproval;
  token: string;
  onClose: () => void;
  onSuccess: (ticket: TicketDetail) => void;
}

export default function ApprovalDecisionModal({
  ticket,
  approval,
  token,
  onClose,
  onSuccess,
}: ApprovalDecisionModalProps) {
  const [decision, setDecision] = useState<"approved" | "rejected">("approved");
  const [amountApproved, setAmountApproved] = useState(approval.amount_requested);
  const [justification, setJustification] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (decision === "approved" && (!amountApproved || Number(amountApproved) < 0)) {
      setErrorMessage("Informe um valor aprovado valido.");
      return;
    }

    if (!justification.trim()) {
      setErrorMessage("Informe a justificativa da decisao.");
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      const updatedTicket = await decideTicketApproval(token, ticket.id, {
        decision,
        amount_approved: decision === "approved" ? amountApproved : null,
        justification: justification.trim(),
      });
      onSuccess(updatedTicket);
    } catch (error: unknown) {
      if (error instanceof ApiError && error.status === 403) {
        setErrorMessage("Seu perfil nao possui alcada para aprovar este valor.");
      } else if (error instanceof ApiError && error.status === 409) {
        setErrorMessage("A aprovacao pendente nao pode mais ser decidida no estado atual.");
      } else {
        setErrorMessage(error instanceof Error ? error.message : "Nao foi possivel registrar a decisao.");
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="modal-backdrop" role="presentation">
      <div className="modal-card">
        <div className="modal-card__header">
          <div>
            <p className="eyebrow">Decisao de aprovacao</p>
            <h3>{ticket.ticket_number}</h3>
            <p className="page__description" style={{ margin: "8px 0 0" }}>
              Alcada aplicada: {approval.approval_level_name ?? "Nao informada"} · perfis{" "}
              {approval.approval_allowed_roles.map((role) => ROLE_LABELS[role]).join(", ")}
            </p>
          </div>
          <button className="button-secondary" type="button" onClick={onClose} disabled={isSubmitting}>
            Fechar
          </button>
        </div>

        <form className="form-grid" onSubmit={handleSubmit}>
          <label className="field">
            <span>Decisao *</span>
            <select value={decision} onChange={(event) => setDecision(event.target.value as "approved" | "rejected")}>
              <option value="approved">Aprovar</option>
              <option value="rejected">Reprovar</option>
            </select>
          </label>

          {decision === "approved" ? (
            <label className="field">
              <span>Valor aprovado</span>
              <input
                type="number"
                min="0"
                step="0.01"
                value={amountApproved}
                onChange={(event) => setAmountApproved(event.target.value)}
                disabled={isSubmitting}
              />
            </label>
          ) : null}

          <label className="field field--full">
            <span>Justificativa *</span>
            <textarea
              value={justification}
              onChange={(event) => setJustification(event.target.value)}
              placeholder="Registre a decisao e o fundamento da aprovacao ou reprovacao."
              disabled={isSubmitting}
            />
          </label>

          {errorMessage ? <div className="form-message form-message--error">{errorMessage}</div> : null}

          <div className="form-actions">
            <button className="button-secondary" type="button" onClick={onClose} disabled={isSubmitting}>
              Cancelar
            </button>
            <button className="button-primary" type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Salvando..." : "Confirmar decisao"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
