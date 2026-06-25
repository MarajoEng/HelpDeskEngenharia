export type AlertType = "sla_late" | "sla_due_soon" | "execution_late";
export type AlertSeverity = "info" | "warning" | "critical";

export interface TicketAlert {
  id: number;
  ticket_id: number;
  ticket_number: string;
  unit_code: string;
  unit_name: string;
  alert_type: AlertType;
  severity: AlertSeverity;
  message: string;
  is_read: boolean;
  created_at: string;
  read_at: string | null;
}

export interface AlertFilters {
  page?: number;
  page_size?: number;
  is_read?: boolean;
  alert_type?: AlertType;
  severity?: AlertSeverity;
  ticket_id?: number;
  unit_id?: number;
}

export interface AlertListResponse {
  items: TicketAlert[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface RunSlaMonitorResponse {
  checked_tickets: number;
  created_alerts: number;
  skipped_duplicates: number;
}
