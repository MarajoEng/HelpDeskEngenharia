import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import ApprovalDecisionModal from "../components/tickets/ApprovalDecisionModal";
import ProgressUpdateModal from "../components/tickets/ProgressUpdateModal";
import RequestApprovalModal from "../components/tickets/RequestApprovalModal";
import StartExecutionModal from "../components/tickets/StartExecutionModal";
import TriageTicketModal from "../components/tickets/TriageTicketModal";
import {
  APPROVAL_STATUS_LABELS,
  PRIORITY_LABELS,
  ROLE_LABELS,
  SEVERITY_LABELS,
  STATUS_LABELS,
  approvalStatusClass,
  canAccessEngineeringQueue,
  canManageApprovalRequest,
  canTriageTicketStatus,
  formatDate,
  formatMoney,
  priorityClass,
  statusClass,
  severityClass,
} from "../components/tickets/ticketUi";
import { getTicketById } from "../api/ticketApi";
import { useAuth } from "../hooks/useAuth";
import type { TicketApproval, TicketDetail, TicketHistory, SlaStatus, TicketStatus } from "../types/ticket";

const CATEGORY_LABELS: Record<string, string> = {
  fuel_pump: "Bomba de combustivel",
  fuel_nozzle: "Bico",
  electrical: "Eletrica",
  plumbing: "Hidraulica",
  leak: "Vazamento",
  structure: "Estrutura",
  roof: "Cobertura",
  pavement: "Pavimento",
  environmental_risk: "Risco ambiental",
  other: "Outro",
};

function slaStatusLabel(slaStatus: SlaStatus) {
  switch (slaStatus) {
    case "on_track":
      return "No prazo";
    case "late":
      return "Atrasado";
    case "no_sla":
      return "Sem SLA";
    case "closed":
      return "Encerrado";
  }
}

function slaStatusColor(slaStatus: SlaStatus) {
  switch (slaStatus) {
    case "on_track":
      return "var(--success)";
    case "late":
      return "var(--danger)";
    case "no_sla":
      return "var(--muted)";
    case "closed":
      return "var(--muted)";
  }
}

