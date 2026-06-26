import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { listTickets } from "../api/ticketApi";
import { getBranchesByGroup, getGroupOptions, listUnits } from "../api/unitApi";
import TriageTicketModal from "../components/tickets/TriageTicketModal";
import Button from "../components/ui/Button";
import EmptyState from "../components/ui/EmptyState";
import ErrorState from "../components/ui/ErrorState";
import FilterBar from "../components/ui/FilterBar";
import LoadingState from "../components/ui/LoadingState";
import PageHeader from "../components/ui/PageHeader";
import Pagination from "../components/ui/Pagination";
import PriorityBadge from "../components/ui/PriorityBadge";
import SeverityBadge from "../components/ui/SeverityBadge";
import StatCard from "../components/ui/StatCard";
import StatusBadge from "../components/ui/StatusBadge";
import Table from "../components/ui/Table";
import {
  PRIORITY_LABELS,
  SEVERITY_LABELS,
  STATUS_LABELS,
  canAccessEngineeringQueue,
  formatDate,
  isSlaLate,
} from "../components/tickets/ticketUi";
import { useAuth } from "../hooks/useAuth";
import type { Ticket, TicketFilters, TicketPriority, TicketSeverity, TicketStatus } from "../types/ticket";
import type { Unit } from "../types/unit";
import { getErrorMessage, LIST_EMPTY_MESSAGES } from "../utils/messages";

const initialFilters: TicketFilters = {
  queue: "engineering",
  page: 1,
  page_size: 20,
  unit_id: "",
  group_code: "",
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

    void listUnits(token, { page: 1, page_size: 100 })
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
        setErrorMessage(getErrorMessage(error, "Nao foi possivel carregar a fila da engenharia."));
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
  }, [canAccessPage, filters.group_code, filters.only_late, filters.priority, filters.severity, filters.unit_id, reloadKey, token]);

  const groupOptions = getGroupOptions(units);
  const branchOptions = filters.group_code ? getBranchesByGroup(units, filters.group_code) : [];

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
        <PageHeader
          eyebrow="Engenharia"
          title="Acesso indisponivel"
          description="A fila de triagem e reservada para admin e engineering."
        />
        <ErrorState description="Seu perfil nao pode acessar a fila da engenharia." />
      </section>
    );
  }

  return (
    <section className="page">
      <PageHeader
        eyebrow="Engenharia central"
        title="Fila da engenharia"
        description="Triagem tecnica, priorizacao, atribuicao e definicao de SLA da operacao."
      />

      <section className="summary-grid">
        <StatCard
          label="Na fila"
          tone="accent"
          value={isLoadingSummary ? "..." : summary.total}
          description="Chamados elegiveis para triagem com os filtros atuais."
        />
        <StatCard
          label="Abertos"
          tone="info"
          value={isLoadingSummary ? "..." : summary.open}
          description="Itens ainda sem passagem tecnica da engenharia."
        />
        <StatCard
          label="Em triagem"
          tone="warning"
          value={isLoadingSummary ? "..." : summary.triage}
          description="Chamados com analise tecnica ativa nesta fase."
        />
        <StatCard
          label="Ag. unidade"
          tone="neutral"
          value={isLoadingSummary ? "..." : summary.waiting_unit}
          description="Chamados que podem voltar para nova tratativa tecnica."
        />
      </section>

      <section className="panel">
        <FilterBar columns={6} className="engineering-filters">
          <label className="field">
            <span>Grupo</span>
            <select
              value={filters.group_code ?? ""}
              onChange={(event) => {
                setFilter("group_code", event.target.value);
                setFilter("unit_id", "");
              }}
            >
              <option value="">Todos</option>
              {groupOptions.map((group) => (
                <option key={group} value={group}>{group}</option>
              ))}
            </select>
          </label>

          <label className="field">
            <span>Filial</span>
            <select
              value={String(filters.unit_id ?? "")}
              onChange={(event) => setFilter("unit_id", event.target.value === "" ? "" : Number(event.target.value))}
            >
              <option value="">{filters.group_code ? "Todas" : "Selecione grupo"}</option>
              {branchOptions.map((unit) => (
                <option key={unit.id} value={unit.id}>
                  {(unit.branch_code ?? unit.code)} — {unit.name}
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
        </FilterBar>

        <div className="engineering-toolbar">
          <span className="text-muted">Use a fila para assumir responsavel, ajustar criticidade e definir SLA.</span>
          <Button variant="secondary" type="button" onClick={clearFilters}>
            Limpar filtros
          </Button>
        </div>

        {successMessage ? <div className="state-card state-card--success">{successMessage}</div> : null}
        {isLoading ? <LoadingState title="Carregando fila da engenharia" description="Atualizando chamados elegiveis para triagem." /> : null}
        {!isLoading && errorMessage ? <ErrorState description={errorMessage} /> : null}
        {!isLoading && !errorMessage && data.items.length === 0 ? (
          <EmptyState
            title="Fila sem chamados"
            description={LIST_EMPTY_MESSAGES.engineering}
          />
        ) : null}

        {!isLoading && !errorMessage && data.items.length > 0 ? (
          <>
            <Table minWidth={980}>
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
                      <td style={{ maxWidth: "220px" }}>
                        <span style={{ display: "block", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                          {[ticket.unit_code, ticket.unit_name].filter(Boolean).join(" · ") || `#${ticket.unit_id}`}
                        </span>
                      </td>
                      <td style={{ maxWidth: "260px" }}>
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
                      <td style={{ maxWidth: "180px" }}>
                        <span style={{ display: "block", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                          {ticket.assigned_to_user_name ?? "Nao atribuido"}
                        </span>
                      </td>
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
                          <Button variant="secondary" size="sm" type="button" onClick={() => setSelectedTicket(ticket)}>
                            Fazer triagem
                          </Button>
                          <Link className="ui-link-button" to={`/tickets/${ticket.id}`}>
                            Detalhe
                          </Link>
                        </div>
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
              onPrevious={() => setFilters((current) => ({ ...current, page: Math.max(1, (current.page || 1) - 1) }))}
              onNext={() => setFilters((current) => ({ ...current, page: (current.page || 1) + 1 }))}
            />
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
