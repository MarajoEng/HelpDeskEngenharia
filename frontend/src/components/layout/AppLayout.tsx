import { useEffect, useMemo, useState, type PropsWithChildren, type ReactNode } from "react";
import { NavLink, useLocation } from "react-router-dom";

import { useAuth } from "../../hooks/useAuth";
import { getSettingsTabs, hasSettingsAccess } from "../settings/settingsTabs";
import { ROLE_LABELS } from "../ui/statusOptions";

interface NavItem {
  label: string;
  to: string;
  icon: ReactNode;
  end?: boolean;
}

const SIDEBAR_COLLAPSED_KEY = "portal_chamados_sidebar_collapsed";
const activeClass = "bg-slate-800 text-white shadow-sm ring-1 ring-inset ring-white/10";
const inactiveClass = "text-slate-300 hover:bg-white/10 hover:text-white";

function readSidebarPreference() {
  if (typeof window === "undefined") {
    return false;
  }

  return window.localStorage.getItem(SIDEBAR_COLLAPSED_KEY) === "true";
}

function IconDashboard() {
  return (
    <svg className="h-[18px] w-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M4 11.5c0-2.12 0-3.18.66-3.84.66-.66 1.72-.66 3.84-.66s3.18 0 3.84.66c.66.66.66 1.72.66 3.84S13 14.68 12.34 15.34c-.66.66-1.72.66-3.84.66s-3.18 0-3.84-.66C4 14.68 4 13.62 4 11.5Z" />
      <path d="M13 7.5c0-1.65 0-2.47.51-2.99.52-.51 1.34-.51 2.99-.51 1.65 0 2.47 0 2.99.51.51.52.51 1.34.51 2.99 0 1.65 0 2.47-.51 2.99-.52.51-1.34.51-2.99.51-1.65 0-2.47 0-2.99-.51C13 9.97 13 9.15 13 7.5Z" />
      <path d="M13 17.5c0-1.65 0-2.47.51-2.99.52-.51 1.34-.51 2.99-.51 1.65 0 2.47 0 2.99.51.51.52.51 1.34.51 2.99 0 1.65 0 2.47-.51 2.99-.52.51-1.34.51-2.99.51-1.65 0-2.47 0-2.99-.51C13 19.97 13 19.15 13 17.5Z" />
    </svg>
  );
}

function IconTickets() {
  return (
    <svg className="h-[18px] w-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M20 12a2 2 0 0 1 2 2v2a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2v-2a2 2 0 0 1 2-2 2 2 0 1 0 0-4 2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v2a2 2 0 0 1-2 2 2 2 0 1 0 0 4Z" />
      <path d="M12 4v16" strokeDasharray="3 3" />
    </svg>
  );
}

function IconEngineering() {
  return (
    <svg className="h-[18px] w-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="m14.7 6.3 3 3" />
      <path d="m7.5 13.5 7.2-7.2a2.12 2.12 0 0 1 3 3l-7.2 7.2-4 1Z" />
      <path d="M5 19h14" />
    </svg>
  );
}

function IconReports() {
  return (
    <svg className="h-[18px] w-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M4 20V10" />
      <path d="M10 20V4" />
      <path d="M16 20v-7" />
      <path d="M22 20v-3" />
    </svg>
  );
}

function IconAlerts() {
  return (
    <svg className="h-[18px] w-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M10.27 21a2 2 0 0 0 3.46 0" />
      <path d="M4.8 17h14.4c-1.2-1.5-2.4-3.6-2.4-7a4.8 4.8 0 1 0-9.6 0c0 3.4-1.2 5.5-2.4 7Z" />
    </svg>
  );
}

