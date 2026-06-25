import type { TicketSeverity } from "../../types/ticket";

import Badge from "./Badge";
import { SEVERITY_LABELS, severityTone } from "./statusOptions";

interface SeverityBadgeProps {
  severity: TicketSeverity;
}

export default function SeverityBadge({ severity }: SeverityBadgeProps) {
  return <Badge tone={severityTone(severity)}>{SEVERITY_LABELS[severity] ?? severity}</Badge>;
}
