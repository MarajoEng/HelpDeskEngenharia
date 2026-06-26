import { requestJson } from "./http";
import type {
  TicketCategoryItem,
  TicketCategoryListResponse,
  TicketCategoryPayload,
  TicketConfigurationFilters,
  TicketCustomFieldFilters,
  TicketCustomFieldItem,
  TicketCustomFieldListResponse,
  TicketCustomFieldPayload,
  TicketFormSchemaResponse,
  TicketPriorityItem,
  TicketPriorityListResponse,
  TicketPriorityPayload,
  TicketSubcategoryFilters,
  TicketSubcategoryItem,
  TicketSubcategoryListResponse,
  TicketSubcategoryPayload,
  TicketTypeItem,
  TicketTypeListResponse,
  TicketTypePayload,
} from "../types/ticketConfiguration";

function authHeaders(token: string) {
  return { Authorization: `Bearer ${token}` };
}

function buildQuery(filters: object) {
  const params = new URLSearchParams();

  Object.entries(filters as Record<string, unknown>).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") {
      return;
    }

    params.set(key, String(value));
  });

  const query = params.toString();
  return query ? `?${query}` : "";
}

export function listAdminTicketCategories(token: string, filters: TicketConfigurationFilters) {
  return requestJson<TicketCategoryListResponse>(
    `/admin/ticket-categories${buildQuery(filters)}`,
    { headers: authHeaders(token) },
  );
}

export function listTicketCategories(filters: TicketConfigurationFilters = {}) {
  return requestJson<TicketCategoryListResponse>(`/ticket-categories${buildQuery(filters)}`);
}

export function createTicketCategory(token: string, payload: TicketCategoryPayload) {
  return requestJson<TicketCategoryItem>("/admin/ticket-categories", {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  });
}

export function updateTicketCategory(token: string, categoryId: number, payload: Partial<TicketCategoryPayload>) {
  return requestJson<TicketCategoryItem>(`/admin/ticket-categories/${categoryId}`, {
    method: "PATCH",
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  });
}

export function listAdminTicketSubcategories(token: string, filters: TicketSubcategoryFilters) {
  return requestJson<TicketSubcategoryListResponse>(
    `/admin/ticket-subcategories${buildQuery(filters)}`,
    { headers: authHeaders(token) },
  );
}

export function listTicketSubcategories(categoryId: number, filters: TicketConfigurationFilters = {}) {
  return requestJson<TicketSubcategoryListResponse>(
    `/ticket-categories/${categoryId}/subcategories${buildQuery(filters)}`,
  );
}

export function createTicketSubcategory(token: string, payload: TicketSubcategoryPayload) {
  return requestJson<TicketSubcategoryItem>("/admin/ticket-subcategories", {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  });
}

export function updateTicketSubcategory(
  token: string,
  subcategoryId: number,
  payload: Partial<TicketSubcategoryPayload>,
) {
  return requestJson<TicketSubcategoryItem>(`/admin/ticket-subcategories/${subcategoryId}`, {
    method: "PATCH",
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  });
}

export function listAdminTicketTypes(token: string, filters: TicketConfigurationFilters) {
  return requestJson<TicketTypeListResponse>(
    `/admin/ticket-types${buildQuery(filters)}`,
    { headers: authHeaders(token) },
  );
}

export function listTicketTypes(filters: TicketConfigurationFilters = {}) {
  return requestJson<TicketTypeListResponse>(`/ticket-types${buildQuery(filters)}`);
}

export function createTicketType(token: string, payload: TicketTypePayload) {
  return requestJson<TicketTypeItem>("/admin/ticket-types", {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  });
}

export function updateTicketType(token: string, typeId: number, payload: Partial<TicketTypePayload>) {
  return requestJson<TicketTypeItem>(`/admin/ticket-types/${typeId}`, {
    method: "PATCH",
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  });
}

export function listAdminTicketPriorities(token: string, filters: TicketConfigurationFilters) {
  return requestJson<TicketPriorityListResponse>(
    `/admin/ticket-priorities${buildQuery(filters)}`,
    { headers: authHeaders(token) },
  );
}

export function listTicketPriorities(filters: TicketConfigurationFilters = {}) {
  return requestJson<TicketPriorityListResponse>(`/ticket-priorities${buildQuery(filters)}`);
}

export function createTicketPriority(token: string, payload: TicketPriorityPayload) {
  return requestJson<TicketPriorityItem>("/admin/ticket-priorities", {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  });
}

export function updateTicketPriority(token: string, priorityId: number, payload: Partial<TicketPriorityPayload>) {
  return requestJson<TicketPriorityItem>(`/admin/ticket-priorities/${priorityId}`, {
    method: "PATCH",
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  });
}

export function listAdminTicketCustomFields(token: string, filters: TicketCustomFieldFilters) {
  return requestJson<TicketCustomFieldListResponse>(
    `/admin/ticket-custom-fields${buildQuery(filters)}`,
    { headers: authHeaders(token) },
  );
}

export function createTicketCustomField(token: string, payload: TicketCustomFieldPayload) {
  return requestJson<TicketCustomFieldItem>("/admin/ticket-custom-fields", {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  });
}

export function updateTicketCustomField(
  token: string,
  customFieldId: number,
  payload: Partial<TicketCustomFieldPayload>,
) {
  return requestJson<TicketCustomFieldItem>(`/admin/ticket-custom-fields/${customFieldId}`, {
    method: "PATCH",
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  });
}

export function getTicketFormSchema(categoryId: number, subcategoryId?: number | null) {
  return requestJson<TicketFormSchemaResponse>(
    `/tickets/form-schema${buildQuery({
      category_id: categoryId,
      subcategory_id: subcategoryId || "",
    })}`,
  );
}
