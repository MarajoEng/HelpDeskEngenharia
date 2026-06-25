import { useEffect, useState } from "react";

import { listSuppliers } from "../../api/supplierApi";
import { updateTicketProgress } from "../../api/ticketApi";
import type { Supplier } from "../../types/supplier";
import type { TicketDetail } from "../../types/ticket";
import { formatDateTimeLocalInput } from "./ticketUi";

interface Props {
  ticket: TicketDetail;
  token: string;
  onClose: () => void;
  onSuccess: (updated: TicketDetail) => void;
}

export default function ProgressUpdateModal({ ticket, token, onClose, onSuccess }: Props) {
  const [progressComment, setProgressComment] = useState("");
  const [expectedResolutionAt, setExpectedResolutionAt] = useState(
    formatDateTimeLocalInput(ticket.expected_resolution_at),
  );
  const [estimatedCost, setEstimatedCost] = useState(ticket.estimated_cost ?? "");
  const [supplierId, setSupplierId] = useState<string>(ticket.supplier_id ? String(ticket.supplier_id) : "");
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
    if (!progressComment.trim()) {
      setError("Comentario de progresso e obrigatorio.");
      return;
    }
    setIsSubmitting(true);
    setError(null);

    updateTicketProgress(token, ticket.id, {
      progress_comment: progressComment.trim(),
      expected_resolution_at: expectedResolutionAt ? new Date(expectedResolutionAt).toISOString() : undefined,
      estimated_cost: estimatedCost || undefined,
      supplier_id: supplierId ? Number(supplierId) : undefined,
    })
      .then((updated) => onSuccess(updated))
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Erro ao registrar progresso.");
        setIsSubmitting(false);
      });
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal__header">
          <h2>Registrar progresso</h2>
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
            <label htmlFor="progress-comment">Comentario de progresso *</label>
            <textarea
              id="progress-comment"
              className="input"
              rows={3}
              value={progressComment}
              onChange={(e) => setProgressComment(e.target.value)}
              placeholder="Descreva o progresso atual..."
              required
            />
          </div>

          <div className="field">
            <label htmlFor="progress-expected">Previsao de conclusao</label>
            <input
              id="progress-expected"
              type="datetime-local"
              className="input"
              value={expectedResolutionAt}
              onChange={(e) => setExpectedResolutionAt(e.target.value)}
            />
          </div>

          <div className="field">
            <label htmlFor="progress-cost">Custo estimado (R$)</label>
            <input
              id="progress-cost"
              type="number"
              min="0"
              step="0.01"
              className="input"
              value={estimatedCost}
              onChange={(e) => setEstimatedCost(e.target.value)}
              placeholder="0.00"
            />
          </div>

          {suppliers.length > 0 ? (
            <div className="field">
              <label htmlFor="progress-supplier">Fornecedor</label>
              <select
                id="progress-supplier"
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

          <div className="modal__footer">
            <button className="button-secondary" type="button" onClick={onClose} disabled={isSubmitting}>
              Cancelar
            </button>
            <button className="button-primary" type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Salvando..." : "Registrar progresso"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
