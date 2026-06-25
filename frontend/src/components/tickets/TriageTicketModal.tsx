import { type FormEvent, useEffect, useState } from "react";

import { ApiError } from "../../api/http";
import { listTriageAssignees, triageTicket } from "../../api/ticketApi";
import type { CurrentUser } from "../../types/auth";
import type {
  TicketDetail,
  TicketPriority,
  TicketSeverity,
  TicketStatus,
  TicketTriagePayload,
} from "../../types/ticket";
import type { UserItem } from "../../types/user";
import {
  PRIORITY_LABELS,
  SEVERITY_LABELS,
  STATUS_LABELS,
  formatDateTimeLocalInput,
} from "./ticketUi";

interface TriageTicketTarget {
  id: number;
  ticket_number: string;
  title: string;
  status: TicketStatus;
  priority: TicketPriority;
  severity: TicketSeverity;
  requires_approval: boolean;
  sla_due_at: string | null;
  assigned_to_user_id: number | null;
  assigned_to?: { id: number; name: string } | null;
  assigned_to_user_name?: string | null;
}

interface TriageTicketModalProps {
  ticket: TriageTicketTarget;
  token: string;
  user: CurrentUser;
  onClose: () => void;
  onSuccess: (ticket: TicketDetail) => void;
}

interface TriageFormState {
  assigned_to_user_id: string;
  priority: TicketPriority;
  severity: TicketSeverity;
  requires_approval: boolean;
  sla_due_at: string;
  technical_comment: string;
}

const priorityOptions: TicketPriority[] = ["low", "medium", "high", "critical"];
const severityOptions: TicketSeverity[] = ["low", "medium", "high", "critical"];

function buildFormState(ticket: TriageTicketTarget): TriageFormState {
  return {
    assigned_to_user_id: ticket.assigned_to_user_id ? String(ticket.assigned_to_user_id) : "",
    priority: ticket.priority,
    severity: ticket.severity,
    requires_approval: ticket.requires_approval,
    sla_due_at: formatDateTimeLocalInput(ticket.sla_due_at),
    technical_comment: "",
  };
}

function buildFallbackAssignees(ticket: TriageTicketTarget, user: CurrentUser) {
  const options: UserItem[] = [
    {
      id: user.id,
      name: user.name,
      email: user.email,
      role: user.role,
      unit_id: user.unit_id,
      is_active: user.is_active,
      created_at: "",
      updated_at: "",
    },
  ];

  if (ticket.assigned_to_user_id && ticket.assigned_to_user_id !== user.id) {
    options.push({
      id: ticket.assigned_to_user_id,
      name: ticket.assigned_to?.name ?? ticket.assigned_to_user_name ?? `Usuario #${ticket.assigned_to_user_id}`,
      email: "",
      role: "engineering",
      unit_id: null,
      is_active: true,
      created_at: "",
      updated_at: "",
    });
  }

  return options;
}

function normalizeAssignees(items: UserItem[]) {
  const map = new Map<number, UserItem>();

  items.forEach((item) => {
    if (!map.has(item.id)) {
      map.set(item.id, item);
    }
  });

  return Array.from(map.values()).sort((left, right) => left.name.localeCompare(right.name, "pt-BR"));
}

