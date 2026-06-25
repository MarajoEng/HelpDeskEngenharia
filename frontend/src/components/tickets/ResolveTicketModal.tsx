import { useState } from "react";

import { resolveTicket } from "../../api/ticketApi";
import ConfirmDialog from "../ui/ConfirmDialog";
import type { TicketDetail } from "../../types/ticket";
import { formatMoney } from "./ticketUi";

interface Props {
  ticket: TicketDetail;
  token: string;
  onClose: () => void;
  onSuccess: (updated: TicketDetail) => void;
}

export default function ResolveTicketModal({ ticket, token, onClose, onSuccess }: Props) {
  const [solutionDescription, setSolutionDescription] = useState("");
  const [finalCost, setFinalCost] = useState(ticket.final_cost ?? "");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);

  function requestConfirm(event: React.FormEvent) {
    event.preventDefault();
    if (!solutionDescription.trim()) {
      setError("Descricao da solucao e obrigatoria.");
      return;
    }
    if (!finalCost || Number(finalCost) < 0) {
      setError("Informe um custo final valido.");
      return;
    }
    if (!ticket.indicators.has_closing_evidence) {
      setError("Anexe uma evidencia de conclusao antes de resolver.");
      return;
    }
    setIsConfirmOpen(true);
  }

  function confirmResolve() {
    setIsSubmitting(true);
    setError(null);
    setSuccess(null);
    setIsConfirmOpen(false);

    resolveTicket(token, ticket.id, {
      solution_description: solutionDescription.trim(),
      final_cost: finalCost,
    })
      .then((updatedTicket) => {
        onSuccess(updatedTicket);
        setSuccess(`Chamado ${updatedTicket.ticket_number} marcado como resolvido.`);
      })
      .catch((requestError: unknown) => {
        setError(requestError instanceof Error ? requestError.message : "Nao foi possivel resolver o chamado.");
      })
      .finally(() => {
        setIsSubmitting(false);
      });
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card" onClick={(event) => event.stopPropagation()}>
        <div className="modal-card__header">
          <div>
            <h3>Resolver chamado</h3>
            <p className="page__description" style={{ margin: "6px 0 0" }}>
              O fechamento tecnico exige evidencia de conclusao e custo final.
            </p>
          </div>
          <button className="button-secondary" type="button" onClick={onClose}>
            Fechar
          </button>
        </div>

        <form className="form-grid" onSubmit={requestConfirm}>
          {error ? <div className="state-card state-card--error">{error}</div> : null}
          {success ? <div className="state-card state-card--success">{success}</div> : null}

          {!ticket.indicators.has_closing_evidence ? (
            <div className="state-card state-card--error">
              Anexe uma evidencia de conclusao antes de resolver.
            </div>
          ) : null}

          <article className="info-card">
            <h2>{ticket.ticket_number}</h2>
            <p style={{ marginBottom: 0 }}>{ticket.title}</p>
          </article>

          <label className="field field--full">
            <span>Descricao da solucao</span>
            <textarea
              value={solutionDescription}
              onChange={(event) => setSolutionDescription(event.target.value)}
              placeholder="Descreva a solucao executada e o que foi validado em campo."
              required
            />
          </label>

          <label className="field">
            <span>Custo final (R$)</span>
            <input
              type="number"
              min="0"
              step="0.01"
              value={finalCost}
              onChange={(event) => setFinalCost(event.target.value)}
              placeholder="0.00"
              required
            />
          </label>

          <div className="state-card">
            Evidencia de conclusao: {ticket.indicators.has_closing_evidence ? "disponivel" : "pendente"}.
            Custo atual: {formatMoney(ticket.final_cost)}.
          </div>

          <div className="form-actions">
            <button className="button-secondary" type="button" onClick={onClose} disabled={isSubmitting}>
              Cancelar
            </button>
            <button className="button-primary" type="submit" disabled={isSubmitting || !ticket.indicators.has_closing_evidence}>
              {isSubmitting ? "Resolvendo..." : "Resolver chamado"}
            </button>
          </div>
        </form>
      </div>
      {isConfirmOpen ? (
        <ConfirmDialog
          title="Confirmar resolucao"
          description="O chamado sera movido para resolvido com custo final e evidencia validada."
          confirmLabel="Resolver chamado"
          onConfirm={confirmResolve}
          onClose={() => setIsConfirmOpen(false)}
          isProcessing={isSubmitting}
        />
      ) : null}
    </div>
  );
}
