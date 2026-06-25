import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { listTickets } from "../api/ticketApi";
import { listUnits } from "../api/unitApi";
import { useAuth } from "../hooks/useAuth";
import type { Ticket, TicketCategory, TicketFilters, TicketPriority, TicketSeverity, TicketStatus } from "../types/ticket";
import type { Unit } from "../types/unit";

const initialFilters: TicketFilters = {
  page: 1,
  page_size: 20,
  unit_id: "",
  status: "",
  category: "",
  priority: "",
  severity: "",
  requires_approval: "",
  search: "",
  only_late: "",
  has_fuel_nozzles_stopped: "",
  min_estimated_cost: "",
  max_estimated_cost: "",
};

const statusOptions: Array<{ value: TicketStatus; label: string }> = [
  { value: "open", label: "Aberto" },
  { value: "triage", label: "Triagem" },
  { value: "waiting_approval", label: "Ag. aprovacao" },
  { value: "approved", label: "Aprovado" },
  { value: "rejected", label: "Rejeitado" },
  { value: "in_progress", label: "Em execucao" },
  { value: "waiting_supplier", label: "Ag. fornecedor" },
  { value: "waiting_unit", label: "Ag. unidade" },
  { value: "resolved", label: "Resolvido" },
  { value: "closed", label: "Encerrado" },
  { value: "canceled", label: "Cancelado" },
];

const categoryOptions: Array<{ value: TicketCategory; label: string }> = [
  { value: "fuel_pump", label: "Bomba" },
  { value: "fuel_nozzle", label: "Bico" },
  { value: "electrical", label: "Eletrica" },
  { value: "plumbing", label: "Hidraulica" },
  { value: "leak", label: "Vazamento" },
  { value: "structure", label: "Estrutura" },
  { value: "roof", label: "Cobertura" },
  { value: "pavement", label: "Pavimento" },
  { value: "environmental_risk", label: "Risco ambiental" },
  { value: "other", label: "Outro" },
];

const priorityOptions: Array<{ value: TicketPriority; label: string }> = [
  { value: "low", label: "Baixa" },
  { value: "medium", label: "Media" },
  { value: "high", label: "Alta" },
  { value: "critical", label: "Critica" },
];

const severityOptions: Array<{ value: TicketSeverity; label: string }> = [
  { value: "low", label: "Baixa" },
  { value: "medium", label: "Media" },
  { value: "high", label: "Alta" },
  { value: "critical", label: "Critica" },
];

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

