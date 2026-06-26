import { useEffect, useMemo, useState } from "react";

import ErrorBoundary from "../components/ui/ErrorBoundary";
import { ApiError } from "../api/http";
import { listTicketCategories, listTicketPriorities } from "../api/ticketConfigurationApi";
import {
  exportCostReportCsv,
  exportSlaReportCsv,
  exportSupplierReportCsv,
  exportTicketReportCsv,
  exportUnitReportCsv,
  listCostReport,
  listSlaReport,
  listSupplierReport,
  listTicketReport,
  listUnitReport,
} from "../api/reportApi";
import { getUnitById, listUnits } from "../api/unitApi";
import { listSuppliers } from "../api/supplierApi";
import Badge from "../components/ui/Badge";
import EmptyState from "../components/ui/EmptyState";
import ErrorState from "../components/ui/ErrorState";
import LoadingState from "../components/ui/LoadingState";
import StatCard from "../components/ui/StatCard";
import StatusBadge from "../components/ui/StatusBadge";
import { getDashboardOverview } from "../api/dashboardApi";
import type { DashboardOverview } from "../types/dashboard";
import {
  CATEGORY_LABELS,
  PRIORITY_LABELS,
  STATUS_LABELS,
} from "../components/ui/statusOptions";
import Table from "../components/ui/Table";
import { useAuth } from "../hooks/useAuth";
import type { Supplier } from "../types/supplier";
import type { TicketPriority, TicketSeverity, TicketStatus } from "../types/ticket";
import type { TicketCategoryItem, TicketPriorityItem } from "../types/ticketConfiguration";
import type { Unit } from "../types/unit";
import type {
  PaginatedReportResponse,
  ReportFilters,
  ReportType,
  CostReportItem,
  SlaReportItem,
  SupplierReportItem,
  TicketReportItem,
  UnitReportItem,
} from "../types/report";
import { formatDate, formatMoney, formatPercentSafe, toNumberSafe } from "../utils/formatters";
import { getErrorMessage } from "../utils/messages";

// ----------------------------------------------------------------------
// Icons (Inline SVG)
// ----------------------------------------------------------------------

const ChartIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M18 20V10" />
    <path d="M12 20V4" />
    <path d="M6 20v-6" />
  </svg>
);

const DollarIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="12" y1="1" x2="12" y2="23" />
    <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
  </svg>
);

const BellIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
    <path d="M13.73 21a2 2 0 0 1-3.46 0" />
  </svg>
);

const BuildingIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M4 22v-4a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v4" />
    <rect x="4" y="2" width="16" height="20" rx="2" />
    <path d="M10 10h.01M14 10h.01M10 14h.01M14 14h.01" />
  </svg>
);

const CalendarIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
    <line x1="16" y1="2" x2="16" y2="6" />
    <line x1="8" y1="2" x2="8" y2="6" />
    <line x1="3" y1="10" x2="21" y2="10" />
  </svg>
);

const TagIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="m15 2-8 8V2Z" />
    <path d="m15 2 8 8-8 8-8-8" />
  </svg>
);

const FilterIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
  </svg>
);

const SearchIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="11" cy="11" r="8" />
    <line x1="21" y1="21" x2="16.65" y2="16.65" />
  </svg>
);

const RefreshIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
    <path d="M3 3v5h5" />
  </svg>
);

const DownloadIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
    <polyline points="7 10 12 15 17 10" />
    <line x1="12" y1="15" x2="12" y2="3" />
  </svg>
);

const InfoIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10" />
    <line x1="12" y1="16" x2="12" y2="12" />
    <line x1="12" y1="8" x2="12.01" y2="8" />
  </svg>
);

const DocumentIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <polyline points="14 2 14 8 20 8" />
    <line x1="16" y1="13" x2="8" y2="13" />
    <line x1="16" y1="17" x2="8" y2="17" />
    <polyline points="10 9 9 9 8 9" />
  </svg>
);

const ClockIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10" />
    <polyline points="12 6 12 12 16 14" />
  </svg>
);

const ShieldCheckIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
    <path d="m9 12 2 2 4-4" />
  </svg>
);

const BigDollarIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="12" y1="1" x2="12" y2="23" />
    <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
  </svg>
);

// ----------------------------------------------------------------------
// Types & Constants
// ----------------------------------------------------------------------

const initialFilters: ReportFilters = {
  page: 1,
  page_size: 20,
  date_from: "",
  date_to: "",
  unit_id: "",
  region: "",
  status: "",
  category: "",
  category_id: "",
  priority: "",
  priority_id: "",
  severity: "",
  supplier_id: "",
  only_late: "",
  requires_approval: "",
};

const reportTabs = [
  { key: "tickets", label: "Chamados", icon: DocumentIcon, filename: "chamados.csv" },
  { key: "costs", label: "Custos", icon: DollarIcon, filename: "custos.csv" },
  { key: "sla", label: "SLA", icon: BellIcon, filename: "sla.csv" },
  { key: "units", label: "Unidades", icon: BuildingIcon, filename: "unidades.csv" },
  { key: "suppliers", label: "Fornecedores", icon: TagIcon, filename: "fornecedores.csv" },
] as const;

const STATUS_CHART = [
  { key: "aberto", label: "Aberto", color: "#3b82f6" },
  { key: "em_execucao", label: "Em execução", color: "#22c55e" },
  { key: "triagem", label: "Triagem", color: "#eab308" },
  { key: "aguardando", label: "Aguardando", color: "#ef4444" },
  { key: "concluido", label: "Concluído", color: "#9ca3af" },
] as const;