function IconSettings() {
  return (
    <svg className="h-[18px] w-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M12 15.5A3.5 3.5 0 1 0 12 8.5a3.5 3.5 0 0 0 0 7Z" />
      <path d="M19.4 15a1 1 0 0 0 .2 1.1l.1.1a1 1 0 0 1 0 1.4l-1.2 1.2a1 1 0 0 1-1.4 0l-.1-.1a1 1 0 0 0-1.1-.2 1 1 0 0 0-.6.9V20a1 1 0 0 1-1 1h-1.7a1 1 0 0 1-1-1v-.2a1 1 0 0 0-.6-.9 1 1 0 0 0-1.1.2l-.1.1a1 1 0 0 1-1.4 0l-1.2-1.2a1 1 0 0 1 0-1.4l.1-.1a1 1 0 0 0 .2-1.1 1 1 0 0 0-.9-.6H4a1 1 0 0 1-1-1v-1.7a1 1 0 0 1 1-1h.2a1 1 0 0 0 .9-.6 1 1 0 0 0-.2-1.1l-.1-.1a1 1 0 0 1 0-1.4l1.2-1.2a1 1 0 0 1 1.4 0l.1.1a1 1 0 0 0 1.1.2 1 1 0 0 0 .6-.9V4a1 1 0 0 1 1-1h1.7a1 1 0 0 1 1 1v.2a1 1 0 0 0 .6.9 1 1 0 0 0 1.1-.2l.1-.1a1 1 0 0 1 1.4 0l1.2 1.2a1 1 0 0 1 0 1.4l-.1.1a1 1 0 0 0-.2 1.1 1 1 0 0 0 .9.6h.2a1 1 0 0 1 1 1v1.7a1 1 0 0 1-1 1h-.2a1 1 0 0 0-.9.6Z" />
    </svg>
  );
}

function IconChevronDouble({ collapsed }: { collapsed: boolean }) {
  return (
    <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      {collapsed ? (
        <>
          <path d="m9 6 6 6-6 6" />
          <path d="m5 6 6 6-6 6" />
        </>
      ) : (
        <>
          <path d="m15 6-6 6 6 6" />
          <path d="m19 6-6 6 6 6" />
        </>
      )}
    </svg>
  );
}

function IconLogout() {
  return (
    <svg className="h-[18px] w-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
      <path d="m16 17 5-5-5-5" />
      <path d="M21 12H9" />
    </svg>
  );
}

function SidebarLink({
  item,
  collapsed,
  isActive,
  onClose,
}: {
  item: NavItem;
  collapsed: boolean;
  isActive: boolean;
  onClose: () => void;
}) {
  return (
    <NavLink
      to={item.to}
      end={item.end}
      onClick={onClose}
      title={collapsed ? item.label : undefined}
      aria-label={item.label}
      aria-current={isActive ? "page" : undefined}
      className={({ isActive: isRouterActive }) =>
        [
          "group flex items-center gap-3 rounded-xl px-3 py-2 text-sm font-medium transition-colors",
          collapsed ? "justify-center px-2" : "",
          isActive || isRouterActive ? activeClass : inactiveClass,
        ]
          .filter(Boolean)
          .join(" ")
      }
    >
      <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-white/5 text-slate-200 transition-colors group-hover:bg-white/10 group-hover:text-white">
        {item.icon}
      </span>
      {!collapsed ? <span className="truncate">{item.label}</span> : null}
    </NavLink>
  );
}

