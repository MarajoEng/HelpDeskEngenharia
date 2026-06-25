import type { UserRole } from "../../types/auth";
import type {
  Ticket,
  TicketDetail,
  TicketStatus,
} from "../../types/ticket";
import {
  APPROVAL_STATUS_LABELS,
  PRIORITY_LABELS,
  ROLE_LABELS,
  SEVERITY_LABELS,
  STATUS_LABELS,
  approvalStatusTone,
  priorityTone,
  severityTone,
  ticketStatusTone,
} from "../ui/statusOptions";
import { formatDate, formatDateTimeLocalInput, formatMoney } from "../../utils/formatters";

export {
  APPROVAL_STATUS_LABELS,
  PRIORITY_LABELS,
  ROLE_LABELS,
  SEVERITY_LABELS,
  STATUS_LABELS,
  formatDate,
  formatDateTimeLocalInput,
  formatMoney,
};

export const TRIAGE_ALLOWED_STATUSES: TicketStatus[] = ["open", "triage", "waiting_unit"];

export function statusClass(status: TicketStatus) {
  return `ui-badge ui-badge--${ticketStatusTone(status)}`;
}

export function approvalStatusClass(status: keyof typeof APPROVAL_STATUS_LABELS) {
  return `ui-badge ui-badge--${approvalStatusTone(status)}`;
}

export function priorityClass(priority: keyof typeof PRIORITY_LABELS) {
  return `ui-badge ui-badge--${priorityTone(priority)}`;
}

export function severityClass(severity: keyof typeof SEVERITY_LABELS) {
  return `ui-badge ui-badge--${severityTone(severity)}`;
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
