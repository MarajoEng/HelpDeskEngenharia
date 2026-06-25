import { useEffect, useMemo, useState } from "react";

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
import Button from "../components/ui/Button";
import EmptyState from "../components/ui/EmptyState";
import ErrorState from "../components/ui/ErrorState";
import FilterBar from "../components/ui/FilterBar";
import Input from "../components/ui/Input";
import LoadingState from "../components/ui/LoadingState";
import PageHeader from "../components/ui/PageHeader";
import Pagination from "../components/ui/Pagination";
import PriorityBadge from "../components/ui/PriorityBadge";
import Select from "../components/ui/Select";
import SeverityBadge from "../components/ui/SeverityBadge";
import StatCard from "../components/ui/StatCard";
import StatusBadge from "../components/ui/StatusBadge";
import Table from "../components/ui/Table";
import {
  CATEGORY_LABELS,
  PRIORITY_LABELS,
  ROLE_LABELS,
  SEVERITY_LABELS,
  STATUS_LABELS,
} from "../components/ui/statusOptions";
import { useAuth } from "../hooks/useAuth";
import type { Supplier } from "../types/supplier";
import type { TicketCategory, TicketPriority, TicketSeverity, TicketStatus } from "../types/ticket";
import type { Unit } from "../types/unit";
import type {
  CostReportItem,
  PaginatedReportResponse,
  ReportFilters,
  ReportType,
  SlaReportItem,
  SupplierReportItem,
  TicketReportItem,
  UnitReportItem,
} from "../types/report";
import { formatDate, formatMoney } from "../utils/formatters";
import { getErrorMessage } from "../utils/messages";

const initialFilters: ReportFilters = {
  page: 1,
  page_size: 20,
  date_from: "",
  date_to: "",
  unit_id: "",
  region: "",
  status: "",
  category: "",
  priority: "",
  severity: "",
  supplier_id: "",
  only_late: "",
  requires_approval: "",
};

const reportTabs: Array<{
  key: ReportType;
  label: string;
  description: string;
  filename: string;
}> = [
  {
    key: "tickets",
    label: "Chamados",
    description: "Base detalhada para operacao, auditoria de fluxo e acompanhamento de SLA.",
    filename: "chamados.csv",
  },
  {
    key: "costs",
    label: "Custos",
    description: "Consolidado por unidade, categoria e fornecedor com ticket medio.",
    filename: "custos.csv",
  },
  {
    key: "sla",
    label: "SLA",
    description: "Cumprimento de prazo, fechamentos no prazo e medias de atendimento.",
    filename: "sla.csv",
  },
  {
    key: "units",
    label: "Unidades",
    description: "Visao executiva por unidade com criticidade, atraso, impacto e custo final.",
    filename: "unidades.csv",
  },
  {
    key: "suppliers",
    label: "Fornecedores",
    description: "Volume, custo, tempo medio de execucao e atraso por parceiro.",
    filename: "fornecedores.csv",
  },
];

