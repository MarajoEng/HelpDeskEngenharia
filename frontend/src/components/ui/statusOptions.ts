import type { AlertSeverity, AlertType } from "../../types/alert";
import type { UserRole } from "../../types/auth";
import type {
  ApprovalStatus,
  SlaStatus,
  TicketCategory,
  TicketPriority,
  TicketSeverity,
  TicketStatus,
} from "../../types/ticket";

export type BadgeTone =
  | "neutral"
  | "info"
  | "success"
  | "warning"
  | "danger"
  | "accent";

export const STATUS_LABELS: Record<TicketStatus, string> = {
  open: "Aberto",
  triage: "Triagem",
  waiting_approval: "Ag. aprovacao",
  approved: "Aprovado",
  rejected: "Rejeitado",
  in_progress: "Em execucao",
  waiting_supplier: "Ag. fornecedor",
  waiting_unit: "Ag. unidade",
  resolved: "Resolvido",
  closed: "Encerrado",
  canceled: "Cancelado",
};

export const PRIORITY_LABELS: Record<TicketPriority, string> = {
  low: "Baixa",
  medium: "Media",
  high: "Alta",
  critical: "Critica",
};

export const SEVERITY_LABELS: Record<TicketSeverity, string> = {
  low: "Baixa",
  medium: "Media",
  high: "Alta",
  critical: "Critica",
};

export const ROLE_LABELS: Record<UserRole, string> = {
  admin: "Admin",
  manager: "Gestor",
  engineering: "Engenharia",
  director: "Diretoria",
  supplier: "Fornecedor",
};

export const APPROVAL_STATUS_LABELS: Record<ApprovalStatus, string> = {
  pending: "Pendente",
  approved: "Aprovado",
  rejected: "Rejeitado",
  canceled: "Cancelado",
};

export const ALERT_TYPE_LABELS: Record<AlertType, string> = {
  sla_late: "SLA vencido",
  sla_due_soon: "SLA proximo",
  execution_late: "Execucao atrasada",
};

export const ALERT_SEVERITY_LABELS: Record<AlertSeverity, string> = {
  info: "Info",
  warning: "Aviso",
  critical: "Critico",
};

export const CATEGORY_LABELS: Record<TicketCategory, string> = {
  fuel_pump: "Bomba",
  fuel_nozzle: "Bico",
  electrical: "Eletrica",
  plumbing: "Hidraulica",
  leak: "Vazamento",
  structure: "Estrutura",
  roof: "Cobertura",
  pavement: "Pavimento",
  environmental_risk: "Risco ambiental",
  other: "Outro",
};

export function ticketStatusTone(status: TicketStatus): BadgeTone {
  if (status === "resolved" || status === "closed" || status === "approved") return "success";
  if (status === "rejected" || status === "canceled") return "danger";
  if (status === "waiting_approval" || status === "waiting_supplier" || status === "waiting_unit") {
    return "warning";
  }
  if (status === "open") return "info";
  return "neutral";
}

export function priorityTone(priority: TicketPriority): BadgeTone {
  if (priority === "critical") return "danger";
  if (priority === "high") return "warning";
  if (priority === "medium") return "accent";
  return "success";
}

export function severityTone(severity: TicketSeverity): BadgeTone {
  if (severity === "critical") return "danger";
  if (severity === "high") return "warning";
  if (severity === "medium") return "accent";
  return "success";
}

export function approvalStatusTone(status: ApprovalStatus): BadgeTone {
  if (status === "approved") return "success";
  if (status === "rejected" || status === "canceled") return "danger";
  return "warning";
}

export function alertSeverityTone(severity: AlertSeverity): BadgeTone {
  if (severity === "critical") return "danger";
  if (severity === "warning") return "warning";
  return "info";
}

export function slaStatusLabel(status: SlaStatus) {
  switch (status) {
    case "on_track":
      return "No prazo";
    case "late":
      return "Atrasado";
    case "no_sla":
      return "Sem SLA";
    case "closed":
      return "Encerrado";
  }
}

export function slaStatusTone(status: SlaStatus): BadgeTone {
  switch (status) {
    case "on_track":
      return "success";
    case "late":
      return "danger";
    case "closed":
      return "neutral";
    case "no_sla":
      return "warning";
  }
}
