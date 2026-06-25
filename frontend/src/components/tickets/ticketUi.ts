import type { UserRole } from "../../types/auth";
import type {
  Ticket,
  TicketDetail,
  TicketPriority,
  TicketSeverity,
  TicketStatus,
} from "../../types/ticket";

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
  manager: "Manager",
  engineering: "Engineering",
  director: "Director",
  supplier: "Supplier",
};

export const APPROVAL_STATUS_LABELS = {
  pending: "Pendente",
  approved: "Aprovado",
  rejected: "Rejeitado",
  canceled: "Cancelado",
} as const;

export const TRIAGE_ALLOWED_STATUSES: TicketStatus[] = ["open", "triage", "waiting_unit"];

export function formatDate(value: string | null | undefined) {
  if (!value) return "—";
  return new Date(value).toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatMoney(value: string | null | undefined) {
  if (!value) return "Nao informado";
  const parsed = Number(value);
  return Number.isNaN(parsed)
    ? value
    : new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(parsed);
}

export function formatDateTimeLocalInput(value: string | null | undefined) {
  if (!value) return "";

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return "";
  }

  const timezoneOffset = parsed.getTimezoneOffset() * 60_000;
  return new Date(parsed.getTime() - timezoneOffset).toISOString().slice(0, 16);
}

export function statusClass(status: TicketStatus) {
  if (status === "open") return "status-badge status-badge--info";
  if (status === "resolved" || status === "closed" || status === "approved") {
    return "status-badge status-badge--success";
  }
  if (status === "rejected" || status === "canceled") return "status-badge status-badge--danger";
  return "status-badge status-badge--muted";
}

export function approvalStatusClass(status: keyof typeof APPROVAL_STATUS_LABELS) {
  if (status === "approved") return "status-badge status-badge--success";
  if (status === "rejected" || status === "canceled") return "status-badge status-badge--danger";
  return "status-badge status-badge--muted";
}

export function priorityClass(priority: TicketPriority) {
  return `priority-badge priority-badge--${priority}`;
}

export function severityClass(severity: TicketSeverity) {
  return `severity-badge severity-badge--${severity}`;
}

export function isSlaLate(ticket: Pick<Ticket | TicketDetail, "sla_due_at" | "status">) {
  if (!ticket.sla_due_at) return false;
  const finalStatuses: TicketStatus[] = ["resolved", "closed", "canceled"];
  if (finalStatuses.includes(ticket.status)) return false;
  return new Date(ticket.sla_due_at) < new Date();
}

export function canAccessEngineeringQueue(role: UserRole | undefined) {
  return role === "admin" || role === "engineering";
}

export function canTriageTicketStatus(status: TicketStatus) {
  return TRIAGE_ALLOWED_STATUSES.includes(status);
}

export function canManageApprovalRequest(role: UserRole | undefined) {
  return role === "admin" || role === "engineering";
}
