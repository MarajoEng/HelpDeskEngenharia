import type { PaginatedResponse } from "./pagination";

export interface Supplier {
  id: number;
  name: string;
  document: string;
  phone: string;
  email: string;
  specialty: string;
  is_active: boolean;
  created_at: string;
}

export interface SupplierCreatePayload {
  name: string;
  document: string;
  phone: string;
  email: string;
  specialty: string;
  is_active: boolean;
}

export interface SupplierUpdatePayload {
  name?: string;
  document?: string;
  phone?: string;
  email?: string;
  specialty?: string;
  is_active?: boolean;
}

export interface SupplierFilters {
  page?: number;
  page_size?: number;
  search?: string;
  is_active?: boolean | "";
  sort?: "name_asc" | "created_at_desc";
}

export type SupplierListResponse = PaginatedResponse<Supplier>;
