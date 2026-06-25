import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { listTickets } from "../api/ticketApi";
import { listUnits } from "../api/unitApi";
import Button from "../components/ui/Button";
import EmptyState from "../components/ui/EmptyState";
import ErrorState from "../components/ui/ErrorState";
import FilterBar from "../components/ui/FilterBar";
import LoadingState from "../components/ui/LoadingState";
import PageHeader from "../components/ui/PageHeader";
import Pagination from "../components/ui/Pagination";
import PriorityBadge from "../components/ui/PriorityBadge";
import SeverityBadge from "../components/ui/SeverityBadge";
import StatusBadge from "../components/ui/StatusBadge";
import Table from "../components/ui/Table";
import { useAuth } from "../hooks/useAuth";
import type { Ticket, TicketCategory, TicketFilters, TicketPriority, TicketSeverity, TicketStatus } from "../types/ticket";
import type { Unit } from "../types/unit";
import { formatDate, formatMoney } from "../utils/formatters";
import { getErrorMessage, LIST_EMPTY_MESSAGES } from "../utils/messages";
import { CATEGORY_LABELS, PRIORITY_LABELS, SEVERITY_LABELS, STATUS_LABELS } from "../components/ui/statusOptions";

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

const categoryOptions: Array<{ value: TicketCategory; label: string }> = Object.entries(CATEGORY_LABELS).map(([value, label]) => ({
  value: value as TicketCategory,
  label,
}));

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
        setErrorMessage(getErrorMessage(error, "Nao foi possivel carregar os chamados."));
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
        <PageHeader
          eyebrow="Chamados"
          title="Acesso indisponivel"
          description="Fornecedores nao acessam chamados nesta fase."
        />
        <ErrorState description="Seu perfil nao pode acessar a listagem de chamados." />
      </section>
    );
  }

  return (
    <section className="page">
      <PageHeader
        eyebrow="Operacao"
        title="Chamados"
        description="Listagem com filtros, prioridade operacional, SLA e acesso rapido ao detalhe."
        actions={
          <Link className="ui-button ui-button--primary button-primary--link" to="/tickets/new">
            Abrir chamado
          </Link>
        }
      />

      <section className="panel">
        <div style={{ display: "grid", gap: "16px", marginBottom: "20px" }}>
          <FilterBar columns={5} className="filters--form">
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
          </FilterBar>

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

            <Button type="button" variant="secondary" onClick={clearFilters} style={{ marginLeft: "auto" }}>
              Limpar filtros
            </Button>
          </div>
        </div>

        {isLoading ? <LoadingState title="Carregando chamados" description="Atualizando a fila operacional." /> : null}

        {!isLoading && errorMessage ? <ErrorState description={errorMessage} /> : null}

        {!isLoading && !errorMessage && data.items.length === 0 ? (
          <EmptyState
            title="Nenhum chamado encontrado"
            description={LIST_EMPTY_MESSAGES.tickets}
            action={
              <Link className="ui-link-button" to="/tickets/new">
                Abrir um novo chamado
              </Link>
            }
          />
        ) : null}

        {!isLoading && !errorMessage && data.items.length > 0 ? (
          <>
            <Table minWidth={1240}>
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
                  <th>Acoes</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((ticket) => {
                  const late = isSlaLate(ticket);
                  return (
                    <tr key={ticket.id}>
                      <td>
                        <span className="text-mono text-sm">{ticket.ticket_number}</span>
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
                        <StatusBadge status={ticket.status} />
                      </td>
                      <td>
                        <PriorityBadge priority={ticket.priority} />
                      </td>
                      <td>
                        <SeverityBadge severity={ticket.severity} />
                      </td>
                      <td className="text-sm">{formatDate(ticket.opened_at)}</td>
                      <td className="text-sm">{ticket.resolved_at ? formatDate(ticket.resolved_at) : "—"}</td>
                      <td className="text-sm">{ticket.closed_at ? formatDate(ticket.closed_at) : "—"}</td>
                      <td className="text-sm">{formatMoney(ticket.final_cost)}</td>
                      <td>
                        <span className={ticket.has_closing_evidence ? "ui-badge ui-badge--success" : "ui-badge ui-badge--neutral"}>
                          {ticket.has_closing_evidence ? "Com evidencia" : "Sem evidencia"}
                        </span>
                      </td>
                      <td>
                        {ticket.sla_due_at ? (
                          <span className={late ? "text-danger" : "text-muted"}>
                            {late ? "Atrasado" : formatDate(ticket.sla_due_at)}
                          </span>
                        ) : (
                          <span className="text-muted">—</span>
                        )}
                      </td>
                      <td>
                        <Link className="ui-link-button" to={`/tickets/${ticket.id}`}>
                          Detalhe
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </Table>

            <Pagination
              total={data.total}
              label="chamado(s)"
              page={data.page}
              pages={data.pages}
              onPrevious={() => setFilters((prev) => ({ ...prev, page: Math.max(1, (prev.page || 1) - 1) }))}
              onNext={() => setFilters((prev) => ({ ...prev, page: (prev.page || 1) + 1 }))}
            />
          </>
        ) : null}
      </section>
    </section>
  );
}
