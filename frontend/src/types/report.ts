import type { PaginatedResponse } from "./pagination";
import type { TicketCategory, TicketPriority, TicketSeverity, TicketStatus } from "./ticket";

export type ReportType = "tickets" | "costs" | "sla" | "units" | "suppliers";

export interface ReportFilters {
  page: number;
  page_size: number;
  date_from?: string;
  date_to?: string;
  unit_id?: number | "";
  group_code?: string;
  branch_code?: string;
  region?: string;
  status?: TicketStatus | "";
  category?: TicketCategory | "";
  category_id?: number | "";
  subcategory_id?: number | "";
  type_id?: number | "";
  priority?: TicketPriority | "";
  priority_id?: number | "";
  severity?: TicketSeverity | "";
  supplier_id?: number | "";
  only_late?: boolean | "";
  requires_approval?: boolean | "";
}

export type PaginatedReportResponse<T> = PaginatedResponse<T>;

export interface TicketReportItem {
  id: number;
  ticket_number: string;
  unit_id: number;
  unit_code: string;
  unit_name: string;
  status: TicketStatus;
  category_id?: number | null;
  subcategory_id?: number | null;
  type_id?: number | null;
  category: TicketCategory;
  category_name: string;
  subcategory_name?: string | null;
  type_name?: string | null;
  priority_id?: number | null;
  priority: TicketPriority;
  priority_name: string;
  priority_color?: string | null;
  priority_weight?: number | null;
  severity: TicketSeverity;
  opened_by_user_name: string | null;
  assigned_to_user_name: string | null;
  supplier_name: string | null;
  opened_at: string;
  resolved_at: string | null;
  closed_at: string | null;
  sla_due_at: string | null;
  is_late: boolean;
  estimated_cost: string | null;
  approved_cost: string | null;
  final_cost: string | null;
  fuel_nozzles_stopped: number | null;
  requires_approval: boolean;
}

export interface CostReportItem {
  unit_id: number;
  unit_code: string;
  unit_name: string;
  category_id?: number | null;
  category: TicketCategory;
  category_name: string;
  supplier_id: number | null;
  supplier_name: string | null;
  estimated_cost_total: string;
  approved_cost_total: string;
  final_cost_total: string;
  total_tickets: number;
  average_ticket_cost: number;
}

export interface SlaReportItem {
  unit_id: number;
  unit_code: string;
  unit_name: string;
  total_with_sla: number;
  on_track: number;
  late: number;
  closed_on_time: number;
  closed_late: number;
  compliance_rate: number | null;
  average_resolution_hours: number | null;
  average_closure_hours: number | null;
}

export interface UnitReportItem {
  unit_id: number;
  unit_code: string;
  unit_name: string;
  region: string;
  total_tickets: number;
  critical_tickets: number;
  late_tickets: number;
  in_progress_tickets: number;
  closed_tickets: number;
  final_cost_total: string;
  total_fuel_nozzles_stopped: number;
  estimated_daily_loss_total: string;
}

export interface SupplierReportItem {
  supplier_id: number;
  supplier_name: string;
  total_tickets: number;
  in_progress_tickets: number;
  resolved_tickets: number;
  closed_tickets: number;
  final_cost_total: string;
  average_execution_hours: number | null;
  late_execution_tickets: number;
}
