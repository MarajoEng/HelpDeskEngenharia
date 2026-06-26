import type { TicketStatus } from "../../types/ticket";

import Badge from "./Badge";
import { STATUS_LABELS, ticketStatusTone } from "./statusOptions";

interface StatusBadgeProps {
  status: TicketStatus;
  label?: string | null;
  color?: string | null;
}

export default function StatusBadge({ status, label, color }: StatusBadgeProps) {
  if (color) {
    return (
      <Badge
        tone="neutral"
        style={{
          backgroundColor: `${color}1a`,
          color,
          border: `1px solid ${color}33`,
        }}
      >
        {label || STATUS_LABELS[status] || status}
      </Badge>
    );
  }

  return <Badge tone={ticketStatusTone(status)}>{STATUS_LABELS[status] ?? status}</Badge>;
}
