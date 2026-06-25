import { useState } from "react";

import { closeTicket } from "../../api/ticketApi";
import type { TicketDetail } from "../../types/ticket";

interface Props {
  ticket: TicketDetail;
  token: string;
  onClose: () => void;
  onSuccess: (updated: TicketDetail) => void;
}

export default function CloseTicketModal({ ticket, token, onClose, onSuccess }: Props) {
  const [closeComment, setCloseComment] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();

    if (!closeComment.trim()) {
      setError("Comentario de fechamento e obrigatorio.");
      return;
    }
    if (!window.confirm("Confirmar o fechamento final deste chamado?")) {
      return;
    }

    setIsSubmitting(true);
    setError(null);

    closeTicket(token, ticket.id, {
      close_comment: closeComment.trim(),
    })
      .then((updatedTicket) => {
        onSuccess(updatedTicket);
      })
      .catch((requestError: unknown) => {
        setError(requestError instanceof Error ? requestError.message : "Nao foi possivel fechar o chamado.");
        setIsSubmitting(false);
      });
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card" onClick={(event) => event.stopPropagation()}>
        <div className="modal-card__header">
          <div>
            <h3>Fechar chamado</h3>
            <p className="page__description" style={{ margin: "6px 0 0" }}>
              Registre o comentario final de auditoria antes do encerramento definitivo.
            </p>
          </div>
          <button className="button-secondary" type="button" onClick={onClose}>
            Fechar
          </button>
        </div>

        <form className="form-grid" onSubmit={handleSubmit}>
          {error ? <div className="state-card state-card--error">{error}</div> : null}

          <label className="field field--full">
            <span>Comentario de fechamento</span>
            <textarea
              value={closeComment}
              onChange={(event) => setCloseComment(event.target.value)}
              placeholder="Registre a validacao final, aceite e observacoes de auditoria."
              required
            />
          </label>

          <div className="form-actions">
            <button className="button-secondary" type="button" onClick={onClose} disabled={isSubmitting}>
              Cancelar
            </button>
            <button className="button-primary" type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Fechando..." : "Fechar chamado"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
