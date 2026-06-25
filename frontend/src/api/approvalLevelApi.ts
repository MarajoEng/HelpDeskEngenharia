import { requestJson } from "./http";
import type {
  ApprovalLevel,
  ApprovalLevelFilters,
  ApprovalLevelListResponse,
  ApprovalLevelPayload,
} from "../types/approvalLevel";

function authHeaders(token: string) {
  return { Authorization: `Bearer ${token}` };
}

function buildQuery(filters: ApprovalLevelFilters) {
  const params = new URLSearchParams();

  Object.entries(filters).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") {
      return;
    }
    params.set(key, String(value));
  });

  const query = params.toString();
  return query ? `/approval-levels?${query}` : "/approval-levels";
}

export function listApprovalLevels(token: string, filters: ApprovalLevelFilters) {
  return requestJson<ApprovalLevelListResponse>(buildQuery(filters), {
    headers: authHeaders(token),
  });
}

export function createApprovalLevel(token: string, payload: ApprovalLevelPayload) {
  return requestJson<ApprovalLevel>("/approval-levels", {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  });
}

export function updateApprovalLevel(
  token: string,
  approvalLevelId: number,
  payload: Partial<ApprovalLevelPayload>,
) {
  return requestJson<ApprovalLevel>(`/approval-levels/${approvalLevelId}`, {
    method: "PATCH",
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  });
}