export default function ReportsPage() {
  const { token, user } = useAuth();
  const [reportType, setReportType] = useState<ReportType>("tickets");
  const [filters, setFilters] = useState<ReportFilters>(initialFilters);
  const [draftFilters, setDraftFilters] = useState<ReportFilters>(initialFilters);
  const [units, setUnits] = useState<Unit[]>([]);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [data, setData] = useState<PaginatedReportResponse<unknown> | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isExporting, setIsExporting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [exportMessage, setExportMessage] = useState<string | null>(null);

  const canAccessReports = user ? user.role !== "supplier" : true;
  const isManager = user?.role === "manager";
  const activeTab = useMemo(() => reportTabs.find((item) => item.key === reportType) ?? reportTabs[0], [reportType]);

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
          const response = await listUnits(currentToken, { page: 1, page_size: 200, sort: "name_asc" });
          if (!isActive) return;
          setUnits(response.items);
        }
      } catch {
        if (!isActive) return;
        setUnits([]);
      }

      try {
        const response = await listSuppliers(currentToken, { page: 1, page_size: 200 });
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
        setErrorMessage(getErrorMessage(error, "Nao foi possivel carregar o relatorio."));
      })
      .finally(() => {
        if (isActive) {
          setIsLoading(false);
        }
      });

    return () => {
      isActive = false;
    };
  }, [canAccessReports, filters, reportType, token]);

  function setDraft<K extends keyof ReportFilters>(key: K, value: ReportFilters[K]) {
    setDraftFilters((current) => ({ ...current, [key]: value }));
  }

  function applyFilters() {
    setExportMessage(null);
    setFilters((current) => ({
      ...draftFilters,
      page: 1,
      page_size: current.page_size,
    }));
  }

  function clearFilters() {
    const reset: ReportFilters = {
      ...initialFilters,
      unit_id: isManager && user?.unit_id ? user.unit_id : "",
    };
    setDraftFilters(reset);
    setFilters(reset);
    setExportMessage(null);
  }

  function changeTab(nextType: ReportType) {
    setReportType(nextType);
    setExportMessage(null);
    setFilters((current) => ({ ...current, page: 1 }));
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
      setExportMessage(`Exportacao concluida para ${activeTab.label.toLowerCase()}.`);
    } catch (error: unknown) {
      setErrorMessage(getErrorMessage(error, "Nao foi possivel exportar o CSV."));
    } finally {
      setIsExporting(false);
    }
  }

  function renderReportTable() {
    if (!data) return null;

    if (reportType === "tickets") {
      const items = data.items as TicketReportItem[];
      return (
        <Table minWidth={1420}>
          <thead>
            <tr>
              <th>Chamado</th>
              <th>Unidade</th>
              <th>Status</th>
              <th>Prioridade</th>
              <th>Severidade</th>
              <th>Solicitante</th>
              <th>Responsavel</th>
              <th>Fornecedor</th>
              <th>Abertura</th>
              <th>SLA</th>
              <th>Custo final</th>
              <th>Bicos</th>
              <th>Aprovacao</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id}>
                <td className="text-mono text-sm">{item.ticket_number}</td>
                <td>
                  <strong>{item.unit_code}</strong>
                  <div className="text-sm text-muted">{item.unit_name}</div>
                </td>
                <td><StatusBadge status={item.status} /></td>
                <td><PriorityBadge priority={item.priority} /></td>
                <td><SeverityBadge severity={item.severity} /></td>
                <td>{item.opened_by_user_name ?? "—"}</td>
                <td>{item.assigned_to_user_name ?? "Nao atribuido"}</td>
                <td>{item.supplier_name ?? "Sem fornecedor"}</td>
                <td className="text-sm">{formatDate(item.opened_at)}</td>
                <td>
                  {item.sla_due_at ? (
                    <Badge tone={item.is_late ? "danger" : "success"}>
                      {item.is_late ? "Atrasado" : formatDate(item.sla_due_at)}
                    </Badge>
                  ) : (
                    <Badge tone="neutral">Sem SLA</Badge>
                  )}
                </td>
                <td>{formatMoney(item.final_cost)}</td>
                <td>{item.fuel_nozzles_stopped ?? 0}</td>
                <td>
                  <Badge tone={item.requires_approval ? "warning" : "neutral"}>
                    {item.requires_approval ? "Exige aprovacao" : "Sem aprovacao"}
                  </Badge>
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
        <Table minWidth={1120}>
          <thead>
            <tr>
              <th>Unidade</th>
              <th>Categoria</th>
              <th>Fornecedor</th>
              <th>Qtd.</th>
              <th>Estimado</th>
              <th>Aprovado</th>
              <th>Final</th>
              <th>Ticket medio</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item, index) => (
              <tr key={`${item.unit_id}-${item.category}-${item.supplier_id ?? "none"}-${index}`}>
                <td>
                  <strong>{item.unit_code}</strong>
                  <div className="text-sm text-muted">{item.unit_name}</div>
                </td>
                <td>{CATEGORY_LABELS[item.category]}</td>
                <td>{item.supplier_name ?? "Sem fornecedor"}</td>
                <td>{item.total_tickets}</td>
                <td>{formatMoney(item.estimated_cost_total)}</td>
                <td>{formatMoney(item.approved_cost_total)}</td>
                <td>{formatMoney(item.final_cost_total)}</td>
                <td>{formatMoney(item.average_ticket_cost)}</td>
              </tr>
            ))}
          </tbody>
        </Table>
      );
    }

    if (reportType === "sla") {
      const items = data.items as SlaReportItem[];
      return (
        <Table minWidth={1080}>
          <thead>
            <tr>
              <th>Unidade</th>
              <th>Total com SLA</th>
              <th>No prazo</th>
              <th>Atrasados</th>
              <th>Fechados no prazo</th>
              <th>Fechados atrasados</th>
              <th>Taxa</th>
              <th>Media resolucao</th>
              <th>Media fechamento</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.unit_id}>
                <td>
                  <strong>{item.unit_code}</strong>
                  <div className="text-sm text-muted">{item.unit_name}</div>
                </td>
                <td>{item.total_with_sla}</td>
                <td>{item.on_track}</td>
                <td>{item.late}</td>
                <td>{item.closed_on_time}</td>
                <td>{item.closed_late}</td>
                <td>
                  <Badge tone={item.compliance_rate >= 80 ? "success" : item.compliance_rate >= 50 ? "warning" : "danger"}>
                    {item.compliance_rate.toFixed(2)}%
                  </Badge>
                </td>
                <td>{item.average_resolution_hours.toFixed(2)}h</td>
                <td>{item.average_closure_hours.toFixed(2)}h</td>
              </tr>
            ))}
          </tbody>
        </Table>
      );
    }

    if (reportType === "units") {
      const items = data.items as UnitReportItem[];
      return (
        <Table minWidth={1120}>
          <thead>
            <tr>
              <th>Unidade</th>
              <th>Regiao</th>
              <th>Total</th>
              <th>Criticos</th>
              <th>Atrasados</th>
              <th>Em andamento</th>
              <th>Fechados</th>
              <th>Custo final</th>
              <th>Bicos parados</th>
              <th>Perda estimada</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.unit_id}>
                <td>
                  <strong>{item.unit_code}</strong>
                  <div className="text-sm text-muted">{item.unit_name}</div>
                </td>
                <td>{item.region}</td>
                <td>{item.total_tickets}</td>
                <td>{item.critical_tickets}</td>
                <td>{item.late_tickets}</td>
                <td>{item.in_progress_tickets}</td>
                <td>{item.closed_tickets}</td>
                <td>{formatMoney(item.final_cost_total)}</td>
                <td>{item.total_fuel_nozzles_stopped}</td>
                <td>{formatMoney(item.estimated_daily_loss_total)}</td>
              </tr>
            ))}
          </tbody>
        </Table>
      );
    }

    const items = data.items as SupplierReportItem[];
    return (
      <Table minWidth={980}>
        <thead>
          <tr>
            <th>Fornecedor</th>
            <th>Total</th>
            <th>Em andamento</th>
            <th>Resolvidos</th>
            <th>Fechados</th>
            <th>Custo final</th>
            <th>Media execucao</th>
            <th>Atrasos</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.supplier_id}>
              <td>{item.supplier_name}</td>
              <td>{item.total_tickets}</td>
              <td>{item.in_progress_tickets}</td>
              <td>{item.resolved_tickets}</td>
              <td>{item.closed_tickets}</td>
              <td>{formatMoney(item.final_cost_total)}</td>
              <td>{item.average_execution_hours.toFixed(2)}h</td>
              <td>{item.late_execution_tickets}</td>
            </tr>
          ))}
        </tbody>
      </Table>
    );
  }

  if (!canAccessReports) {
    return (
      <section className="page">
        <PageHeader
          eyebrow="Relatorios"
          title="Acesso indisponivel"
          description="Este perfil nao pode acessar relatorios nesta fase."
        />
        <ErrorState description="Seu perfil atual nao possui permissao para visualizar relatorios." />
      </section>
    );
  }

  return (
    <section className="page">
      <PageHeader
        eyebrow="Relatorios"
        title="Relatorios operacionais e executivos"
        description={activeTab.description}
        actions={
          <Button variant="primary" type="button" onClick={handleExport} disabled={isExporting || isLoading}>
            {isExporting ? "Exportando..." : "Exportar CSV"}
          </Button>
        }
      />

      <section className="summary-grid">
        <StatCard
          label="Relatorio ativo"
          tone="accent"
          value={activeTab.label}
          description="Selecione a visao conforme a analise desejada."
        />
        <StatCard
          label="Escopo do usuario"
          tone="info"
          value={ROLE_LABELS[user?.role ?? "manager"]}
          description={isManager ? "A consulta esta restrita automaticamente a sua unidade." : "A consulta respeita as permissoes do backend."}
        />
        <StatCard
          label="Linhas atuais"
          tone="warning"
          value={data?.total ?? 0}
          description="Total retornado com os filtros atualmente aplicados."
        />
      </section>

      <section className="panel panel--stack">
        <div className="header-actions">
          {reportTabs.map((tab) => (
            <Button
              key={tab.key}
              variant={reportType === tab.key ? "primary" : "secondary"}
              type="button"
              onClick={() => changeTab(tab.key)}
            >
              {tab.label}
            </Button>
          ))}
        </div>

        {exportMessage ? <div className="state-card state-card--success">{exportMessage}</div> : null}
        {errorMessage ? <ErrorState description={errorMessage} /> : null}

        <FilterBar columns={4}>
          <Input
            label="Data inicial"
            type="date"
            value={draftFilters.date_from || ""}
            onChange={(event) => setDraft("date_from", event.target.value)}
          />
          <Input
            label="Data final"
            type="date"
            value={draftFilters.date_to || ""}
            onChange={(event) => setDraft("date_to", event.target.value)}
          />
          <Select
            label="Unidade"
            value={String(draftFilters.unit_id ?? "")}
            onChange={(event) => setDraft("unit_id", event.target.value === "" ? "" : Number(event.target.value))}
            disabled={isManager}
          >
            <option value="">Todas</option>
            {units.map((unit) => (
              <option key={unit.id} value={unit.id}>
                {unit.code} · {unit.name}
              </option>
            ))}
          </Select>
          <Input
            label="Regiao"
            value={draftFilters.region || ""}
            onChange={(event) => setDraft("region", event.target.value)}
            placeholder="Ex.: Sul"
          />
        </FilterBar>

        <FilterBar columns={4}>
          <Select
            label="Status"
            value={draftFilters.status || ""}
            onChange={(event) => setDraft("status", (event.target.value as TicketStatus | "") || "")}
          >
            <option value="">Todos</option>
            {Object.entries(STATUS_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </Select>
          <Select
            label="Categoria"
            value={draftFilters.category || ""}
            onChange={(event) => setDraft("category", (event.target.value as TicketCategory | "") || "")}
          >
            <option value="">Todas</option>
            {Object.entries(CATEGORY_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </Select>
          <Select
            label="Prioridade"
            value={draftFilters.priority || ""}
            onChange={(event) => setDraft("priority", (event.target.value as TicketPriority | "") || "")}
          >
            <option value="">Todas</option>
            {Object.entries(PRIORITY_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </Select>
          <Select
            label="Severidade"
            value={draftFilters.severity || ""}
            onChange={(event) => setDraft("severity", (event.target.value as TicketSeverity | "") || "")}
          >
            <option value="">Todas</option>
            {Object.entries(SEVERITY_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </Select>
        </FilterBar>

        <FilterBar columns={4}>
          <Select
            label="Fornecedor"
            value={String(draftFilters.supplier_id ?? "")}
            onChange={(event) => setDraft("supplier_id", event.target.value === "" ? "" : Number(event.target.value))}
          >
            <option value="">Todos</option>
            {suppliers.map((supplier) => (
              <option key={supplier.id} value={supplier.id}>
                {supplier.name}
              </option>
            ))}
          </Select>
          <Select
            label="Atraso"
            value={String(draftFilters.only_late ?? "")}
            onChange={(event) => {
              const value = event.target.value;
              setDraft("only_late", value === "" ? "" : value === "true");
            }}
          >
            <option value="">Todos</option>
            <option value="true">Somente atrasados</option>
            <option value="false">Sem restricao</option>
          </Select>
          <Select
            label="Aprovacao"
            value={String(draftFilters.requires_approval ?? "")}
            onChange={(event) => {
              const value = event.target.value;
              setDraft("requires_approval", value === "" ? "" : value === "true");
            }}
          >
            <option value="">Todos</option>
            <option value="true">Exige aprovacao</option>
            <option value="false">Sem aprovacao</option>
          </Select>
          <div className="filters-actions">
            <Button variant="primary" type="button" onClick={applyFilters}>
              Aplicar filtros
            </Button>
            <Button variant="secondary" type="button" onClick={clearFilters}>
              Limpar
            </Button>
          </div>
        </FilterBar>

        {isLoading ? (
          <LoadingState title="Carregando relatorio" description="Consolidando os dados reais do banco." />
        ) : data && data.items.length === 0 ? (
          <EmptyState
            title="Nenhum dado encontrado"
            description="Ajuste os filtros para localizar registros dentro do escopo permitido."
          />
        ) : (
          <>
            {renderReportTable()}
            {data ? (
              <Pagination
                total={data.total}
                label="linha(s)"
                page={data.page}
                pages={data.pages}
                onPrevious={() => setFilters((current) => ({ ...current, page: Math.max(1, current.page - 1) }))}
                onNext={() => setFilters((current) => ({ ...current, page: current.page + 1 }))}
              />
            ) : null}
          </>
        )}
      </section>
    </section>
  );
}
