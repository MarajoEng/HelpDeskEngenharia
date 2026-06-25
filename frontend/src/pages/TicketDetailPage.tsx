import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { getTicketById } from "../api/ticketApi";
import { useAuth } from "../hooks/useAuth";
import type { TicketDetail, TicketHistory, TicketPriority, TicketSeverity, TicketStatus, SlaStatus } from "../types/ticket";

const STATUS_LABELS: Record<TicketStatus, string> = {
  open: "Aberto",
  triage: "Triagem",
  waiting_approval: "Ag. aprovacao",
  approved: "Aprovado",
  rejected: "Rejeitado",
  in_progress: "Em execucao",
  waiting_supplier: "Ag. fornecedor",
  waiting_unit: "Ag. unidade",
  resolved: "Resolvido",
  closed: "Encerrado",
  canceled: "Cancelado",
};

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

const PRIORITY_LABELS: Record<TicketPriority, string> = {
  low: "Baixa",
  medium: "Media",
  high: "Alta",
  critical: "Critica",
};

const SEVERITY_LABELS: Record<TicketSeverity, string> = {
  low: "Baixa",
  medium: "Media",
  high: "Alta",
  critical: "Critica",
};

function formatDate(value: string | null | undefined) {
  if (!value) return "—";
  return new Date(value).toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function moneyLabel(value: string | null | undefined) {
  if (!value) return "Nao informado";
  const parsed = Number(value);
  return Number.isNaN(parsed)
    ? value
    : new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(parsed);
}

function statusClass(status: TicketStatus) {
  if (status === "open") return "status-badge status-badge--info";
  if (status === "resolved" || status === "closed" || status === "approved") return "status-badge status-badge--success";
  if (status === "rejected" || status === "canceled") return "status-badge status-badge--danger";
  return "status-badge status-badge--muted";
}

function slaStatusLabel(slaStatus: SlaStatus) {
  switch (slaStatus) {
    case "on_track": return "No prazo";
    case "late": return "Atrasado";
    case "no_sla": return "Sem SLA";
    case "closed": return "Encerrado";
  }
}

function slaStatusColor(slaStatus: SlaStatus) {
  switch (slaStatus) {
    case "on_track": return "var(--success)";
    case "late": return "var(--danger)";
    case "no_sla": return "var(--muted)";
    case "closed": return "var(--muted)";
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
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "12px", marginBottom: "4px" }}>
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
              {entry.comment ? (
                <span> · {entry.comment}</span>
              ) : null}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

export default function TicketDetailPage() {
  const { ticketId } = useParams();
  const { token } = useAuth();
  const [ticket, setTicket] = useState<TicketDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

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
        if (isActive) setIsLoading(false);
      });

    return () => {
      isActive = false;
    };
  }, [ticketId, token]);

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
        <Link className="button-primary button-primary--link" to="/tickets">
          Voltar
        </Link>
      </div>

      <section className="panel panel--stack">
        {/* Cabecalho com status e badges */}
        <div className="ticket-summary">
          <div>
            <h3 style={{ margin: "0 0 6px" }}>{ticket.title}</h3>
            <p style={{ margin: 0, fontSize: "0.9rem", color: "var(--muted)" }}>
              {CATEGORY_LABELS[ticket.category] ?? ticket.category} · {ticket.problem_type}
            </p>
          </div>
          <div className="ticket-summary__meta">
            <span className={statusClass(ticket.status)}>
              {STATUS_LABELS[ticket.status] ?? ticket.status}
            </span>
            <span className={`priority-badge priority-badge--${ticket.priority}`}>
              {PRIORITY_LABELS[ticket.priority]}
            </span>
            <span className={`severity-badge severity-badge--${ticket.severity}`}>
              {SEVERITY_LABELS[ticket.severity]}
            </span>
          </div>
        </div>

        {/* Indicadores */}
        <div>
          <h3 style={{ margin: "0 0 12px", fontSize: "0.95rem", textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--muted)" }}>
            Indicadores
          </h3>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(4, minmax(0, 1fr))",
              gap: "12px",
            }}
          >
            <div
              style={{
                padding: "14px 16px",
                borderRadius: "16px",
                background: "rgba(255,255,255,0.6)",
                border: "1px solid var(--line)",
              }}
            >
              <p style={{ margin: "0 0 4px", fontSize: "0.72rem", textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--muted)" }}>
                SLA
              </p>
              <p style={{ margin: 0, fontWeight: 700, fontSize: "1rem", color: slaStatusColor(indicators.sla_status) }}>
                {slaStatusLabel(indicators.sla_status)}
              </p>
            </div>
            <div
              style={{
                padding: "14px 16px",
                borderRadius: "16px",
                background: "rgba(255,255,255,0.6)",
                border: "1px solid var(--line)",
              }}
            >
              <p style={{ margin: "0 0 4px", fontSize: "0.72rem", textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--muted)" }}>
                Tempo decorrido
              </p>
              <p style={{ margin: 0, fontWeight: 700, fontSize: "1rem" }}>
                {indicators.elapsed_hours != null ? `${indicators.elapsed_hours}h` : "—"}
              </p>
            </div>
            <div
              style={{
                padding: "14px 16px",
                borderRadius: "16px",
                background: "rgba(255,255,255,0.6)",
                border: "1px solid var(--line)",
              }}
            >
              <p style={{ margin: "0 0 4px", fontSize: "0.72rem", textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--muted)" }}>
                Perda estimada total
              </p>
              <p style={{ margin: 0, fontWeight: 700, fontSize: "1rem" }}>
                {moneyLabel(indicators.estimated_loss_total)}
              </p>
            </div>
            <div
              style={{
                padding: "14px 16px",
                borderRadius: "16px",
                background: indicators.is_late ? "rgba(185,56,56,0.08)" : "rgba(255,255,255,0.6)",
                border: indicators.is_late ? "1px solid rgba(185,56,56,0.2)" : "1px solid var(--line)",
              }}
            >
              <p style={{ margin: "0 0 4px", fontSize: "0.72rem", textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--muted)" }}>
                Atrasado
              </p>
              <p style={{ margin: 0, fontWeight: 700, fontSize: "1rem", color: indicators.is_late ? "var(--danger)" : "var(--success)" }}>
                {indicators.is_late ? "Sim" : "Nao"}
              </p>
            </div>
          </div>
        </div>

        {/* Dados do chamado */}
        <div>
          <h3 style={{ margin: "0 0 12px", fontSize: "0.95rem", textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--muted)" }}>
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
              <dt>SLA previsto</dt>
              <dd>{formatDate(ticket.sla_due_at)}</dd>
            </div>
            <div>
              <dt>Bicos parados</dt>
              <dd>{ticket.fuel_nozzles_stopped != null ? ticket.fuel_nozzles_stopped : "Nao informado"}</dd>
            </div>
            <div>
              <dt>Exige aprovacao</dt>
              <dd>{ticket.requires_approval ? "Sim" : "Nao"}</dd>
            </div>
            <div>
              <dt>Perda diaria estimada</dt>
              <dd>{moneyLabel(ticket.estimated_daily_loss)}</dd>
            </div>
            <div>
              <dt>Custo estimado</dt>
              <dd>{moneyLabel(ticket.estimated_cost)}</dd>
            </div>
          </dl>
        </div>

        {/* Descricao e impacto */}
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

        {/* Historico */}
        <div>
          <h3 style={{ margin: "0 0 16px", fontSize: "0.95rem", textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--muted)" }}>
            Historico
          </h3>
          <HistoryTimeline history={ticket.history} />
        </div>

        {/* Aviso de proxima fase */}
        <article className="state-card">
          Triagem da engenharia, comentarios e mudanca de status serao implementados na FASE 7.
        </article>
      </section>
    </section>
  );
}
