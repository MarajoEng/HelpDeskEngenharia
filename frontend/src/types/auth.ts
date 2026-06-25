export type UserRole =
  | "admin"
  | "manager"
  | "engineering"
  | "director"
  | "supplier";

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface CurrentUser {
  id: number;
  name: string;
  email: string;
  role: UserRole;
  unit_id: number | null;
  is_active: boolean;
}
