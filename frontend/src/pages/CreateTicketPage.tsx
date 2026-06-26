import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import {
  getTicketFormSchema,
  listTicketCategories,
  listTicketPriorities,
  listTicketSubcategories,
  listTicketTypes,
} from "../api/ticketConfigurationApi";
import { createTicket } from "../api/ticketApi";
import { getUnitById, listUnits } from "../api/unitApi";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import EmptyState from "../components/ui/EmptyState";
import ErrorState from "../components/ui/ErrorState";
import Input from "../components/ui/Input";
import LoadingState from "../components/ui/LoadingState";
import PageHeader from "../components/ui/PageHeader";
import Select from "../components/ui/Select";
import Textarea from "../components/ui/Textarea";
import { useAuth } from "../hooks/useAuth";
import type { Ticket, TicketCategory, TicketCreatePayload, TicketPriority, TicketSeverity } from "../types/ticket";
import type {
  TicketCategoryItem,
  TicketCustomFieldItem,
  TicketPriorityItem,
  TicketSubcategoryItem,
  TicketTypeItem,
} from "../types/ticketConfiguration";
import type { Unit } from "../types/unit";
import { getErrorMessage } from "../utils/messages";

const severityOptions: Array<{ value: TicketSeverity; label: string }> = [
  { value: "low", label: "Baixa" },
  { value: "medium", label: "Media" },
  { value: "high", label: "Alta" },
  { value: "critical", label: "Critica" },
];

type TicketFormState = {
  unit_id: string;
  category_id: string;
  subcategory_id: string;
  type_id: string;
  problem_type: string;
  title: string;
  description: string;
  priority_id: string;
  severity: TicketSeverity;
  operational_impact: string;
  fuel_nozzles_stopped: string;
  estimated_daily_loss: string;
  estimated_cost: string;
  requires_approval: boolean;
};

const initialForm: TicketFormState = {
  unit_id: "",
  category_id: "",
  subcategory_id: "",
  type_id: "",
  problem_type: "",
  title: "",
  description: "",
  priority_id: "",
  severity: "high",
  operational_impact: "",
  fuel_nozzles_stopped: "",
  estimated_daily_loss: "",
  estimated_cost: "",
  requires_approval: false,
};

function toOptionalDecimal(value: string) {
  const normalized = value.trim();
  return normalized ? normalized : null;
}

function toOptionalInteger(value: string) {
  const normalized = value.trim();
  return normalized ? Number(normalized) : null;
}

function toOptionalConfigId(value: string) {
  const normalized = value.trim();
  return normalized ? Number(normalized) : null;
}

function unitLabel(unit: Unit) {
  return `${unit.code} · ${unit.name}`;
}

function preferredConfigId<T extends { id: number; legacy_value?: string | null }>(
  items: T[],
  preferredLegacyValue: string,
) {
  const preferredItem = items.find((item) => item.legacy_value === preferredLegacyValue);
  if (preferredItem) {
    return String(preferredItem.id);
  }

  return items[0] ? String(items[0].id) : "";
}

