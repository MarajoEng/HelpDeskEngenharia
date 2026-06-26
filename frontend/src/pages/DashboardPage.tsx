import type { ReactNode } from "react";
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { listAlerts } from "../api/alertApi";
import { getDashboardOverview } from "../api/dashboardApi";
import { listTicketCategories } from "../api/ticketConfigurationApi";
import { listUnits } from "../api/unitApi";
import type { TicketAlert } from "../types/alert";
import {
  PRIORITY_LABELS,
  SEVERITY_LABELS,
  STATUS_LABELS,
  formatDate,
  formatMoney,
  priorityClass,
  severityClass,
  statusClass,
} from "../components/tickets/ticketUi";
import { useAuth } from "../hooks/useAuth";
import type { DashboardFilters, DashboardOverview, DistributionItem, RankingItem } from "../types/dashboard";
import type { TicketCategory, TicketStatus } from "../types/ticket";
import type { TicketCategoryItem } from "../types/ticketConfiguration";
import type { Unit } from "../types/unit";

import FilterBar from "../components/ui/FilterBar";

const initialFilters: DashboardFilters = {
  date_from: "",
  date_to: "",
  unit_id: "",
  region: "",
  status: "",
  category: "",
  category_id: "",
};

const LEGACY_CATEGORY_LABELS: Record<TicketCategory, string> = {
  fuel_pump: "Bomba",
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

const statusOptions: Array<{ value: TicketStatus; label: string }> = Object.entries(STATUS_LABELS).map(([value, label]) => ({
  value: value as TicketStatus,
  label,
}));

function percentageWidth(items: DistributionItem[], total: number) {
  if (total <= 0) return 0;
  return Math.max(8, Math.round((items.length / total) * 100));
}

function distributionLabel(item: DistributionItem) {
  if (item.status) return STATUS_LABELS[item.status] ?? item.status;
  if (item.category_name) return item.category_name;
  if (item.category) return LEGACY_CATEGORY_LABELS[item.category] ?? item.category;
  if (item.priority_name) return item.priority_name;
  if (item.priority) return PRIORITY_LABELS[item.priority] ?? item.priority;
  if (item.severity) return SEVERITY_LABELS[item.severity] ?? item.severity;
  return "Nao definido";
}

function DistributionSection({
  title,
  description,
  items,
  total,
}: {
  title: string;
  description: string;
  items: DistributionItem[];
  total: number;
}) {
  return (
    <article className="panel panel--stack">
      <div>
        <h3 style={{ margin: "0 0 6px" }}>{title}</h3>
        <p className="page__description" style={{ margin: 0 }}>
          {description}
        </p>
      </div>

      {items.length === 0 ? (
        <div className="state-card">Nenhum dado disponivel para esta distribuicao.</div>
      ) : (
        <div className="metric-bar-list">
          {items.map((item) => {
            const width = total > 0 ? Math.max(8, Math.round((item.total / total) * 100)) : percentageWidth(items, total);
            const itemKey =
              item.status ??
              item.category_id ??
              item.category ??
              item.priority_id ??
              item.priority ??
              item.severity ??
              item.category_name ??
              item.priority_name;
            return (
              <div className="metric-bar" key={String(itemKey)}>
                <div className="metric-bar__label">
                  <span>
                    {item.category_name ??
                      item.priority_name ??
                      (item.category
                        ? distributionLabel(item)
                        : item.priority
                          ? distributionLabel(item)
                          : distributionLabel(item))}
                  </span>
                  <strong>{item.total}</strong>
                </div>
                <div className="metric-bar__track">
                  <div className="metric-bar__fill" style={{ width: `${width}%` }} />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </article>
  );
}

function RankingTable({
  title,
  description,
  headers,
  rows,
  renderCells,
}: {
  title: string;
  description: string;
  headers: string[];
  rows: RankingItem[];
  renderCells: (row: RankingItem) => ReactNode;
}) {
  return (
    <article className="panel panel--stack">
      <div>
        <h3 style={{ margin: "0 0 6px" }}>{title}</h3>
        <p className="page__description" style={{ margin: 0 }}>
          {description}
        </p>
      </div>

      {rows.length === 0 ? (
        <div className="state-card">Nenhuma unidade elegivel com os filtros atuais.</div>
      ) : (
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Unidade</th>
                {headers.map((header) => (
                  <th key={header}>{header}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.unit_id}>
                  <td>
                    <strong>{row.unit_code}</strong>
                    <div style={{ color: "var(--muted)", fontSize: "0.88rem" }}>{row.unit_name}</div>
                  </td>
                  {renderCells(row)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </article>
  );
}

export default function DashboardPage() {
  const { token, user } = useAuth();
  const [filters, setFilters] = useState<DashboardFilters>(initialFilters);
  const [draftFilters, setDraftFilters] = useState<DashboardFilters>(initialFilters);
  const [units, setUnits] = useState<Unit[]>([]);
  const [configuredCategories, setConfiguredCategories] = useState<TicketCategoryItem[]>([]);
  const [dashboard, setDashboard] = useState<DashboardOverview | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isFilterLoading, setIsFilterLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [recentAlerts, setRecentAlerts] = useState<TicketAlert[]>([]);

  const isSupplier = user?.role === "supplier";
  const isManager = user?.role === "manager";

  useEffect(() => {
    if (!token || isSupplier) return;
    let isActive = true;
    listAlerts(token, { page: 1, page_size: 5, is_read: false, severity: "critical" })
      .then((res) => {
        if (!isActive) return;
        setRecentAlerts(res.items);
      })
      .catch(() => {
        if (!isActive) return;
      });
    return () => {
      isActive = false;
    };
  }, [isSupplier, token]);

  useEffect(() => {
    if (!token || isManager || isSupplier) return;
    let isActive = true;
    listUnits(token, { page: 1, page_size: 100 })
      .then((response) => {
        if (!isActive) return;
        setUnits(response.items);
      })
      .catch(() => {
        if (!isActive) return;
        setUnits([]);
      });

    return () => {
      isActive = false;
    };
  }, [isManager, isSupplier, token]);

  useEffect(() => {
    if (!token || isSupplier) return;

    let isActive = true;
    listTicketCategories({ page: 1, page_size: 100, sort: "display_order_asc" })
      .then((categoriesResponse) => {
        if (!isActive) return;
        setConfiguredCategories(categoriesResponse.items);
      })
      .catch(() => {
        if (!isActive) return;
        setConfiguredCategories([]);
      });

    return () => {
      isActive = false;
    };
  }, [isSupplier, token]);

  useEffect(() => {
    if (!token) {
      setIsLoading(false);
      return;
    }

    let isActive = true;
    setErrorMessage(null);
    setIsLoading(true);

    getDashboardOverview(token, filters)
      .then((response) => {
        if (!isActive) return;
        setDashboard(response);
      })
      .catch((error: unknown) => {
        if (!isActive) return;
        setErrorMessage(error instanceof Error ? error.message : "Nao foi possivel carregar o dashboard.");
      })
      .finally(() => {
        if (isActive) {
          setIsLoading(false);
          setIsFilterLoading(false);
        }
      });

    return () => {
      isActive = false;
    };
  }, [filters, token]);

  const regions = useMemo(() => {
    const values = new Set(units.map((unit) => unit.region));
    return Array.from(values).sort((a, b) => a.localeCompare(b));
  }, [units]);

  const configuredCategoryOptions = useMemo(
    () =>
      configuredCategories
        .map((category) => ({
          value: category.id,
          label: category.name,
        })),
    [configuredCategories],
  );

  function setDraft<K extends keyof DashboardFilters>(key: K, value: DashboardFilters[K]) {
    setDraftFilters((current) => ({ ...current, [key]: value }));
  }

  function applyFilters() {
    setIsFilterLoading(true);
    setFilters(draftFilters);
  }

  function clearFilters() {
    setDraftFilters(initialFilters);
    setIsFilterLoading(true);
    setFilters(initialFilters);
  }

  if (isSupplier) {
    return (
      <section className="page">
        <div className="page__header">
          <div>
            <p className="eyebrow">Dashboard</p>
            <h2 className="page__title">Acesso indisponivel</h2>
            <p className="page__description">Fornecedores nao acessam indicadores operacionais nesta fase.</p>
          </div>
        </div>
        <div className="state-card state-card--error">Seu perfil nao pode acessar o dashboard.</div>
      </section>
    );
  }

  return (
    <section className="page">
      <div className="page__header">
        <div>
          <p className="eyebrow">Dashboard operacional</p>
          <h2 className="page__title">Visao executiva e operacional da rede</h2>
          <p className="page__description">
            Priorize vencidos, críticos e chamados em atendimento com base nos dados do backend.
          </p>
        </div>
        <div className="header-actions">
          <Link className="button-secondary" to="/tickets">
            Ver chamados
          </Link>
          <Link className="button-primary button-primary--link" to="/tickets/new">
            Novo chamado
          </Link>
        </div>
      </div>

      <section className="panel panel--stack">
        <div className="section-heading">
          <div>
            <h3 style={{ margin: "0 0 6px" }}>Filtros</h3>
            <p className="page__description" style={{ margin: 0 }}>
              Recorte o dashboard por periodo, unidade, regiao, status e categoria.
            </p>
          </div>
          {isManager ? <span className="status-badge status-badge--info">Escopo da sua unidade</span> : null}
        </div>

        <FilterBar columns={6} dense={true}>
          <label className="field">
            <span>Data inicial</span>
            <input
              type="date"
              value={draftFilters.date_from || ""}
              onChange={(event) => setDraft("date_from", event.target.value)}
            />
          </label>

          <label className="field">
            <span>Data final</span>
            <input
              type="date"
              value={draftFilters.date_to || ""}
              onChange={(event) => setDraft("date_to", event.target.value)}
            />
          </label>

          {!isManager ? (
            <label className="field">
              <span>Unidade</span>
              <select
                value={String(draftFilters.unit_id ?? "")}
                onChange={(event) => setDraft("unit_id", event.target.value === "" ? "" : Number(event.target.value))}
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

          {!isManager ? (
            <label className="field">
              <span>Regiao</span>
              <select
                value={draftFilters.region || ""}
                onChange={(event) => setDraft("region", event.target.value)}
              >
                <option value="">Todas</option>
                {regions.map((region) => (
                  <option key={region} value={region}>
                    {region}
                  </option>
                ))}
              </select>
            </label>
          ) : null}

          <label className="field">
            <span>Status</span>
            <select
              value={draftFilters.status || ""}
              onChange={(event) => setDraft("status", (event.target.value as TicketStatus | "") || "")}
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
              value={String(draftFilters.category_id ?? "")}
              onChange={(event) => setDraft("category_id", event.target.value === "" ? "" : Number(event.target.value))}
            >
              <option value="">Todas</option>
              {configuredCategoryOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
        </FilterBar>

        <div className="form-actions">
          <button className="button-secondary" type="button" onClick={clearFilters} disabled={isFilterLoading}>
            Limpar
          </button>
          <button className="button-primary" type="button" onClick={applyFilters} disabled={isFilterLoading}>
            {isFilterLoading ? "Atualizando..." : "Aplicar filtros"}
          </button>
        </div>
      </section>

      {isLoading ? <div className="state-card">Carregando dashboard...</div> : null}
      {!isLoading && errorMessage ? <div className="state-card state-card--error">{errorMessage}</div> : null}
      {!isLoading && !errorMessage && !dashboard ? (
        <div className="state-card">Nao foi possivel montar o dashboard com os filtros atuais.</div>
      ) : null}

      {!isLoading && !errorMessage && dashboard ? (
        <>
          <section className="dashboard-kpi-grid">
            <article className="summary-card summary-card--danger">
              <span className="summary-card__label">Atrasados</span>
              <strong>{dashboard.executive_cards.total_late}</strong>
              <p>Chamados com SLA vencido no recorte.</p>
            </article>
            <article className="summary-card summary-card--danger">
              <span className="summary-card__label">Criticos</span>
              <strong>{dashboard.executive_cards.total_critical}</strong>
              <p>Maior risco operacional e técnico.</p>
            </article>
            <article className="summary-card summary-card--warning">
              <span className="summary-card__label">Em execucao</span>
              <strong>{dashboard.executive_cards.total_in_progress}</strong>
              <p>Tratativas ativas em campo.</p>
            </article>
            <article className="summary-card">
              <span className="summary-card__label">SLA no prazo</span>
              <strong>{dashboard.executive_cards.sla_compliance_rate}%</strong>
              <p>Cumprimento dentro do prazo.</p>
            </article>
          </section>

          <section className="dashboard-columns">
            <article className="panel panel--stack">
              <div>
                <h3 style={{ margin: "0 0 6px" }}>Resumo de SLA</h3>
                <p className="page__description" style={{ margin: 0 }}>
                  Status atual dos tickets com prazo definido e historico de cumprimento.
                </p>
              </div>
              <dl className="details-list details-list--metrics">
                <div>
                  <dt>Com SLA</dt>
                  <dd>{dashboard.sla_summary.total_with_sla}</dd>
                </div>
                <div>
                  <dt>No prazo</dt>
                  <dd>{dashboard.sla_summary.on_track}</dd>
                </div>
                <div>
                  <dt>Atrasados</dt>
                  <dd>{dashboard.sla_summary.late}</dd>
                </div>
                <div>
                  <dt>Fechados no prazo</dt>
                  <dd>{dashboard.sla_summary.closed_on_time}</dd>
                </div>
                <div>
                  <dt>Fechados fora do prazo</dt>
                  <dd>{dashboard.sla_summary.closed_late}</dd>
                </div>
                <div>
                  <dt>Compliance</dt>
                  <dd>{dashboard.sla_summary.compliance_rate}%</dd>
                </div>
                <div>
                  <dt>Media resolucao</dt>
                  <dd>{dashboard.average_resolution_hours}h</dd>
                </div>
                <div>
                  <dt>Media fechamento</dt>
                  <dd>{dashboard.average_closure_hours}h</dd>
                </div>
              </dl>
            </article>

            <article className="panel panel--stack">
              <div>
                <h3 style={{ margin: "0 0 6px" }}>Custos e manutencao</h3>
                <p className="page__description" style={{ margin: 0 }}>
                  Consolidado financeiro e operacional dos chamados filtrados.
                </p>
              </div>
              <dl className="details-list">
                <div>
                  <dt>Abertos</dt>
                  <dd>{dashboard.executive_cards.total_open}</dd>
                </div>
                <div>
                  <dt>Bicos parados</dt>
                  <dd>{dashboard.executive_cards.total_fuel_nozzles_stopped}</dd>
                </div>
                <div>
                  <dt>Custo estimado</dt>
                  <dd>{formatMoney(String(dashboard.estimated_cost_total))}</dd>
                </div>
                <div>
                  <dt>Custo aprovado</dt>
                  <dd>{formatMoney(String(dashboard.approved_cost_total))}</dd>
                </div>
                <div>
                  <dt>Custo final</dt>
                  <dd>{formatMoney(String(dashboard.final_cost_total))}</dd>
                </div>
                <div>
                  <dt>Perda diaria estimada</dt>
                  <dd>{formatMoney(String(dashboard.estimated_daily_loss_total))}</dd>
                </div>
                <div>
                  <dt>Chamados com bicos parados</dt>
                  <dd>{dashboard.tickets_with_fuel_nozzles_stopped}</dd>
                </div>
                <div>
                  <dt>Total de bicos parados</dt>
                  <dd>{dashboard.total_fuel_nozzles_stopped}</dd>
                </div>
              </dl>
            </article>
          </section>

          <section className="dashboard-columns">
            <DistributionSection
              title="Distribuicao por status"
              description="Volume dos chamados por etapa do fluxo."
              items={dashboard.tickets_by_status}
              total={dashboard.total_tickets}
            />
            <DistributionSection
              title="Distribuicao por categoria"
              description="Onde a operacao concentra a maior demanda tecnica."
              items={dashboard.tickets_by_category}
              total={dashboard.total_tickets}
            />
          </section>

          <section className="dashboard-columns">
            <DistributionSection
              title="Distribuicao por prioridade"
              description="Pressao operacional sob a perspectiva de prioridade."
              items={dashboard.tickets_by_priority}
              total={dashboard.total_tickets}
            />
            <DistributionSection
              title="Distribuicao por severidade"
              description="Leitura de risco tecnico dentro do recorte ativo."
              items={dashboard.tickets_by_severity}
              total={dashboard.total_tickets}
            />
          </section>

          <section className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <RankingTable
              title="Ranking de unidades por volume"
              description="Top 10 de unidades com maior pressao de chamados."
              headers={["Chamados", "Atrasados", "Criticos"]}
              rows={dashboard.ranking_units_by_tickets}
              renderCells={(row) => (
                <>
                  <td>{row.total_tickets ?? 0}</td>
                  <td>{row.late_tickets ?? 0}</td>
                  <td>{row.critical_tickets ?? 0}</td>
                </>
              )}
            />
            <RankingTable
              title="Ranking de unidades por custo"
              description="Comparativo entre custo estimado e custo final."
              headers={["Estimado", "Final"]}
              rows={dashboard.ranking_units_by_cost}
              renderCells={(row) => (
                <>
                  <td>{formatMoney(String(row.estimated_cost_total ?? 0))}</td>
                  <td>{formatMoney(String(row.final_cost_total ?? 0))}</td>
                </>
              )}
            />
            <RankingTable
              title="Ranking de unidades por bicos parados"
              description="Top 10 de impacto operacional em abastecimento."
              headers={["Bicos", "Perda diaria"]}
              rows={dashboard.ranking_units_by_fuel_nozzles}
              renderCells={(row) => (
                <>
                  <td>{row.total_fuel_nozzles_stopped ?? 0}</td>
                  <td>{formatMoney(String(row.estimated_daily_loss_total ?? 0))}</td>
                </>
              )}
            />
          </section>

          <section className="w-full">

            <article className="panel panel--stack">
              <div>
                <h3 style={{ margin: "0 0 6px" }}>Chamados atrasados</h3>
                <p className="page__description" style={{ margin: 0 }}>
                  Preview limitado aos 10 chamados com SLA mais pressionado.
                </p>
              </div>

              {dashboard.late_tickets_preview.length === 0 ? (
                <div className="state-card">Nenhum chamado atrasado no recorte atual.</div>
              ) : (
                <div className="table-wrap">
                  <table className="data-table" style={{ minWidth: 980 }}>
                    <thead>
                      <tr>
                        <th>Chamado</th>
                        <th>Unidade</th>
                        <th>Titulo</th>
                        <th>Status</th>
                        <th>Prioridade</th>
                        <th>Severidade</th>
                        <th>SLA</th>
                        <th>Abertura</th>
                      </tr>
                    </thead>
                    <tbody>
                      {dashboard.late_tickets_preview.map((ticket) => (
                        <tr key={ticket.id}>
                          <td>
                            <Link className="button-link" to={`/tickets/${ticket.id}`}>
                              {ticket.ticket_number}
                            </Link>
                          </td>
                          <td>
                            <strong>{ticket.unit_code}</strong>
                            <div style={{ color: "var(--muted)", fontSize: "0.88rem" }}>{ticket.unit_name}</div>
                          </td>
                          <td style={{ maxWidth: "280px" }}>
                            <span style={{ display: "block", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                              {ticket.title}
                            </span>
                          </td>
                          <td>
                            <span className={statusClass(ticket.status)}>{STATUS_LABELS[ticket.status]}</span>
                          </td>
                          <td>
                            <span className={priorityClass(ticket.priority)}>{ticket.priority_name ?? PRIORITY_LABELS[ticket.priority]}</span>
                          </td>
                          <td>
                            <span className={severityClass(ticket.severity)}>{SEVERITY_LABELS[ticket.severity]}</span>
                          </td>
                          <td>{formatDate(ticket.sla_due_at)}</td>
                          <td>{formatDate(ticket.opened_at)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </article>
          </section>
        </>
      ) : null}

      {recentAlerts.length > 0 ? (
        <section className="panel panel--stack" style={{ marginTop: "24px" }}>
          <div className="section-heading">
            <div>
              <h3 style={{ margin: "0 0 6px" }}>Alertas criticos nao lidos</h3>
              <p className="page__description" style={{ margin: 0 }}>
                Chamados com SLA vencido ou execucao atrasada que requerem atencao imediata.
              </p>
            </div>
            <Link className="button-secondary" to="/alerts">
              Ver todos os alertas
            </Link>
          </div>
          <div className="table-wrap">
            <table className="data-table" style={{ minWidth: 920 }}>
              <thead>
                <tr>
                  <th>Chamado</th>
                  <th>Unidade</th>
                  <th>Tipo</th>
                  <th>Mensagem</th>
                  <th>Data</th>
                </tr>
              </thead>
              <tbody>
                {recentAlerts.map((alert) => (
                  <tr key={alert.id}>
                    <td>
                      <Link className="button-link" to={`/tickets/${alert.ticket_id}`}>
                        {alert.ticket_number}
                      </Link>
                    </td>
                    <td>
                      <strong>{alert.unit_code}</strong>
                      <div style={{ color: "var(--muted)", fontSize: "0.88rem" }}>{alert.unit_name}</div>
                    </td>
                    <td>
                      <span className="status-badge status-badge--error">
                        {alert.alert_type === "sla_late"
                          ? "SLA Vencido"
                          : alert.alert_type === "sla_due_soon"
                          ? "SLA Proximo"
                          : "Execucao Atrasada"}
                      </span>
                    </td>
                    <td style={{ fontSize: "0.85rem", maxWidth: "280px" }}>
                      <span style={{ display: "block", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        {alert.message}
                      </span>
                    </td>
                    <td style={{ fontSize: "0.85rem" }}>
                      {new Date(alert.created_at).toLocaleString("pt-BR")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}
    </section>
  );
}
