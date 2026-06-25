import type { TicketPriority } from "../../types/ticket";

import Badge from "./Badge";
import { PRIORITY_LABELS, priorityTone } from "./statusOptions";

interface PriorityBadgeProps {
  priority: TicketPriority;
}

export default function PriorityBadge({ priority }: PriorityBadgeProps) {
  return <Badge tone={priorityTone(priority)}>{PRIORITY_LABELS[priority] ?? priority}</Badge>;
}
