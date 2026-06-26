import type { PaginatedResponse } from "./pagination";

export interface Unit {
  id: number;
  code: string;
  group_code: string | null;
  branch_code: string | null;
  name: string;
  city: string;
  state: string;
  region: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface UnitPayload {
  group_code: string;
  branch_code: string;
  name: string;
  city: string;
  state: string;
  region: string;
  is_active: boolean;
}

export interface UnitFilters {
  page?: number;
  page_size?: number;
  search?: string;
  is_active?: boolean | "";
  state?: string;
  region?: string;
  group_code?: string;
  branch_code?: string;
  sort?: "name_asc" | "created_at_desc";
}

export interface UnitGroupOption {
  group_code: string;
  total_units: number;
}

export type UnitListResponse = PaginatedResponse<Unit>;
