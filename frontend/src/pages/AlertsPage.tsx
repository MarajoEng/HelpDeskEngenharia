import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { listAlerts, markAlertRead, markAllAlertsRead, runSlaMonitor } from "../api/alertApi";
import { useAuth } from "../hooks/useAuth";
import type { AlertFilters, AlertSeverity, AlertType, TicketAlert } from "../types/alert";

const ALERT_TYPE_LABELS: Record<AlertType, string> = {
  sla_late: "SLA Vencido",
  sla_due_soon: "SLA Proximo",
  execution_late: "Execucao Atrasada",
};

const SEVERITY_LABELS: Record<AlertSeverity, string> = {
  info: "Info",
  warning: "Aviso",
  critical: "Critico",
};

function severityClass(severity: AlertSeverity) {
  switch (severity) {
    case "critical":
      return "status-badge status-badge--error";
    case "warning":
      return "status-badge status-badge--warning";
    default:
      return "status-badge status-badge--info";
  }
}

function formatDate(value: string | null | undefined) {
  if (!value) return "—";
  return new Date(value).toLocaleString("pt-BR");
}

export default function AlertsPage() {
  const { token, user } = useAuth();

  const [alerts, setAlerts] = useState<TicketAlert[]>([]);
  const [total, setTotal] = useState(0);
  const [pages, setPages] = useState(1);
  const [page, setPage] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [monitorResult, setMonitorResult] = useState<string | null>(null);
  const [isRunningMonitor, setIsRunningMonitor] = useState(false);

  const [isReadFilter, setIsReadFilter] = useState<"" | "true" | "false">("");
  const [alertTypeFilter, setAlertTypeFilter] = useState<AlertType | "">("");
  const [severityFilter, setSeverityFilter] = useState<AlertSeverity | "">("");

  const isAdmin = user?.role === "admin";
  const isEngineering = user?.role === "engineering";
  const canRunMonitor = isAdmin || isEngineering;

  function buildFilters(): AlertFilters {
    return {
      page,
      page_size: 20,
      is_read: isReadFilter === "" ? undefined : isReadFilter === "true",
      alert_type: alertTypeFilter || undefined,
      severity: severityFilter || undefined,
    };
  }

  function load(currentPage = page) {
    if (!token) return;
    setIsLoading(true);
    setError(null);
    listAlerts(token, { ...buildFilters(), page: currentPage })
      .then((res) => {
        setAlerts(res.items);
        setTotal(res.total);
        setPages(res.pages);
        setPage(currentPage);
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Erro ao carregar alertas.");
      })
      .finally(() => setIsLoading(false));
  }

  useEffect(() => {
    load(1);
  }, [token, isReadFilter, alertTypeFilter, severityFilter]);

  function handleMarkRead(alert: TicketAlert) {
    if (!token) return;
    markAlertRead(token, alert.id)
      .then(() => load(page))
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Erro ao marcar alerta como lido.");
      });
  }

  function handleMarkAllRead() {
    if (!token) return;
    markAllAlertsRead(token)
      .then(() => load(1))
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Erro ao marcar todos como lidos.");
      });
  }

  function handleRunMonitor() {
    if (!token) return;
    setIsRunningMonitor(true);
    setMonitorResult(null);
    runSlaMonitor(token)
      .then((res) => {
        setMonitorResult(
          `Monitoramento concluido: ${res.checked_tickets} chamados verificados, ` +
          `${res.created_alerts} alertas criados, ${res.skipped_duplicates} duplicatas ignoradas.`,
        );
        load(1);
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Erro ao executar monitoramento.");
      })
      .finally(() => setIsRunningMonitor(false));
  }

  const unread = alerts.filter((a) => !a.is_read).length;
  const critical = alerts.filter((a) => a.severity === "critical").length;

  return (
    <section className="page">
      <div className="page__header">
        <div>
          <p className="eyebrow">Monitoramento</p>
          <h2 className="page__title">Alertas de SLA</h2>
          <p className="page__description">
            {total} alerta{total !== 1 ? "s" : ""} encontrado{total !== 1 ? "s" : ""}
          </p>
        </div>
        <div style={{ display: "flex", gap: "8px" }}>
          {canRunMonitor ? (
            <button
              className="button-primary"
              type="button"
              onClick={handleRunMonitor}
              disabled={isRunningMonitor}
            >
              {isRunningMonitor ? "Verificando..." : "Verificar SLA agora"}
            </button>
          ) : null}
          <button className="button-secondary" type="button" onClick={handleMarkAllRead}>
            Marcar todos como lidos
          </button>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "16px", marginBottom: "24px" }}>
        <article className="panel">
          <p className="eyebrow">Total na pagina</p>
          <strong style={{ fontSize: "2rem" }}>{total}</strong>
        </article>
        <article className="panel">
          <p className="eyebrow">Nao lidos</p>
          <strong style={{ fontSize: "2rem", color: unread > 0 ? "var(--warning)" : undefined }}>{unread}</strong>
        </article>
        <article className="panel">
          <p className="eyebrow">Criticos</p>
          <strong style={{ fontSize: "2rem", color: critical > 0 ? "var(--danger)" : undefined }}>{critical}</strong>
        </article>
      </div>

      {monitorResult ? (
        <div className="state-card state-card--success" style={{ marginBottom: "16px" }}>
          {monitorResult}
        </div>
      ) : null}

      {error ? <div className="state-card state-card--error">{error}</div> : null}

      <div className="filter-bar" style={{ marginBottom: "16px" }}>
        <select
          className="input"
          value={isReadFilter}
          onChange={(e) => setIsReadFilter(e.target.value as "" | "true" | "false")}
        >
          <option value="">Todos (lido/nao lido)</option>
          <option value="false">Nao lidos</option>
          <option value="true">Lidos</option>
        </select>
        <select
          className="input"
          value={alertTypeFilter}
          onChange={(e) => setAlertTypeFilter(e.target.value as AlertType | "")}
        >
          <option value="">Todos os tipos</option>
          <option value="sla_late">SLA Vencido</option>
          <option value="sla_due_soon">SLA Proximo</option>
          <option value="execution_late">Execucao Atrasada</option>
        </select>
        <select
          className="input"
          value={severityFilter}
          onChange={(e) => setSeverityFilter(e.target.value as AlertSeverity | "")}
        >
          <option value="">Todas as severidades</option>
          <option value="critical">Critico</option>
          <option value="warning">Aviso</option>
          <option value="info">Info</option>
        </select>
      </div>

      {isLoading ? (
        <div className="state-card">Carregando alertas...</div>
      ) : alerts.length === 0 ? (
        <div className="state-card">Nenhum alerta encontrado com os filtros atuais.</div>
      ) : (
        <div className="table-wrapper">
          <table className="table">
            <thead>
              <tr>
                <th>Chamado</th>
                <th>Unidade</th>
                <th>Tipo</th>
                <th>Severidade</th>
                <th>Mensagem</th>
                <th>Data</th>
                <th>Status</th>
                <th>Acao</th>
              </tr>
            </thead>
            <tbody>
              {alerts.map((alert) => (
                <tr key={alert.id} style={{ opacity: alert.is_read ? 0.65 : 1 }}>
                  <td>
                    <Link className="button-link" to={`/tickets/${alert.ticket_id}`}>
                      {alert.ticket_number}
                    </Link>
                  </td>
                  <td>
                    <strong>{alert.unit_code}</strong>
                    <div style={{ color: "var(--muted)", fontSize: "0.85rem" }}>{alert.unit_name}</div>
                  </td>
                  <td>{ALERT_TYPE_LABELS[alert.alert_type]}</td>
                  <td>
                    <span className={severityClass(alert.severity)}>
                      {SEVERITY_LABELS[alert.severity]}
                    </span>
                  </td>
                  <td style={{ maxWidth: "280px", fontSize: "0.85rem" }}>{alert.message}</td>
                  <td style={{ fontSize: "0.85rem" }}>{formatDate(alert.created_at)}</td>
                  <td>
                    {alert.is_read ? (
                      <span className="status-badge status-badge--muted">Lido</span>
                    ) : (
                      <span className="status-badge status-badge--warning">Nao lido</span>
                    )}
                  </td>
                  <td>
                    {!alert.is_read ? (
                      <button
                        className="button-secondary"
                        type="button"
                        onClick={() => handleMarkRead(alert)}
                      >
                        Marcar lido
                      </button>
                    ) : null}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {pages > 1 ? (
        <div className="pagination">
          <button
            className="button-secondary"
            type="button"
            disabled={page <= 1}
            onClick={() => load(page - 1)}
          >
            Anterior
          </button>
          <span>
            {page} / {pages}
          </span>
          <button
            className="button-secondary"
            type="button"
            disabled={page >= pages}
            onClick={() => load(page + 1)}
          >
            Proxima
          </button>
        </div>
      ) : null}
    </section>
  );
}
