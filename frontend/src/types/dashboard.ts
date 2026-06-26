import type { TicketCategory, TicketPriority, TicketSeverity, TicketStatus } from "./ticket";

export interface DashboardFilters {
  date_from?: string;
  date_to?: string;
  unit_id?: number | "";
  group_code?: string;
  region?: string;
  status?: TicketStatus | "";
  category?: TicketCategory | "";
  category_id?: number | "";
  priority_id?: number | "";
}

export interface ExecutiveCards {
  total_open: number;
  total_late: number;
  total_critical: number;
  total_in_progress: number;
  total_fuel_nozzles_stopped: number;
  estimated_daily_loss_total: number;
  final_cost_total: number;
  sla_compliance_rate: number;
}

export interface RankingItem {
  unit_id: number;
  unit_code: string;
  unit_name: string;
  total_tickets?: number;
  late_tickets?: number;
  critical_tickets?: number;
  estimated_cost_total?: number;
  final_cost_total?: number;
  total_fuel_nozzles_stopped?: number;
  estimated_daily_loss_total?: number;
}

export interface DistributionItem {
  total: number;
  status?: TicketStatus;
  category?: TicketCategory;
  category_id?: number | null;
  category_name?: string | null;
  priority?: TicketPriority;
  priority_id?: number | null;
  priority_name?: string | null;
  priority_color?: string | null;
  priority_weight?: number | null;
  severity?: TicketSeverity;
}

export interface SlaSummary {
  total_with_sla: number;
  on_track: number;
  late: number;
  closed_on_time: number;
  closed_late: number;
  compliance_rate: number;
}

export interface LateTicketPreview {
  id: number;
  ticket_number: string;
  unit_code: string;
  unit_name: string;
  title: string;
  status: TicketStatus;
  priority: TicketPriority;
  priority_id?: number | null;
  priority_name?: string | null;
  priority_color?: string | null;
  priority_weight?: number | null;
  severity: TicketSeverity;
  sla_due_at: string;
  opened_at: string;
}

export interface DashboardOverview {
  total_tickets: number;
  open_tickets: number;
  triage_tickets: number;
  waiting_approval_tickets: number;
  approved_tickets: number;
  in_progress_tickets: number;
  resolved_tickets: number;
  closed_tickets: number;
  canceled_tickets: number;
  late_tickets: number;
  critical_tickets: number;
  tickets_with_fuel_nozzles_stopped: number;
  total_fuel_nozzles_stopped: number;
  estimated_daily_loss_total: number;
  estimated_cost_total: number;
  approved_cost_total: number;
  final_cost_total: number;
  average_resolution_hours: number;
  average_closure_hours: number;
  sla_compliance_rate: number;
  executive_cards: ExecutiveCards;
  ranking_units_by_tickets: RankingItem[];
  ranking_units_by_cost: RankingItem[];
  ranking_units_by_fuel_nozzles: RankingItem[];
  tickets_by_status: DistributionItem[];
  tickets_by_category: DistributionItem[];
  tickets_by_priority: DistributionItem[];
  tickets_by_severity: DistributionItem[];
  sla_summary: SlaSummary;
  late_tickets_preview: LateTicketPreview[];
}
