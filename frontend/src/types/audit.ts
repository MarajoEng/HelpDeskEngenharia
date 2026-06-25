export interface AuditLog {
  id: number;
  actor_user_id: number | null;
  actor_user_name: string | null;
  action: string;
  entity_type: string;
  entity_id: number | null;
  ip_address: string | null;
  user_agent: string | null;
  metadata_json: Record<string, unknown> | null;
  created_at: string;
}

export interface AuditLogFilters {
  page?: number;
  page_size?: number;
  actor_user_id?: number;
  action?: string;
  entity_type?: string;
  entity_id?: number;
  date_from?: string;
  date_to?: string;
  search?: string;
}

export interface AuditLogListResponse {
  items: AuditLog[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}
