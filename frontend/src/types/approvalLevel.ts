import type { UserRole } from "./auth";
import type { PaginatedResponse } from "./pagination";

export interface ApprovalLevel {
  id: number;
  name: string;
  min_amount: string;
  max_amount: string | null;
  allowed_roles: UserRole[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ApprovalLevelPayload {
  name: string;
  min_amount: string;
  max_amount: string | null;
  allowed_roles: UserRole[];
  is_active: boolean;
}

export interface ApprovalLevelFilters {
  page?: number;
  page_size?: number;
  search?: string;
  is_active?: boolean | "";
  sort?: "name_asc" | "created_at_desc";
}

export type ApprovalLevelListResponse = PaginatedResponse<ApprovalLevel>;
