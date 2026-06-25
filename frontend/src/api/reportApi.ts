import { ApiError, apiBaseUrl, requestJson } from "./http";
import type {
  CostReportItem,
  PaginatedReportResponse,
  ReportFilters,
  SlaReportItem,
  SupplierReportItem,
  TicketReportItem,
  UnitReportItem,
} from "../types/report";

function authHeaders(token: string) {
  return { Authorization: `Bearer ${token}` };
}

function buildQuery(path: string, filters: ReportFilters) {
  const params = new URLSearchParams();

  Object.entries(filters).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") {
      return;
    }
    params.set(key, String(value));
  });

  const query = params.toString();
  return query ? `${path}?${query}` : path;
}

async function downloadCsv(token: string, path: string) {
  const response = await fetch(new URL(path, apiBaseUrl).toString(), {
    headers: authHeaders(token),
  });

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;
    const contentType = response.headers.get("content-type") || "";

    if (contentType.includes("application/json")) {
      const data = (await response.json()) as { detail?: string };
      if (data.detail) {
        detail = data.detail;
      }
    }

    throw new ApiError(response.status, detail);
  }

  return {
    blob: await response.blob(),
    contentType: response.headers.get("content-type") || "text/csv",
  };
}

export function listTicketReport(token: string, filters: ReportFilters) {
  return requestJson<PaginatedReportResponse<TicketReportItem>>(buildQuery("/reports/tickets", filters), {
    headers: authHeaders(token),
  });
}

export function listCostReport(token: string, filters: ReportFilters) {
  return requestJson<PaginatedReportResponse<CostReportItem>>(buildQuery("/reports/costs", filters), {
    headers: authHeaders(token),
  });
}

export function listSlaReport(token: string, filters: ReportFilters) {
  return requestJson<PaginatedReportResponse<SlaReportItem>>(buildQuery("/reports/sla", filters), {
    headers: authHeaders(token),
  });
}

export function listUnitReport(token: string, filters: ReportFilters) {
  return requestJson<PaginatedReportResponse<UnitReportItem>>(buildQuery("/reports/units", filters), {
    headers: authHeaders(token),
  });
}

export function listSupplierReport(token: string, filters: ReportFilters) {
  return requestJson<PaginatedReportResponse<SupplierReportItem>>(buildQuery("/reports/suppliers", filters), {
    headers: authHeaders(token),
  });
}

export function exportTicketReportCsv(token: string, filters: ReportFilters) {
  return downloadCsv(token, buildQuery("/reports/tickets/export.csv", filters));
}

export function exportCostReportCsv(token: string, filters: ReportFilters) {
  return downloadCsv(token, buildQuery("/reports/costs/export.csv", filters));
}

export function exportSlaReportCsv(token: string, filters: ReportFilters) {
  return downloadCsv(token, buildQuery("/reports/sla/export.csv", filters));
}

export function exportUnitReportCsv(token: string, filters: ReportFilters) {
  return downloadCsv(token, buildQuery("/reports/units/export.csv", filters));
}

export function exportSupplierReportCsv(token: string, filters: ReportFilters) {
  return downloadCsv(token, buildQuery("/reports/suppliers/export.csv", filters));
}
