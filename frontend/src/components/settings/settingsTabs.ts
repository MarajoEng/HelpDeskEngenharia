import type { UserRole } from "../../types/auth";

export interface SettingsTab {
  label: string;
  to: string;
}

export function getSettingsTabs(role?: UserRole): SettingsTab[] {
  const canAccessTicketSettings = role === "admin";
  const canAccessUnits = role === "admin" || role === "engineering" || role === "director";
  const canAccessUsers = role === "admin";
  const canAccessSuppliers = role === "admin" || role === "engineering" || role === "director";
  const canAccessApprovalLevels = role === "admin";
  const canAccessAuditLogs = role === "admin";

  return [
    { label: "Chamados", to: "/settings/tickets", enabled: canAccessTicketSettings },
    { label: "Unidades", to: "/settings/units", enabled: canAccessUnits },
    { label: "Usuários", to: "/settings/users", enabled: canAccessUsers },
    { label: "Fornecedores", to: "/settings/suppliers", enabled: canAccessSuppliers },
    { label: "Alçadas", to: "/settings/approval-levels", enabled: canAccessApprovalLevels },
    { label: "Auditoria", to: "/settings/audit-logs", enabled: canAccessAuditLogs },
  ]
    .filter((tab) => tab.enabled)
    .map(({ label, to }) => ({ label, to }));
}

export function hasSettingsAccess(role?: UserRole) {
  return getSettingsTabs(role).length > 0;
}
