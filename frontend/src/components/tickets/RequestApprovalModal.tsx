import { type FormEvent, useState } from "react";

import { ApiError } from "../../api/http";
import { requestTicketApproval } from "../../api/ticketApi";
import type { TicketDetail } from "../../types/ticket";

interface RequestApprovalModalProps {
  ticket: TicketDetail;
  token: string;
  onClose: () => void;
  onSuccess: (ticket: TicketDetail) => void;
}

export default function RequestApprovalModal({
  ticket,
  token,
  onClose,
  onSuccess,
}: RequestApprovalModalProps) {
  const [amountRequested, setAmountRequested] = useState(ticket.estimated_cost ?? "");
  const [justification, setJustification] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!amountRequested || Number(amountRequested) <= 0) {
      setErrorMessage("Informe um valor solicitado maior que zero.");
      return;
    }

    if (!justification.trim()) {
      setErrorMessage("Informe a justificativa da solicitacao de aprovacao.");
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      const updatedTicket = await requestTicketApproval(token, ticket.id, {
        amount_requested: amountRequested,
        justification: justification.trim(),
      });
      onSuccess(updatedTicket);
    } catch (error: unknown) {
      if (error instanceof ApiError && error.status === 409) {
        setErrorMessage("Este chamado ja possui uma aprovacao pendente ou nao esta mais em triagem.");
      } else {
        setErrorMessage(error instanceof Error ? error.message : "Nao foi possivel solicitar a aprovacao.");
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
            <p className="eyebrow">Solicitar aprovacao</p>
            <h3>{ticket.ticket_number}</h3>
            <p className="page__description" style={{ margin: "8px 0 0" }}>
              O valor solicitado define automaticamente a alcada aplicavel.
            </p>
          </div>
          <button className="button-secondary" type="button" onClick={onClose} disabled={isSubmitting}>
            Fechar
          </button>
        </div>

        <form className="form-grid" onSubmit={handleSubmit}>
          <label className="field">
            <span>Valor solicitado *</span>
            <input
              type="number"
              min="0.01"
              step="0.01"
              value={amountRequested}
              onChange={(event) => setAmountRequested(event.target.value)}
              disabled={isSubmitting}
            />
          </label>

          <label className="field field--full">
            <span>Justificativa *</span>
            <textarea
              value={justification}
              onChange={(event) => setJustification(event.target.value)}
              placeholder="Explique o custo solicitado e o motivo da aprovacao."
              disabled={isSubmitting}
            />
          </label>

          {errorMessage ? <div className="form-message form-message--error">{errorMessage}</div> : null}

          <div className="form-actions">
            <button className="button-secondary" type="button" onClick={onClose} disabled={isSubmitting}>
              Cancelar
            </button>
            <button className="button-primary" type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Solicitando..." : "Solicitar aprovacao"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
