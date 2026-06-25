import { requestJson } from "./http";
import type { UserFilters, UserItem, UserListResponse, UserPayload } from "../types/user";

function buildQuery(filters: UserFilters) {
  const params = new URLSearchParams();

  Object.entries(filters).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") {
      return;
    }
    params.set(key, String(value));
  });

  const query = params.toString();
  return query ? `/users?${query}` : "/users";
}

function authHeaders(token: string) {
  return { Authorization: `Bearer ${token}` };
}

export function listUsers(token: string, filters: UserFilters) {
  return requestJson<UserListResponse>(buildQuery(filters), {
    headers: authHeaders(token),
  });
}

export function createUser(token: string, payload: UserPayload) {
  return requestJson<UserItem>("/users", {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  });
}

export function updateUser(
  token: string,
  userId: number,
  payload: Partial<UserPayload>,
) {
  return requestJson<UserItem>(`/users/${userId}`, {
    method: "PATCH",
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  });
}