function formatDate(value: string) {
  return new Date(value).toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatMoney(value: string | null) {
  if (!value) return "—";
  const amount = Number(value);
  if (Number.isNaN(amount)) return value;
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(amount);
}

function statusClass(status: TicketStatus) {
  if (status === "open") return "status-badge status-badge--info";
  if (status === "resolved" || status === "closed" || status === "approved") return "status-badge status-badge--success";
  if (status === "rejected" || status === "canceled") return "status-badge status-badge--danger";
  return "status-badge status-badge--muted";
}

function priorityClass(priority: TicketPriority) {
  return `priority-badge priority-badge--${priority}`;
}

function severityClass(severity: TicketSeverity) {
  return `severity-badge severity-badge--${severity}`;
}

function unitLabel(ticket: Ticket, units: Unit[]) {
  if (ticket.unit_code || ticket.unit_name) {
    return [ticket.unit_code, ticket.unit_name].filter(Boolean).join(" · ");
  }
  const unit = units.find((item) => item.id === ticket.unit_id);
  if (!unit) return `#${ticket.unit_id}`;
  return `${unit.code} · ${unit.name}`;
}

function isSlaLate(ticket: Ticket) {
  if (!ticket.sla_due_at) return false;
  const finalStatuses: TicketStatus[] = ["resolved", "closed", "canceled"];
  if (finalStatuses.includes(ticket.status)) return false;
  return new Date(ticket.sla_due_at) < new Date();
}

export default function TicketsPage() {
  const { token, user } = useAuth();
  const [filters, setFilters] = useState<TicketFilters>(initialFilters);
  const [data, setData] = useState<{ items: Ticket[]; total: number; page: number; page_size: number; pages: number }>({
    items: [],
    total: 0,
    page: 1,
    page_size: 20,
    pages: 0,
  });
  const [units, setUnits] = useState<Unit[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const isSupplier = user?.role === "supplier";
  const canFilterByUnit = user?.role !== "manager";

  useEffect(() => {
    if (!token || !canFilterByUnit) return;
    void listUnits(token, { page: 1, page_size: 200, sort: "name_asc" })
      .then((response) => setUnits(response.items))
      .catch(() => setUnits([]));
  }, [token, canFilterByUnit]);

  useEffect(() => {
    if (!token || isSupplier) {
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
        setErrorMessage(error instanceof Error ? error.message : "Nao foi possivel carregar os chamados.");
      })
      .finally(() => {
        if (isActive) setIsLoading(false);
      });

    return () => {
      isActive = false;
    };
  }, [
    filters.category,
    filters.page,
    filters.page_size,
    filters.priority,
    filters.requires_approval,
    filters.search,
    filters.severity,
    filters.status,
    filters.unit_id,
    filters.only_late,
    filters.has_fuel_nozzles_stopped,
    filters.min_estimated_cost,
    filters.max_estimated_cost,
    isSupplier,
    token,
  ]);

  function setFilter<K extends keyof TicketFilters>(key: K, value: TicketFilters[K]) {
    setFilters((prev) => ({ ...prev, page: 1, [key]: value }));
  }

  function clearFilters() {
    setFilters(initialFilters);
  }

  if (isSupplier) {
    return (
      <section className="page">
        <div className="page__header">
          <div>
            <p className="eyebrow">Chamados</p>
            <h2 className="page__title">Acesso indisponivel</h2>
            <p className="page__description">Fornecedores nao acessam chamados nesta fase.</p>
          </div>
        </div>
        <div className="state-card state-card--error">Seu perfil nao pode acessar a listagem de chamados.</div>
      </section>
    );
  }

  return (
    <section className="page">
      <div className="page__header">
        <div>
          <p className="eyebrow">Operacao</p>
          <h2 className="page__title">Chamados</h2>
          <p className="page__description">Listagem com filtros avancados, busca textual e recorte por perfil.</p>
        </div>
        <Link className="button-primary button-primary--link" to="/tickets/new">
          Abrir chamado
        </Link>
      </div>

      <section className="panel">
        <div style={{ display: "grid", gap: "16px", marginBottom: "20px" }}>
          <div className="filters filters--form">
            <label className="field">
              <span>Busca</span>
              <input
                value={filters.search || ""}
                onChange={(e) => setFilter("search", e.target.value)}
                placeholder="Numero, titulo, unidade..."
              />
            </label>

            {canFilterByUnit ? (
              <label className="field">
                <span>Unidade</span>
                <select
                  value={String(filters.unit_id ?? "")}
                  onChange={(e) =>
                    setFilter("unit_id", e.target.value === "" ? "" : Number(e.target.value))
                  }
                >
                  <option value="">Todas</option>
                  {units.map((unit) => (
                    <option key={unit.id} value={unit.id}>
                      {unit.code} · {unit.name}
                    </option>
                  ))}
                </select>
              </label>
            ) : null}

            <label className="field">
              <span>Status</span>
              <select
                value={filters.status || ""}
                onChange={(e) => setFilter("status", (e.target.value as TicketStatus | "") || "")}
              >
                <option value="">Todos</option>
                {statusOptions.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </label>

            <label className="field">
              <span>Categoria</span>
              <select
                value={filters.category || ""}
                onChange={(e) => setFilter("category", (e.target.value as TicketCategory | "") || "")}
              >
                <option value="">Todas</option>
                {categoryOptions.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </label>

            <label className="field">
              <span>Prioridade</span>
              <select
                value={filters.priority || ""}
                onChange={(e) => setFilter("priority", (e.target.value as TicketPriority | "") || "")}
              >
                <option value="">Todas</option>
                {priorityOptions.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </label>

            <label className="field">
              <span>Severidade</span>
              <select
                value={filters.severity || ""}
                onChange={(e) => setFilter("severity", (e.target.value as TicketSeverity | "") || "")}
              >
                <option value="">Todas</option>
                {severityOptions.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </label>

            <label className="field">
              <span>Custo min. (R$)</span>
              <input
                type="number"
                min={0}
                step="0.01"
                value={filters.min_estimated_cost || ""}
                onChange={(e) => setFilter("min_estimated_cost", e.target.value || "")}
                placeholder="0.00"
              />
            </label>

            <label className="field">
              <span>Custo max. (R$)</span>
              <input
                type="number"
                min={0}
                step="0.01"
                value={filters.max_estimated_cost || ""}
                onChange={(e) => setFilter("max_estimated_cost", e.target.value || "")}
                placeholder="0.00"
              />
            </label>
          </div>

          <div style={{ display: "flex", gap: "24px", alignItems: "center", flexWrap: "wrap" }}>
            <label className="field field--checkbox" style={{ margin: 0 }}>
              <input
                type="checkbox"
                checked={filters.only_late === true}
                onChange={(e) => setFilter("only_late", e.target.checked ? true : "")}
              />
              <span>Somente atrasados</span>
            </label>

            <label className="field field--checkbox" style={{ margin: 0 }}>
              <input
                type="checkbox"
                checked={filters.has_fuel_nozzles_stopped === true}
                onChange={(e) => setFilter("has_fuel_nozzles_stopped", e.target.checked ? true : "")}
              />
              <span>Com bicos parados</span>
            </label>

            <button
              type="button"
              className="button-secondary"
              onClick={clearFilters}
              style={{ marginLeft: "auto" }}
            >
              Limpar filtros
            </button>
          </div>
        </div>

        {isLoading ? (
          <div className="state-card">Carregando chamados...</div>
        ) : null}

        {!isLoading && errorMessage ? (
          <div className="state-card state-card--error">{errorMessage}</div>
        ) : null}

        {!isLoading && !errorMessage && data.items.length === 0 ? (
          <div className="state-card">
            Nenhum chamado encontrado para os filtros selecionados.
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
                    <th>Solicitante</th>
                    <th>Titulo</th>
                    <th>Status</th>
                    <th>Prioridade</th>
                    <th>Severidade</th>
                    <th>Abertura</th>
                    <th>Resolvido em</th>
                    <th>Fechado em</th>
                    <th>Custo final</th>
                    <th>Evidencia final</th>
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
                        <td style={{ fontSize: "0.9rem" }}>{unitLabel(ticket, units)}</td>
                        <td style={{ fontSize: "0.9rem", color: "var(--muted)" }}>
                          {ticket.opened_by_user_name ?? `#${ticket.opened_by_user_id}`}
                        </td>
                        <td style={{ maxWidth: "220px" }}>
                          <span style={{ display: "block", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                            {ticket.title}
                          </span>
                        </td>
                        <td>
                          <span className={statusClass(ticket.status)}>
                            {STATUS_LABELS[ticket.status] ?? ticket.status}
                          </span>
                        </td>
                        <td>
                          <span className={priorityClass(ticket.priority)}>
                            {PRIORITY_LABELS[ticket.priority] ?? ticket.priority}
                          </span>
                        </td>
                        <td>
                          <span className={severityClass(ticket.severity)}>
                            {SEVERITY_LABELS[ticket.severity] ?? ticket.severity}
                          </span>
                        </td>
                        <td style={{ fontSize: "0.88rem", whiteSpace: "nowrap" }}>
                          {formatDate(ticket.opened_at)}
                        </td>
                        <td style={{ fontSize: "0.88rem", whiteSpace: "nowrap" }}>
                          {ticket.resolved_at ? formatDate(ticket.resolved_at) : "—"}
                        </td>
                        <td style={{ fontSize: "0.88rem", whiteSpace: "nowrap" }}>
                          {ticket.closed_at ? formatDate(ticket.closed_at) : "—"}
                        </td>
                        <td style={{ fontSize: "0.88rem", whiteSpace: "nowrap" }}>
                          {formatMoney(ticket.final_cost)}
                        </td>
                        <td>
                          <span className={ticket.has_closing_evidence ? "status-badge status-badge--success" : "status-badge status-badge--muted"}>
                            {ticket.has_closing_evidence ? "Com evidencia" : "Sem evidencia"}
                          </span>
                        </td>
                        <td>
                          {ticket.sla_due_at ? (
                            <span
                              style={{
                                fontSize: "0.82rem",
                                fontWeight: 600,
                                color: late ? "var(--danger)" : "var(--muted)",
                              }}
                            >
                              {late ? "Atrasado" : formatDate(ticket.sla_due_at)}
                            </span>
                          ) : (
                            <span style={{ color: "var(--muted)", fontSize: "0.82rem" }}>—</span>
                          )}
                        </td>
                        <td>
                          <Link className="button-link" to={`/tickets/${ticket.id}`}>
                            Detalhe
                          </Link>
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
                  onClick={() => setFilters((prev) => ({ ...prev, page: Math.max(1, (prev.page || 1) - 1) }))}
                >
                  Anterior
                </button>
                <button
                  className="button-secondary"
                  type="button"
                  disabled={data.pages === 0 || data.page >= data.pages}
                  onClick={() => setFilters((prev) => ({ ...prev, page: (prev.page || 1) + 1 }))}
                >
                  Proxima
                </button>
              </div>
            </div>
          </>
        ) : null}
      </section>
    </section>
  );
}
