import { useEffect, useState } from "react";

import { listSuppliers } from "../../api/supplierApi";
import { startTicketExecution } from "../../api/ticketApi";
import type { Supplier } from "../../types/supplier";
import type { TicketDetail } from "../../types/ticket";
import { formatDateTimeLocalInput } from "./ticketUi";

interface Props {
  ticket: TicketDetail;
  token: string;
  onClose: () => void;
  onSuccess: (updated: TicketDetail) => void;
}

export default function StartExecutionModal({ ticket, token, onClose, onSuccess }: Props) {
  const [executionComment, setExecutionComment] = useState("");
  const [supplierId, setSupplierId] = useState<string>("");
  const [expectedResolutionAt, setExpectedResolutionAt] = useState("");
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listSuppliers(token, { is_active: true, page_size: 100 })
      .then((res) => setSuppliers(res.items))
      .catch(() => setSuppliers([]));
  }, [token]);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!executionComment.trim()) {
      setError("Comentario de execucao e obrigatorio.");
      return;
    }
    setIsSubmitting(true);
    setError(null);

    startTicketExecution(token, ticket.id, {
      execution_comment: executionComment.trim(),
      supplier_id: supplierId ? Number(supplierId) : undefined,
      expected_resolution_at: expectedResolutionAt ? new Date(expectedResolutionAt).toISOString() : undefined,
    })
      .then((updated) => onSuccess(updated))
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Erro ao iniciar execucao.");
        setIsSubmitting(false);
      });
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal__header">
          <h2>Iniciar execucao</h2>
          <button className="modal__close" type="button" onClick={onClose}>
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className="modal__body">
          {error ? <div className="state-card state-card--error">{error}</div> : null}

          <p className="eyebrow">
            {ticket.ticket_number} · {ticket.title}
          </p>

          <div className="field">
            <label htmlFor="start-exec-comment">Comentario de execucao *</label>
            <textarea
              id="start-exec-comment"
              className="input"
              rows={3}
              value={executionComment}
              onChange={(e) => setExecutionComment(e.target.value)}
              placeholder="Descreva o inicio da execucao..."
              required
            />
          </div>

          {suppliers.length > 0 ? (
            <div className="field">
              <label htmlFor="start-exec-supplier">Fornecedor (opcional)</label>
              <select
                id="start-exec-supplier"
                className="input"
                value={supplierId}
                onChange={(e) => setSupplierId(e.target.value)}
              >
                <option value="">Nenhum</option>
                {suppliers.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name} · {s.specialty}
                  </option>
                ))}
              </select>
            </div>
          ) : null}

          <div className="field">
            <label htmlFor="start-exec-expected">Previsao de conclusao (opcional)</label>
            <input
              id="start-exec-expected"
              type="datetime-local"
              className="input"
              value={expectedResolutionAt || formatDateTimeLocalInput(ticket.expected_resolution_at)}
              onChange={(e) => setExpectedResolutionAt(e.target.value)}
            />
          </div>

          <div className="modal__footer">
            <button className="button-secondary" type="button" onClick={onClose} disabled={isSubmitting}>
              Cancelar
            </button>
            <button className="button-primary" type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Iniciando..." : "Iniciar execucao"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
