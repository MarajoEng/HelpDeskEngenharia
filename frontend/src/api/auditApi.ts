import type { AuditLogFilters, AuditLogListResponse } from "../types/audit";
import { requestJson } from "./http";

function buildAuditQuery(filters: AuditLogFilters): string {
  const params = new URLSearchParams();
  if (filters.page) params.set("page", String(filters.page));
  if (filters.page_size) params.set("page_size", String(filters.page_size));
  if (filters.actor_user_id) params.set("actor_user_id", String(filters.actor_user_id));
  if (filters.action) params.set("action", filters.action);
  if (filters.entity_type) params.set("entity_type", filters.entity_type);
  if (filters.entity_id) params.set("entity_id", String(filters.entity_id));
  if (filters.date_from) params.set("date_from", filters.date_from);
  if (filters.date_to) params.set("date_to", filters.date_to);
  if (filters.search) params.set("search", filters.search);
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

export function listAuditLogs(
  token: string,
  filters: AuditLogFilters = {},
): Promise<AuditLogListResponse> {
  return requestJson<AuditLogListResponse>(`/audit-logs${buildAuditQuery(filters)}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}
