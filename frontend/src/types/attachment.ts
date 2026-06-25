import type { PaginatedResponse } from "./pagination";

export type TicketAttachmentType = "opening_evidence" | "progress_evidence" | "closing_evidence";

export interface TicketAttachment {
  id: number;
  ticket_id: number;
  uploaded_by_user_id: number;
  uploaded_by_user_name: string | null;
  file_url: string;
  file_type: string;
  attachment_type: TicketAttachmentType | string;
  created_at: string;
}

export type TicketAttachmentListResponse = PaginatedResponse<TicketAttachment>;
