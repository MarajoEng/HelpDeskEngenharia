import { requestJson } from "./http";
import type { Unit, UnitFilters, UnitGroupOption, UnitListResponse, UnitPayload } from "../types/unit";

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

export function listUnitGroups(token: string) {
  return requestJson<UnitGroupOption[]>("/units/groups", {
    headers: authHeaders(token),
  });
}

export function getGroupOptions(units: Unit[]): string[] {
  const seen = new Set<string>();
  const groups: string[] = [];
  for (const unit of units) {
    if (unit.group_code && !seen.has(unit.group_code)) {
      seen.add(unit.group_code);
      groups.push(unit.group_code);
    }
  }
  return groups.sort();
}

export function getBranchesByGroup(units: Unit[], group: string): Unit[] {
  return units.filter((unit) => unit.group_code === group);
}

export function formatBranchLabel(unit: Unit): string {
  const code = unit.branch_code ?? unit.code;
  return `${code} — ${unit.name}`;
}
