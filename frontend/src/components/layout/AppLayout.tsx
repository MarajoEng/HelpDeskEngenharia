import { useMemo, useState, type PropsWithChildren } from "react";
import { NavLink } from "react-router-dom";

import Badge from "../ui/Badge";
import Button from "../ui/Button";
import { useAuth } from "../../hooks/useAuth";
import { ROLE_LABELS } from "../tickets/ticketUi";

interface NavItem {
  label: string;
  to: string;
  enabled: boolean;
}

export default function AppLayout({ children }: PropsWithChildren) {
  const { logout, user } = useAuth();
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const canAccessDashboard = user?.role !== "supplier";
  const canAccessTickets = user?.role !== "supplier";
  const canAccessReports =
    user?.role === "admin" ||
    user?.role === "director" ||
    user?.role === "engineering" ||
    user?.role === "manager";
  const canAccessEngineering = user?.role === "admin" || user?.role === "engineering";
  const canAccessApprovalLevels = user?.role === "admin";
  const canAccessUnits = user?.role === "admin" || user?.role === "engineering" || user?.role === "director";
  const canAccessSuppliers = user?.role === "admin" || user?.role === "engineering" || user?.role === "director";
  const canAccessAlerts = user?.role !== "supplier";
  const canAccessAuditLogs = user?.role === "admin";
  const canAccessUsers = user?.role === "admin";

  const operationLinks = useMemo<NavItem[]>(
    () => [
      { label: "Dashboard", to: "/dashboard", enabled: canAccessDashboard },
      { label: "Chamados", to: "/tickets", enabled: canAccessTickets },
      { label: "Abrir chamado", to: "/tickets/new", enabled: canAccessTickets },
      { label: "Engenharia", to: "/engineering", enabled: canAccessEngineering },
      { label: "Alertas", to: "/alerts", enabled: canAccessAlerts },
    ],
    [canAccessAlerts, canAccessDashboard, canAccessEngineering, canAccessTickets],
  );

  const analyticsLinks = useMemo<NavItem[]>(
    () => [{ label: "Relatorios", to: "/reports", enabled: canAccessReports }],
    [canAccessReports],
  );

  const adminLinks = useMemo<NavItem[]>(
    () => [
      { label: "Unidades", to: "/units", enabled: canAccessUnits },
      { label: "Usuarios", to: "/users", enabled: canAccessUsers },
      { label: "Fornecedores", to: "/suppliers", enabled: canAccessSuppliers },
      { label: "Alcadas", to: "/approval-levels", enabled: canAccessApprovalLevels },
      { label: "Auditoria", to: "/audit-logs", enabled: canAccessAuditLogs },
    ],
    [canAccessApprovalLevels, canAccessAuditLogs, canAccessSuppliers, canAccessUnits, canAccessUsers],
  );

  const visibleOperationLinks = operationLinks.filter((item) => item.enabled);
  const visibleAnalyticsLinks = analyticsLinks.filter((item) => item.enabled);
  const visibleAdminLinks = adminLinks.filter((item) => item.enabled);
  const userInitials = user?.name
    ? user.name
        .split(" ")
        .slice(0, 2)
        .map((part) => part[0]?.toUpperCase() ?? "")
        .join("")
    : "US";

  function renderLink(item: NavItem) {
    return (
      <NavLink
        key={item.to}
        to={item.to}
        className={({ isActive }) => (isActive ? "nav-link nav-link--active" : "nav-link")}
        onClick={() => setIsSidebarOpen(false)}
      >
        <span>{item.label}</span>
      </NavLink>
    );
  }

  return (
    <div className="shell">
      <aside className={`shell__sidebar${!isSidebarOpen ? " is-mobile-hidden" : ""}`}>
        <div className="shell__brand-block">
          <p className="eyebrow">Operacao central</p>
          <h1 className="shell__brand">Portal de Chamados</h1>
          <p className="shell__sidebar-copy">
            Operacao tecnica, engenharia e controle administrativo em um fluxo unico.
          </p>
        </div>

        <nav className="shell__nav" aria-label="Navegacao principal">
          {visibleOperationLinks.length > 0 ? (
            <div className="shell__sidebar-group">
              <p className="shell__sidebar-group-title">Operacao</p>
              {visibleOperationLinks.map(renderLink)}
            </div>
          ) : null}
          {visibleAnalyticsLinks.length > 0 ? (
            <div className="shell__sidebar-group">
              <p className="shell__sidebar-group-title">Analise</p>
              {visibleAnalyticsLinks.map(renderLink)}
            </div>
          ) : null}
          {visibleAdminLinks.length > 0 ? (
            <div className="shell__sidebar-group">
              <p className="shell__sidebar-group-title">Administracao</p>
              {visibleAdminLinks.map(renderLink)}
            </div>
          ) : null}
        </nav>

        <div className="shell__sidebar-footer">
          <div className="shell__quick-user">
            <div className="shell__avatar" aria-hidden="true">
              {userInitials}
            </div>
            <div>
              <strong>{user?.name || "Usuario"}</strong>
              <p className="shell__meta">{ROLE_LABELS[user?.role ?? "manager"]}</p>
            </div>
          </div>

          <div className="shell__sidebar-card">
            <Badge tone="info">Fase 15</Badge>
            <p>Relatorios protegidos, filtros reais no banco e exportacao CSV dentro do escopo autorizado.</p>
          </div>
        </div>
      </aside>

      <div className="shell__main">
        <header className="shell__header">
          <div>
            <p className="eyebrow">Sessao autenticada</p>
            <strong>{user?.name || "Usuario"}</strong>
            <p className="shell__meta">
              {user?.email} · perfil {ROLE_LABELS[user?.role ?? "manager"]}
            </p>
          </div>

          <div className="shell__header-actions">
            <Button
              className="shell__mobile-toggle"
              variant="ghost"
              aria-label={isSidebarOpen ? "Fechar menu lateral" : "Abrir menu lateral"}
              onClick={() => setIsSidebarOpen((current) => !current)}
            >
              {isSidebarOpen ? "Fechar menu" : "Menu"}
            </Button>
            <Badge tone="success">Ativo</Badge>
            <Button variant="secondary" type="button" onClick={logout}>
              Sair
            </Button>
          </div>
        </header>

        <main className="shell__content">{children}</main>
      </div>
    </div>
  );
}
