import { useMemo, useState, type PropsWithChildren } from "react";
import { NavLink } from "react-router-dom";

import { useAuth } from "../../hooks/useAuth";
import { ROLE_LABELS } from "../ui/statusOptions";

interface NavItem {
  label: string;
  to: string;
  enabled: boolean;
}

const activeClass = "flex items-center px-3 py-2 rounded-lg bg-slate-700 !text-white font-medium text-sm transition-colors";
const inactiveClass = "flex items-center px-3 py-2 rounded-lg !text-slate-300 hover:bg-slate-800 hover:!text-white font-medium text-sm transition-colors";

function SidebarLink({ item, onClose }: { item: NavItem; onClose: () => void }) {
  return (
    <NavLink
      key={item.to}
      to={item.to}
      className={({ isActive }) => (isActive ? activeClass : inactiveClass)}
      onClick={onClose}
    >
      <span>{item.label}</span>
    </NavLink>
  );
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
  const canAccessAlerts = user?.role !== "supplier";

  const canAccessSettings =
    user?.role === "admin" || user?.role === "engineering" || user?.role === "director";

  const operationLinks = useMemo<NavItem[]>(
    () => [
      { label: "Dashboard", to: "/dashboard", enabled: canAccessDashboard },
      { label: "Chamados", to: "/tickets", enabled: canAccessTickets },
      { label: "Abrir chamado", to: "/tickets/new", enabled: canAccessTickets },
      { label: "Engenharia", to: "/engineering", enabled: canAccessEngineering },
      { label: "Alertas", to: "/alerts", enabled: canAccessAlerts },
      { label: "Relatorios", to: "/reports", enabled: canAccessReports },
    ],
    [canAccessAlerts, canAccessDashboard, canAccessEngineering, canAccessReports, canAccessTickets],
  );

  const configLinks = useMemo<NavItem[]>(
    () => [
      { label: "Configurações", to: "/settings", enabled: canAccessSettings },
    ],
    [canAccessSettings],
  );

  const visibleOperationLinks = operationLinks.filter((item) => item.enabled);
  const visibleConfigLinks = configLinks.filter((item) => item.enabled);

  const userInitials = user?.name
    ? user.name
        .split(" ")
        .slice(0, 2)
        .map((part) => part[0]?.toUpperCase() ?? "")
        .join("")
    : "US";

  function closeSidebar() {
    setIsSidebarOpen(false);
  }

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      {/* Mobile overlay */}
      {isSidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-20 lg:hidden"
          onClick={closeSidebar}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed inset-y-0 left-0 z-30 w-56 bg-slate-900 flex flex-col
          transform transition-transform duration-300 ease-in-out
          lg:relative lg:translate-x-0 lg:flex
          ${isSidebarOpen ? "translate-x-0" : "-translate-x-full"}
        `}
      >
        {/* Brand */}
        <div className="px-4 py-4 border-b border-slate-800">
          <h1 className="text-base font-bold text-white leading-tight">Portal Chamados</h1>
          <p className="text-[10px] text-slate-400 mt-0.5 uppercase tracking-wide">Engenharia</p>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto px-2 py-4 space-y-4" aria-label="Navegacao principal">
          {visibleOperationLinks.length > 0 && (
            <div>
              <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider px-3 mb-1.5">
                Operação
              </p>
              <div className="space-y-0.5">
                {visibleOperationLinks.map((item) => (
                  <SidebarLink key={item.to} item={item} onClose={closeSidebar} />
                ))}
              </div>
            </div>
          )}

          {visibleConfigLinks.length > 0 && (
            <div>
              <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider px-3 mb-1.5">
                Sistema
              </p>
              <div className="space-y-0.5">
                {visibleConfigLinks.map((item) => (
                  <SidebarLink key={item.to} item={item} onClose={closeSidebar} />
                ))}
              </div>
            </div>
          )}
        </nav>

        {/* User footer */}
        <div className="px-2 py-3 border-t border-slate-800">
          <div className="flex items-center gap-2.5 px-2 py-2 rounded-lg bg-slate-800/50">
            <div className="w-8 h-8 rounded-lg bg-teal-600 flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
              {userInitials}
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-xs font-semibold text-white truncate">{user?.name || "Usuario"}</p>
              <p className="text-[10px] text-slate-400 truncate">
                {ROLE_LABELS[user?.role ?? "manager"]}
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={logout}
            className="mt-1.5 w-full px-2 py-1.5 text-xs text-slate-400 hover:text-white hover:bg-slate-800 rounded-md transition-colors text-left font-medium"
          >
            Sair da conta
          </button>
        </div>
      </aside>

      {/* Main area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Topbar */}
        <header className="h-14 bg-white border-b border-slate-200 flex items-center justify-between px-6 flex-shrink-0">
          <div className="flex items-center gap-3">
            <button
              type="button"
              className="lg:hidden p-1.5 rounded-md text-slate-500 hover:text-slate-900 hover:bg-slate-100 transition-colors"
              aria-label={isSidebarOpen ? "Fechar menu lateral" : "Abrir menu lateral"}
              onClick={() => setIsSidebarOpen((current) => !current)}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <div className="hidden sm:block">
              <p className="text-sm font-medium text-slate-900">{user?.name || "Usuario"}</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <span className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-emerald-50 text-emerald-700 ring-1 ring-inset ring-emerald-600/20">
              Sessão ativa
            </span>
            <button
              type="button"
              onClick={logout}
              className="hidden sm:inline-flex items-center px-2.5 py-1 text-xs font-medium text-slate-600 bg-white border border-slate-200 rounded-md hover:bg-slate-50 transition-colors"
            >
              Sair
            </button>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto p-4 sm:p-6">
          <div className="max-w-7xl mx-auto w-full">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
