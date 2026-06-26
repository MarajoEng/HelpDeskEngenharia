import type { PaginatedResponse } from "./pagination";
import type { TicketCategory, TicketPriority } from "./ticket";

export type TicketConfigurationSort =
  | "display_order_asc"
  | "created_at_desc"
  | "name_asc";

export interface TicketConfigurationFilters {
  page?: number;
  page_size?: number;
  search?: string;
  is_active?: boolean | "";
  sort?: TicketConfigurationSort;
}

export interface TicketSubcategoryFilters extends TicketConfigurationFilters {
  category_id?: number | "";
}

export interface TicketCustomFieldFilters extends TicketConfigurationFilters {
  category_id?: number | "";
  subcategory_id?: number | "";
}

export type TicketCustomFieldType = "text" | "textarea" | "number" | "boolean" | "select" | "date";

export interface TicketCustomFieldOption {
  label: string;
  value: string;
  display_order: number;
  is_active: boolean;
}

export interface TicketCategoryItem {
  id: number;
  name: string;
  legacy_value?: TicketCategory | string | null;
  description: string | null;
  is_active: boolean;
  display_order: number;
  requires_attachment: boolean;
  requires_location: boolean;
  type_ids: number[];
  created_at: string;
  updated_at: string;
}

export interface TicketSubcategoryItem {
  id: number;
  category_id: number;
  category_name: string;
  name: string;
  description: string | null;
  is_active: boolean;
  display_order: number;
  created_at: string;
  updated_at: string;
}

export interface TicketTypeItem {
  id: number;
  name: string;
  description: string | null;
  is_active: boolean;
  display_order: number;
  created_at: string;
  updated_at: string;
}

export interface TicketPriorityItem {
  id: number;
  name: string;
  legacy_value?: TicketPriority | string | null;
  description: string | null;
  color: string;
  weight: number;
  sla_hours: number;
  requires_reason: boolean;
  is_active: boolean;
  display_order: number;
  created_at: string;
  updated_at: string;
}

export interface TicketCustomFieldItem {
  id: number;
  category_id: number;
  category_name: string;
  subcategory_id: number | null;
  subcategory_name: string | null;
  name: string;
  label: string;
  description: string | null;
  field_type: TicketCustomFieldType;
  is_required: boolean;
  is_active: boolean;
  display_order: number;
  placeholder: string | null;
  help_text: string | null;
  validation_json: Record<string, unknown> | null;
  options: TicketCustomFieldOption[];
  created_at: string;
  updated_at: string;
}

export interface TicketCategoryPayload {
  name: string;
  description: string | null;
  is_active: boolean;
  display_order: number;
  requires_attachment: boolean;
  requires_location: boolean;
  type_ids: number[];
}

export interface TicketSubcategoryPayload {
  category_id: number;
  name: string;
  description: string | null;
  is_active: boolean;
  display_order: number;
}

export interface TicketTypePayload {
  name: string;
  description: string | null;
  is_active: boolean;
  display_order: number;
}

export interface TicketPriorityPayload {
  name: string;
  description: string | null;
  color: string;
  weight: number;
  sla_hours: number;
  requires_reason: boolean;
  is_active: boolean;
  display_order: number;
}

export interface TicketCustomFieldPayload {
  category_id: number;
  subcategory_id?: number | null;
  name: string;
  label: string;
  description: string | null;
  field_type: TicketCustomFieldType;
  is_required: boolean;
  is_active: boolean;
  display_order: number;
  placeholder: string | null;
  help_text: string | null;
  validation_json?: Record<string, unknown> | null;
  options: TicketCustomFieldOption[];
}

export interface TicketFormSchemaResponse {
  category_id: number;
  subcategory_id: number | null;
  fields: TicketCustomFieldItem[];
}

export type TicketCategoryListResponse = PaginatedResponse<TicketCategoryItem>;
export type TicketSubcategoryListResponse = PaginatedResponse<TicketSubcategoryItem>;
export type TicketTypeListResponse = PaginatedResponse<TicketTypeItem>;
export type TicketPriorityListResponse = PaginatedResponse<TicketPriorityItem>;
export type TicketCustomFieldListResponse = PaginatedResponse<TicketCustomFieldItem>;