function HistoryTimeline({ history }: { history: TicketHistory[] }) {
  if (history.length === 0) {
    return <div className="state-card">Nenhum historico disponivel.</div>;
  }

  return (
    <div style={{ display: "grid", gap: "12px" }}>
      {history.map((entry, index) => (
        <div
          key={entry.id}
          style={{
            display: "grid",
            gridTemplateColumns: "auto 1fr",
            gap: "14px",
            alignItems: "flex-start",
          }}
        >
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: "0",
            }}
          >
            <div
              style={{
                width: "12px",
                height: "12px",
                borderRadius: "50%",
                background: index === 0 ? "var(--primary)" : "var(--muted)",
                flexShrink: 0,
                marginTop: "4px",
              }}
            />
            {index < history.length - 1 ? (
              <div
                style={{
                  width: "2px",
                  height: "32px",
                  background: "var(--line)",
                  marginTop: "4px",
                }}
              />
            ) : null}
          </div>
          <div
            style={{
              padding: "12px 14px",
              borderRadius: "14px",
              background: "rgba(255, 255, 255, 0.54)",
              border: "1px solid rgba(24, 37, 37, 0.08)",
              marginBottom: index < history.length - 1 ? "8px" : 0,
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "flex-start",
                gap: "12px",
                marginBottom: "4px",
              }}
            >
              <span style={{ fontWeight: 600, fontSize: "0.9rem" }}>
                {STATUS_LABELS[entry.new_status] ?? entry.new_status}
                {entry.old_status ? (
                  <span style={{ color: "var(--muted)", fontWeight: 400 }}>
                    {" "}← {STATUS_LABELS[entry.old_status] ?? entry.old_status}
                  </span>
                ) : null}
              </span>
              <span style={{ fontSize: "0.78rem", color: "var(--muted)", whiteSpace: "nowrap" }}>
                {formatDate(entry.created_at)}
              </span>
            </div>
            <div style={{ fontSize: "0.85rem", color: "var(--muted)" }}>
              {entry.user_name ?? `Usuario #${entry.user_id}`}
              {entry.comment ? <span> · {entry.comment}</span> : null}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

function ApprovalSection({
  ticket,
  pendingApproval,
}: {
  ticket: TicketDetail;
  pendingApproval: TicketApproval | null;
}) {
  if (ticket.approvals.length === 0) {
    return <div className="state-card">Nenhuma aprovacao registrada para este chamado.</div>;
  }

  return (
    <div className="approval-stack">
      {ticket.approvals.map((approval) => (
        <article className="approval-card" key={approval.id}>
          <div className="approval-card__header">
            <div>
              <h4 style={{ margin: "0 0 6px" }}>
                {approval.approval_level_name ?? "Aprovacao sem alcada"}
              </h4>
              <p className="page__description" style={{ margin: 0 }}>
                Solicitado por {approval.requested_by_user_name ?? `#${approval.requested_by_user_id}`} em{" "}
                {formatDate(approval.created_at)}
              </p>
            </div>
            <span className={approvalStatusClass(approval.status)}>
              {APPROVAL_STATUS_LABELS[approval.status]}
            </span>
          </div>

          <dl className="details-list">
            <div>
              <dt>Valor solicitado</dt>
              <dd>{formatMoney(approval.amount_requested)}</dd>
            </div>
            <div>
              <dt>Valor aprovado</dt>
              <dd>{formatMoney(approval.amount_approved)}</dd>
            </div>
            <div>
              <dt>Perfis permitidos</dt>
              <dd>{approval.approval_allowed_roles.map((role) => ROLE_LABELS[role]).join(", ") || "—"}</dd>
            </div>
            <div>
              <dt>Aprovador</dt>
              <dd>{approval.approved_by_user_name ?? "Pendente"}</dd>
            </div>
            <div>
              <dt>Data da decisao</dt>
              <dd>{formatDate(approval.approved_at)}</dd>
            </div>
            <div>
              <dt>Alcada aplicada</dt>
              <dd>{approval.approval_level_name ?? "Nao informada"}</dd>
            </div>
          </dl>

          <article className="info-card" style={{ marginTop: "16px" }}>
            <h2>Justificativa</h2>
            <p style={{ whiteSpace: "pre-wrap" }}>{approval.justification}</p>
          </article>

          {pendingApproval?.id === approval.id ? (
            <div className="state-card" style={{ marginTop: "16px" }}>
              Esta e a aprovacao pendente atualmente vinculada ao chamado.
            </div>
          ) : null}
        </article>
      ))}
    </div>
  );
}

export default function TicketDetailPage() {
  const { ticketId } = useParams();
  const { token, user } = useAuth();
  const [ticket, setTicket] = useState<TicketDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [isTriageOpen, setIsTriageOpen] = useState(false);
  const [isRequestApprovalOpen, setIsRequestApprovalOpen] = useState(false);
  const [isDecisionOpen, setIsDecisionOpen] = useState(false);
  const [isStartExecutionOpen, setIsStartExecutionOpen] = useState(false);
  const [isProgressOpen, setIsProgressOpen] = useState(false);

  useEffect(() => {
    if (!token || !ticketId) return;

    let isActive = true;
    setIsLoading(true);
    setErrorMessage(null);

    getTicketById(token, Number(ticketId))
      .then((response) => {
        if (!isActive) return;
        setTicket(response);
      })
      .catch((error: unknown) => {
        if (!isActive) return;
        setErrorMessage(error instanceof Error ? error.message : "Nao foi possivel carregar o chamado.");
      })
      .finally(() => {
        if (isActive) {
          setIsLoading(false);
        }
      });

    return () => {
      isActive = false;
    };
  }, [ticketId, token]);

  const pendingApproval = useMemo(() => {
    if (!ticket) return null;
    return [...ticket.approvals].reverse().find((approval) => approval.status === "pending") ?? null;
  }, [ticket]);

  if (isLoading) {
    return (
      <section className="page">
        <div className="state-card">Carregando chamado...</div>
      </section>
    );
  }

  if (errorMessage) {
    return (
      <section className="page">
        <div className="state-card state-card--error">{errorMessage}</div>
      </section>
    );
  }

  if (!ticket) {
    return (
      <section className="page">
        <div className="state-card">Chamado nao encontrado.</div>
      </section>
    );
  }

  const { indicators } = ticket;
  const canAccessTriage = canAccessEngineeringQueue(user?.role);
  const canOpenTriage = canTriageTicketStatus(ticket.status);
  const canRequestApproval = canManageApprovalRequest(user?.role) && ticket.status === "triage" && ticket.requires_approval;
  const canDecideApproval = Boolean(
    pendingApproval &&
      user &&
      pendingApproval.approval_allowed_roles.includes(user.role),
  );
  const shouldShowNoAuthorityMessage =
    Boolean(pendingApproval) &&
    ticket.status === "waiting_approval" &&
    Boolean(user) &&
    !canDecideApproval;

  const _executionFromStatuses: TicketStatus[] = ["triage", "approved"];
  const canStartExecution =
    canAccessEngineeringQueue(user?.role) &&
    _executionFromStatuses.includes(ticket.status) &&
    !(ticket.status === "triage" && ticket.requires_approval) &&
    !(ticket.status === "approved" && !ticket.requires_approval);
  const canUpdateProgress =
    canAccessEngineeringQueue(user?.role) && ticket.status === "in_progress";

  return (
    <section className="page">
      <div className="page__header">
        <div>
          <p className="eyebrow">Detalhe do chamado</p>
          <h2 className="page__title" style={{ fontFamily: "monospace", fontSize: "1.6rem" }}>
            {ticket.ticket_number}
          </h2>
          <p className="page__description">
            {ticket.unit ? `${ticket.unit.code} · ${ticket.unit.name}` : `Unidade #${ticket.unit_id}`}
          </p>
        </div>
        <div className="header-actions">
          {canAccessTriage ? (
            <button
              className="button-primary"
              type="button"
              disabled={!canOpenTriage}
              onClick={() => setIsTriageOpen(true)}
            >
              Fazer triagem
            </button>
          ) : null}
          {canRequestApproval ? (
            <button className="button-secondary" type="button" onClick={() => setIsRequestApprovalOpen(true)}>
              Solicitar aprovacao
            </button>
          ) : null}
          {canDecideApproval ? (
            <button className="button-secondary" type="button" onClick={() => setIsDecisionOpen(true)}>
              Decidir aprovacao
            </button>
          ) : null}
          {canStartExecution ? (
            <button className="button-secondary" type="button" onClick={() => setIsStartExecutionOpen(true)}>
              Iniciar execucao
            </button>
          ) : null}
          {canUpdateProgress ? (
            <button className="button-secondary" type="button" onClick={() => setIsProgressOpen(true)}>
              Registrar progresso
            </button>
          ) : null}
          <Link className="button-secondary button-primary--link" to="/tickets">
            Voltar
          </Link>
        </div>
      </div>

      {successMessage ? <div className="state-card state-card--success">{successMessage}</div> : null}
      {canAccessTriage && !canOpenTriage ? (
        <div className="state-card">
          A fase atual permite triagem apenas para chamados `open`, `waiting_unit` ou ja em `triage`.
        </div>
      ) : null}
      {shouldShowNoAuthorityMessage ? (
        <div className="state-card">
          Seu perfil nao possui alcada para aprovar este valor.
        </div>
      ) : null}

      <section className="panel panel--stack">
        <div className="ticket-summary">
          <div>
            <h3 style={{ margin: "0 0 6px" }}>{ticket.title}</h3>
            <p style={{ margin: 0, fontSize: "0.9rem", color: "var(--muted)" }}>
              {CATEGORY_LABELS[ticket.category] ?? ticket.category} · {ticket.problem_type}
            </p>
          </div>
          <div className="ticket-summary__meta">
            <span className={statusClass(ticket.status)}>{STATUS_LABELS[ticket.status]}</span>
            <span className={priorityClass(ticket.priority)}>{PRIORITY_LABELS[ticket.priority]}</span>
            <span className={severityClass(ticket.severity)}>{SEVERITY_LABELS[ticket.severity]}</span>
          </div>
        </div>

        <div>
          <h3
            style={{
              margin: "0 0 12px",
              fontSize: "0.95rem",
              textTransform: "uppercase",
              letterSpacing: "0.06em",
              color: "var(--muted)",
            }}
          >
            Indicadores
          </h3>
          <div className="details-list details-list--metrics">
            <div>
              <dt>SLA</dt>
              <dd style={{ color: slaStatusColor(indicators.sla_status) }}>{slaStatusLabel(indicators.sla_status)}</dd>
            </div>
            <div>
              <dt>Tempo decorrido</dt>
              <dd>{indicators.elapsed_hours != null ? `${indicators.elapsed_hours}h` : "—"}</dd>
            </div>
            <div>
              <dt>Perda estimada total</dt>
              <dd>{formatMoney(indicators.estimated_loss_total)}</dd>
            </div>
            <div>
              <dt>Atrasado</dt>
              <dd style={{ color: indicators.is_late ? "var(--danger)" : "var(--success)" }}>
                {indicators.is_late ? "Sim" : "Nao"}
              </dd>
            </div>
            {indicators.elapsed_execution_hours != null ? (
              <div>
                <dt>Tempo em execucao</dt>
                <dd>{indicators.elapsed_execution_hours}h</dd>
              </div>
            ) : null}
            {ticket.status === "in_progress" ? (
              <div>
                <dt>Execucao atrasada</dt>
                <dd style={{ color: indicators.execution_is_late ? "var(--danger)" : "var(--success)" }}>
                  {indicators.execution_is_late ? "Sim" : "Nao"}
                </dd>
              </div>
            ) : null}
          </div>
        </div>

        <div>
          <h3
            style={{
              margin: "0 0 12px",
              fontSize: "0.95rem",
              textTransform: "uppercase",
              letterSpacing: "0.06em",
              color: "var(--muted)",
            }}
          >
            Informacoes
          </h3>
          <dl className="details-list">
            <div>
              <dt>Unidade</dt>
              <dd>{ticket.unit ? `${ticket.unit.code} · ${ticket.unit.name}` : `#${ticket.unit_id}`}</dd>
            </div>
            <div>
              <dt>Cidade / Estado</dt>
              <dd>{ticket.unit ? `${ticket.unit.city} / ${ticket.unit.state}` : "—"}</dd>
            </div>
            <div>
              <dt>Solicitante</dt>
              <dd>{ticket.opened_by?.name ?? `#${ticket.opened_by_user_id}`}</dd>
            </div>
            <div>
              <dt>Responsavel</dt>
              <dd>{ticket.assigned_to?.name ?? "Nao atribuido"}</dd>
            </div>
            <div>
              <dt>Data de abertura</dt>
              <dd>{formatDate(ticket.opened_at)}</dd>
            </div>
            <div>
              <dt>Triagem iniciada em</dt>
              <dd>{formatDate(ticket.triaged_at)}</dd>
            </div>
            <div>
              <dt>SLA previsto</dt>
              <dd>{formatDate(ticket.sla_due_at)}</dd>
            </div>
            <div>
              <dt>Exige aprovacao</dt>
              <dd>{ticket.requires_approval ? "Sim" : "Nao"}</dd>
            </div>
            <div>
              <dt>Bicos parados</dt>
              <dd>{ticket.fuel_nozzles_stopped != null ? ticket.fuel_nozzles_stopped : "Nao informado"}</dd>
            </div>
            <div>
              <dt>Perda diaria estimada</dt>
              <dd>{formatMoney(ticket.estimated_daily_loss)}</dd>
            </div>
            <div>
              <dt>Custo estimado</dt>
              <dd>{formatMoney(ticket.estimated_cost)}</dd>
            </div>
            <div>
              <dt>Custo aprovado</dt>
              <dd>{formatMoney(ticket.approved_cost)}</dd>
            </div>
            <div>
              <dt>Previsao de conclusao</dt>
              <dd>{formatDate(ticket.expected_resolution_at)}</dd>
            </div>
            <div>
              <dt>Fornecedor</dt>
              <dd>
                {ticket.supplier
                  ? `${ticket.supplier.name} · ${ticket.supplier.specialty}`
                  : "Nao informado"}
              </dd>
            </div>
            <div>
              <dt>Ultima atualizacao</dt>
              <dd>{formatDate(ticket.updated_at)}</dd>
            </div>
          </dl>
        </div>

        <article className="info-card">
          <h2>Descricao</h2>
          <p>{ticket.description}</p>
        </article>

        {ticket.operational_impact ? (
          <article className="info-card">
            <h2>Impacto operacional</h2>
            <p>{ticket.operational_impact}</p>
          </article>
        ) : null}

        <div>
          <h3
            style={{
              margin: "0 0 16px",
              fontSize: "0.95rem",
              textTransform: "uppercase",
              letterSpacing: "0.06em",
              color: "var(--muted)",
            }}
          >
            Aprovacoes
          </h3>
          <ApprovalSection ticket={ticket} pendingApproval={pendingApproval} />
        </div>

        <div>
          <h3
            style={{
              margin: "0 0 16px",
              fontSize: "0.95rem",
              textTransform: "uppercase",
              letterSpacing: "0.06em",
              color: "var(--muted)",
            }}
          >
            Historico
          </h3>
          <HistoryTimeline history={ticket.history} />
        </div>

        <article className="state-card">
          Encerramento, upload, dashboard, relatorios e Celery continuam fora do escopo desta fase.
        </article>
      </section>

      {isTriageOpen && token && user ? (
        <TriageTicketModal
          ticket={ticket}
          token={token}
          user={user}
          onClose={() => setIsTriageOpen(false)}
          onSuccess={(updatedTicket) => {
            setTicket(updatedTicket);
            setIsTriageOpen(false);
            setSuccessMessage(`Triagem registrada para ${updatedTicket.ticket_number}.`);
          }}
        />
      ) : null}

      {isRequestApprovalOpen && token ? (
        <RequestApprovalModal
          ticket={ticket}
          token={token}
          onClose={() => setIsRequestApprovalOpen(false)}
          onSuccess={(updatedTicket) => {
            setTicket(updatedTicket);
            setIsRequestApprovalOpen(false);
            setSuccessMessage(`Solicitacao de aprovacao registrada para ${updatedTicket.ticket_number}.`);
          }}
        />
      ) : null}

      {isDecisionOpen && token && pendingApproval ? (
        <ApprovalDecisionModal
          ticket={ticket}
          approval={pendingApproval}
          token={token}
          onClose={() => setIsDecisionOpen(false)}
          onSuccess={(updatedTicket) => {
            setTicket(updatedTicket);
            setIsDecisionOpen(false);
            setSuccessMessage(`Decisao de aprovacao registrada para ${updatedTicket.ticket_number}.`);
          }}
        />
      ) : null}

      {isStartExecutionOpen && token ? (
        <StartExecutionModal
          ticket={ticket}
          token={token}
          onClose={() => setIsStartExecutionOpen(false)}
          onSuccess={(updatedTicket) => {
            setTicket(updatedTicket);
            setIsStartExecutionOpen(false);
            setSuccessMessage(`Execucao iniciada para ${updatedTicket.ticket_number}.`);
          }}
        />
      ) : null}

      {isProgressOpen && token ? (
        <ProgressUpdateModal
          ticket={ticket}
          token={token}
          onClose={() => setIsProgressOpen(false)}
          onSuccess={(updatedTicket) => {
            setTicket(updatedTicket);
            setIsProgressOpen(false);
            setSuccessMessage(`Progresso registrado para ${updatedTicket.ticket_number}.`);
          }}
        />
      ) : null}
    </section>
  );
}