export default function TriageTicketModal({
  ticket,
  token,
  user,
  onClose,
  onSuccess,
}: TriageTicketModalProps) {
  const [form, setForm] = useState<TriageFormState>(() => buildFormState(ticket));
  const [assignees, setAssignees] = useState<UserItem[]>(() => buildFallbackAssignees(ticket, user));
  const [isLoadingAssignees, setIsLoadingAssignees] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    setForm(buildFormState(ticket));
    setErrorMessage(null);
  }, [ticket]);

  useEffect(() => {
    let isActive = true;
    setIsLoadingAssignees(true);

    listTriageAssignees(token, { page: 1, page_size: 100 })
      .then((response) => {
        if (!isActive) return;

        const merged = normalizeAssignees([
          ...response.items,
          ...buildFallbackAssignees(ticket, user),
        ]);
        setAssignees(merged);
      })
      .catch(() => {
        if (!isActive) return;
        setAssignees(buildFallbackAssignees(ticket, user));
      })
      .finally(() => {
        if (isActive) {
          setIsLoadingAssignees(false);
        }
      });

    return () => {
      isActive = false;
    };
  }, [ticket, token, user]);

  function updateField<K extends keyof TriageFormState>(key: K, value: TriageFormState[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const technicalComment = form.technical_comment.trim();
    if (!technicalComment) {
      setErrorMessage("Informe um comentario tecnico para registrar a triagem.");
      return;
    }

    const payload: TicketTriagePayload = {
      assigned_to_user_id: form.assigned_to_user_id ? Number(form.assigned_to_user_id) : null,
      priority: form.priority,
      severity: form.severity,
      requires_approval: form.requires_approval,
      sla_due_at: form.sla_due_at ? new Date(form.sla_due_at).toISOString() : null,
      technical_comment: technicalComment,
    };

    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      const updatedTicket = await triageTicket(token, ticket.id, payload);
      onSuccess(updatedTicket);
    } catch (error: unknown) {
      if (error instanceof ApiError && error.status === 403) {
        setErrorMessage("Seu perfil nao pode executar a triagem deste chamado.");
      } else if (error instanceof ApiError && error.status === 409) {
        setErrorMessage("A triagem nao pode ser aplicada a partir do status atual do chamado.");
      } else {
        setErrorMessage(error instanceof Error ? error.message : "Nao foi possivel salvar a triagem.");
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
            <p className="eyebrow">Triagem tecnica</p>
            <h3>{ticket.ticket_number}</h3>
            <p className="page__description" style={{ margin: "8px 0 0" }}>
              {ticket.title} · status atual {STATUS_LABELS[ticket.status]}
            </p>
          </div>
          <button className="button-secondary" type="button" onClick={onClose} disabled={isSubmitting}>
            Fechar
          </button>
        </div>

        <form className="form-grid" onSubmit={handleSubmit}>
          <div className="ticket-triage-grid">
            <label className="field">
              <span>Responsavel tecnico</span>
              <select
                value={form.assigned_to_user_id}
                onChange={(event) => updateField("assigned_to_user_id", event.target.value)}
                disabled={isSubmitting}
              >
                <option value="">Nao atribuir agora</option>
                {assignees.map((assignee) => (
                  <option key={assignee.id} value={assignee.id}>
                    {assignee.name}
                  </option>
                ))}
              </select>
              <small className="field__hint">
                {isLoadingAssignees ? "Carregando responsaveis elegiveis..." : "Somente usuarios ativos com perfil engineering ou admin."}
              </small>
            </label>

            <label className="field">
              <span>Prioridade</span>
              <select
                value={form.priority}
                onChange={(event) => updateField("priority", event.target.value as TicketPriority)}
                disabled={isSubmitting}
              >
                {priorityOptions.map((priority) => (
                  <option key={priority} value={priority}>
                    {PRIORITY_LABELS[priority]}
                  </option>
                ))}
              </select>
            </label>

            <label className="field">
              <span>Severidade</span>
              <select
                value={form.severity}
                onChange={(event) => updateField("severity", event.target.value as TicketSeverity)}
                disabled={isSubmitting}
              >
                {severityOptions.map((severity) => (
                  <option key={severity} value={severity}>
                    {SEVERITY_LABELS[severity]}
                  </option>
                ))}
              </select>
            </label>

            <label className="field">
              <span>SLA previsto</span>
              <input
                type="datetime-local"
                value={form.sla_due_at}
                onChange={(event) => updateField("sla_due_at", event.target.value)}
                disabled={isSubmitting}
              />
            </label>

            <label className="field field--checkbox">
              <input
                type="checkbox"
                checked={form.requires_approval}
                onChange={(event) => updateField("requires_approval", event.target.checked)}
                disabled={isSubmitting}
              />
              <span>Exige aprovacao</span>
            </label>
          </div>

          <label className="field field--full">
            <span>Comentario tecnico obrigatorio *</span>
            <textarea
              value={form.technical_comment}
              onChange={(event) => updateField("technical_comment", event.target.value)}
              placeholder="Registre a avaliacao tecnica, a direcao da triagem e a justificativa das decisoes."
              disabled={isSubmitting}
            />
          </label>

          {errorMessage ? <div className="form-message form-message--error">{errorMessage}</div> : null}

          <div className="form-actions">
            <button className="button-secondary" type="button" onClick={onClose} disabled={isSubmitting}>
              Cancelar
            </button>
            <button className="button-primary" type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Salvando..." : "Salvar triagem"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
