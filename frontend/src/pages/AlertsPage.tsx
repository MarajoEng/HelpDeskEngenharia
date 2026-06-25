import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { listAlerts, markAlertRead, markAllAlertsRead, runSlaMonitor } from "../api/alertApi";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import EmptyState from "../components/ui/EmptyState";
import ErrorState from "../components/ui/ErrorState";
import FilterBar from "../components/ui/FilterBar";
import LoadingState from "../components/ui/LoadingState";
import PageHeader from "../components/ui/PageHeader";
import Pagination from "../components/ui/Pagination";
import Select from "../components/ui/Select";
import StatCard from "../components/ui/StatCard";
import Table from "../components/ui/Table";
import { ALERT_SEVERITY_LABELS, ALERT_TYPE_LABELS, alertSeverityTone } from "../components/ui/statusOptions";
import { useAuth } from "../hooks/useAuth";
import type { AlertFilters, AlertSeverity, AlertType, TicketAlert } from "../types/alert";
import { formatDate } from "../utils/formatters";
import { getErrorMessage, LIST_EMPTY_MESSAGES } from "../utils/messages";

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
      .then((response) => {
        setAlerts(response.items);
        setTotal(response.total);
        setPages(response.pages);
        setPage(currentPage);
      })
      .catch((requestError: unknown) => {
        setError(getErrorMessage(requestError, "Erro ao carregar alertas."));
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
      .catch((requestError: unknown) => {
        setError(getErrorMessage(requestError, "Erro ao marcar alerta como lido."));
      });
  }

  function handleMarkAllRead() {
    if (!token) return;
    markAllAlertsRead(token)
      .then(() => load(1))
      .catch((requestError: unknown) => {
        setError(getErrorMessage(requestError, "Erro ao marcar todos como lidos."));
      });
  }

  function handleRunMonitor() {
    if (!token) return;
    setIsRunningMonitor(true);
    setMonitorResult(null);
    runSlaMonitor(token)
      .then((response) => {
        setMonitorResult(
          `Monitoramento concluido: ${response.checked_tickets} chamados verificados, ${response.created_alerts} alertas criados, ${response.skipped_duplicates} duplicatas ignoradas.`,
        );
        load(1);
      })
      .catch((requestError: unknown) => {
        setError(getErrorMessage(requestError, "Erro ao executar monitoramento."));
      })
      .finally(() => setIsRunningMonitor(false));
  }

  const unread = alerts.filter((item) => !item.is_read).length;
  const critical = alerts.filter((item) => item.severity === "critical").length;

  return (
    <section className="page">
      <PageHeader
        eyebrow="Monitoramento"
        title="Alertas de SLA"
        description={`${total} alerta${total !== 1 ? "s" : ""} encontrado${total !== 1 ? "s" : ""}`}
        actions={
          <>
            {canRunMonitor ? (
              <Button variant="primary" type="button" onClick={handleRunMonitor} disabled={isRunningMonitor}>
                {isRunningMonitor ? "Verificando..." : "Verificar SLA agora"}
              </Button>
            ) : null}
            <Button variant="secondary" type="button" onClick={handleMarkAllRead}>
              Marcar todos como lidos
            </Button>
          </>
        }
      />

      <section className="summary-grid">
        <StatCard label="Total na pagina" tone="accent" value={total} description="Alertas retornados com os filtros atuais." />
        <StatCard label="Nao lidos" tone="warning" value={unread} description="Itens que ainda exigem leitura operacional." />
        <StatCard label="Criticos" tone="danger" value={critical} description="Alertas com impacto imediato no SLA." />
      </section>

      {monitorResult ? <div className="state-card state-card--success">{monitorResult}</div> : null}
      {error ? <ErrorState description={error} /> : null}

      <section className="panel panel--stack">
        <FilterBar columns={3}>
          <Select
            label="Leitura"
            value={isReadFilter}
            onChange={(event) => setIsReadFilter(event.target.value as "" | "true" | "false")}
          >
            <option value="">Todos (lido/nao lido)</option>
            <option value="false">Nao lidos</option>
            <option value="true">Lidos</option>
          </Select>
          <Select
            label="Tipo"
            value={alertTypeFilter}
            onChange={(event) => setAlertTypeFilter(event.target.value as AlertType | "")}
          >
            <option value="">Todos os tipos</option>
            <option value="sla_late">SLA vencido</option>
            <option value="sla_due_soon">SLA proximo</option>
            <option value="execution_late">Execucao atrasada</option>
          </Select>
          <Select
            label="Severidade"
            value={severityFilter}
            onChange={(event) => setSeverityFilter(event.target.value as AlertSeverity | "")}
          >
            <option value="">Todas as severidades</option>
            <option value="critical">Critico</option>
            <option value="warning">Aviso</option>
            <option value="info">Info</option>
          </Select>
        </FilterBar>

        {isLoading ? (
          <LoadingState title="Carregando alertas" />
        ) : alerts.length === 0 ? (
          <EmptyState title="Nenhum alerta encontrado" description={LIST_EMPTY_MESSAGES.alerts} />
        ) : (
          <>
            <Table minWidth={1040}>
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
                  <tr key={alert.id} style={{ opacity: alert.is_read ? 0.68 : 1 }}>
                    <td>
                      <Link className="ui-link-button" to={`/tickets/${alert.ticket_id}`}>
                        {alert.ticket_number}
                      </Link>
                    </td>
                    <td>
                      <strong>{alert.unit_code}</strong>
                      <div className="text-sm text-muted">{alert.unit_name}</div>
                    </td>
                    <td>{ALERT_TYPE_LABELS[alert.alert_type]}</td>
                    <td>
                      <Badge tone={alertSeverityTone(alert.severity)}>
                        {ALERT_SEVERITY_LABELS[alert.severity]}
                      </Badge>
                    </td>
                    <td style={{ maxWidth: "280px", fontSize: "0.85rem" }}>{alert.message}</td>
                    <td className="text-sm">{formatDate(alert.created_at)}</td>
                    <td>
                      <Badge tone={alert.is_read ? "neutral" : "warning"}>
                        {alert.is_read ? "Lido" : "Nao lido"}
                      </Badge>
                    </td>
                    <td>
                      {!alert.is_read ? (
                        <Button variant="secondary" size="sm" type="button" onClick={() => handleMarkRead(alert)}>
                          Marcar lido
                        </Button>
                      ) : null}
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>

            {pages > 1 ? (
              <Pagination
                total={total}
                label="alerta(s)"
                page={page}
                pages={pages}
                onPrevious={() => load(page - 1)}
                onNext={() => load(page + 1)}
              />
            ) : null}
          </>
        )}
      </section>
    </section>
  );
}
