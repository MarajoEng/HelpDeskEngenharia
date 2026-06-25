import { requestJson } from "./http";
import type { Unit, UnitFilters, UnitListResponse, UnitPayload } from "../types/unit";

function buildQuery(filters: UnitFilters) {
  const params = new URLSearchParams();

  Object.entries(filters).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") {
      return;
    }
    params.set(key, String(value));
  });

  const query = params.toString();
  return query ? `/units?${query}` : "/units";
}

function authHeaders(token: string) {
  return { Authorization: `Bearer ${token}` };
}

export function listUnits(token: string, filters: UnitFilters) {
  return requestJson<UnitListResponse>(buildQuery(filters), {
    headers: authHeaders(token),
  });
}

export function getUnitById(token: string, unitId: number) {
  return requestJson<Unit>(`/units/${unitId}`, {
    headers: authHeaders(token),
  });
}

export function createUnit(token: string, payload: UnitPayload) {
  return requestJson<Unit>("/units", {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  });
}

export function updateUnit(token: string, unitId: number, payload: Partial<UnitPayload>) {
  return requestJson<Unit>(`/units/${unitId}`, {
    method: "PATCH",
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  });
}
