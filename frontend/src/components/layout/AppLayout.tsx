import type { PropsWithChildren } from "react";
import { NavLink } from "react-router-dom";

import { useAuth } from "../../hooks/useAuth";

export default function AppLayout({ children }: PropsWithChildren) {
  const { logout, user } = useAuth();
  const canAccessDashboard = user?.role !== "supplier";
  const canAccessTickets = user?.role !== "supplier";
  const canAccessEngineering = user?.role === "admin" || user?.role === "engineering";
  const canAccessApprovalLevels = user?.role === "admin";
  const canAccessUnits = user?.role === "admin" || user?.role === "engineering" || user?.role === "director";
  const canAccessSuppliers = user?.role === "admin" || user?.role === "engineering" || user?.role === "director";
  const canAccessAlerts = user?.role !== "supplier";
  const canAccessUsers = user?.role === "admin";

  return (
    <div className="shell">
      <aside className="shell__sidebar">
        <div>
          <p className="eyebrow">Operacao central</p>
          <h1 className="shell__brand">Portal de Chamados</h1>
          <p className="shell__sidebar-copy">
            Base autenticada para engenharia e manutencao estrutural.
          </p>
        </div>

        <nav className="shell__nav" aria-label="Navegacao principal">
          {canAccessDashboard ? (
            <NavLink
              to="/dashboard"
              className={({ isActive }) =>
                isActive ? "nav-link nav-link--active" : "nav-link"
              }
            >
              Dashboard
            </NavLink>
          ) : null}
          {canAccessTickets ? (
            <>
              <NavLink
                to="/tickets"
                className={({ isActive }) =>
                  isActive ? "nav-link nav-link--active" : "nav-link"
                }
              >
                Chamados
              </NavLink>
              {canAccessEngineering ? (
                <NavLink
                  to="/engineering"
                  className={({ isActive }) =>
                    isActive ? "nav-link nav-link--active" : "nav-link"
                  }
                >
                  Engenharia
                </NavLink>
              ) : null}
              {canAccessApprovalLevels ? (
                <NavLink
                  to="/approval-levels"
                  className={({ isActive }) =>
                    isActive ? "nav-link nav-link--active" : "nav-link"
                  }
                >
                  Alcadas
                </NavLink>
              ) : null}
              <NavLink
                to="/tickets/new"
                className={({ isActive }) =>
                  isActive ? "nav-link nav-link--active" : "nav-link"
                }
              >
                Abrir chamado
              </NavLink>
            </>
          ) : null}
          {canAccessAlerts ? (
            <NavLink
              to="/alerts"
              className={({ isActive }) =>
                isActive ? "nav-link nav-link--active" : "nav-link"
              }
            >
              Alertas
            </NavLink>
          ) : null}
          {canAccessSuppliers ? (
            <NavLink
              to="/suppliers"
              className={({ isActive }) =>
                isActive ? "nav-link nav-link--active" : "nav-link"
              }
            >
              Fornecedores
            </NavLink>
          ) : null}
          {canAccessUnits ? (
            <NavLink
              to="/units"
              className={({ isActive }) =>
                isActive ? "nav-link nav-link--active" : "nav-link"
              }
            >
              Unidades
            </NavLink>
          ) : null}
          {canAccessUsers ? (
            <NavLink
              to="/users"
              className={({ isActive }) =>
                isActive ? "nav-link nav-link--active" : "nav-link"
              }
            >
              Usuarios
            </NavLink>
          ) : null}
        </nav>

        <div className="shell__sidebar-card">
          <span className="status-badge status-badge--info">Fase 11</span>
          <p>
            Dashboard operacional com SLA, custos, unidades criticas e indicadores reais da rede.
          </p>
        </div>
      </aside>

      <div className="shell__main">
        <header className="shell__header">
          <div>
            <p className="eyebrow">Sessao autenticada</p>
            <strong>{user?.name || "Usuario"}</strong>
            <p className="shell__meta">
              {user?.email} · perfil {user?.role}
            </p>
          </div>

          <div className="shell__header-actions">
            <span className="status-badge status-badge--success">Ativo</span>
            <button className="button-secondary" type="button" onClick={logout}>
              Sair
            </button>
          </div>
        </header>

        <main className="shell__content">{children}</main>
      </div>
    </div>
  );
}