const PRIORITY_CHART = [
  { key: "critica", label: "Crítica", color: "#ef4444" },
  { key: "alta", label: "Alta", color: "#f97316" },
  { key: "media", label: "Média", color: "#22c55e" },
  { key: "baixa", label: "Baixa", color: "#3b82f6" },
] as const;

function formatPercentDisplay(value: number | null | undefined, decimals = 1) {
  return formatPercentSafe(value, decimals).replace(".", ",");
}

function getVisiblePages(page: number, totalPages: number) {
  if (totalPages <= 0) {
    return [];
  }

  const start = Math.max(1, Math.min(page - 1, totalPages - 2));
  const end = Math.min(totalPages, start + 2);
  const pages: number[] = [];

  for (let current = start; current <= end; current += 1) {
    pages.push(current);
  }

  return pages;
}

export default function ReportsPage() {
  const { token, user, logout } = useAuth();
  const [reportType, setReportType] = useState<ReportType>("tickets");
  const [filters, setFilters] = useState<ReportFilters>(initialFilters);
  const [draftFilters, setDraftFilters] = useState<ReportFilters>(initialFilters);
  const [units, setUnits] = useState<Unit[]>([]);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [configuredCategories, setConfiguredCategories] = useState<TicketCategoryItem[]>([]);
  const [configuredPriorities, setConfiguredPriorities] = useState<TicketPriorityItem[]>([]);
  const [data, setData] = useState<PaginatedReportResponse<unknown> | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isExporting, setIsExporting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [exportMessage, setExportMessage] = useState<string | null>(null);
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);

  const [dashboardData, setDashboardData] = useState<DashboardOverview | null>(null);

  const canAccessReports = user ? user.role !== "supplier" : true;

  const stats = useMemo(() => {
    if (!dashboardData) return null;

    const statuses: Record<string, number> = { "aberto": 0, "em_execucao": 0, "triagem": 0, "aguardando": 0, "concluido": 0 };
    const priorities: Record<string, number> = { "critica": 0, "alta": 0, "media": 0, "baixa": 0 };

    dashboardData.tickets_by_status.forEach((item) => {
      if (!item.status) {
        return;
      }

      const status = item.status as TicketStatus;
      if (status === "open") {
        statuses.aberto += item.total;
      } else if (status === "in_progress") {
        statuses.em_execucao += item.total;
      } else if (status === "triage") {
        statuses.triagem += item.total;
      } else if (status === "resolved" || status === "closed" || status === "canceled") {
        statuses.concluido += item.total;
      } else if (status.startsWith("waiting_") || status === "approved" || status === "rejected") {
        statuses.aguardando += item.total;
      }
    });

    dashboardData.tickets_by_priority.forEach((item) => {
      if (!item.priority) {
        return;
      }

      const priority = item.priority as TicketPriority;
      if (priority === "critical") {
        priorities.critica += item.total;
      } else if (priority === "high") {
        priorities.alta += item.total;
      } else if (priority === "medium") {
        priorities.media += item.total;
      } else if (priority === "low") {
        priorities.baixa += item.total;
      }
    });

    const count = dashboardData.total_tickets;

    return {
      total: dashboardData.total_tickets,
      atrasados: dashboardData.late_tickets,
      custoFinal: dashboardData.final_cost_total,
      slaNoPrazo: dashboardData.sla_compliance_rate,
      statuses,
      priorities,
      count,
    };
  }, [dashboardData]);

  const activeTab = useMemo(() => reportTabs.find((item) => item.key === reportType) ?? reportTabs[0], [reportType]);
  const configuredCategoryOptions = useMemo(
    () =>
      configuredCategories
        .map((category) => ({
          value: category.id,
          label: category.name,
        })),
    [configuredCategories],
  );
  const configuredPriorityOptions = useMemo(
    () =>
      configuredPriorities.map((priority) => ({
        value: priority.id,
        label: priority.name,
      })),
    [configuredPriorities],
  );
  const visiblePages = useMemo(() => {
    if (!data) {
      return [];
    }

    return getVisiblePages(data.page, data.pages);
  }, [data]);

  useEffect(() => {
    if (!token || !user || user.role === "supplier") return;
    const currentToken = token;
    const currentUser = user;
    let isActive = true;

    async function loadOptions() {
      try {
        if (currentUser.role === "manager" && currentUser.unit_id) {
          const unit = await getUnitById(currentToken, currentUser.unit_id);
          if (!isActive) return;
          setUnits([unit]);
          setDraftFilters((current) => ({ ...current, unit_id: unit.id }));
          setFilters((current) => ({ ...current, unit_id: unit.id }));
        } else {
          const response = await listUnits(currentToken, { page: 1, page_size: 100 });
          if (!isActive) return;
          setUnits(response.items);
        }
      } catch {
        if (!isActive) return;
        setUnits([]);
      }

      try {
        const response = await listSuppliers(currentToken, { page: 1, page_size: 100 });
        if (!isActive) return;
        setSuppliers(response.items);
      } catch {
        if (!isActive) return;
        setSuppliers([]);
      }
    }

    void loadOptions();

    return () => {
      isActive = false;
    };
  }, [token, user]);

  useEffect(() => {
    if (!token || !user || user.role === "supplier") return;

    let isActive = true;
    Promise.all([
      listTicketCategories({ page: 1, page_size: 100, sort: "display_order_asc" }),
      listTicketPriorities({ page: 1, page_size: 100, sort: "display_order_asc" }),
    ])
      .then(([categoriesResponse, prioritiesResponse]) => {
        if (!isActive) return;
        setConfiguredCategories(categoriesResponse.items);
        setConfiguredPriorities(prioritiesResponse.items);
      })
      .catch(() => {
        if (!isActive) return;
        setConfiguredCategories([]);
        setConfiguredPriorities([]);
      });

    return () => {
      isActive = false;
    };
  }, [token, user]);

  useEffect(() => {
    if (!token || !canAccessReports) {
      setIsLoading(false);
      return;
    }

    let isActive = true;
    setIsLoading(true);
    setErrorMessage(null);

    const request =
      reportType === "tickets"
        ? listTicketReport(token, filters)
        : reportType === "costs"
          ? listCostReport(token, filters)
          : reportType === "sla"
            ? listSlaReport(token, filters)
            : reportType === "units"
              ? listUnitReport(token, filters)
              : listSupplierReport(token, filters);

    request
      .then((response) => {
        if (!isActive) return;
        setData(response as PaginatedReportResponse<unknown>);
      })
      .catch((error: unknown) => {
        if (!isActive) return;
        if (error instanceof ApiError && error.status === 401) {
          setErrorMessage("Sessão expirada. Faça login novamente.");
          logout();
        } else if (error instanceof ApiError && error.status === 422) {
          setErrorMessage("Filtros inválidos. Verifique os parâmetros selecionados.");
        } else {
          setErrorMessage(getErrorMessage(error, "Não foi possível carregar o relatório."));
        }
      })
      .finally(() => {
        if (isActive) {
          setIsLoading(false);
        }
      });

    return () => {
      isActive = false;
    };
  }, [canAccessReports, filters, reportType, token, logout]);

  useEffect(() => {
    if (!token || !canAccessReports) {
      return;
    }

    let isActive = true;

    getDashboardOverview(token, filters)
      .then((res) => {
        if (isActive) setDashboardData(res);
      })
      .catch(() => {
        if (isActive) setDashboardData(null);
      });

    return () => {
      isActive = false;
    };
  }, [canAccessReports, filters, token]);

  function changeTab(nextType: ReportType) {
    setReportType(nextType);
    setExportMessage(null);
    setFilters((current) => ({ ...current, page: 1 }));
    setDraftFilters((current) => ({ ...current, page: 1 }));
  }

  function setDraft<K extends keyof ReportFilters>(key: K, value: ReportFilters[K]) {
    setDraftFilters((current) => ({ ...current, page: 1, [key]: value }));
  }

  function applyFilters() {
    setFilters({ ...draftFilters, page: 1 });
  }

  function clearFilters() {
    setDraftFilters(initialFilters);
    setFilters(initialFilters);
  }

  async function handleExport() {
    if (!token) return;

    setIsExporting(true);
    setExportMessage(null);
    setErrorMessage(null);

    try {
      const response =
        reportType === "tickets"
          ? await exportTicketReportCsv(token, filters)
          : reportType === "costs"
            ? await exportCostReportCsv(token, filters)
            : reportType === "sla"
              ? await exportSlaReportCsv(token, filters)
              : reportType === "units"
                ? await exportUnitReportCsv(token, filters)
                : await exportSupplierReportCsv(token, filters);

      const blobUrl = URL.createObjectURL(response.blob);
      const anchor = document.createElement("a");
      anchor.href = blobUrl;
      anchor.download = activeTab.filename;
      anchor.click();
      URL.revokeObjectURL(blobUrl);
      setExportMessage(`Exportação concluída para ${activeTab.label.toLowerCase()}.`);
    } catch (error: unknown) {
      const errorStatus = error instanceof ApiError ? error.status : 500;
      if (errorStatus === 401) {
        setErrorMessage("Sessão expirada. Faça login novamente.");
        logout();
      } else {
        setErrorMessage(getErrorMessage(error, "Não foi possível exportar o CSV."));
      }
    } finally {
      setIsExporting(false);
    }
  }

  function renderReportTable() {
    if (!data) return null;

    if (reportType === "tickets") {
      const items = data.items as TicketReportItem[];
      return (
        <Table className="w-full text-sm" minWidth={1420}>
          <thead>
            <tr className="border-b border-slate-200">
              <th className="py-3 px-4 font-semibold text-slate-900 text-left whitespace-nowrap">Chamado</th>
              <th className="py-3 px-4 font-semibold text-slate-900 text-left whitespace-nowrap">Unidade</th>
              <th className="py-3 px-4 font-semibold text-slate-900 text-left whitespace-nowrap">Status</th>
              <th className="py-3 px-4 font-semibold text-slate-900 text-left whitespace-nowrap">Prioridade</th>
              <th className="py-3 px-4 font-semibold text-slate-900 text-left whitespace-nowrap">Responsável</th>
              <th className="py-3 px-4 font-semibold text-slate-900 text-left whitespace-nowrap">Abertura</th>
              <th className="py-3 px-4 font-semibold text-slate-900 text-left whitespace-nowrap">SLA</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={`ticket-${item.id}`} className="border-b border-slate-100 hover:bg-slate-50 transition-colors">
                <td className="py-3 px-4 text-slate-600 font-mono text-[13px]">{item.ticket_number}</td>
                <td className="py-3 px-4 text-slate-600">{item.unit_name}</td>
                <td className="py-3 px-4">
                  <StatusBadge status={item.status} />
                </td>
                <td className="py-3 px-4">
                  <Badge tone="neutral">{item.priority_name ?? PRIORITY_LABELS[item.priority]}</Badge>
                </td>
                <td className="py-3 px-4 text-slate-600">{item.assigned_to_user_name ?? "Não atribuído"}</td>
                <td className="py-3 px-4 text-slate-600 text-[13px]">{formatDate(item.opened_at)}</td>
                <td className="py-3 px-4">
                  {item.sla_due_at ? (
                    <Badge tone={item.is_late ? "danger" : "success"}>
                      {item.is_late ? "Atrasado" : "No prazo"}
                    </Badge>
                  ) : (
                    <Badge tone="neutral">Sem SLA</Badge>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      );
    }

    if (reportType === "costs") {
      const items = data.items as CostReportItem[];
      return (
        <Table className="w-full text-sm" minWidth={1120}>
          <thead>
            <tr className="border-b border-slate-200">
              <th className="py-3 px-4 font-semibold text-slate-900 text-left whitespace-nowrap">Unidade</th>
              <th className="py-3 px-4 font-semibold text-slate-900 text-left whitespace-nowrap">Categoria</th>
              <th className="py-3 px-4 font-semibold text-slate-900 text-left whitespace-nowrap">Fornecedor</th>
              <th className="py-3 px-4 font-semibold text-slate-900 text-left whitespace-nowrap">Qtd.</th>
              <th className="py-3 px-4 font-semibold text-slate-900 text-left whitespace-nowrap">Estimado</th>
              <th className="py-3 px-4 font-semibold text-slate-900 text-left whitespace-nowrap">Aprovado</th>
              <th className="py-3 px-4 font-semibold text-slate-900 text-left whitespace-nowrap">Final</th>
              <th className="py-3 px-4 font-semibold text-slate-900 text-left whitespace-nowrap">Ticket médio</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={`cost-${item.unit_id}-${item.category_id ?? item.category}-${item.supplier_id ?? "none"}`} className="border-b border-slate-100 hover:bg-slate-50 transition-colors">
                <td className="py-3 px-4">
                  <strong className="block text-slate-900">{item.unit_code}</strong>
                  <div className="text-[13px] text-slate-500">{item.unit_name}</div>
                </td>
                <td className="py-3 px-4 text-slate-600">{item.category_name ?? CATEGORY_LABELS[item.category]}</td>
                <td className="py-3 px-4 text-slate-600">{item.supplier_name ?? "Sem fornecedor"}</td>
                <td className="py-3 px-4 text-slate-600">{item.total_tickets}</td>
                <td className="py-3 px-4 text-slate-600">{formatMoney(item.estimated_cost_total)}</td>
                <td className="py-3 px-4 text-slate-600">{formatMoney(item.approved_cost_total)}</td>
                <td className="py-3 px-4 text-slate-600">{formatMoney(item.final_cost_total)}</td>
                <td className="py-3 px-4 text-slate-600">{formatMoney(item.average_ticket_cost)}</td>
              </tr>
            ))}
          </tbody>
        </Table>
      );
    }

    if (reportType === "sla") {
      const items = data.items as SlaReportItem[];
      return (
        <Table className="w-full text-sm" minWidth={1080}>
          <thead>
            <tr className="border-b border-slate-200">
              <th className="py-3 px-4 font-semibold text-slate-900 text-left whitespace-nowrap">Unidade</th>
              <th className="py-3 px-4 font-semibold text-slate-900 text-left whitespace-nowrap">Total com SLA</th>
              <th className="py-3 px-4 font-semibold text-slate-900 text-left whitespace-nowrap">No prazo</th>
              <th className="py-3 px-4 font-semibold text-slate-900 text-left whitespace-nowrap">Atrasados</th>
              <th className="py-3 px-4 font-semibold text-slate-900 text-left whitespace-nowrap">Taxa</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => {
              const rate = toNumberSafe(item.compliance_rate);
              return (
                <tr key={`sla-${item.unit_id}`} className="border-b border-slate-100 hover:bg-slate-50 transition-colors">
                  <td className="py-3 px-4">
                    <strong className="block text-slate-900">{item.unit_code}</strong>
                    <div className="text-[13px] text-slate-500">{item.unit_name}</div>
                  </td>
                  <td className="py-3 px-4 text-slate-600">{item.total_with_sla}</td>
                  <td className="py-3 px-4 text-slate-600">{item.on_track}</td>
                  <td className="py-3 px-4 text-slate-600">{item.late}</td>
                  <td className="py-3 px-4">
                    <Badge tone={rate >= 80 ? "success" : rate >= 50 ? "warning" : "danger"}>
                      {formatPercentSafe(item.compliance_rate, 2)}
                    </Badge>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </Table>
      );
    }

    if (reportType === "units") {
      const items = data.items as UnitReportItem[];
      return (
        <Table className="w-full text-sm" minWidth={1120}>
          <thead>
            <tr className="border-b border-slate-200">
              <th className="py-3 px-4 font-semibold text-slate-900 text-left whitespace-nowrap">Unidade</th>
              <th className="py-3 px-4 font-semibold text-slate-900 text-left whitespace-nowrap">Região</th>
              <th className="py-3 px-4 font-semibold text-slate-900 text-left whitespace-nowrap">Total</th>
              <th className="py-3 px-4 font-semibold text-slate-900 text-left whitespace-nowrap">Críticos</th>
              <th className="py-3 px-4 font-semibold text-slate-900 text-left whitespace-nowrap">Atrasados</th>
              <th className="py-3 px-4 font-semibold text-slate-900 text-left whitespace-nowrap">Custo final</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={`units-${item.unit_id}`} className="border-b border-slate-100 hover:bg-slate-50 transition-colors">
                <td className="py-3 px-4">
                  <strong className="block text-slate-900">{item.unit_code}</strong>
                  <div className="text-[13px] text-slate-500">{item.unit_name}</div>
                </td>
                <td className="py-3 px-4 text-slate-600">{item.region ?? "—"}</td>
                <td className="py-3 px-4 text-slate-600">{item.total_tickets}</td>
                <td className="py-3 px-4 text-slate-600">{item.critical_tickets}</td>
                <td className="py-3 px-4 text-slate-600">{item.late_tickets}</td>
                <td className="py-3 px-4 text-slate-600">{formatMoney(item.final_cost_total)}</td>
              </tr>
            ))}
          </tbody>
        </Table>
      );
    }

    const items = data.items as SupplierReportItem[];
    return (
      <Table className="w-full text-sm" minWidth={980}>
        <thead>
          <tr className="border-b border-slate-200">
            <th className="py-3 px-4 font-semibold text-slate-900 text-left whitespace-nowrap">Fornecedor</th>
            <th className="py-3 px-4 font-semibold text-slate-900 text-left whitespace-nowrap">Total</th>
            <th className="py-3 px-4 font-semibold text-slate-900 text-left whitespace-nowrap">Em andamento</th>
            <th className="py-3 px-4 font-semibold text-slate-900 text-left whitespace-nowrap">Custo final</th>
            <th className="py-3 px-4 font-semibold text-slate-900 text-left whitespace-nowrap">Atrasos</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={`suppliers-${item.supplier_id}`} className="border-b border-slate-100 hover:bg-slate-50 transition-colors">
              <td className="py-3 px-4 text-slate-600">{item.supplier_name ?? "—"}</td>
              <td className="py-3 px-4 text-slate-600">{item.total_tickets}</td>
              <td className="py-3 px-4 text-slate-600">{item.in_progress_tickets}</td>
              <td className="py-3 px-4 text-slate-600">{formatMoney(item.final_cost_total)}</td>
              <td className="py-3 px-4 text-slate-600">{item.late_execution_tickets}</td>
            </tr>
          ))}
        </tbody>
      </Table>
    );
  }

  if (!canAccessReports) {
    return (
      <div className="p-8">
        <ErrorState description="Seu perfil atual não possui permissão para visualizar relatórios." />
      </div>
    );
  }

  return (
    <div className="mx-auto flex w-full max-w-[1600px] flex-col gap-6 font-sans">
      {/* Header */}
      <div className="flex min-w-0 flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-teal-50 text-teal-600 rounded-xl flex items-center justify-center">
            <ChartIcon />
          </div>
          <div>
            <h1 className="text-[28px] font-bold text-slate-900 leading-tight">Relatórios</h1>
            <p className="text-[15px] text-slate-500">Análises operacionais e executivas</p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex max-w-full gap-1 overflow-x-auto rounded-xl border border-slate-200 bg-white p-1 shadow-sm">
        {reportTabs.map((tab) => {
          const isActive = reportType === tab.key;
          const Icon = tab.icon;
          return (
            <button
              key={tab.key}
              onClick={() => changeTab(tab.key)}
              className={`flex shrink-0 items-center gap-2 rounded-lg px-4 py-2.5 text-[14px] font-medium transition-colors ${
                isActive
                  ? "bg-[#0f766e] text-white"
                  : "text-slate-600 hover:bg-slate-50"
              }`}
            >
              <div className="w-4 h-4 flex items-center justify-center">
                <Icon />
              </div>
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Filters Area */}
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
          <label className="field">
            <span className="flex items-center gap-2">
              <CalendarIcon />
              Data inicial
            </span>
            <input
              type="date"
              value={draftFilters.date_from || ""}
              onChange={(event) => setDraft("date_from", event.target.value)}
            />
          </label>

          <label className="field">
            <span>Data final</span>
            <input
              type="date"
              value={draftFilters.date_to || ""}
              onChange={(event) => setDraft("date_to", event.target.value)}
            />
          </label>

          <label className="field">
            <span className="flex items-center gap-2">
              <BuildingIcon />
              Unidade
            </span>
            <select
              value={String(draftFilters.unit_id ?? "")}
              onChange={(event) => setDraft("unit_id", event.target.value === "" ? "" : Number(event.target.value))}
            >
              <option value="">Todas as unidades</option>
              {units.map((unit) => (
                <option key={unit.id} value={unit.id}>
                  {unit.code} · {unit.name}
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            <span className="flex items-center gap-2">
              <TagIcon />
              Categoria
            </span>
            <select
              value={String(draftFilters.category_id ?? "")}
              onChange={(event) => setDraft("category_id", event.target.value === "" ? "" : Number(event.target.value))}
            >
              <option value="">Todas as categorias</option>
              {configuredCategoryOptions.map((category) => (
                <option key={category.value} value={category.value}>
                  {category.label}
                </option>
              ))}
            </select>
          </label>
        </div>

        {showAdvancedFilters ? (
          <div className="mt-4 grid grid-cols-1 gap-4 border-t border-slate-100 pt-4 md:grid-cols-2 xl:grid-cols-5">
            <label className="field">
              <span>Status</span>
              <select
                value={draftFilters.status || ""}
                onChange={(event) => setDraft("status", (event.target.value as TicketStatus | "") || "")}
              >
                <option value="">Todos</option>
                {Object.entries(STATUS_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </label>

            <label className="field">
              <span>Prioridade</span>
              <select
              value={String(draftFilters.priority_id ?? "")}
              onChange={(event) => setDraft("priority_id", event.target.value === "" ? "" : Number(event.target.value))}
            >
              <option value="">Todas</option>
                {configuredPriorityOptions.map(({ value, label }) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </label>

            <label className="field">
              <span>Severidade</span>
              <select
                value={draftFilters.severity || ""}
                onChange={(event) => setDraft("severity", (event.target.value as TicketSeverity | "") || "")}
              >
                <option value="">Todas</option>
                <option value="low">Baixa</option>
                <option value="medium">Media</option>
                <option value="high">Alta</option>
                <option value="critical">Critica</option>
              </select>
            </label>

            <label className="field">
              <span>Fornecedor</span>
              <select
                value={String(draftFilters.supplier_id ?? "")}
                onChange={(event) => setDraft("supplier_id", event.target.value === "" ? "" : Number(event.target.value))}
              >
                <option value="">Todos</option>
                {suppliers.map((supplier) => (
                  <option key={supplier.id} value={supplier.id}>
                    {supplier.name}
                  </option>
                ))}
              </select>
            </label>

            <div className="flex flex-wrap items-end gap-4">
              <label className="flex min-h-[38px] items-center gap-2 text-sm text-slate-700">
                <input
                  type="checkbox"
                  checked={draftFilters.only_late === true}
                  onChange={(event) => setDraft("only_late", event.target.checked ? true : "")}
                />
                Somente atrasados
              </label>
            </div>
          </div>
        ) : null}

        <div className="mt-4 flex flex-col gap-3 border-t border-slate-100 pt-4 sm:flex-row sm:flex-wrap sm:items-center sm:justify-end">
          <button
            className="flex h-[42px] items-center justify-center gap-2 rounded-lg border border-slate-300 bg-white px-4 text-[14px] font-medium text-slate-700 transition-colors hover:bg-slate-50"
            type="button"
            onClick={() => setShowAdvancedFilters((current) => !current)}
          >
            <FilterIcon />
            Mais filtros
          </button>

          <button
            className="flex h-[42px] items-center justify-center gap-2 rounded-lg bg-[#0f766e] px-6 text-[14px] font-medium text-white shadow-sm transition-colors hover:bg-[#0d645d]"
            type="button"
            onClick={applyFilters}
          >
            <SearchIcon />
            Aplicar
          </button>

          <button
            className="flex h-[42px] items-center justify-center gap-2 rounded-lg px-4 text-[14px] font-medium text-slate-600 transition-colors hover:text-slate-900"
            type="button"
            onClick={clearFilters}
          >
            <RefreshIcon />
            Limpar
          </button>
        </div>
      </div>

      {exportMessage ? <div className="state-card state-card--success">{exportMessage}</div> : null}
      {errorMessage ? <ErrorState description={errorMessage} /> : null}

      {/* Summary StatCards */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
        {reportType === "tickets" && (
          <>
            <StatCard label="Total de chamados" value={stats ? stats.total.toLocaleString("pt-BR") : "Sem dados"} trendDirection="neutral" icon={<DocumentIcon />} iconBgColor="bg-[#f0fdf4]" iconColor="text-[#16a34a]" />
            <StatCard label="Atrasados" value={stats ? stats.atrasados.toString() : "Sem dados"} trendDirection="neutral" icon={<ClockIcon />} iconBgColor="bg-[#fef2f2]" iconColor="text-[#dc2626]" />
            <StatCard label="Custo final" value={stats ? formatMoney(stats.custoFinal) : "Sem dados"} trendDirection="neutral" icon={<BigDollarIcon />} iconBgColor="bg-[#fffbeb]" iconColor="text-[#d97706]" />
            <StatCard label="SLA no prazo" value={stats ? formatPercentDisplay(stats.slaNoPrazo) : "Sem dados"} trendDirection="neutral" icon={<ShieldCheckIcon />} iconBgColor="bg-[#f0fdf4]" iconColor="text-[#16a34a]" />
          </>
        )}
        {reportType === "costs" && (
          <>
            <StatCard label="Custo Estimado" value={dashboardData ? formatMoney(dashboardData.estimated_cost_total) : "Sem dados"} trendDirection="neutral" icon={<BigDollarIcon />} iconBgColor="bg-[#f8fafc]" iconColor="text-[#64748b]" />
            <StatCard label="Custo Aprovado" value={dashboardData ? formatMoney(dashboardData.approved_cost_total) : "Sem dados"} trendDirection="neutral" icon={<BigDollarIcon />} iconBgColor="bg-[#eff6ff]" iconColor="text-[#3b82f6]" />
            <StatCard label="Custo Final" value={dashboardData ? formatMoney(dashboardData.final_cost_total) : "Sem dados"} trendDirection="neutral" icon={<BigDollarIcon />} iconBgColor="bg-[#fffbeb]" iconColor="text-[#d97706]" />
            <StatCard label="Total de chamados" value={dashboardData ? dashboardData.total_tickets.toString() : "Sem dados"} trendDirection="neutral" icon={<DocumentIcon />} iconBgColor="bg-[#f0fdf4]" iconColor="text-[#16a34a]" />
          </>
        )}
        {reportType === "sla" && (
          <>
            <StatCard label="Chamados com SLA" value={dashboardData ? dashboardData.sla_summary.total_with_sla.toString() : "Sem dados"} trendDirection="neutral" icon={<DocumentIcon />} iconBgColor="bg-[#eff6ff]" iconColor="text-[#3b82f6]" />
            <StatCard label="No prazo" value={dashboardData ? dashboardData.sla_summary.on_track.toString() : "Sem dados"} trendDirection="neutral" icon={<ShieldCheckIcon />} iconBgColor="bg-[#f0fdf4]" iconColor="text-[#16a34a]" />
            <StatCard label="Atrasados" value={dashboardData ? dashboardData.sla_summary.late.toString() : "Sem dados"} trendDirection="neutral" icon={<ClockIcon />} iconBgColor="bg-[#fef2f2]" iconColor="text-[#dc2626]" />
            <StatCard label="Taxa de cumprimento" value={dashboardData ? formatPercentDisplay(dashboardData.sla_summary.compliance_rate) : "Sem dados"} trendDirection="neutral" icon={<ChartIcon />} iconBgColor="bg-[#f0fdf4]" iconColor="text-[#16a34a]" />
          </>
        )}
        {reportType === "units" && (
          <>
            <StatCard label="Total de chamados" value={dashboardData ? dashboardData.total_tickets.toLocaleString("pt-BR") : "Sem dados"} trendDirection="neutral" icon={<DocumentIcon />} iconBgColor="bg-[#f0fdf4]" iconColor="text-[#16a34a]" />
            <StatCard label="Atrasados" value={dashboardData ? dashboardData.late_tickets.toString() : "Sem dados"} trendDirection="neutral" icon={<ClockIcon />} iconBgColor="bg-[#fef2f2]" iconColor="text-[#dc2626]" />
            <StatCard label="Custo final" value={dashboardData ? formatMoney(dashboardData.final_cost_total) : "Sem dados"} trendDirection="neutral" icon={<BigDollarIcon />} iconBgColor="bg-[#fffbeb]" iconColor="text-[#d97706]" />
            <StatCard label="SLA no prazo" value={dashboardData ? formatPercentDisplay(dashboardData.sla_compliance_rate) : "Sem dados"} trendDirection="neutral" icon={<ShieldCheckIcon />} iconBgColor="bg-[#f0fdf4]" iconColor="text-[#16a34a]" />
          </>
        )}
        {reportType === "suppliers" && data && (
          (() => {
            const items = (data.items as SupplierReportItem[]) || [];
            const activeCount = items.length;
            const topCost = items.reduce((prev, current) => (toNumberSafe(prev.final_cost_total) > toNumberSafe(current.final_cost_total)) ? prev : current, items[0] || { supplier_name: "-", final_cost_total: 0 });
            const topLate = items.reduce((prev, current) => (prev.late_execution_tickets > current.late_execution_tickets) ? prev : current, items[0] || { supplier_name: "-", late_execution_tickets: 0 });
            const totalInProgress = items.reduce((sum, current) => sum + (current.in_progress_tickets || 0), 0);

            return (
              <>
                <StatCard label="Fornecedores na visão" value={activeCount.toString()} trendDirection="neutral" icon={<BuildingIcon />} iconBgColor="bg-[#eff6ff]" iconColor="text-[#3b82f6]" />
                <StatCard label="Maior Custo" value={Number(topCost.final_cost_total) > 0 ? formatMoney(topCost.final_cost_total) : "Sem dados"} description={topCost.supplier_name || "Nenhum"} trendDirection="neutral" icon={<BigDollarIcon />} iconBgColor="bg-[#fffbeb]" iconColor="text-[#d97706]" />
                <StatCard label="Mais Atrasos" value={topLate.late_execution_tickets.toString()} description={topLate.supplier_name || "Nenhum"} trendDirection="neutral" icon={<ClockIcon />} iconBgColor="bg-[#fef2f2]" iconColor="text-[#dc2626]" />
                <StatCard label="Em andamento" value={totalInProgress.toString()} trendDirection="neutral" icon={<DocumentIcon />} iconBgColor="bg-[#f0fdf4]" iconColor="text-[#16a34a]" />
              </>
            );
          })()
        )}
      </div>

      {/* Main Content Area (Two Columns) */}
      <div className={`grid grid-cols-1 ${reportType === "suppliers" ? "xl:grid-cols-1" : "xl:grid-cols-[1fr_400px]"} gap-6`}>

        {/* Left Column - Table */}
        <div className="flex min-w-0 flex-col rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div className="flex flex-col gap-3 border-b border-slate-200 p-5 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex min-w-0 items-center gap-3">
              <div className="text-slate-400 w-5 h-5">
                <DocumentIcon />
              </div>
              <h2 className="text-[16px] font-semibold text-slate-900">{activeTab.label}</h2>
            </div>
            <button
              onClick={handleExport}
              className="flex items-center gap-2 h-[36px] px-4 rounded-lg font-medium text-[13px] text-slate-700 bg-white border border-slate-300 hover:bg-slate-50 transition-colors shadow-sm"
              disabled={isExporting}
            >
              <DownloadIcon />
              Exportar CSV
            </button>
          </div>

          <div className="min-w-0 flex-grow p-0">
             <ErrorBoundary>
             {isLoading ? (
                <div className="p-8">
                  <LoadingState title="Carregando" />
                </div>
              ) : data && data.items.length === 0 ? (
                <div className="p-8">
                  <EmptyState title="Nenhum dado" description="Não foram encontrados resultados para os filtros informados." />
                </div>
              ) : (
                renderReportTable()
              )}
              </ErrorBoundary>
          </div>

          {data && (
            <div className="flex flex-col gap-3 rounded-b-2xl border-t border-slate-200 bg-slate-50/50 p-4 text-[13px] text-slate-500 sm:flex-row sm:items-center sm:justify-between">
              <div>
                Mostrando {Math.max(1, (data.page - 1) * data.page_size + 1)} a {Math.min(data.page * data.page_size, data.total)} de {data.total.toLocaleString("pt-BR")} resultados
              </div>
              <div className="flex flex-wrap items-center gap-1">
                <button
                  className="w-8 h-8 flex items-center justify-center rounded border border-slate-200 bg-white hover:bg-slate-50 text-slate-400 disabled:cursor-not-allowed disabled:opacity-50"
                  onClick={() => setFilters((current) => ({ ...current, page: Math.max(1, current.page - 1) }))}
                  disabled={data.page <= 1}
                >
                  &lt;
                </button>
                {visiblePages.map((page) => (
                  <button
                    key={page}
                    className={
                      page === data.page
                        ? "w-8 h-8 flex items-center justify-center rounded border border-[#0f766e] bg-[#0f766e] text-white font-medium"
                        : "w-8 h-8 flex items-center justify-center rounded border border-slate-200 bg-white hover:bg-slate-50 text-slate-600 font-medium"
                    }
                    onClick={() => setFilters((current) => ({ ...current, page }))}
                  >
                    {page}
                  </button>
                ))}
                {visiblePages[visiblePages.length - 1] < data.pages ? (
                  <span className="w-8 flex items-center justify-center text-slate-400">...</span>
                ) : null}
                {visiblePages[visiblePages.length - 1] !== data.pages && data.pages > 0 ? (
                  <button
                    className="w-8 h-8 flex items-center justify-center rounded border border-slate-200 bg-white hover:bg-slate-50 text-slate-600 font-medium"
                    onClick={() => setFilters((current) => ({ ...current, page: data.pages }))}
                  >
                    {data.pages}
                  </button>
                ) : null}
                <button
                  className="w-8 h-8 flex items-center justify-center rounded border border-slate-200 bg-white hover:bg-slate-50 text-slate-400 disabled:cursor-not-allowed disabled:opacity-50"
                  onClick={() => setFilters((current) => ({ ...current, page: Math.min(data.pages, current.page + 1) }))}
                  disabled={data.page >= data.pages}
                >
                  &gt;
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Right Column - Charts */}
        {reportType !== "suppliers" && (
        <div className="flex min-w-0 flex-col rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between mb-8">
            <h2 className="text-[16px] font-semibold text-slate-900">Visão geral do período</h2>
            <div className="text-slate-400 cursor-pointer">
              <InfoIcon />
            </div>
          </div>

          {stats && stats.count > 0 ? (
            <>
              <div className="mb-4">
                <h3 className="text-[14px] font-medium text-slate-900 mb-6">Distribuição por status</h3>
                <div className="flex flex-col gap-6 sm:flex-row sm:items-center">
                  <div className="relative w-32 h-32 flex-shrink-0">
                    <svg viewBox="0 0 36 36" className="w-full h-full transform -rotate-90">
                      {(() => {
                        const s = stats.statuses;
                        const total = stats.count;
                        let offset = 0;
                        const calcOffset = (p: number) => {
                          const o = offset;
                          offset -= p;
                          return o;
                        };

                        return (
                          <>
                            {STATUS_CHART.map((segment) => {
                              const value = s[segment.key] ?? 0;
                              const percentage = total > 0 ? (value / total) * 100 : 0;

                              if (percentage <= 0) {
                                return null;
                              }

                              return (
                                <circle
                                  key={segment.key}
                                  cx="18"
                                  cy="18"
                                  r="15.915"
                                  fill="transparent"
                                  stroke={segment.color}
                                  strokeWidth="8"
                                  strokeDasharray={`${percentage} ${100 - percentage}`}
                                  strokeDashoffset={calcOffset(percentage)}
                                />
                              );
                            })}
                          </>
                        );
                      })()}
                    </svg>
                    <div className="absolute inset-0 m-auto w-20 h-20 bg-white rounded-full flex items-center justify-center">
                      <span className="text-[16px] font-bold text-slate-900">{stats.count}</span>
                    </div>
                  </div>
                  <div className="flex-1 flex flex-col gap-2">
                    {STATUS_CHART.map((segment) => (
                      <div key={segment.key} className="flex items-center justify-between text-[13px]">
                        <div className="flex items-center gap-2">
                          <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: segment.color }} />
                          <span className="text-slate-600">{segment.label}</span>
                        </div>
                        <span className="text-slate-900 font-medium">{stats.statuses[segment.key]}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div className="mt-8">
                <h3 className="text-[14px] font-medium text-slate-900 mb-5">Chamados por prioridade</h3>
                <div className="flex flex-col gap-4">
                  {PRIORITY_CHART.map((segment) => (
                    <div key={segment.key} className="flex items-center gap-4">
                      <span className="text-[13px] text-slate-600 w-12">{segment.label}</span>
                      <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full"
                          style={{
                            width: `${stats.count > 0 ? (stats.priorities[segment.key] / stats.count) * 100 : 0}%`,
                            backgroundColor: segment.color,
                          }}
                        />
                      </div>
                      <span className="text-[13px] text-slate-900 font-medium w-8 text-right">{stats.priorities[segment.key]}</span>
                    </div>
                  ))}
                </div>
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-[13px] text-slate-500 text-center">
              Não há dados suficientes para exibição no momento.
            </div>
          )}

          <div className="mt-auto pt-8 text-[13px] text-slate-400">
            Dados consolidados pela API para o recorte aplicado.
          </div>
        </div>
        )}
      </div>
    </div>
  );
}
