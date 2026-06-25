import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { listTickets } from "../api/ticketApi";
import { listUnits } from "../api/unitApi";
import { useAuth } from "../hooks/useAuth";
import type { Ticket, TicketCategory, TicketFilters, TicketPriority, TicketSeverity, TicketStatus } from "../types/ticket";
import type { Unit } from "../types/unit";

const initialFilters: TicketFilters = {
  page: 1,
  page_size: 10,
  unit_id: "",
  status: "",
  category: "",
  priority: "",
  severity: "",
  requires_approval: "",
  search: "",
};

const statusOptions: Array<{ value: TicketStatus; label: string }> = [
  { value: "open", label: "Aberto" },
  { value: "triage", label: "Triagem" },
  { value: "waiting_approval", label: "Aguardando aprovacao" },
  { value: "approved", label: "Aprovado" },
  { value: "rejected", label: "Rejeitado" },
  { value: "in_progress", label: "Em execucao" },
  { value: "waiting_supplier", label: "Aguardando fornecedor" },
  { value: "waiting_unit", label: "Aguardando unidade" },
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

function formatDate(value: string) {
  return new Date(value).toLocaleString("pt-BR");
}

function labelFromValue(value: string) {
  return value.split("_").join(" ");
}

function statusClass(status: TicketStatus) {
  if (status === "open") {
    return "status-badge status-badge--info";
  }
  if (status === "resolved" || status === "closed" || status === "approved") {
    return "status-badge status-badge--success";
  }
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
  if (!unit) {
    return `Unidade #${ticket.unit_id}`;
  }
  return `${unit.code} · ${unit.name}`;
}

export default function TicketsPage() {
  const { token, user } = useAuth();
  const [filters, setFilters] = useState<TicketFilters>(initialFilters);
  const [data, setData] = useState<{ items: Ticket[]; total: number; page: number; page_size: number; pages: number }>({
    items: [],
    total: 0,
    page: 1,
    page_size: 10,
    pages: 0,
  });
  const [units, setUnits] = useState<Unit[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const isSupplier = user?.role === "supplier";
  const canFilterByUnit = user?.role !== "manager";

  useEffect(() => {
    if (!token || !canFilterByUnit) {
      return;
    }

    void listUnits(token, { page: 1, page_size: 100, sort: "name_asc" })
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
        if (!isActive) {
          return;
        }
        setData(response);
      })
      .catch((error: unknown) => {
        if (!isActive) {
          return;
        }
        setErrorMessage(error instanceof Error ? error.message : "Nao foi possivel carregar os chamados.");
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
    filters.category,
    filters.page,
    filters.page_size,
    filters.priority,
    filters.requires_approval,
    filters.search,
    filters.severity,
    filters.status,
    filters.unit_id,
    isSupplier,
    token,
  ]);

  if (isSupplier) {
    return (
      <section className="page">
        <div className="page__header">
          <div>
            <p className="eyebrow">Chamados</p>
            <h2 className="page__title">Listagem indisponivel para este perfil</h2>
            <p className="page__description">
              Fornecedores ainda nao participam da operacao de chamados nesta fase.
            </p>
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
          <p className="page__description">
            Listagem inicial com paginacao, filtros e recorte por perfil no backend.
          </p>
        </div>
        <Link className="button-primary button-primary--link" to="/tickets/new">
          Abrir chamado
        </Link>
      </div>

      <section className="panel">
        <div className="filters filters--form">
          <label className="field">
            <span>Busca</span>
            <input
              value={filters.search || ""}
              onChange={(event) =>
                setFilters((current) => ({ ...current, page: 1, search: event.target.value }))
              }
              placeholder="Numero, titulo ou descricao"
            />
          </label>

          {canFilterByUnit ? (
            <label className="field">
              <span>Unidade</span>
              <select
                value={String(filters.unit_id ?? "")}
                onChange={(event) =>
                  setFilters((current) => ({
                    ...current,
                    page: 1,
                    unit_id: event.target.value === "" ? "" : Number(event.target.value),
                  }))
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
              onChange={(event) =>
                setFilters((current) => ({
                  ...current,
                  page: 1,
                  status: (event.target.value as TicketStatus | "") || "",
                }))
              }
            >
              <option value="">Todos</option>
              {statusOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            <span>Categoria</span>
            <select
              value={filters.category || ""}
              onChange={(event) =>
                setFilters((current) => ({
                  ...current,
                  page: 1,
                  category: (event.target.value as TicketCategory | "") || "",
                }))
              }
            >
              <option value="">Todas</option>
              {categoryOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            <span>Prioridade</span>
            <select
              value={filters.priority || ""}
              onChange={(event) =>
                setFilters((current) => ({
                  ...current,
                  page: 1,
                  priority: (event.target.value as TicketPriority | "") || "",
                }))
              }
            >
              <option value="">Todas</option>
              {priorityOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            <span>Severidade</span>
            <select
              value={filters.severity || ""}
              onChange={(event) =>
                setFilters((current) => ({
                  ...current,
                  page: 1,
                  severity: (event.target.value as TicketSeverity | "") || "",
                }))
              }
            >
              <option value="">Todas</option>
              {severityOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
        </div>

        {isLoading ? <div className="state-card">Carregando chamados...</div> : null}
        {!isLoading && errorMessage ? <div className="state-card state-card--error">{errorMessage}</div> : null}
        {!isLoading && !errorMessage && data.items.length === 0 ? (
          <div className="state-card">Nenhum chamado encontrado para os filtros atuais.</div>
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
                    <th>Abertura</th>
                    <th>Acoes</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((ticket) => (
                    <tr key={ticket.id}>
                      <td>{ticket.ticket_number}</td>
                      <td>{unitLabel(ticket, units)}</td>
                      <td>{ticket.title}</td>
                      <td>
                        <span className={statusClass(ticket.status)}>{labelFromValue(ticket.status)}</span>
                      </td>
                      <td>
                        <span className={priorityClass(ticket.priority)}>{labelFromValue(ticket.priority)}</span>
                      </td>
                      <td>
                        <span className={severityClass(ticket.severity)}>{labelFromValue(ticket.severity)}</span>
                      </td>
                      <td>{formatDate(ticket.opened_at)}</td>
                      <td>
                        <Link className="button-link" to={`/tickets/${ticket.id}`}>
                          Ver detalhe
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="pagination-bar">
              <span>
                {data.total} registro(s) · pagina {data.page} de {Math.max(data.pages, 1)}
              </span>
              <div className="pagination-actions">
                <button
                  className="button-secondary"
                  type="button"
                  disabled={data.page <= 1}
                  onClick={() =>
                    setFilters((current) => ({ ...current, page: Math.max(1, (current.page || 1) - 1) }))
                  }
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
    </section>
  );
}
