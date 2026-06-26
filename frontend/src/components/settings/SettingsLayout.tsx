import { Outlet, NavLink, Navigate, useLocation } from "react-router-dom";

import { useAuth } from "../../hooks/useAuth";
import { getSettingsTabs } from "./settingsTabs";

export default function SettingsLayout() {
  const { user } = useAuth();
  const location = useLocation();

  const tabs = getSettingsTabs(user?.role);

  if (tabs.length === 0) {
    return <Navigate to="/dashboard" replace />;
  }

  if (location.pathname === "/settings" || location.pathname === "/settings/") {
    return <Navigate to={tabs[0].to} replace />;
  }

  return (
    <div className="mx-auto flex w-full max-w-7xl flex-col gap-6">
      <header className="space-y-1">
        <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-[#c9a24a]">Sistema</p>
        <h1 className="text-[1.8rem] font-extrabold tracking-tight text-slate-950">Configurações</h1>
        <p className="max-w-3xl text-sm leading-relaxed text-slate-500">
          Chamados, unidades, usuários, fornecedores, alçadas e auditoria ficam concentrados nesta área.
        </p>
      </header>

      <div className="min-w-0 rounded-[22px] border border-[#e7dfcf] bg-white px-3 py-2 shadow-[0_18px_60px_rgba(17,24,39,0.07)]">
        <nav className="flex max-w-full gap-1 overflow-x-auto overscroll-x-contain" aria-label="Tabs de configurações">
          {tabs.map((tab) => (
            <NavLink
              key={tab.to}
              to={tab.to}
              className={({ isActive }) =>
                `whitespace-nowrap rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-slate-950 text-white ring-1 ring-inset ring-slate-900"
                    : "text-slate-500 hover:bg-[#f3eee2] hover:text-slate-800"
                }`
              }
            >
              {tab.label}
            </NavLink>
          ))}
        </nav>
      </div>

      <main className="flex-1">
        <Outlet />
      </main>
    </div>
  );
}