export default function AppLayout({ children }: PropsWithChildren) {
  const { logout, user } = useAuth();
  const location = useLocation();
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(readSidebarPreference);

  const canAccessDashboard = user?.role !== "supplier";
  const canAccessTickets = user?.role !== "supplier";
  const canAccessReports =
    user?.role === "admin" ||
    user?.role === "director" ||
    user?.role === "engineering" ||
    user?.role === "manager";
  const canAccessEngineering = user?.role === "admin" || user?.role === "engineering";
  const canAccessAlerts = user?.role !== "supplier";
  const canAccessSettings = hasSettingsAccess(user?.role);

  const settingsTabs = useMemo(() => getSettingsTabs(user?.role), [user?.role]);
  const navItems = useMemo(
    () =>
      [
        canAccessDashboard ? { label: "Dashboard", to: "/dashboard", icon: <IconDashboard />, end: true } : null,
        canAccessTickets ? { label: "Chamados", to: "/tickets", icon: <IconTickets /> } : null,
        canAccessEngineering ? { label: "Engenharia", to: "/engineering", icon: <IconEngineering />, end: true } : null,
        canAccessReports ? { label: "Relatórios", to: "/reports", icon: <IconReports />, end: true } : null,
        canAccessAlerts ? { label: "Alertas", to: "/alerts", icon: <IconAlerts />, end: true } : null,
        canAccessSettings ? { label: "Configurações", to: "/settings", icon: <IconSettings /> } : null,
      ].filter(Boolean) as NavItem[],
    [canAccessAlerts, canAccessDashboard, canAccessEngineering, canAccessReports, canAccessSettings, canAccessTickets],
  );

  const userInitials = user?.name
    ? user.name
        .split(" ")
        .slice(0, 2)
        .map((part) => part[0]?.toUpperCase() ?? "")
        .join("")
    : "US";

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    window.localStorage.setItem(SIDEBAR_COLLAPSED_KEY, String(isSidebarCollapsed));
  }, [isSidebarCollapsed]);

  function closeSidebar() {
    setIsSidebarOpen(false);
  }

  function isNavItemActive(item: NavItem) {
    if (item.to === "/dashboard") {
      return location.pathname === "/dashboard";
    }

    if (item.to === "/settings") {
      return location.pathname === "/settings" || location.pathname.startsWith("/settings/");
    }

    return location.pathname === item.to || location.pathname.startsWith(`${item.to}/`);
  }

  const topbarSubtitle = ROLE_LABELS[user?.role ?? "manager"];
  const userScope = settingsTabs.length > 0 ? `${settingsTabs.length} area(s) administrativas` : "Sem acesso administrativo";

  return (
    <div className="flex h-screen overflow-hidden bg-[#f8f6f1]">
      {isSidebarOpen ? (
        <div className="fixed inset-0 z-20 bg-black/50 lg:hidden" onClick={closeSidebar} aria-hidden="true" />
      ) : null}

      <aside
        className={[
          "fixed inset-y-0 left-0 z-30 flex w-[224px] flex-col bg-[#111111] text-slate-100 shadow-[16px_0_60px_rgba(17,17,17,0.12)] transition-transform duration-300 ease-in-out",
          isSidebarOpen ? "translate-x-0" : "-translate-x-full",
          isSidebarCollapsed ? "lg:w-[88px]" : "lg:w-[224px]",
          "lg:relative lg:translate-x-0 lg:transition-[width]",
        ].join(" ")}
      >
        <div className={["border-b border-slate-800/80", isSidebarCollapsed ? "px-3 py-3" : "px-4 py-3.5"].join(" ")}>
          <div className={`flex items-center ${isSidebarCollapsed ? "justify-center" : "justify-between gap-3"}`}>
            <div className={`flex min-w-0 items-center gap-3 ${isSidebarCollapsed ? "justify-center" : ""}`}>
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#c9a24a] text-sm font-bold text-[#111111]">
                EC
              </div>
              {!isSidebarCollapsed ? (
                <div className="min-w-0">
                  <h1 className="truncate text-sm font-semibold leading-tight text-white">Portal de Chamados</h1>
                  <p className="mt-0.5 text-[10px] uppercase tracking-[0.14em] text-slate-400">Engenharia</p>
                </div>
              ) : null}
            </div>

            <button
              type="button"
              onClick={() => setIsSidebarCollapsed((current) => !current)}
              className="inline-flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg text-slate-400 transition-colors hover:bg-slate-800 hover:text-white"
              aria-label={isSidebarCollapsed ? "Expandir menu" : "Recolher menu"}
              data-testid="sidebar-collapse-button"
              title={isSidebarCollapsed ? "Expandir menu lateral" : "Recolher menu lateral"}
            >
              <IconChevronDouble collapsed={isSidebarCollapsed} />
            </button>
          </div>
        </div>

        <nav
          className={`flex-1 overflow-y-auto ${isSidebarCollapsed ? "px-2 py-3" : "px-3 py-4"}`}
          aria-label="Navegacao principal"
        >
          <div className="space-y-1">
            {navItems.map((item) => (
              <SidebarLink
                key={item.to}
                item={item}
                collapsed={isSidebarCollapsed}
                isActive={isNavItemActive(item)}
                onClose={closeSidebar}
              />
            ))}
          </div>
        </nav>

        <div className={["border-t border-slate-800/80", isSidebarCollapsed ? "px-2 py-3" : "px-3 py-3"].join(" ")}>
          <div
            className={[
              "rounded-xl bg-slate-900/80 ring-1 ring-inset ring-white/5",
              isSidebarCollapsed ? "px-2 py-2" : "px-3 py-2.5",
            ].join(" ")}
            title={isSidebarCollapsed ? `${user?.name || "Usuario"} · ${topbarSubtitle}` : undefined}
          >
            <div className={`flex items-center ${isSidebarCollapsed ? "justify-center" : "gap-2.5"}`}>
              <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-[#c9a24a] text-[11px] font-bold text-[#111111]">
                {userInitials}
              </div>
              {!isSidebarCollapsed ? (
                <div className="min-w-0 flex-1">
                  <p className="truncate text-xs font-semibold text-white">{user?.name || "Usuario"}</p>
                  <p className="truncate text-[10px] text-slate-400">{topbarSubtitle}</p>
                </div>
              ) : null}
            </div>
            {!isSidebarCollapsed ? <p className="mt-2 truncate text-[10px] text-slate-500">{userScope}</p> : null}
          </div>

          <button
            type="button"
            onClick={logout}
            className={[
              "mt-2 inline-flex items-center rounded-lg text-xs font-medium text-slate-400 transition-colors hover:bg-slate-800 hover:text-white",
              isSidebarCollapsed ? "h-9 w-full justify-center" : "w-full gap-2 px-3 py-2",
            ].join(" ")}
            aria-label="Sair"
            title="Sair"
          >
            <IconLogout />
            {!isSidebarCollapsed ? <span>Sair</span> : null}
          </button>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
        <header className="flex h-14 flex-shrink-0 items-center justify-between border-b border-[#e7dfcf] bg-white/90 px-4 backdrop-blur sm:px-6">
          <div className="flex min-w-0 items-center gap-3">
            <button
              type="button"
              className="inline-flex h-9 w-9 items-center justify-center rounded-lg text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-900 lg:hidden"
              aria-label={isSidebarOpen ? "Fechar menu lateral" : "Abrir menu lateral"}
              onClick={() => setIsSidebarOpen((current) => !current)}
            >
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <div className="min-w-0">
              <p className="truncate text-sm font-medium text-slate-900">{user?.name || "Usuario"}</p>
              <p className="truncate text-xs text-slate-500">{topbarSubtitle}</p>
            </div>
          </div>

          <div className="flex items-center gap-2 sm:gap-3">
            <span className="hidden items-center rounded-full bg-[#f3eee2] px-2.5 py-1 text-[11px] font-semibold text-slate-700 ring-1 ring-inset ring-[#e7dfcf] sm:inline-flex">
              Sessao ativa
            </span>
            <button
              type="button"
              onClick={logout}
              className="inline-flex h-9 items-center justify-center rounded-xl border border-[#e7dfcf] bg-white px-3 text-xs font-semibold text-slate-600 transition-colors hover:bg-[#f3eee2] hover:text-slate-900 sm:gap-2"
              aria-label="Encerrar sessao"
            >
              <IconLogout />
              <span className="hidden sm:inline">Sair</span>
            </button>
          </div>
        </header>

        <main className="min-w-0 flex-1 overflow-y-auto overflow-x-hidden p-4 sm:p-6 lg:p-8">
          <div className="mx-auto min-w-0 w-full max-w-7xl">{children}</div>
        </main>
      </div>
    </div>
  );
}
