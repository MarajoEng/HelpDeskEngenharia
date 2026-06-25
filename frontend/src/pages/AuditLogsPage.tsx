import { useEffect, useState } from "react";
import { listAuditLogs } from "../api/auditApi";
import { useAuth } from "../hooks/useAuth";
import type { AuditLog, AuditLogFilters } from "../types/audit";

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

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "medium" });
}

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
      <div className="screen-state">
        <div className="screen-state__card panel">
          <p className="eyebrow">Acesso restrito</p>
          <h2>Sem permissao</h2>
          <p>Apenas administradores podem acessar o log de auditoria.</p>
        </div>
      </div>
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
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Erro ao carregar auditoria.");
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
    <div>
      <div className="page-header">
        <div>
          <p className="eyebrow">Administracao</p>
          <h1>Log de Auditoria</h1>
          <p className="page-header__subtitle">
            Registro de acoes realizadas no sistema. Total: {total} evento(s).
          </p>
        </div>
      </div>

      <div className="panel filters-panel">
        <div className="filters-row">
          <div className="form-field">
            <label className="form-label">Busca</label>
            <input
              className="form-input"
              type="text"
              placeholder="Acao, entidade, usuario..."
              value={pendingSearch}
              onChange={(e) => setPendingSearch(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && applyFilters()}
            />
          </div>
          <div className="form-field">
            <label className="form-label">Acao</label>
            <input
              className="form-input"
              type="text"
              placeholder="ex: login_success"
              value={pendingAction}
              onChange={(e) => setPendingAction(e.target.value)}
            />
          </div>
          <div className="form-field">
            <label className="form-label">Entidade</label>
            <input
              className="form-input"
              type="text"
              placeholder="ex: ticket, user"
              value={pendingEntityType}
              onChange={(e) => setPendingEntityType(e.target.value)}
            />
          </div>
          <div className="filters-actions">
            <button className="button-primary" type="button" onClick={applyFilters}>
              Filtrar
            </button>
            <button className="button-secondary" type="button" onClick={clearFilters}>
              Limpar
            </button>
          </div>
        </div>
      </div>

      {error ? (
        <div className="panel panel--error">
          <p>{error}</p>
        </div>
      ) : loading ? (
        <div className="panel">
          <p>Carregando...</p>
        </div>
      ) : items.length === 0 ? (
        <div className="panel">
          <p>Nenhum evento de auditoria encontrado.</p>
        </div>
      ) : (
        <div className="panel">
          <div className="table-wrapper">
            <table className="data-table">
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
                    <td className="text-mono text-sm">{formatDate(log.created_at)}</td>
                    <td>{log.actor_user_name ?? <span className="text-muted">Sistema</span>}</td>
                    <td>
                      <span className="status-badge status-badge--info">
                        {ACTION_LABELS[log.action] ?? log.action}
                      </span>
                    </td>
                    <td>
                      {log.entity_type}
                      {log.entity_id != null ? ` #${log.entity_id}` : ""}
                    </td>
                    <td className="text-mono text-sm">{log.ip_address ?? "—"}</td>
                    <td className="text-sm">
                      {log.metadata_json && Object.keys(log.metadata_json).length > 0
                        ? Object.entries(log.metadata_json)
                            .map(([k, v]) => `${k}: ${v}`)
                            .join(", ")
                        : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {pages > 1 && (
            <div className="pagination">
              <button
                className="button-secondary"
                type="button"
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
              >
                Anterior
              </button>
              <span>
                Pagina {page} de {pages}
              </span>
              <button
                className="button-secondary"
                type="button"
                disabled={page >= pages}
                onClick={() => setPage((p) => p + 1)}
              >
                Proxima
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
