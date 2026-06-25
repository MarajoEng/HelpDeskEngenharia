import type { PaginatedResponse } from "./pagination";
import type { UserRole } from "./auth";

export interface UserItem {
  id: number;
  name: string;
  email: string;
  role: UserRole;
  unit_id: number | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface UserPayload {
  name: string;
  email: string;
  role: UserRole;
  unit_id: number | null;
  is_active: boolean;
  password?: string;
}

export interface UserFilters {
  page?: number;
  page_size?: number;
  search?: string;
  role?: UserRole | "";
  unit_id?: number | "";
  is_active?: boolean | "";
  sort?: "name_asc" | "created_at_desc";
}

export type UserListResponse = PaginatedResponse<UserItem>;
