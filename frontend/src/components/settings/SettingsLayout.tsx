import { Outlet, NavLink, Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";

export default function SettingsLayout() {
  const { user } = useAuth();
  const location = useLocation();

  const canAccessUnits = user?.role === "admin" || user?.role === "engineering" || user?.role === "director";
  const canAccessUsers = user?.role === "admin";
  const canAccessSuppliers = user?.role === "admin" || user?.role === "engineering" || user?.role === "director";
  const canAccessApprovalLevels = user?.role === "admin";
  const canAccessAuditLogs = user?.role === "admin";

  const tabs = [
    { label: "Unidades", to: "/settings/units", enabled: canAccessUnits },
    { label: "Usuários", to: "/settings/users", enabled: canAccessUsers },
    { label: "Fornecedores", to: "/settings/suppliers", enabled: canAccessSuppliers },
    { label: "Alçadas", to: "/settings/approval-levels", enabled: canAccessApprovalLevels },
    { label: "Auditoria", to: "/settings/audit-logs", enabled: canAccessAuditLogs },
  ].filter((tab) => tab.enabled);

  // Se o usuário não tem acesso a nada, não deve estar aqui
  if (tabs.length === 0) {
    return <Navigate to="/dashboard" replace />;
  }

  // Redirecionar /settings para a primeira aba disponível
  if (location.pathname === "/settings" || location.pathname === "/settings/") {
    return <Navigate to={tabs[0].to} replace />;
  }

  return (
    <div className="flex flex-col gap-6 max-w-7xl mx-auto w-full">
      <header>
        <h1 className="text-2xl font-bold text-slate-900">Configurações</h1>
        <p className="text-slate-500 text-sm mt-1">
          Gerencie permissões, unidades, alçadas e recursos do sistema.
        </p>
      </header>

      <div className="border-b border-slate-200">
        <nav className="-mb-px flex gap-6 overflow-x-auto" aria-label="Tabs de configurações">
          {tabs.map((tab) => (
            <NavLink
              key={tab.to}
              to={tab.to}
              className={({ isActive }) =>
                `whitespace-nowrap py-3 px-1 border-b-2 font-medium text-sm transition-colors ${
                  isActive
                    ? "border-teal-500 text-teal-600"
                    : "border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300"
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
