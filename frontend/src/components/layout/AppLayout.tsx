import type { PropsWithChildren } from "react";
import { NavLink } from "react-router-dom";

import { useAuth } from "../../hooks/useAuth";

export default function AppLayout({ children }: PropsWithChildren) {
  const { logout, user } = useAuth();

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
          <NavLink
            to="/"
            className={({ isActive }) =>
              isActive ? "nav-link nav-link--active" : "nav-link"
            }
          >
            Visao geral
          </NavLink>
        </nav>

        <div className="shell__sidebar-card">
          <span className="status-badge status-badge--info">Fase 3</span>
          <p>
            Autenticacao habilitada com token, sessao do usuario e bloqueio
            inicial por perfil.
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
