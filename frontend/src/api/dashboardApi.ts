import { requestJson } from "./http";
import type { DashboardFilters, DashboardOverview } from "../types/dashboard";

function authHeaders(token: string) {
  return { Authorization: `Bearer ${token}` };
}

function buildQuery(filters: DashboardFilters) {
  const params = new URLSearchParams();

  Object.entries(filters).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") {
      return;
    }
    params.set(key, String(value));
  });

  const query = params.toString();
  return query ? `/dashboard/overview?${query}` : "/dashboard/overview";
}

export function getDashboardOverview(token: string, filters: DashboardFilters) {
  return requestJson<DashboardOverview>(buildQuery(filters), {
    headers: authHeaders(token),
  });
}
