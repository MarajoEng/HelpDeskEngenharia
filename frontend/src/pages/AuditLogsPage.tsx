import { useEffect, useState } from "react";

import { listAuditLogs } from "../api/auditApi";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import EmptyState from "../components/ui/EmptyState";
import ErrorState from "../components/ui/ErrorState";
import FilterBar from "../components/ui/FilterBar";
import Input from "../components/ui/Input";
import LoadingState from "../components/ui/LoadingState";
import Pagination from "../components/ui/Pagination";
import Table from "../components/ui/Table";
import { useAuth } from "../hooks/useAuth";
import type { AuditLog, AuditLogFilters } from "../types/audit";
import { formatAuditDate } from "../utils/formatters";
import { getErrorMessage, LIST_EMPTY_MESSAGES } from "../utils/messages";

const PAGE_SIZE = 20;

const ACTION_LABELS: Record<string, string> = {
  login_success: "Login realizado",
  login_failed: "Login falhou",
  login_rate_limited: "Login bloqueado",
  user_created: "Usuario criado",
  user_updated: "Usuario atualizado",
  unit_created: "Unidade criada",
  unit_updated: "Unidade atualizada",
  ticket_created: "Chamado aberto",
  ticket_triaged: "Chamado triado",
  approval_requested: "Aprovacao solicitada",
  approval_decided: "Aprovacao decidida",
  execution_started: "Execucao iniciada",
  progress_updated: "Progresso atualizado",
  ticket_resolved: "Chamado resolvido",
  ticket_closed: "Chamado encerrado",
  attachment_uploaded: "Anexo enviado",
  approval_level_created: "Alcada criada",
  approval_level_updated: "Alcada atualizada",
  supplier_created: "Fornecedor criado",
  supplier_updated: "Fornecedor atualizado",
  alert_marked_read: "Alerta lido",
  alerts_marked_all_read: "Todos alertas lidos",
  sla_monitor_run: "Monitor SLA executado",
};

export default function AuditLogsPage() {
  const { token, user } = useAuth();
  const [items, setItems] = useState<AuditLog[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [search, setSearch] = useState("");
  const [actionFilter, setActionFilter] = useState("");
  const [entityTypeFilter, setEntityTypeFilter] = useState("");

  const [pendingSearch, setPendingSearch] = useState("");
  const [pendingAction, setPendingAction] = useState("");
  const [pendingEntityType, setPendingEntityType] = useState("");

  if (user?.role !== "admin") {
    return (
      <section className="space-y-6">
        <ErrorState description="Seu perfil nao pode visualizar a auditoria do sistema." />
      </section>
    );
  }

  useEffect(() => {
    if (!token) return;
    setLoading(true);
    setError(null);

    const filters: AuditLogFilters = {
      page,
      page_size: PAGE_SIZE,
    };
    if (search) filters.search = search;
    if (actionFilter) filters.action = actionFilter;
    if (entityTypeFilter) filters.entity_type = entityTypeFilter;

    listAuditLogs(token, filters)
      .then((data) => {
        setItems(data.items);
        setTotal(data.total);
        setPages(data.pages);
      })
      .catch((requestError: unknown) => {
        setError(getErrorMessage(requestError, "Erro ao carregar auditoria."));
      })
      .finally(() => setLoading(false));
  }, [token, page, search, actionFilter, entityTypeFilter]);

  function applyFilters() {
    setSearch(pendingSearch);
    setActionFilter(pendingAction);
    setEntityTypeFilter(pendingEntityType);
    setPage(1);
  }

  function clearFilters() {
    setPendingSearch("");
    setPendingAction("");
    setPendingEntityType("");
    setSearch("");
    setActionFilter("");
    setEntityTypeFilter("");
    setPage(1);
  }

  return (
    <section className="space-y-6">

      <section className="panel panel--stack">
        <FilterBar columns={4}>
          <Input
            label="Busca"
            type="text"
            placeholder="Acao, entidade, usuario..."
            value={pendingSearch}
            onChange={(event) => setPendingSearch(event.target.value)}
            onKeyDown={(event) => event.key === "Enter" && applyFilters()}
          />
          <Input
            label="Acao"
            type="text"
            placeholder="ex: login_success"
            value={pendingAction}
            onChange={(event) => setPendingAction(event.target.value)}
          />
          <Input
            label="Entidade"
            type="text"
            placeholder="ex: ticket, user"
            value={pendingEntityType}
            onChange={(event) => setPendingEntityType(event.target.value)}
          />
          <div className="filters-actions">
            <Button variant="primary" type="button" onClick={applyFilters}>
              Filtrar
            </Button>
            <Button variant="secondary" type="button" onClick={clearFilters}>
              Limpar
            </Button>
          </div>
        </FilterBar>

        {error ? (
          <ErrorState description={error} />
        ) : loading ? (
          <LoadingState title="Carregando auditoria" />
        ) : items.length === 0 ? (
          <EmptyState title="Nenhum evento encontrado" description={LIST_EMPTY_MESSAGES.audit} />
        ) : (
          <>
            <Table minWidth={1120}>
              <thead>
                <tr>
                  <th>Data/Hora</th>
                  <th>Ator</th>
                  <th>Acao</th>
                  <th>Entidade</th>
                  <th>IP</th>
                  <th>Detalhes</th>
                </tr>
              </thead>
              <tbody>
                {items.map((log) => (
                  <tr key={log.id}>
                    <td className="text-mono text-sm">{formatAuditDate(log.created_at)}</td>
                    <td>{log.actor_user_name ?? <span className="text-muted">Sistema</span>}</td>
                    <td>
                      <Badge tone="info">{ACTION_LABELS[log.action] ?? log.action}</Badge>
                    </td>
                    <td>
                      {log.entity_type}
                      {log.entity_id != null ? ` #${log.entity_id}` : ""}
                    </td>
                    <td className="text-mono text-sm">{log.ip_address ?? "—"}</td>
                    <td className="text-sm">
                      {log.metadata_json && Object.keys(log.metadata_json).length > 0
                        ? Object.entries(log.metadata_json)
                            .map(([key, value]) => `${key}: ${value}`)
                            .join(", ")
                        : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>

            {pages > 1 ? (
              <Pagination
                total={total}
                label="evento(s)"
                page={page}
                pages={pages}
                onPrevious={() => setPage((current) => current - 1)}
                onNext={() => setPage((current) => current + 1)}
              />
            ) : null}
          </>
        )}
      </section>
    </section>
  );
}
