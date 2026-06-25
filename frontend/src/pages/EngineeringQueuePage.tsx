import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { listTickets } from "../api/ticketApi";
import { listUnits } from "../api/unitApi";
import TriageTicketModal from "../components/tickets/TriageTicketModal";
import {
  PRIORITY_LABELS,
  SEVERITY_LABELS,
  STATUS_LABELS,
  canAccessEngineeringQueue,
  formatDate,
  isSlaLate,
  priorityClass,
  severityClass,
  statusClass,
} from "../components/tickets/ticketUi";
import { useAuth } from "../hooks/useAuth";
import type { Ticket, TicketFilters, TicketPriority, TicketSeverity, TicketStatus } from "../types/ticket";
import type { Unit } from "../types/unit";

const initialFilters: TicketFilters = {
  queue: "engineering",
  page: 1,
  page_size: 20,
  unit_id: "",
  status: "",
  priority: "",
  severity: "",
  only_late: "",
};

const statusOptions: TicketStatus[] = ["open", "triage", "waiting_unit"];
const priorityOptions: TicketPriority[] = ["low", "medium", "high", "critical"];
const severityOptions: TicketSeverity[] = ["low", "medium", "high", "critical"];

interface QueueSummary {
  total: number;
  open: number;
  triage: number;
  waiting_unit: number;
}

