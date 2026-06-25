import type { PaginatedResponse } from "./pagination";

export interface Unit {
  id: number;
  code: string;
  name: string;
  city: string;
  state: string;
  region: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface UnitPayload {
  code: string;
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
  sort?: "name_asc" | "created_at_desc";
}

export type UnitListResponse = PaginatedResponse<Unit>;