export default function CreateTicketPage() {
  const { token, user } = useAuth();
  const [units, setUnits] = useState<Unit[]>([]);
  const [categories, setCategories] = useState<TicketCategoryItem[]>([]);
  const [subcategories, setSubcategories] = useState<TicketSubcategoryItem[]>([]);
  const [ticketTypes, setTicketTypes] = useState<TicketTypeItem[]>([]);
  const [priorities, setPriorities] = useState<TicketPriorityItem[]>([]);
  const [form, setForm] = useState<TicketFormState>(initialForm);
  const [createdTicket, setCreatedTicket] = useState<Ticket | null>(null);
  const [isLoadingPage, setIsLoadingPage] = useState(true);
  const [isLoadingSubcategories, setIsLoadingSubcategories] = useState(false);
  const [isLoadingCustomFields, setIsLoadingCustomFields] = useState(false);
  const [customFieldSchema, setCustomFieldSchema] = useState<TicketCustomFieldItem[]>([]);
  const [customFieldValues, setCustomFieldValues] = useState<Record<number, string | boolean>>({});
  const [customFieldErrors, setCustomFieldErrors] = useState<Record<number, string>>({});
  const [customFieldSchemaError, setCustomFieldSchemaError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [pageErrorMessage, setPageErrorMessage] = useState<string | null>(null);
  const [submitErrorMessage, setSubmitErrorMessage] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  const isSupplier = user?.role === "supplier";
  const isManager = user?.role === "manager";

  useEffect(() => {
    if (!token || !user) {
      return;
    }

    let isActive = true;
    setIsLoadingPage(true);
    setPageErrorMessage(null);

    const loadResources = async () => {
      try {
        const unitPromise =
          user.role === "manager" && user.unit_id
            ? getUnitById(token, user.unit_id).then((currentUnit) => [currentUnit])
            : listUnits(token, {
                page: 1,
                page_size: 100,
                is_active: true,
              }).then((response) => response.items);

        const [loadedUnits, categoriesResponse, typesResponse, prioritiesResponse] = await Promise.all([
          unitPromise,
          listTicketCategories({ page: 1, page_size: 100, sort: "display_order_asc" }),
          listTicketTypes({ page: 1, page_size: 100, sort: "display_order_asc" }),
          listTicketPriorities({ page: 1, page_size: 100, sort: "display_order_asc" }),
        ]);

        if (!isActive) {
          return;
        }

        setUnits(loadedUnits);
        setCategories(categoriesResponse.items);
        setTicketTypes(typesResponse.items);
        setPriorities(prioritiesResponse.items);
        setForm((current) => ({
          ...current,
          unit_id:
            user.role === "manager" && loadedUnits[0]
              ? String(loadedUnits[0].id)
              : current.unit_id && loadedUnits.some((unit) => String(unit.id) === current.unit_id)
                ? current.unit_id
                : "",
          category_id:
            current.category_id && categoriesResponse.items.some((item) => String(item.id) === current.category_id)
              ? current.category_id
              : preferredConfigId(categoriesResponse.items, "fuel_pump"),
          priority_id:
            current.priority_id && prioritiesResponse.items.some((item) => String(item.id) === current.priority_id)
              ? current.priority_id
              : preferredConfigId(prioritiesResponse.items, "high"),
        }));
      } catch (error: unknown) {
        if (!isActive) {
          return;
        }

        const detail = getErrorMessage(error, "Nao foi possivel carregar a configuracao do chamado.");
        setPageErrorMessage(
          detail === "Nao foi possivel carregar a configuracao do chamado."
            ? detail
            : `Nao foi possivel carregar a configuracao do chamado. ${detail}`,
        );
      } finally {
        if (isActive) {
          setIsLoadingPage(false);
        }
      }
    };

    void loadResources();

    return () => {
      isActive = false;
    };
  }, [reloadKey, token, user]);

  useEffect(() => {
    if (!form.category_id) {
      setSubcategories([]);
      setForm((current) => (current.subcategory_id ? { ...current, subcategory_id: "" } : current));
      return;
    }

    let isActive = true;
    setIsLoadingSubcategories(true);

    listTicketSubcategories(Number(form.category_id), {
      page: 1,
      page_size: 100,
      sort: "display_order_asc",
    })
      .then((response) => {
        if (!isActive) {
          return;
        }

        setSubcategories(response.items);
        setForm((current) => ({
          ...current,
          subcategory_id: response.items.some((item) => String(item.id) === current.subcategory_id)
            ? current.subcategory_id
            : "",
        }));
      })
      .catch(() => {
        if (!isActive) {
          return;
        }

        setSubcategories([]);
        setForm((current) => ({ ...current, subcategory_id: "" }));
      })
      .finally(() => {
        if (isActive) {
          setIsLoadingSubcategories(false);
        }
      });

    return () => {
      isActive = false;
    };
  }, [form.category_id]);

  useEffect(() => {
    if (!form.category_id) {
      setCustomFieldSchema([]);
      setCustomFieldValues({});
      setCustomFieldErrors({});
      setCustomFieldSchemaError(null);
      return;
    }

    let isActive = true;
    setIsLoadingCustomFields(true);
    setCustomFieldSchemaError(null);
    setCustomFieldErrors({});

    getTicketFormSchema(Number(form.category_id), toOptionalConfigId(form.subcategory_id))
      .then((response) => {
        if (!isActive) {
          return;
        }

        setCustomFieldSchema(response.fields);
        setCustomFieldValues(
          Object.fromEntries(
            response.fields
              .filter((field) => field.field_type === "boolean")
              .map((field) => [field.id, false]),
          ),
        );
      })
      .catch((error: unknown) => {
        if (!isActive) {
          return;
        }

        setCustomFieldSchema([]);
        setCustomFieldValues({});
        setCustomFieldSchemaError(getErrorMessage(error, "Nao foi possivel carregar os campos adicionais."));
      })
      .finally(() => {
        if (isActive) {
          setIsLoadingCustomFields(false);
        }
      });

    return () => {
      isActive = false;
    };
  }, [form.category_id, form.subcategory_id]);

  const selectedUnit = useMemo(
    () => units.find((unit) => String(unit.id) === form.unit_id) || null,
    [form.unit_id, units],
  );

  const selectedCategory = useMemo(
    () => categories.find((category) => String(category.id) === form.category_id) || null,
    [categories, form.category_id],
  );

  const selectedPriority = useMemo(
    () => priorities.find((priority) => String(priority.id) === form.priority_id) || null,
    [form.priority_id, priorities],
  );

  const availableTypes = useMemo(() => {
    if (!selectedCategory || selectedCategory.type_ids.length === 0) {
      return ticketTypes;
    }

    return ticketTypes.filter((ticketType) => selectedCategory.type_ids.includes(ticketType.id));
  }, [selectedCategory, ticketTypes]);

  useEffect(() => {
    if (!form.type_id) {
      return;
    }

    if (availableTypes.some((ticketType) => String(ticketType.id) === form.type_id)) {
      return;
    }

    setForm((current) => ({ ...current, type_id: "" }));
  }, [availableTypes, form.type_id]);

  function isCustomFieldEmpty(field: TicketCustomFieldItem, value: string | boolean | undefined) {
    if (field.field_type === "boolean") {
      return typeof value !== "boolean";
    }
    return value === undefined || String(value).trim() === "";
  }

  function validateCustomFields() {
    const nextErrors: Record<number, string> = {};

    customFieldSchema.forEach((field) => {
      if (field.is_required && isCustomFieldEmpty(field, customFieldValues[field.id])) {
        nextErrors[field.id] = "Campo obrigatorio.";
      }
    });

    setCustomFieldErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  }

  function buildCustomFieldPayload() {
    return customFieldSchema
      .filter((field) => field.is_required || !isCustomFieldEmpty(field, customFieldValues[field.id]))
      .map((field) => ({
        field_id: field.id,
        value:
          field.field_type === "boolean"
            ? Boolean(customFieldValues[field.id])
            : String(customFieldValues[field.id] ?? "").trim() || null,
      }));
  }

  function renderCustomField(field: TicketCustomFieldItem) {
    const commonProps = {
      label: field.label,
      required: field.is_required,
      hint: field.help_text || field.description || undefined,
      error: customFieldErrors[field.id],
    };

    if (field.field_type === "textarea") {
      return (
        <Textarea
          key={field.id}
          {...commonProps}
          containerClassName="field field--full"
          value={String(customFieldValues[field.id] ?? "")}
          onChange={(event) =>
            setCustomFieldValues((current) => ({ ...current, [field.id]: event.target.value }))
          }
          placeholder={field.placeholder || undefined}
          rows={4}
        />
      );
    }

    if (field.field_type === "select") {
      const activeOptions = field.options.filter((option) => option.is_active);
      return (
        <Select
          key={field.id}
          {...commonProps}
          value={String(customFieldValues[field.id] ?? "")}
          onChange={(event) =>
            setCustomFieldValues((current) => ({ ...current, [field.id]: event.target.value }))
          }
        >
          <option value="">Selecione</option>
          {activeOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </Select>
      );
    }

    if (field.field_type === "boolean") {
      return (
        <label
          key={field.id}
          className="field field--checkbox rounded-lg border border-slate-200 bg-slate-50 px-3 py-2"
        >
          <input
            checked={Boolean(customFieldValues[field.id])}
            onChange={(event) =>
              setCustomFieldValues((current) => ({ ...current, [field.id]: event.target.checked }))
            }
            type="checkbox"
          />
          <span>
            {field.label}
            {field.is_required ? <strong aria-hidden="true" className="ml-0.5 text-red-500">*</strong> : null}
            {field.help_text ? <small className="block text-xs text-slate-500">{field.help_text}</small> : null}
            {customFieldErrors[field.id] ? (
              <small className="block text-xs font-medium text-red-600">{customFieldErrors[field.id]}</small>
            ) : null}
          </span>
        </label>
      );
    }

    return (
      <Input
        key={field.id}
        {...commonProps}
        type={field.field_type === "number" ? "number" : field.field_type === "date" ? "date" : "text"}
        value={String(customFieldValues[field.id] ?? "")}
        onChange={(event) =>
          setCustomFieldValues((current) => ({ ...current, [field.id]: event.target.value }))
        }
        placeholder={field.placeholder || undefined}
      />
    );
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || isSupplier || !selectedCategory || !selectedPriority) {
      return;
    }

    if (!validateCustomFields()) {
      setSubmitErrorMessage("Preencha os campos adicionais obrigatorios.");
      return;
    }

    setIsSubmitting(true);
    setSubmitErrorMessage(null);
    setCreatedTicket(null);

    try {
      const payload: TicketCreatePayload = {
        unit_id: Number(form.unit_id),
        category: (selectedCategory.legacy_value as TicketCategory | undefined) ?? undefined,
        category_id: Number(form.category_id),
        subcategory_id: toOptionalConfigId(form.subcategory_id),
        type_id: toOptionalConfigId(form.type_id),
        problem_type: form.problem_type.trim(),
        title: form.title.trim(),
        description: form.description.trim(),
        priority: (selectedPriority.legacy_value as TicketPriority | undefined) ?? undefined,
        priority_id: Number(form.priority_id),
        severity: form.severity,
        operational_impact: form.operational_impact.trim() || null,
        fuel_nozzles_stopped: toOptionalInteger(form.fuel_nozzles_stopped),
        estimated_daily_loss: toOptionalDecimal(form.estimated_daily_loss),
        estimated_cost: toOptionalDecimal(form.estimated_cost),
        requires_approval: form.requires_approval,
        custom_fields: buildCustomFieldPayload(),
      };

      const response = await createTicket(token, payload);
      setCreatedTicket(response);
      setForm((current) => ({
        ...initialForm,
        unit_id: isManager ? current.unit_id : "",
        category_id: preferredConfigId(categories, "fuel_pump"),
        priority_id: preferredConfigId(priorities, "high"),
      }));
    } catch (error: unknown) {
      setSubmitErrorMessage(getErrorMessage(error, "Nao foi possivel abrir o chamado."));
    } finally {
      setIsSubmitting(false);
    }
  }

  if (isSupplier) {
    return (
      <section className="page">
        <PageHeader
          eyebrow="Chamados"
          title="Abertura indisponivel para este perfil"
          description="Fornecedores nao podem abrir chamados nesta fase. A validacao definitiva permanece no backend."
        />
        <ErrorState description="Seu perfil atual nao possui permissao para criar chamados." />
      </section>
    );
  }

  const hasActiveConfiguration = categories.length > 0 && priorities.length > 0;

  return (
    <section className="page">
      <PageHeader
        eyebrow="Abertura de chamados"
        title="Novo chamado critico"
        description="Registro inicial do incidente com unidade, impacto operacional e perda estimada."
        actions={
          <Link className="ui-button ui-button--primary button-primary--link" to="/tickets">
            Ver chamados
          </Link>
        }
      />

      {createdTicket ? (
        <section className="state-card state-card--success">
          <strong>Chamado criado com sucesso.</strong>
          <p>
            Numero gerado: <strong>{createdTicket.ticket_number}</strong>.
          </p>
          <Link className="button-link" to={`/tickets/${createdTicket.id}`}>
            Abrir detalhe do chamado
          </Link>
        </section>
      ) : null}

      {pageErrorMessage ? (
        <ErrorState
          description={pageErrorMessage}
          onRetry={() => setReloadKey((current) => current + 1)}
        />
      ) : null}

      {submitErrorMessage ? <ErrorState description={submitErrorMessage} /> : null}

      {isLoadingPage ? (
        <LoadingState
          title="Carregando configuracoes do chamado"
          description="Buscando categorias, tipos, prioridades e unidades disponiveis."
        />
      ) : null}

      {!isLoadingPage && !pageErrorMessage && !hasActiveConfiguration ? (
        <EmptyState
          title="Configuracao de chamados indisponivel"
          description="Nao existem categorias e prioridades ativas suficientes para abrir um chamado agora."
          action={
            <Link className="ui-button ui-button--secondary" to="/settings/tickets">
              Revisar configuracoes
            </Link>
          }
        />
      ) : null}

      {!isLoadingPage && !pageErrorMessage && hasActiveConfiguration ? (
        <section className="panel panel--stack">
          <div className="ticket-summary">
            <div>
              <p className="eyebrow">Escopo desta fase</p>
              <h3>Abertura protegida por perfil</h3>
              <p>
                O chamado nasce com status inicial `open`, numero unico e historico de abertura criado no backend.
              </p>
            </div>
            <div className="ticket-summary__meta">
              <Badge tone="info">Token obrigatorio</Badge>
              {selectedUnit ? <Badge tone="success">{unitLabel(selectedUnit)}</Badge> : null}
            </div>
          </div>

          <form className="form-grid" onSubmit={handleSubmit}>
            <div className="ticket-grid">
              <Select
                label="Unidade"
                value={form.unit_id}
                onChange={(event) => setForm((current) => ({ ...current, unit_id: event.target.value }))}
                disabled={isLoadingPage || isManager}
                required
              >
                <option value="">{isLoadingPage ? "Carregando..." : "Selecione"}</option>
                {units.map((unit) => (
                  <option key={unit.id} value={unit.id}>
                    {unitLabel(unit)}
                  </option>
                ))}
              </Select>

              <Select
                label="Categoria"
                aria-label="Categoria"
                value={form.category_id}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    category_id: event.target.value,
                    subcategory_id: "",
                  }))
                }
                required
              >
                <option value="">Selecione</option>
                {categories.map((category) => (
                  <option key={category.id} value={category.id}>
                    {category.name}
                  </option>
                ))}
              </Select>

              <Select
                label="Subcategoria"
                aria-label="Subcategoria"
                value={form.subcategory_id}
                onChange={(event) =>
                  setForm((current) => ({ ...current, subcategory_id: event.target.value }))
                }
                disabled={!form.category_id || isLoadingSubcategories || subcategories.length === 0}
                hint={
                  !form.category_id
                    ? "Selecione uma categoria para carregar as subcategorias."
                    : isLoadingSubcategories
                      ? "Carregando subcategorias ativas."
                      : subcategories.length === 0
                        ? "Nenhuma subcategoria ativa para esta categoria."
                        : undefined
                }
              >
                <option value="">
                  {!form.category_id
                    ? "Selecione uma categoria"
                    : isLoadingSubcategories
                      ? "Carregando..."
                      : subcategories.length === 0
                        ? "Sem subcategorias ativas"
                        : "Selecione"}
                </option>
                {subcategories.map((subcategory) => (
                  <option key={subcategory.id} value={subcategory.id}>
                    {subcategory.name}
                  </option>
                ))}
              </Select>

              <Select
                label="Tipo de chamado"
                value={form.type_id}
                onChange={(event) => setForm((current) => ({ ...current, type_id: event.target.value }))}
                disabled={availableTypes.length === 0}
                hint={
                  selectedCategory && availableTypes.length === 0
                    ? "Nenhum tipo ativo permitido para a categoria atual."
                    : undefined
                }
              >
                <option value="">{availableTypes.length === 0 ? "Sem tipos ativos" : "Selecione"}</option>
                {availableTypes.map((ticketType) => (
                  <option key={ticketType.id} value={ticketType.id}>
                    {ticketType.name}
                  </option>
                ))}
              </Select>

              <Input
                label="Tipo do problema"
                containerClassName="field field--full"
                value={form.problem_type}
                onChange={(event) => setForm((current) => ({ ...current, problem_type: event.target.value }))}
                placeholder="Ex.: Falha de pressao na linha principal"
                required
              />

              <Input
                label="Titulo"
                containerClassName="field field--full"
                value={form.title}
                onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))}
                placeholder="Resumo objetivo do incidente"
                required
              />

              <Textarea
                label="Descricao"
                containerClassName="field field--full"
                value={form.description}
                onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))}
                placeholder="Descreva o problema, contexto operacional e risco atual."
                rows={5}
                required
              />

              <Select
                label="Prioridade"
                value={form.priority_id}
                onChange={(event) =>
                  setForm((current) => ({ ...current, priority_id: event.target.value }))
                }
                required
              >
                <option value="">Selecione</option>
                {priorities.map((priority) => (
                  <option key={priority.id} value={priority.id}>
                    {priority.name}
                  </option>
                ))}
              </Select>

              <Select
                label="Severidade"
                value={form.severity}
                onChange={(event) =>
                  setForm((current) => ({ ...current, severity: event.target.value as TicketSeverity }))
                }
              >
                {severityOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </Select>

              <Textarea
                label="Impacto operacional"
                containerClassName="field field--full"
                value={form.operational_impact}
                onChange={(event) => setForm((current) => ({ ...current, operational_impact: event.target.value }))}
                placeholder="Ex.: Pista 2 parada, fila crescente, risco de perda de venda."
                rows={3}
              />

              <Input
                label="Bicos parados"
                type="number"
                min="0"
                value={form.fuel_nozzles_stopped}
                onChange={(event) =>
                  setForm((current) => ({ ...current, fuel_nozzles_stopped: event.target.value }))
                }
                placeholder="0"
              />

              <Input
                label="Perda estimada diaria"
                type="number"
                min="0"
                step="0.01"
                value={form.estimated_daily_loss}
                onChange={(event) =>
                  setForm((current) => ({ ...current, estimated_daily_loss: event.target.value }))
                }
                placeholder="1500.00"
              />

              <Input
                label="Custo estimado"
                type="number"
                min="0"
                step="0.01"
                value={form.estimated_cost}
                onChange={(event) => setForm((current) => ({ ...current, estimated_cost: event.target.value }))}
                placeholder="8000.00"
              />

              <label className="field field--checkbox">
                <input
                  checked={form.requires_approval}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, requires_approval: event.target.checked }))
                  }
                  type="checkbox"
                />
                <span>Exige aprovacao futura</span>
              </label>
            </div>

            <section className="field field--full rounded-2xl border border-slate-200 bg-slate-50/70 p-4">
              <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="eyebrow">Informacoes adicionais</p>
                  <h3 className="m-0 text-base font-semibold text-slate-900">Campos da classificacao</h3>
                  <p className="mt-1 text-sm text-slate-500">
                    Campos carregados conforme categoria e subcategoria selecionadas.
                  </p>
                </div>
                {isLoadingCustomFields ? <Badge tone="info">Carregando</Badge> : null}
              </div>

              {customFieldSchemaError ? <ErrorState description={customFieldSchemaError} /> : null}

              {!isLoadingCustomFields && !customFieldSchemaError && customFieldSchema.length === 0 ? (
                <EmptyState
                  title="Sem campos adicionais"
                  description="Esta classificacao nao possui informacoes extras configuradas."
                />
              ) : null}

              {!customFieldSchemaError && customFieldSchema.length > 0 ? (
                <div className="ticket-grid">{customFieldSchema.map((field) => renderCustomField(field))}</div>
              ) : null}
            </section>

            <div className="form-actions">
              <Button
                variant="primary"
                type="submit"
                disabled={isSubmitting || isLoadingPage || !form.unit_id || !form.category_id || !form.priority_id}
              >
                {isSubmitting ? "Criando chamado..." : "Criar chamado"}
              </Button>
            </div>
          </form>
        </section>
      ) : null}
    </section>
  );
}
