import type { CurrentUser, LoginRequest, TokenResponse } from "../types/auth";
import { requestJson } from "./http";

export function loginRequest(payload: LoginRequest) {
  return requestJson<TokenResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getCurrentUser(token: string) {
  return requestJson<CurrentUser>("/auth/me", {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
}