export default function EngineeringQueuePage() {
  const { token, user } = useAuth();
  const [filters, setFilters] = useState<TicketFilters>(initialFilters);
  const [data, setData] = useState<{ items: Ticket[]; total: number; page: number; page_size: number; pages: number }>({
    items: [],
    total: 0,
    page: 1,
    page_size: 20,
    pages: 0,
  });
  const [summary, setSummary] = useState<QueueSummary>({
    total: 0,
    open: 0,
    triage: 0,
    waiting_unit: 0,
  });
  const [units, setUnits] = useState<Unit[]>([]);
  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingSummary, setIsLoadingSummary] = useState(true);
  const [reloadKey, setReloadKey] = useState(0);

  const canAccessPage = canAccessEngineeringQueue(user?.role);

  useEffect(() => {
    if (!token || !canAccessPage) return;

    void listUnits(token, { page: 1, page_size: 100, sort: "name_asc" })
      .then((response) => setUnits(response.items))
      .catch(() => setUnits([]));
  }, [canAccessPage, token]);

  useEffect(() => {
    if (!token || !canAccessPage) {
      setIsLoading(false);
      return;
    }

    let isActive = true;
    setIsLoading(true);
    setErrorMessage(null);

    listTickets(token, filters)
      .then((response) => {
        if (!isActive) return;
        setData(response);
      })
      .catch((error: unknown) => {
        if (!isActive) return;
        setErrorMessage(error instanceof Error ? error.message : "Nao foi possivel carregar a fila da engenharia.");
      })
      .finally(() => {
        if (isActive) {
          setIsLoading(false);
        }
      });

    return () => {
      isActive = false;
    };
  }, [
    canAccessPage,
    filters.only_late,
    filters.page,
    filters.page_size,
    filters.priority,
    filters.queue,
    filters.severity,
    filters.status,
    filters.unit_id,
    reloadKey,
    token,
  ]);

  useEffect(() => {
    if (!token || !canAccessPage) {
      setIsLoadingSummary(false);
      return;
    }

    let isActive = true;
    setIsLoadingSummary(true);

    const sharedFilters: TicketFilters = {
      queue: "engineering",
      page: 1,
      page_size: 1,
      unit_id: filters.unit_id,
      priority: filters.priority,
      severity: filters.severity,
      only_late: filters.only_late,
    };

    Promise.all([
      listTickets(token, sharedFilters),
      listTickets(token, { ...sharedFilters, status: "open" }),
      listTickets(token, { ...sharedFilters, status: "triage" }),
      listTickets(token, { ...sharedFilters, status: "waiting_unit" }),
    ])
      .then(([allTickets, openTickets, triageTickets, waitingUnitTickets]) => {
        if (!isActive) return;
        setSummary({
          total: allTickets.total,
          open: openTickets.total,
          triage: triageTickets.total,
          waiting_unit: waitingUnitTickets.total,
        });
      })
      .catch(() => {
        if (!isActive) return;
        setSummary({ total: 0, open: 0, triage: 0, waiting_unit: 0 });
      })
      .finally(() => {
        if (isActive) {
          setIsLoadingSummary(false);
        }
      });

    return () => {
      isActive = false;
    };
  }, [canAccessPage, filters.only_late, filters.priority, filters.severity, filters.unit_id, reloadKey, token]);

  function setFilter<K extends keyof TicketFilters>(key: K, value: TicketFilters[K]) {
    setFilters((current) => ({ ...current, page: 1, [key]: value }));
  }

  function clearFilters() {
    setFilters(initialFilters);
    setSuccessMessage(null);
  }

  function refreshQueue() {
    setReloadKey((current) => current + 1);
  }

  if (!canAccessPage) {
    return (
      <section className="page">
        <div className="page__header">
          <div>
            <p className="eyebrow">Engenharia</p>
            <h2 className="page__title">Acesso indisponivel</h2>
            <p className="page__description">A fila de triagem e reservada para admin e engineering.</p>
          </div>
        </div>
        <div className="state-card state-card--error">Seu perfil nao pode acessar a fila da engenharia.</div>
      </section>
    );
  }

  return (
    <section className="page">
      <div className="page__header">
        <div>
          <p className="eyebrow">Engenharia central</p>
          <h2 className="page__title">Fila da engenharia</h2>
          <p className="page__description">
            Triagem tecnica de chamados abertos, em triagem ou aguardando retorno da unidade.
          </p>
        </div>
      </div>

      <section className="summary-grid">
        <article className="summary-card">
          <span className="summary-card__label">Na fila</span>
          <strong>{isLoadingSummary ? "..." : summary.total}</strong>
          <p>Chamados elegiveis para triagem com os filtros atuais.</p>
        </article>
        <article className="summary-card">
          <span className="summary-card__label">Abertos</span>
          <strong>{isLoadingSummary ? "..." : summary.open}</strong>
          <p>Itens ainda sem passagem tecnica da engenharia.</p>
        </article>
        <article className="summary-card">
          <span className="summary-card__label">Em triagem</span>
          <strong>{isLoadingSummary ? "..." : summary.triage}</strong>
          <p>Chamados com analise tecnica ativa nesta fase.</p>
        </article>
        <article className="summary-card">
          <span className="summary-card__label">Ag. unidade</span>
          <strong>{isLoadingSummary ? "..." : summary.waiting_unit}</strong>
          <p>Chamados que podem voltar para nova tratativa tecnica.</p>
        </article>
      </section>

      <section className="panel">
        <div className="filters engineering-filters">
          <label className="field">
            <span>Unidade</span>
            <select
              value={String(filters.unit_id ?? "")}
              onChange={(event) => setFilter("unit_id", event.target.value === "" ? "" : Number(event.target.value))}
            >
              <option value="">Todas</option>
              {units.map((unit) => (
                <option key={unit.id} value={unit.id}>
                  {unit.code} · {unit.name}
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            <span>Status</span>
            <select
              value={filters.status || ""}
              onChange={(event) => setFilter("status", (event.target.value as TicketStatus | "") || "")}
            >
              <option value="">Todos</option>
              {statusOptions.map((status) => (
                <option key={status} value={status}>
                  {STATUS_LABELS[status]}
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            <span>Prioridade</span>
            <select
              value={filters.priority || ""}
              onChange={(event) => setFilter("priority", (event.target.value as TicketPriority | "") || "")}
            >
              <option value="">Todas</option>
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
              value={filters.severity || ""}
              onChange={(event) => setFilter("severity", (event.target.value as TicketSeverity | "") || "")}
            >
              <option value="">Todas</option>
              {severityOptions.map((severity) => (
                <option key={severity} value={severity}>
                  {SEVERITY_LABELS[severity]}
                </option>
              ))}
            </select>
          </label>

          <label className="field field--checkbox engineering-filters__checkbox">
            <input
              type="checkbox"
              checked={filters.only_late === true}
              onChange={(event) => setFilter("only_late", event.target.checked ? true : "")}
            />
            <span>Somente atrasados</span>
          </label>
        </div>

        <div className="engineering-toolbar">
          <span className="text-muted">Use a fila para assumir responsavel, ajustar criticidade e definir SLA.</span>
          <button className="button-secondary" type="button" onClick={clearFilters}>
            Limpar filtros
          </button>
        </div>

        {successMessage ? <div className="state-card state-card--success">{successMessage}</div> : null}
        {isLoading ? <div className="state-card">Carregando fila da engenharia...</div> : null}
        {!isLoading && errorMessage ? <div className="state-card state-card--error">{errorMessage}</div> : null}
        {!isLoading && !errorMessage && data.items.length === 0 ? (
          <div className="state-card">
            Nenhum chamado da fila de engenharia corresponde aos filtros selecionados.
          </div>
        ) : null}

        {!isLoading && !errorMessage && data.items.length > 0 ? (
          <>
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Chamado</th>
                    <th>Unidade</th>
                    <th>Titulo</th>
                    <th>Status</th>
                    <th>Prioridade</th>
                    <th>Severidade</th>
                    <th>Responsavel</th>
                    <th>SLA</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((ticket) => {
                    const late = isSlaLate(ticket);
                    return (
                      <tr key={ticket.id}>
                        <td>
                          <span style={{ fontFamily: "monospace", fontSize: "0.85rem" }}>
                            {ticket.ticket_number}
                          </span>
                        </td>
                        <td>{[ticket.unit_code, ticket.unit_name].filter(Boolean).join(" · ") || `#${ticket.unit_id}`}</td>
                        <td style={{ maxWidth: "260px" }}>
                          <span style={{ display: "block", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                            {ticket.title}
                          </span>
                        </td>
                        <td>
                          <span className={statusClass(ticket.status)}>{STATUS_LABELS[ticket.status]}</span>
                        </td>
                        <td>
                          <span className={priorityClass(ticket.priority)}>{PRIORITY_LABELS[ticket.priority]}</span>
                        </td>
                        <td>
                          <span className={severityClass(ticket.severity)}>{SEVERITY_LABELS[ticket.severity]}</span>
                        </td>
                        <td>{ticket.assigned_to_user_name ?? "Nao atribuido"}</td>
                        <td>
                          {ticket.sla_due_at ? (
                            <span className={late ? "text-danger" : "text-muted"}>
                              {late ? "Atrasado" : formatDate(ticket.sla_due_at)}
                            </span>
                          ) : (
                            <span className="text-muted">Sem SLA</span>
                          )}
                        </td>
                        <td>
                          <div className="table-actions">
                            <button className="button-secondary" type="button" onClick={() => setSelectedTicket(ticket)}>
                              Fazer triagem
                            </button>
                            <Link className="button-link" to={`/tickets/${ticket.id}`}>
                              Detalhe
                            </Link>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            <div className="pagination-bar">
              <span style={{ fontSize: "0.9rem" }}>
                {data.total} chamado(s) · pagina {data.page} de {Math.max(data.pages, 1)}
              </span>
              <div className="pagination-actions">
                <button
                  className="button-secondary"
                  type="button"
                  disabled={data.page <= 1}
                  onClick={() => setFilters((current) => ({ ...current, page: Math.max(1, (current.page || 1) - 1) }))}
                >
                  Anterior
                </button>
                <button
                  className="button-secondary"
                  type="button"
                  disabled={data.pages === 0 || data.page >= data.pages}
                  onClick={() => setFilters((current) => ({ ...current, page: (current.page || 1) + 1 }))}
                >
                  Proxima
                </button>
              </div>
            </div>
          </>
        ) : null}
      </section>

      {selectedTicket && token && user ? (
        <TriageTicketModal
          ticket={selectedTicket}
          token={token}
          user={user}
          onClose={() => setSelectedTicket(null)}
          onSuccess={(updatedTicket) => {
            setSelectedTicket(null);
            setSuccessMessage(`Triagem registrada para ${updatedTicket.ticket_number}.`);
            setData((current) => ({
              ...current,
              items: current.items.map((item) => (item.id === updatedTicket.id ? { ...item, ...updatedTicket } : item)),
            }));
            refreshQueue();
          }}
        />
      ) : null}
    </section>
  );
}
