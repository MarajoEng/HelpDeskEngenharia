import type { PaginatedResponse } from "./pagination";

export type TicketCategory =
  | "fuel_pump"
  | "fuel_nozzle"
  | "electrical"
  | "plumbing"
  | "leak"
  | "structure"
  | "roof"
  | "pavement"
  | "environmental_risk"
  | "other";

export type TicketPriority = "low" | "medium" | "high" | "critical";

export type TicketSeverity = "low" | "medium" | "high" | "critical";

export type TicketStatus =
  | "open"
  | "triage"
  | "waiting_approval"
  | "approved"
  | "rejected"
  | "in_progress"
  | "waiting_supplier"
  | "waiting_unit"
  | "resolved"
  | "closed"
  | "canceled";

export interface Ticket {
  id: number;
  ticket_number: string;
  unit_id: number;
  opened_by_user_id: number;
  assigned_to_user_id: number | null;
  category: TicketCategory;
  problem_type: string;
  title: string;
  description: string;
  priority: TicketPriority;
  severity: TicketSeverity;
  status: TicketStatus;
  operational_impact: string | null;
  fuel_nozzles_stopped: number | null;
  estimated_daily_loss: string | null;
  estimated_loss_total: string | null;
  estimated_cost: string | null;
  approved_cost: string | null;
  final_cost: string | null;
  requires_approval: boolean;
  opened_at: string;
  triaged_at: string | null;
  approved_at: string | null;
  started_at: string | null;
  resolved_at: string | null;
  closed_at: string | null;
  sla_due_at: string | null;
  created_at: string;
  updated_at: string;
  unit_name?: string | null;
  unit_code?: string | null;
  opened_by_user_name?: string | null;
}

export interface TicketCreatePayload {
  unit_id: number;
  category: TicketCategory;
  problem_type: string;
  title: string;
  description: string;
  priority: TicketPriority;
  severity: TicketSeverity;
  operational_impact?: string | null;
  fuel_nozzles_stopped?: number | null;
  estimated_daily_loss?: string | null;
  estimated_cost?: string | null;
  requires_approval: boolean;
}

export interface TicketFilters {
  page?: number;
  page_size?: number;
  unit_id?: number | "";
  status?: TicketStatus | "";
  category?: TicketCategory | "";
  priority?: TicketPriority | "";
  severity?: TicketSeverity | "";
  requires_approval?: boolean | "";
  opened_from?: string;
  opened_to?: string;
  search?: string;
}

export type TicketListResponse = PaginatedResponse<Ticket>;
