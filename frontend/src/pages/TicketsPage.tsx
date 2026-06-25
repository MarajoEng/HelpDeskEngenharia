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
    void listUnits(token, { page: 1, page_size: 100 })
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
      <div className="space-y-6">
        <PageHeader
          eyebrow="Chamados"
          title="Acesso indisponivel"
          description="Fornecedores nao acessam chamados nesta fase."
        />
        <ErrorState description="Seu perfil nao pode acessar a listagem de chamados." />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <PageHeader
          eyebrow="Operacao"
          title="Chamados"
          description="Listagem com filtros, prioridade operacional, SLA e acesso rapido ao detalhe."
        />
        <Link
          to="/tickets/new"
          className="inline-flex items-center gap-2 px-4 py-2 bg-teal-600 text-white rounded-lg hover:bg-teal-700 font-medium text-sm transition-colors flex-shrink-0"
        >
          + Abrir chamado
        </Link>
      </div>

      {/* Filters card */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
        <FilterBar columns={6} dense={true}>
          <div className="flex flex-col gap-1">
            <label htmlFor="search-filter" className="block text-sm font-medium text-slate-700">Busca</label>
            <input
              id="search-filter"
              className="block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 placeholder-slate-400 focus:border-teal-500 focus:outline-none focus:ring-1 focus:ring-teal-500"
              value={filters.search || ""}
              onChange={(e) => setFilter("search", e.target.value)}
              placeholder="Numero, titulo, unidade..."
            />
          </div>

          {canFilterByUnit ? (
            <div className="flex flex-col gap-1">
              <label htmlFor="unit-filter" className="block text-sm font-medium text-slate-700">Unidade</label>
              <select
                id="unit-filter"
                className="block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 bg-white focus:border-teal-500 focus:outline-none focus:ring-1 focus:ring-teal-500"
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
            </div>
          ) : null}

          <div className="flex flex-col gap-1">
            <label htmlFor="status-filter" className="block text-sm font-medium text-slate-700">Status</label>
            <select
              id="status-filter"
              className="block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 bg-white focus:border-teal-500 focus:outline-none focus:ring-1 focus:ring-teal-500"
              value={filters.status || ""}
              onChange={(e) => setFilter("status", (e.target.value as TicketStatus | "") || "")}
            >
              <option value="">Todos</option>
              {statusOptions.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>

          <div className="flex flex-col gap-1">
            <label htmlFor="category-filter" className="block text-sm font-medium text-slate-700">Categoria</label>
            <select
              id="category-filter"
              className="block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 bg-white focus:border-teal-500 focus:outline-none focus:ring-1 focus:ring-teal-500"
              value={filters.category || ""}
              onChange={(e) => setFilter("category", (e.target.value as TicketCategory | "") || "")}
            >
              <option value="">Todas</option>
              {categoryOptions.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>

          <div className="flex flex-col gap-1">
            <label htmlFor="priority-filter" className="block text-sm font-medium text-slate-700">Prioridade</label>
            <select
              id="priority-filter"
              className="block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 bg-white focus:border-teal-500 focus:outline-none focus:ring-1 focus:ring-teal-500"
              value={filters.priority || ""}
              onChange={(e) => setFilter("priority", (e.target.value as TicketPriority | "") || "")}
            >
              <option value="">Todas</option>
              {priorityOptions.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>

          <div className="flex flex-col gap-1">
            <label htmlFor="severity-filter" className="block text-sm font-medium text-slate-700">Severidade</label>
            <select
              id="severity-filter"
              className="block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 bg-white focus:border-teal-500 focus:outline-none focus:ring-1 focus:ring-teal-500"
              value={filters.severity || ""}
              onChange={(e) => setFilter("severity", (e.target.value as TicketSeverity | "") || "")}
            >
              <option value="">Todas</option>
              {severityOptions.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>

          <div className="flex flex-col gap-1">
            <label htmlFor="mincost-filter" className="block text-sm font-medium text-slate-700">Custo min. (R$)</label>
            <input
              id="mincost-filter"
              type="number"
              min={0}
              step="0.01"
              className="block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 placeholder-slate-400 focus:border-teal-500 focus:outline-none focus:ring-1 focus:ring-teal-500"
              value={filters.min_estimated_cost || ""}
              onChange={(e) => setFilter("min_estimated_cost", e.target.value || "")}
              placeholder="0.00"
            />
          </div>

          <div className="flex flex-col gap-1">
            <label htmlFor="maxcost-filter" className="block text-sm font-medium text-slate-700">Custo max. (R$)</label>
            <input
              id="maxcost-filter"
              type="number"
              min={0}
              step="0.01"
              className="block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 placeholder-slate-400 focus:border-teal-500 focus:outline-none focus:ring-1 focus:ring-teal-500"
              value={filters.max_estimated_cost || ""}
              onChange={(e) => setFilter("max_estimated_cost", e.target.value || "")}
              placeholder="0.00"
            />
          </div>
        </FilterBar>

        <div className="flex items-center gap-6 mt-4 pt-4 border-t border-slate-100 flex-wrap">
          <label className="flex items-center gap-2 text-sm text-slate-700 cursor-pointer">
            <input
              type="checkbox"
              className="rounded border-slate-300 text-teal-600 focus:ring-teal-500"
              checked={filters.only_late === true}
              onChange={(e) => setFilter("only_late", e.target.checked ? true : "")}
            />
            <span>Somente atrasados</span>
          </label>

          <label className="flex items-center gap-2 text-sm text-slate-700 cursor-pointer">
            <input
              type="checkbox"
              className="rounded border-slate-300 text-teal-600 focus:ring-teal-500"
              checked={filters.has_fuel_nozzles_stopped === true}
              onChange={(e) => setFilter("has_fuel_nozzles_stopped", e.target.checked ? true : "")}
            />
            <span>Com bicos parados</span>
          </label>

          <div className="ml-auto flex items-center gap-2">
            <Button type="button" variant="secondary" size="sm" onClick={clearFilters}>
              Limpar filtros
            </Button>
          </div>
        </div>
      </div>

      {/* Results card */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {isLoading ? (
          <div className="p-6">
            <LoadingState title="Carregando chamados" description="Atualizando a fila operacional." />
          </div>
        ) : null}

        {!isLoading && errorMessage ? (
          <div className="p-6">
            <ErrorState description={errorMessage} />
          </div>
        ) : null}

        {!isLoading && !errorMessage && data.items.length === 0 ? (
          <EmptyState
            title="Nenhum chamado encontrado"
            description={LIST_EMPTY_MESSAGES.tickets}
            action={
              <Link
                to="/tickets/new"
                className="inline-flex items-center px-4 py-2 bg-teal-600 text-white rounded-lg hover:bg-teal-700 font-medium text-sm transition-colors"
              >
                Abrir um novo chamado
              </Link>
            }
          />
        ) : null}

        {!isLoading && !errorMessage && data.items.length > 0 ? (
          <>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200" style={{ minWidth: 1240 }}>
                <thead className="bg-slate-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider whitespace-nowrap">Chamado</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider whitespace-nowrap">Unidade</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider whitespace-nowrap">Solicitante</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider whitespace-nowrap">Titulo</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider whitespace-nowrap">Status</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider whitespace-nowrap">Prioridade</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider whitespace-nowrap">Severidade</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider whitespace-nowrap">Abertura</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider whitespace-nowrap">Resolvido</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider whitespace-nowrap">Fechado</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider whitespace-nowrap">Custo final</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider whitespace-nowrap">Evidencia</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider whitespace-nowrap">SLA</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider whitespace-nowrap">Acoes</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-slate-100">
                  {data.items.map((ticket) => {
                    const late = isSlaLate(ticket);
                    return (
                      <tr key={ticket.id} className="hover:bg-slate-50 transition-colors">
                        <td className="px-4 py-3 text-sm">
                          <span className="font-mono text-slate-900 text-xs">{ticket.ticket_number}</span>
                        </td>
                        <td className="px-4 py-3 text-sm text-slate-700">{unitLabel(ticket, units)}</td>
                        <td className="px-4 py-3 text-sm text-slate-500">
                          {ticket.opened_by_user_name ?? `#${ticket.opened_by_user_id}`}
                        </td>
                        <td className="px-4 py-3 text-sm text-slate-900 max-w-[200px]">
                          <span className="block truncate">{ticket.title}</span>
                        </td>
                        <td className="px-4 py-3">
                          <StatusBadge status={ticket.status} />
                        </td>
                        <td className="px-4 py-3">
                          <PriorityBadge priority={ticket.priority} />
                        </td>
                        <td className="px-4 py-3">
                          <SeverityBadge severity={ticket.severity} />
                        </td>
                        <td className="px-4 py-3 text-xs text-slate-500 whitespace-nowrap">{formatDate(ticket.opened_at)}</td>
                        <td className="px-4 py-3 text-xs text-slate-500 whitespace-nowrap">
                          {ticket.resolved_at ? formatDate(ticket.resolved_at) : "—"}
                        </td>
                        <td className="px-4 py-3 text-xs text-slate-500 whitespace-nowrap">
                          {ticket.closed_at ? formatDate(ticket.closed_at) : "—"}
                        </td>
                        <td className="px-4 py-3 text-sm text-slate-900 whitespace-nowrap">
                          {formatMoney(ticket.final_cost)}
                        </td>
                        <td className="px-4 py-3">
                          <span
                            className={
                              ticket.has_closing_evidence
                                ? "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800"
                                : "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-700"
                            }
                          >
                            {ticket.has_closing_evidence ? "Com evidencia" : "Sem evidencia"}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-xs whitespace-nowrap">
                          {ticket.sla_due_at ? (
                            <span className={late ? "text-red-600 font-semibold" : "text-slate-500"}>
                              {late ? "Atrasado" : formatDate(ticket.sla_due_at)}
                            </span>
                          ) : (
                            <span className="text-slate-400">—</span>
                          )}
                        </td>
                        <td className="px-4 py-3">
                          <Link
                            to={`/tickets/${ticket.id}`}
                            className="text-teal-600 hover:text-teal-800 font-semibold text-sm"
                          >
                            Detalhe
                          </Link>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            <div className="px-6 py-4 border-t border-slate-200">
              <Pagination
                total={data.total}
                label="chamado(s)"
                page={data.page}
                pages={data.pages}
                onPrevious={() => setFilters((prev) => ({ ...prev, page: Math.max(1, (prev.page || 1) - 1) }))}
                onNext={() => setFilters((prev) => ({ ...prev, page: (prev.page || 1) + 1 }))}
              />
            </div>
          </>
        ) : null}
      </div>
    </div>
  );
}
