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

const toneToClass: Record<string, string> = {
  info: "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-800",
  success: "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800",
  warning: "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800",
  danger: "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-red-100 text-red-800",
  neutral: "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-700",
  accent: "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-teal-100 text-teal-800",
};

export function statusClass(status: TicketStatus) {
  return toneToClass[ticketStatusTone(status)] ?? toneToClass.neutral;
}

export function approvalStatusClass(status: keyof typeof APPROVAL_STATUS_LABELS) {
  return toneToClass[approvalStatusTone(status)] ?? toneToClass.neutral;
}

export function priorityClass(priority: keyof typeof PRIORITY_LABELS) {
  return toneToClass[priorityTone(priority)] ?? toneToClass.neutral;
}

export function severityClass(severity: keyof typeof SEVERITY_LABELS) {
  return toneToClass[severityTone(severity)] ?? toneToClass.neutral;
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
