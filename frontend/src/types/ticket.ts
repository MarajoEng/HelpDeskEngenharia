import type { UserRole } from "./auth";
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

export type SlaStatus = "on_track" | "late" | "no_sla" | "closed";
export type ApprovalStatus = "pending" | "approved" | "rejected" | "canceled";

export interface TicketUnitSummary {
  id: number;
  code: string;
  name: string;
  city: string;
  state: string;
}

export interface TicketUserSummary {
  id: number;
  name: string;
}

export interface TicketSupplierSummary {
  id: number;
  name: string;
  document: string;
  phone: string;
  email: string;
  specialty: string;
  is_active: boolean;
}

export interface TicketHistory {
  id: number;
  user_id: number;
  user_name: string | null;
  old_status: TicketStatus | null;
  new_status: TicketStatus;
  comment: string | null;
  created_at: string;
}

export interface TicketIndicators {
  estimated_loss_total: string | null;
  elapsed_hours: number | null;
  is_late: boolean;
  sla_status: SlaStatus;
  elapsed_execution_hours: number | null;
  execution_is_late: boolean;
}

export interface TicketApproval {
  id: number;
  ticket_id: number;
  requested_by_user_id: number;
  requested_by_user_name: string | null;
  approved_by_user_id: number | null;
  approved_by_user_name: string | null;
  approval_level_id: number | null;
  approval_level_name: string | null;
  approval_allowed_roles: UserRole[];
  status: ApprovalStatus;
  amount_requested: string;
  amount_approved: string | null;
  justification: string;
  approved_at: string | null;
  created_at: string;
}

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
  expected_resolution_at: string | null;
  supplier_id: number | null;
  created_at: string;
  updated_at: string;
  unit_name?: string | null;
  unit_code?: string | null;
  opened_by_user_name?: string | null;
  assigned_to_user_name?: string | null;
  supplier_name?: string | null;
}

export interface TicketDetail {
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
  expected_resolution_at: string | null;
  supplier_id: number | null;
  created_at: string;
  updated_at: string;
  unit: TicketUnitSummary | null;
  opened_by: TicketUserSummary | null;
  assigned_to: TicketUserSummary | null;
  supplier: TicketSupplierSummary | null;
  history: TicketHistory[];
  approvals: TicketApproval[];
  indicators: TicketIndicators;
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

export interface TicketTriagePayload {
  assigned_to_user_id?: number | null;
  priority?: TicketPriority;
  severity?: TicketSeverity;
  requires_approval?: boolean;
  sla_due_at?: string | null;
  technical_comment: string;
}

export interface TicketApprovalRequestPayload {
  amount_requested: string;
  justification: string;
}

export interface TicketApprovalDecisionPayload {
  decision: "approved" | "rejected";
  amount_approved?: string | null;
  justification: string;
}

export interface TicketStartExecutionPayload {
  assigned_to_user_id?: number | null;
  supplier_id?: number | null;
  expected_resolution_at?: string | null;
  execution_comment: string;
}

export interface TicketProgressUpdatePayload {
  progress_comment: string;
  expected_resolution_at?: string | null;
  estimated_cost?: string | null;
  supplier_id?: number | null;
  assigned_to_user_id?: number | null;
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
  only_late?: boolean | "";
  has_fuel_nozzles_stopped?: boolean | "";
  min_estimated_cost?: string | "";
  max_estimated_cost?: string | "";
  queue?: "engineering" | "";
}

export type TicketListResponse = PaginatedResponse<Ticket>;
