import type { TicketStatus } from "../../types/ticket";

import Badge from "./Badge";
import { STATUS_LABELS, ticketStatusTone } from "./statusOptions";

interface StatusBadgeProps {
  status: TicketStatus;
}

export default function StatusBadge({ status }: StatusBadgeProps) {
  return <Badge tone={ticketStatusTone(status)}>{STATUS_LABELS[status] ?? status}</Badge>;
}
