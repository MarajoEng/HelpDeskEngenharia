import { requestJson } from "./http";
import type { Ticket, TicketCreatePayload, TicketDetail, TicketFilters, TicketListResponse } from "../types/ticket";

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
