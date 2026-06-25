import { requestJson } from "./http";
import type { AlertFilters, AlertListResponse, RunSlaMonitorResponse, TicketAlert } from "../types/alert";

function authHeaders(token: string) {
  return { Authorization: `Bearer ${token}` };
}

export function listAlerts(token: string, filters: AlertFilters = {}) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      params.set(key, String(value));
    }
  });
  const query = params.toString();
  return requestJson<AlertListResponse>(query ? `/alerts?${query}` : "/alerts", {
    headers: authHeaders(token),
  });
}

export function markAlertRead(token: string, alertId: number) {
  return requestJson<TicketAlert>(`/alerts/${alertId}/read`, {
    method: "PATCH",
    headers: authHeaders(token),
  });
}

export function markAllAlertsRead(token: string) {
  return requestJson<{ marked_read: number }>("/alerts/read-all", {
    method: "PATCH",
    headers: authHeaders(token),
  });
}

export function runSlaMonitor(token: string) {
  return requestJson<RunSlaMonitorResponse>("/alerts/run-sla-monitor", {
    method: "POST",
    headers: authHeaders(token),
  });
}
