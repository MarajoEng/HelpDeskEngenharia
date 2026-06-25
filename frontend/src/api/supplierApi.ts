import { requestJson } from "./http";
import type {
  Supplier,
  SupplierCreatePayload,
  SupplierFilters,
  SupplierListResponse,
  SupplierUpdatePayload,
} from "../types/supplier";

function authHeaders(token: string) {
  return { Authorization: `Bearer ${token}` };
}

function buildQuery(filters: SupplierFilters) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") return;
    params.set(key, String(value));
  });
  const query = params.toString();
  return query ? `/suppliers?${query}` : "/suppliers";
}

export function listSuppliers(token: string, filters: SupplierFilters = {}) {
  return requestJson<SupplierListResponse>(buildQuery(filters), {
    headers: authHeaders(token),
  });
}

export function createSupplier(token: string, payload: SupplierCreatePayload) {
  return requestJson<Supplier>("/suppliers", {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  });
}

export function updateSupplier(token: string, supplierId: number, payload: SupplierUpdatePayload) {
  return requestJson<Supplier>(`/suppliers/${supplierId}`, {
    method: "PATCH",
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  });
}
