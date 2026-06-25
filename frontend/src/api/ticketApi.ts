import { requestJson } from "./http";
import type {
  Ticket,
  TicketApprovalDecisionPayload,
  TicketApprovalRequestPayload,
  TicketCreatePayload,
  TicketDetail,
  TicketFilters,
  TicketListResponse,
  TicketTriagePayload,
} from "../types/ticket";
import type { UserFilters, UserListResponse } from "../types/user";

function authHeaders(token: string) {
  return { Authorization: `Bearer ${token}` };
}

function buildQuery(filters: TicketFilters) {
  const params = new URLSearchParams();

  Object.entries(filters).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") {
      return;
    }
    params.set(key, String(value));
  });

  const query = params.toString();
  return query ? `/tickets?${query}` : "/tickets";
}

export function createTicket(token: string, payload: TicketCreatePayload) {
  return requestJson<Ticket>("/tickets", {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  });
}

export function listTickets(token: string, filters: TicketFilters) {
  return requestJson<TicketListResponse>(buildQuery(filters), {
    headers: authHeaders(token),
  });
}

export function getTicketById(token: string, ticketId: number) {
  return requestJson<TicketDetail>(`/tickets/${ticketId}`, {
    headers: authHeaders(token),
  });
}

export function listTriageAssignees(token: string, filters: UserFilters) {
  const params = new URLSearchParams();

  Object.entries(filters).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") {
      return;
    }
    params.set(key, String(value));
  });

  const query = params.toString();
  return requestJson<UserListResponse>(query ? `/tickets/triage-assignees?${query}` : "/tickets/triage-assignees", {
    headers: authHeaders(token),
  });
}

export function triageTicket(token: string, ticketId: number, payload: TicketTriagePayload) {
  return requestJson<TicketDetail>(`/tickets/${ticketId}/triage`, {
    method: "PATCH",
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  });
}

export function requestTicketApproval(token: string, ticketId: number, payload: TicketApprovalRequestPayload) {
  return requestJson<TicketDetail>(`/tickets/${ticketId}/approval-request`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  });
}

export function decideTicketApproval(token: string, ticketId: number, payload: TicketApprovalDecisionPayload) {
  return requestJson<TicketDetail>(`/tickets/${ticketId}/approval-decision`, {
    method: "PATCH",
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  });
}
