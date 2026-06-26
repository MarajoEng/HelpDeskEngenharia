import { type FormEvent, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";

import {
  createTicketCategory,
  createTicketCustomField,
  createTicketPriority,
  createTicketStatus,
  createTicketStatusTransition,
  createTicketSubcategory,
  createTicketType,
  listAdminTicketCategories,
  listAdminTicketCustomFields,
  listAdminTicketPriorities,
  listAdminTicketStatuses,
  listAdminTicketStatusTransitions,
  listAdminTicketSubcategories,
  listAdminTicketTypes,
  updateTicketCategory,
  updateTicketCustomField,
  updateTicketPriority,
  updateTicketStatus,
  updateTicketStatusTransition,
  updateTicketSubcategory,
  updateTicketType,
} from "../api/ticketConfigurationApi";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import EmptyState from "../components/ui/EmptyState";
import ErrorState from "../components/ui/ErrorState";
import FilterBar from "../components/ui/FilterBar";
import Input from "../components/ui/Input";
import LoadingState from "../components/ui/LoadingState";
import Modal from "../components/ui/Modal";
import PageHeader from "../components/ui/PageHeader";
import Pagination from "../components/ui/Pagination";
import Select from "../components/ui/Select";
import Table from "../components/ui/Table";
import Textarea from "../components/ui/Textarea";
import { useAuth } from "../hooks/useAuth";
import type {
  TicketCategoryItem,
  TicketCategoryListResponse,
  TicketCategoryPayload,
  TicketConfigurationFilters,
  TicketCustomFieldFilters,
  TicketCustomFieldItem,
  TicketCustomFieldListResponse,
  TicketCustomFieldOption,
  TicketCustomFieldPayload,
  TicketCustomFieldType,
  TicketPriorityItem,
  TicketPriorityListResponse,
  TicketPriorityPayload,
  TicketStatusItem,
  TicketStatusListResponse,
  TicketStatusPayload,
  TicketStatusTransitionItem,
  TicketStatusTransitionListResponse,
  TicketStatusTransitionPayload,
  TicketSubcategoryFilters,
  TicketSubcategoryItem,
  TicketSubcategoryListResponse,
  TicketSubcategoryPayload,
  TicketTypeItem,
  TicketTypeListResponse,
  TicketTypePayload,
} from "../types/ticketConfiguration";
import { getErrorMessage } from "../utils/messages";

type TicketSettingsTabId = "categories" | "subcategories" | "types" | "priorities" | "workflow" | "custom_fields";

type PaginatedState<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
};

type CategoryFormState = {
  name: string;
  description: string;
  is_active: boolean;
  display_order: string;
  requires_attachment: boolean;
  requires_location: boolean;
  type_ids: number[];
};

type SubcategoryFormState = {
  category_id: string;
  name: string;
  description: string;
  is_active: boolean;
  display_order: string;
};

type TypeFormState = {
  name: string;
  description: string;
  is_active: boolean;
  display_order: string;
};

type PriorityFormState = {
  name: string;
  description: string;
  color: string;
  weight: string;
  sla_hours: string;
  requires_reason: boolean;
  is_active: boolean;
  display_order: string;
};

type StatusFormState = {
  name: string;
  legacy_value: string;
  description: string;
  color: string;
  is_initial: boolean;
  is_final: boolean;
  pauses_sla: boolean;
  allows_reopen: boolean;
  is_active: boolean;
  display_order: string;
};

type TransitionFormState = {
  from_status_id: string;
  to_status_id: string;
  requires_comment: boolean;
  requires_attachment: boolean;
  allowed_roles: string;
  is_active: boolean;
};

type CustomFieldFormState = {
  category_id: string;
  subcategory_id: string;
  name: string;
  label: string;
  description: string;
  field_type: TicketCustomFieldType;
  is_required: boolean;
  is_active: boolean;
  display_order: string;
  placeholder: string;
  help_text: string;
  options_text: string;
};

const settingsTabs: Array<{ id: TicketSettingsTabId; label: string }> = [
  { id: "categories", label: "Categorias" },
  { id: "subcategories", label: "Subcategorias" },
  { id: "types", label: "Tipos de chamado" },
  { id: "priorities", label: "Prioridades" },
  { id: "workflow", label: "Status e fluxo" },
  { id: "custom_fields", label: "Campos personalizados" },
];

const emptyCategoryState: PaginatedState<TicketCategoryItem> = {
  items: [],
  total: 0,
  page: 1,
  page_size: 10,
  pages: 0,
};

const emptySubcategoryState: PaginatedState<TicketSubcategoryItem> = {
  items: [],
  total: 0,
  page: 1,
  page_size: 10,
  pages: 0,
};

const emptyTypeState: PaginatedState<TicketTypeItem> = {
  items: [],
  total: 0,
  page: 1,
  page_size: 10,
  pages: 0,
};

const emptyPriorityState: PaginatedState<TicketPriorityItem> = {
  items: [],
  total: 0,
  page: 1,
  page_size: 10,
  pages: 0,
};

const emptyCustomFieldState: PaginatedState<TicketCustomFieldItem> = {
  items: [],
  total: 0,
  page: 1,
  page_size: 10,
  pages: 0,
};

const emptyStatusState: PaginatedState<TicketStatusItem> = {
  items: [],
  total: 0,
  page: 1,
  page_size: 50,
  pages: 0,
};

const emptyTransitionState: PaginatedState<TicketStatusTransitionItem> = {
  items: [],
  total: 0,
  page: 1,
  page_size: 100,
  pages: 0,
};

const initialCategoryFilters: TicketConfigurationFilters = {
  page: 1,
  page_size: 10,
  search: "",
  is_active: "",
};

const initialSubcategoryFilters: TicketSubcategoryFilters = {
  page: 1,
  page_size: 10,
  search: "",
  is_active: "",
  category_id: "",
};

const initialTypeFilters: TicketConfigurationFilters = {
  page: 1,
  page_size: 10,
  search: "",
  is_active: "",
};

const initialPriorityFilters: TicketConfigurationFilters = {
  page: 1,
  page_size: 10,
  search: "",
  is_active: "",
};

const initialCustomFieldFilters: TicketCustomFieldFilters = {
  page: 1,
  page_size: 10,
  search: "",
  is_active: "",
  category_id: "",
  subcategory_id: "",
};

const initialStatusFilters: TicketConfigurationFilters = {
  page: 1,
  page_size: 50,
  search: "",
  is_active: "",
};

const initialCategoryForm: CategoryFormState = {
  name: "",
  description: "",
  is_active: true,
  display_order: "0",
  requires_attachment: false,
  requires_location: false,
  type_ids: [],
};

const initialSubcategoryForm: SubcategoryFormState = {
  category_id: "",
  name: "",
  description: "",
  is_active: true,
  display_order: "0",
};

const initialTypeForm: TypeFormState = {
  name: "",
  description: "",
  is_active: true,
  display_order: "0",
};

const initialPriorityForm: PriorityFormState = {
  name: "",
  description: "",
  color: "#0f766e",
  weight: "10",
  sla_hours: "24",
  requires_reason: false,
  is_active: true,
  display_order: "0",
};

const initialCustomFieldForm: CustomFieldFormState = {
  category_id: "",
  subcategory_id: "",
  name: "",
  label: "",
  description: "",
  field_type: "text",
  is_required: false,
  is_active: true,
  display_order: "0",
  placeholder: "",
  help_text: "",
  options_text: "",
};

const initialStatusForm: StatusFormState = {
  name: "",
  legacy_value: "",
  description: "",
  color: "#0f766e",
  is_initial: false,
  is_final: false,
  pauses_sla: false,
  allows_reopen: false,
  is_active: true,
  display_order: "0",
};

const initialTransitionForm: TransitionFormState = {
  from_status_id: "",
  to_status_id: "",
  requires_comment: true,
  requires_attachment: false,
  allowed_roles: "",
  is_active: true,
};

function parseTab(value: string | null): TicketSettingsTabId {
  if (
    value === "categories" ||
    value === "subcategories" ||
    value === "types" ||
    value === "priorities" ||
    value === "workflow" ||
    value === "custom_fields"
  ) {
    return value;
  }
  return "categories";
}

function parseStatusValue(value: string): boolean | "" {
  if (value === "true") return true;
  if (value === "false") return false;
  return "";
}

function toOptionalString(value: string) {
  const normalized = value.trim();
  return normalized ? normalized : null;
}

function toNumberValue(value: string, fallback = 0) {
  const numericValue = Number(value);
  return Number.isFinite(numericValue) ? numericValue : fallback;
}

function statusBadge(isActive: boolean) {
  return <Badge tone={isActive ? "success" : "neutral"}>{isActive ? "Ativo" : "Inativo"}</Badge>;
}

function getTypeLabels(typeIds: number[], types: TicketTypeItem[]) {
  if (typeIds.length === 0) {
    return "Sem vinculo";
  }

  const names = typeIds
    .map((typeId) => types.find((item) => item.id === typeId)?.name)
    .filter((value): value is string => Boolean(value));

  return names.length > 0 ? names.join(", ") : "Sem vinculo";
}

function customFieldTypeLabel(type: TicketCustomFieldType) {
  const labels: Record<TicketCustomFieldType, string> = {
    text: "Texto curto",
    textarea: "Texto longo",
    number: "Numero",
    boolean: "Sim/Nao",
    select: "Selecao",
    date: "Data",
  };
  return labels[type];
}

function buildStatusPayload(form: StatusFormState): TicketStatusPayload {
  return {
    name: form.name.trim(),
    legacy_value: toOptionalString(form.legacy_value),
    description: toOptionalString(form.description),
    color: form.color.trim(),
    is_initial: form.is_initial,
    is_final: form.is_final,
    pauses_sla: form.pauses_sla,
    allows_reopen: form.allows_reopen,
    is_active: form.is_active,
    display_order: toNumberValue(form.display_order),
  };
}

function buildTransitionPayload(form: TransitionFormState): TicketStatusTransitionPayload {
  const allowedRoles = form.allowed_roles
    .split(",")
    .map((role) => role.trim())
    .filter(Boolean);

  return {
    from_status_id: Number(form.from_status_id),
    to_status_id: Number(form.to_status_id),
    requires_comment: form.requires_comment,
    requires_attachment: form.requires_attachment,
    allowed_roles_json: allowedRoles.length > 0 ? allowedRoles : null,
    is_active: form.is_active,
  };
}

function formatOptionsText(options: TicketCustomFieldOption[]) {
  return options.map((option) => `${option.label}|${option.value}`).join("\n");
}

function parseOptionsText(optionsText: string): TicketCustomFieldOption[] {
  return optionsText
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line, index) => {
      const [rawLabel, rawValue] = line.split("|");
      const label = rawLabel.trim();
      return {
        label,
        value: (rawValue || rawLabel).trim(),
        display_order: index,
        is_active: true,
      };
    });
}

function TicketCategoriesSection({
  token,
  typeOptions,
  onReferencesChanged,
}: {
  token: string;
  typeOptions: TicketTypeItem[];
  onReferencesChanged: () => Promise<void>;
}) {
  const [filters, setFilters] = useState<TicketConfigurationFilters>(initialCategoryFilters);
  const [data, setData] = useState<TicketCategoryListResponse>(emptyCategoryState);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<TicketCategoryItem | null>(null);
  const [form, setForm] = useState<CategoryFormState>(initialCategoryForm);
  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function loadData() {
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const response = await listAdminTicketCategories(token, filters);
      setData(response);
    } catch (error: unknown) {
      setErrorMessage(getErrorMessage(error, "Nao foi possivel carregar as categorias."));
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadData();
  }, [token, filters.page, filters.page_size, filters.search, filters.is_active, filters.sort]);

  function openCreateModal() {
    setEditingItem(null);
    setForm(initialCategoryForm);
    setFormError(null);
    setIsModalOpen(true);
  }

  function openEditModal(item: TicketCategoryItem) {
    setEditingItem(item);
    setForm({
      name: item.name,
      description: item.description || "",
      is_active: item.is_active,
      display_order: String(item.display_order),
      requires_attachment: item.requires_attachment,
      requires_location: item.requires_location,
      type_ids: item.type_ids,
    });
    setFormError(null);
    setIsModalOpen(true);
  }

  function closeModal() {
    setIsModalOpen(false);
    setEditingItem(null);
    setFormError(null);
  }

  function toggleType(typeId: number) {
    setForm((current) => ({
      ...current,
      type_ids: current.type_ids.includes(typeId)
        ? current.type_ids.filter((item) => item !== typeId)
        : [...current.type_ids, typeId].sort((left, right) => left - right),
    }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setFormError(null);

    const payload: TicketCategoryPayload = {
      name: form.name.trim(),
      description: toOptionalString(form.description),
      is_active: form.is_active,
      display_order: toNumberValue(form.display_order),
      requires_attachment: form.requires_attachment,
      requires_location: form.requires_location,
      type_ids: form.type_ids,
    };

    try {
      if (editingItem) {
        await updateTicketCategory(token, editingItem.id, payload);
      } else {
        await createTicketCategory(token, payload);
      }
      closeModal();
      await Promise.all([loadData(), onReferencesChanged()]);
    } catch (error: unknown) {
      setFormError(getErrorMessage(error, "Nao foi possivel salvar a categoria."));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="space-y-6">
      <div className="flex justify-end">
        <Button variant="primary" type="button" onClick={openCreateModal}>
          Nova categoria
        </Button>
      </div>

      <section className="panel">
        <FilterBar columns={2}>
          <Input
            label="Busca"
            value={filters.search || ""}
            onChange={(event) => setFilters((current) => ({ ...current, page: 1, search: event.target.value }))}
            placeholder="Nome ou descricao"
          />

          <Select
            label="Status"
            value={String(filters.is_active ?? "")}
            onChange={(event) =>
              setFilters((current) => ({
                ...current,
                page: 1,
                is_active: parseStatusValue(event.target.value),
              }))
            }
          >
            <option value="">Todos</option>
            <option value="true">Ativos</option>
            <option value="false">Inativos</option>
          </Select>
        </FilterBar>

        {isLoading ? <LoadingState title="Carregando categorias" /> : null}
        {!isLoading && errorMessage ? <ErrorState description={errorMessage} /> : null}
        {!isLoading && !errorMessage && data.items.length === 0 ? (
          <EmptyState
            title="Nenhuma categoria encontrada"
            description="Cadastre categorias para substituir a manutencao de listas fixas no frontend."
          />
        ) : null}

        {!isLoading && !errorMessage && data.items.length > 0 ? (
          <>
            <Table minWidth={980}>
              <thead>
                <tr>
                  <th>Nome</th>
                  <th>Tipos vinculados</th>
                  <th>Exigencias</th>
                  <th>Ordem</th>
                  <th>Status</th>
                  <th>Acoes</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((item) => (
                  <tr key={item.id}>
                    <td>
                      <div className="space-y-1">
                        <strong className="block text-slate-900">{item.name}</strong>
                        <span className="block max-w-[360px] truncate text-xs text-slate-500" title={item.description || "Sem descricao informada."}>{item.description || "Sem descricao informada."}</span>
                      </div>
                    </td>
                    <td className="text-sm text-slate-600">{getTypeLabels(item.type_ids, typeOptions)}</td>
                    <td className="text-sm text-slate-600">
                      {item.requires_attachment ? "Anexo" : "Sem anexo"} · {item.requires_location ? "Local obrigatorio" : "Local opcional"}
                    </td>
                    <td>{item.display_order}</td>
                    <td>{statusBadge(item.is_active)}</td>
                    <td>
                      <button className="ui-link-button" type="button" onClick={() => openEditModal(item)}>
                        Editar
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>

            <Pagination
              total={data.total}
              label="categoria(s)"
              page={data.page}
              pages={data.pages}
              onPrevious={() => setFilters((current) => ({ ...current, page: Math.max(1, (current.page || 1) - 1) }))}
              onNext={() => setFilters((current) => ({ ...current, page: (current.page || 1) + 1 }))}
            />
          </>
        ) : null}
      </section>

      {isModalOpen ? (
        <Modal
          title={editingItem ? "Editar categoria" : "Nova categoria"}
          subtitle="Configura os grupos principais usados pelos chamados."
          onClose={closeModal}
        >
          <form className="form-grid" onSubmit={handleSubmit}>
            <Input
              label="Nome"
              value={form.name}
              onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
              required
            />
            <Input
              label="Ordem"
              type="number"
              min={0}
              value={form.display_order}
              onChange={(event) => setForm((current) => ({ ...current, display_order: event.target.value }))}
              required
            />

            <Textarea
              label="Descricao"
              containerClassName="field field--full"
              value={form.description}
              onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))}
              rows={4}
            />

            <div className="field field--full rounded-xl border border-slate-200 bg-slate-50 p-4">
              <div className="mb-3 space-y-1">
                <p className="text-sm font-medium text-slate-700">Tipos vinculados</p>
                <p className="text-xs text-slate-500">Selecione quais tipos de chamado podem ser usados nesta categoria.</p>
              </div>
              <div className="grid gap-2 sm:grid-cols-2">
                {typeOptions.map((item) => (
                  <label
                    key={item.id}
                    className="flex items-center gap-3 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700"
                  >
                    <input
                      type="checkbox"
                      checked={form.type_ids.includes(item.id)}
                      onChange={() => toggleType(item.id)}
                    />
                    <span>{item.name}</span>
                    {!item.is_active ? <Badge tone="neutral">Inativo</Badge> : null}
                  </label>
                ))}
              </div>
            </div>

            <div className="field field--full grid gap-3 sm:grid-cols-3">
              <label className="flex items-center gap-2 text-sm text-slate-700">
                <input
                  type="checkbox"
                  checked={form.requires_attachment}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, requires_attachment: event.target.checked }))
                  }
                />
                Exigir anexo
              </label>
              <label className="flex items-center gap-2 text-sm text-slate-700">
                <input
                  type="checkbox"
                  checked={form.requires_location}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, requires_location: event.target.checked }))
                  }
                />
                Exigir localizacao
              </label>
              <label className="flex items-center gap-2 text-sm text-slate-700">
                <input
                  type="checkbox"
                  checked={form.is_active}
                  onChange={(event) => setForm((current) => ({ ...current, is_active: event.target.checked }))}
                />
                Registro ativo
              </label>
            </div>

            {formError ? <ErrorState description={formError} /> : null}

            <div className="field field--full flex justify-end gap-3">
              <Button variant="secondary" type="button" onClick={closeModal} disabled={isSubmitting}>
                Cancelar
              </Button>
              <Button variant="primary" type="submit" disabled={isSubmitting}>
                {isSubmitting ? "Salvando..." : editingItem ? "Salvar ajustes" : "Criar categoria"}
              </Button>
            </div>
          </form>
        </Modal>
      ) : null}
    </section>
  );
}

function TicketSubcategoriesSection({
  token,
  categoryOptions,
}: {
  token: string;
  categoryOptions: TicketCategoryItem[];
}) {
  const [filters, setFilters] = useState<TicketSubcategoryFilters>(initialSubcategoryFilters);
  const [data, setData] = useState<TicketSubcategoryListResponse>(emptySubcategoryState);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<TicketSubcategoryItem | null>(null);
  const [form, setForm] = useState<SubcategoryFormState>(initialSubcategoryForm);
  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function loadData() {
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const response = await listAdminTicketSubcategories(token, filters);
      setData(response);
    } catch (error: unknown) {
      setErrorMessage(getErrorMessage(error, "Nao foi possivel carregar as subcategorias."));
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadData();
  }, [token, filters.page, filters.page_size, filters.search, filters.is_active, filters.category_id, filters.sort]);

  function openCreateModal() {
    setEditingItem(null);
    setForm(initialSubcategoryForm);
    setFormError(null);
    setIsModalOpen(true);
  }

  function openEditModal(item: TicketSubcategoryItem) {
    setEditingItem(item);
    setForm({
      category_id: String(item.category_id),
      name: item.name,
      description: item.description || "",
      is_active: item.is_active,
      display_order: String(item.display_order),
    });
    setFormError(null);
    setIsModalOpen(true);
  }

  function closeModal() {
    setIsModalOpen(false);
    setEditingItem(null);
    setFormError(null);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setFormError(null);

    const payload: TicketSubcategoryPayload = {
      category_id: Number(form.category_id),
      name: form.name.trim(),
      description: toOptionalString(form.description),
      is_active: form.is_active,
      display_order: toNumberValue(form.display_order),
    };

    try {
      if (editingItem) {
        await updateTicketSubcategory(token, editingItem.id, payload);
      } else {
        await createTicketSubcategory(token, payload);
      }
      closeModal();
      await loadData();
    } catch (error: unknown) {
      setFormError(getErrorMessage(error, "Nao foi possivel salvar a subcategoria."));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="space-y-6">
      <div className="flex justify-end">
        <Button variant="primary" type="button" onClick={openCreateModal}>
          Nova subcategoria
        </Button>
      </div>

      <section className="panel">
        <FilterBar columns={3}>
          <Input
            label="Busca"
            value={filters.search || ""}
            onChange={(event) => setFilters((current) => ({ ...current, page: 1, search: event.target.value }))}
            placeholder="Nome ou descricao"
          />

          <Select
            label="Categoria"
            value={String(filters.category_id ?? "")}
            onChange={(event) =>
              setFilters((current) => ({
                ...current,
                page: 1,
                category_id: event.target.value ? Number(event.target.value) : "",
              }))
            }
          >
            <option value="">Todas</option>
            {categoryOptions.map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </Select>

          <Select
            label="Status"
            value={String(filters.is_active ?? "")}
            onChange={(event) =>
              setFilters((current) => ({
                ...current,
                page: 1,
                is_active: parseStatusValue(event.target.value),
              }))
            }
          >
            <option value="">Todos</option>
            <option value="true">Ativos</option>
            <option value="false">Inativos</option>
          </Select>
        </FilterBar>

        {isLoading ? <LoadingState title="Carregando subcategorias" /> : null}
        {!isLoading && errorMessage ? <ErrorState description={errorMessage} /> : null}
        {!isLoading && !errorMessage && data.items.length === 0 ? (
          <EmptyState
            title="Nenhuma subcategoria encontrada"
            description="Use subcategorias para refinar o motivo do chamado sem criar novas telas administrativas."
          />
        ) : null}

        {!isLoading && !errorMessage && data.items.length > 0 ? (
          <>
            <Table minWidth={920}>
              <thead>
                <tr>
                  <th>Nome</th>
                  <th>Categoria</th>
                  <th>Ordem</th>
                  <th>Status</th>
                  <th>Acoes</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((item) => (
                  <tr key={item.id}>
                    <td>
                      <div className="space-y-1">
                        <strong className="block text-slate-900">{item.name}</strong>
                        <span className="block max-w-[360px] truncate text-xs text-slate-500" title={item.description || "Sem descricao informada."}>{item.description || "Sem descricao informada."}</span>
                      </div>
                    </td>
                    <td>{item.category_name}</td>
                    <td>{item.display_order}</td>
                    <td>{statusBadge(item.is_active)}</td>
                    <td>
                      <button className="ui-link-button" type="button" onClick={() => openEditModal(item)}>
                        Editar
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>

            <Pagination
              total={data.total}
              label="subcategoria(s)"
              page={data.page}
              pages={data.pages}
              onPrevious={() => setFilters((current) => ({ ...current, page: Math.max(1, (current.page || 1) - 1) }))}
              onNext={() => setFilters((current) => ({ ...current, page: (current.page || 1) + 1 }))}
            />
          </>
        ) : null}
      </section>

      {isModalOpen ? (
        <Modal
          title={editingItem ? "Editar subcategoria" : "Nova subcategoria"}
          subtitle="Mantem a classificacao detalhada dentro da categoria principal."
          onClose={closeModal}
        >
          <form className="form-grid" onSubmit={handleSubmit}>
            <Select
              label="Categoria"
              value={form.category_id}
              onChange={(event) => setForm((current) => ({ ...current, category_id: event.target.value }))}
              required
            >
              <option value="">Selecione</option>
              {categoryOptions.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </Select>

            <Input
              label="Ordem"
              type="number"
              min={0}
              value={form.display_order}
              onChange={(event) => setForm((current) => ({ ...current, display_order: event.target.value }))}
              required
            />

            <Input
              label="Nome"
              containerClassName="field field--full"
              value={form.name}
              onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
              required
            />

            <Textarea
              label="Descricao"
              containerClassName="field field--full"
              value={form.description}
              onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))}
              rows={4}
            />

            <label className="field field--full flex items-center gap-2 text-sm text-slate-700">
              <input
                type="checkbox"
                checked={form.is_active}
                onChange={(event) => setForm((current) => ({ ...current, is_active: event.target.checked }))}
              />
              Registro ativo
            </label>

            {formError ? <ErrorState description={formError} /> : null}

            <div className="field field--full flex justify-end gap-3">
              <Button variant="secondary" type="button" onClick={closeModal} disabled={isSubmitting}>
                Cancelar
              </Button>
              <Button variant="primary" type="submit" disabled={isSubmitting}>
                {isSubmitting ? "Salvando..." : editingItem ? "Salvar ajustes" : "Criar subcategoria"}
              </Button>
            </div>
          </form>
        </Modal>
      ) : null}
    </section>
  );
}

function TicketTypesSection({
  token,
  onReferencesChanged,
}: {
  token: string;
  onReferencesChanged: () => Promise<void>;
}) {
  const [filters, setFilters] = useState<TicketConfigurationFilters>(initialTypeFilters);
  const [data, setData] = useState<TicketTypeListResponse>(emptyTypeState);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<TicketTypeItem | null>(null);
  const [form, setForm] = useState<TypeFormState>(initialTypeForm);
  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function loadData() {
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const response = await listAdminTicketTypes(token, filters);
      setData(response);
    } catch (error: unknown) {
      setErrorMessage(getErrorMessage(error, "Nao foi possivel carregar os tipos de chamado."));
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadData();
  }, [token, filters.page, filters.page_size, filters.search, filters.is_active, filters.sort]);

  function openCreateModal() {
    setEditingItem(null);
    setForm(initialTypeForm);
    setFormError(null);
    setIsModalOpen(true);
  }

  function openEditModal(item: TicketTypeItem) {
    setEditingItem(item);
    setForm({
      name: item.name,
      description: item.description || "",
      is_active: item.is_active,
      display_order: String(item.display_order),
    });
    setFormError(null);
    setIsModalOpen(true);
  }

  function closeModal() {
    setIsModalOpen(false);
    setEditingItem(null);
    setFormError(null);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setFormError(null);

    const payload: TicketTypePayload = {
      name: form.name.trim(),
      description: toOptionalString(form.description),
      is_active: form.is_active,
      display_order: toNumberValue(form.display_order),
    };

    try {
      if (editingItem) {
        await updateTicketType(token, editingItem.id, payload);
      } else {
        await createTicketType(token, payload);
      }
      closeModal();
      await Promise.all([loadData(), onReferencesChanged()]);
    } catch (error: unknown) {
      setFormError(getErrorMessage(error, "Nao foi possivel salvar o tipo de chamado."));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="space-y-6">
      <div className="flex justify-end">
        <Button variant="primary" type="button" onClick={openCreateModal}>
          Novo tipo
        </Button>
      </div>

      <section className="panel">
        <FilterBar columns={2}>
          <Input
            label="Busca"
            value={filters.search || ""}
            onChange={(event) => setFilters((current) => ({ ...current, page: 1, search: event.target.value }))}
            placeholder="Nome ou descricao"
          />

          <Select
            label="Status"
            value={String(filters.is_active ?? "")}
            onChange={(event) =>
              setFilters((current) => ({
                ...current,
                page: 1,
                is_active: parseStatusValue(event.target.value),
              }))
            }
          >
            <option value="">Todos</option>
            <option value="true">Ativos</option>
            <option value="false">Inativos</option>
          </Select>
        </FilterBar>

        {isLoading ? <LoadingState title="Carregando tipos de chamado" /> : null}
        {!isLoading && errorMessage ? <ErrorState description={errorMessage} /> : null}
        {!isLoading && !errorMessage && data.items.length === 0 ? (
          <EmptyState
            title="Nenhum tipo encontrado"
            description="Crie tipos reutilizaveis para evitar acoplamento da classificacao ao codigo."
          />
        ) : null}

        {!isLoading && !errorMessage && data.items.length > 0 ? (
          <>
            <Table minWidth={860}>
              <thead>
                <tr>
                  <th>Nome</th>
                  <th>Descricao</th>
                  <th>Ordem</th>
                  <th>Status</th>
                  <th>Acoes</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((item) => (
                  <tr key={item.id}>
                    <td>{item.name}</td>
                    <td className="max-w-[360px] text-sm text-slate-600"><span className="block truncate" title={item.description || "Sem descricao informada."}>{item.description || "Sem descricao informada."}</span></td>
                    <td>{item.display_order}</td>
                    <td>{statusBadge(item.is_active)}</td>
                    <td>
                      <button className="ui-link-button" type="button" onClick={() => openEditModal(item)}>
                        Editar
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>

            <Pagination
              total={data.total}
              label="tipo(s)"
              page={data.page}
              pages={data.pages}
              onPrevious={() => setFilters((current) => ({ ...current, page: Math.max(1, (current.page || 1) - 1) }))}
              onNext={() => setFilters((current) => ({ ...current, page: (current.page || 1) + 1 }))}
            />
          </>
        ) : null}
      </section>

      {isModalOpen ? (
        <Modal
          title={editingItem ? "Editar tipo de chamado" : "Novo tipo de chamado"}
          subtitle="Define o tipo operacional permitido para cada categoria."
          onClose={closeModal}
        >
          <form className="form-grid" onSubmit={handleSubmit}>
            <Input
              label="Nome"
              value={form.name}
              onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
              required
            />
            <Input
              label="Ordem"
              type="number"
              min={0}
              value={form.display_order}
              onChange={(event) => setForm((current) => ({ ...current, display_order: event.target.value }))}
              required
            />
            <Textarea
              label="Descricao"
              containerClassName="field field--full"
              value={form.description}
              onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))}
              rows={4}
            />
            <label className="field field--full flex items-center gap-2 text-sm text-slate-700">
              <input
                type="checkbox"
                checked={form.is_active}
                onChange={(event) => setForm((current) => ({ ...current, is_active: event.target.checked }))}
              />
              Registro ativo
            </label>

            {formError ? <ErrorState description={formError} /> : null}

            <div className="field field--full flex justify-end gap-3">
              <Button variant="secondary" type="button" onClick={closeModal} disabled={isSubmitting}>
                Cancelar
              </Button>
              <Button variant="primary" type="submit" disabled={isSubmitting}>
                {isSubmitting ? "Salvando..." : editingItem ? "Salvar ajustes" : "Criar tipo"}
              </Button>
            </div>
          </form>
        </Modal>
      ) : null}
    </section>
  );
}

function TicketPrioritiesSection({ token }: { token: string }) {
  const [filters, setFilters] = useState<TicketConfigurationFilters>(initialPriorityFilters);
  const [data, setData] = useState<TicketPriorityListResponse>(emptyPriorityState);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<TicketPriorityItem | null>(null);
  const [form, setForm] = useState<PriorityFormState>(initialPriorityForm);
  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function loadData() {
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const response = await listAdminTicketPriorities(token, filters);
      setData(response);
    } catch (error: unknown) {
      setErrorMessage(getErrorMessage(error, "Nao foi possivel carregar as prioridades."));
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadData();
  }, [token, filters.page, filters.page_size, filters.search, filters.is_active, filters.sort]);

  function openCreateModal() {
    setEditingItem(null);
    setForm(initialPriorityForm);
    setFormError(null);
    setIsModalOpen(true);
  }

  function openEditModal(item: TicketPriorityItem) {
    setEditingItem(item);
    setForm({
      name: item.name,
      description: item.description || "",
      color: item.color,
      weight: String(item.weight),
      sla_hours: String(item.sla_hours),
      requires_reason: item.requires_reason,
      is_active: item.is_active,
      display_order: String(item.display_order),
    });
    setFormError(null);
    setIsModalOpen(true);
  }

  function closeModal() {
    setIsModalOpen(false);
    setEditingItem(null);
    setFormError(null);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setFormError(null);

    const payload: TicketPriorityPayload = {
      name: form.name.trim(),
      description: toOptionalString(form.description),
      color: form.color,
      weight: toNumberValue(form.weight),
      sla_hours: toNumberValue(form.sla_hours, 1),
      requires_reason: form.requires_reason,
      is_active: form.is_active,
      display_order: toNumberValue(form.display_order),
    };

    try {
      if (editingItem) {
        await updateTicketPriority(token, editingItem.id, payload);
      } else {
        await createTicketPriority(token, payload);
      }
      closeModal();
      await loadData();
    } catch (error: unknown) {
      setFormError(getErrorMessage(error, "Nao foi possivel salvar a prioridade."));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="space-y-6">
      <div className="flex justify-end">
        <Button variant="primary" type="button" onClick={openCreateModal}>
          Nova prioridade
        </Button>
      </div>

      <section className="panel">
        <FilterBar columns={2}>
          <Input
            label="Busca"
            value={filters.search || ""}
            onChange={(event) => setFilters((current) => ({ ...current, page: 1, search: event.target.value }))}
            placeholder="Nome ou descricao"
          />

          <Select
            label="Status"
            value={String(filters.is_active ?? "")}
            onChange={(event) =>
              setFilters((current) => ({
                ...current,
                page: 1,
                is_active: parseStatusValue(event.target.value),
              }))
            }
          >
            <option value="">Todos</option>
            <option value="true">Ativos</option>
            <option value="false">Inativos</option>
          </Select>
        </FilterBar>

        {isLoading ? <LoadingState title="Carregando prioridades" /> : null}
        {!isLoading && errorMessage ? <ErrorState description={errorMessage} /> : null}
        {!isLoading && !errorMessage && data.items.length === 0 ? (
          <EmptyState
            title="Nenhuma prioridade encontrada"
            description="Ajuste peso, SLA e obrigatoriedade de justificativa sem depender de constantes fixas."
          />
        ) : null}

        {!isLoading && !errorMessage && data.items.length > 0 ? (
          <>
            <Table minWidth={920}>
              <thead>
                <tr>
                  <th>Nome</th>
                  <th>SLA</th>
                  <th>Peso</th>
                  <th>Regras</th>
                  <th>Status</th>
                  <th>Acoes</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((item) => (
                  <tr key={item.id}>
                    <td>
                      <div className="flex items-center gap-3">
                        <span className="h-3 w-3 rounded-full border border-slate-200" style={{ backgroundColor: item.color }} />
                        <div className="space-y-1">
                          <strong className="block text-slate-900">{item.name}</strong>
                          <span className="block max-w-[360px] truncate text-xs text-slate-500" title={item.description || "Sem descricao informada."}>{item.description || "Sem descricao informada."}</span>
                        </div>
                      </div>
                    </td>
                    <td>{item.sla_hours}h</td>
                    <td>{item.weight}</td>
                    <td className="text-sm text-slate-600">
                      {item.requires_reason ? "Justificativa obrigatoria" : "Justificativa opcional"}
                    </td>
                    <td>{statusBadge(item.is_active)}</td>
                    <td>
                      <button className="ui-link-button" type="button" onClick={() => openEditModal(item)}>
                        Editar
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>

            <Pagination
              total={data.total}
              label="prioridade(s)"
              page={data.page}
              pages={data.pages}
              onPrevious={() => setFilters((current) => ({ ...current, page: Math.max(1, (current.page || 1) - 1) }))}
              onNext={() => setFilters((current) => ({ ...current, page: (current.page || 1) + 1 }))}
            />
          </>
        ) : null}
      </section>

      {isModalOpen ? (
        <Modal
          title={editingItem ? "Editar prioridade" : "Nova prioridade"}
          subtitle="Controla peso, SLA e justificativa obrigatoria do chamado."
          onClose={closeModal}
        >
          <form className="form-grid" onSubmit={handleSubmit}>
            <Input
              label="Nome"
              value={form.name}
              onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
              required
            />
            <Input
              label="Cor"
              type="color"
              value={form.color}
              onChange={(event) => setForm((current) => ({ ...current, color: event.target.value }))}
              required
            />
            <Input
              label="Peso"
              type="number"
              min={0}
              value={form.weight}
              onChange={(event) => setForm((current) => ({ ...current, weight: event.target.value }))}
              required
            />
            <Input
              label="SLA (horas)"
              type="number"
              min={1}
              value={form.sla_hours}
              onChange={(event) => setForm((current) => ({ ...current, sla_hours: event.target.value }))}
              required
            />
            <Input
              label="Ordem"
              type="number"
              min={0}
              value={form.display_order}
              onChange={(event) => setForm((current) => ({ ...current, display_order: event.target.value }))}
              required
            />

            <Textarea
              label="Descricao"
              containerClassName="field field--full"
              value={form.description}
              onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))}
              rows={4}
            />

            <div className="field field--full grid gap-3 sm:grid-cols-2">
              <label className="flex items-center gap-2 text-sm text-slate-700">
                <input
                  type="checkbox"
                  checked={form.requires_reason}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, requires_reason: event.target.checked }))
                  }
                />
                Exigir justificativa
              </label>
              <label className="flex items-center gap-2 text-sm text-slate-700">
                <input
                  type="checkbox"
                  checked={form.is_active}
                  onChange={(event) => setForm((current) => ({ ...current, is_active: event.target.checked }))}
                />
                Registro ativo
              </label>
            </div>

            {formError ? <ErrorState description={formError} /> : null}

            <div className="field field--full flex justify-end gap-3">
              <Button variant="secondary" type="button" onClick={closeModal} disabled={isSubmitting}>
                Cancelar
              </Button>
              <Button variant="primary" type="submit" disabled={isSubmitting}>
                {isSubmitting ? "Salvando..." : editingItem ? "Salvar ajustes" : "Criar prioridade"}
              </Button>
            </div>
          </form>
        </Modal>
      ) : null}
    </section>
  );
}

function TicketCustomFieldsSection({
  token,
  categoryOptions,
}: {
  token: string;
  categoryOptions: TicketCategoryItem[];
}) {
  const [filters, setFilters] = useState<TicketCustomFieldFilters>(initialCustomFieldFilters);
  const [data, setData] = useState<TicketCustomFieldListResponse>(emptyCustomFieldState);
  const [subcategoryOptions, setSubcategoryOptions] = useState<TicketSubcategoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<TicketCustomFieldItem | null>(null);
  const [form, setForm] = useState<CustomFieldFormState>(initialCustomFieldForm);
  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function loadData() {
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const response = await listAdminTicketCustomFields(token, filters);
      setData(response);
    } catch (error: unknown) {
      setErrorMessage(getErrorMessage(error, "Nao foi possivel carregar os campos personalizados."));
    } finally {
      setIsLoading(false);
    }
  }

  async function loadSubcategories(categoryId: string) {
    if (!categoryId) {
      setSubcategoryOptions([]);
      return;
    }

    try {
      const response = await listAdminTicketSubcategories(token, {
        page: 1,
        page_size: 100,
        category_id: Number(categoryId),
        sort: "display_order_asc",
      });
      setSubcategoryOptions(response.items);
    } catch {
      setSubcategoryOptions([]);
    }
  }

  useEffect(() => {
    void loadData();
  }, [
    token,
    filters.page,
    filters.page_size,
    filters.search,
    filters.is_active,
    filters.category_id,
    filters.subcategory_id,
    filters.sort,
  ]);

  useEffect(() => {
    void loadSubcategories(String(filters.category_id || ""));
  }, [token, filters.category_id]);

  function openCreateModal() {
    setEditingItem(null);
    setForm(initialCustomFieldForm);
    setSubcategoryOptions([]);
    setFormError(null);
    setIsModalOpen(true);
  }

  function openEditModal(item: TicketCustomFieldItem) {
    setEditingItem(item);
    setForm({
      category_id: String(item.category_id),
      subcategory_id: item.subcategory_id ? String(item.subcategory_id) : "",
      name: item.name,
      label: item.label,
      description: item.description || "",
      field_type: item.field_type,
      is_required: item.is_required,
      is_active: item.is_active,
      display_order: String(item.display_order),
      placeholder: item.placeholder || "",
      help_text: item.help_text || "",
      options_text: formatOptionsText(item.options),
    });
    void loadSubcategories(String(item.category_id));
    setFormError(null);
    setIsModalOpen(true);
  }

  function closeModal() {
    setIsModalOpen(false);
    setEditingItem(null);
    setFormError(null);
  }

  function updateFormCategory(categoryId: string) {
    setForm((current) => ({ ...current, category_id: categoryId, subcategory_id: "" }));
    void loadSubcategories(categoryId);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setFormError(null);

    const payload: TicketCustomFieldPayload = {
      category_id: Number(form.category_id),
      subcategory_id: form.subcategory_id ? Number(form.subcategory_id) : null,
      name: form.name.trim(),
      label: form.label.trim(),
      description: toOptionalString(form.description),
      field_type: form.field_type,
      is_required: form.is_required,
      is_active: form.is_active,
      display_order: toNumberValue(form.display_order),
      placeholder: toOptionalString(form.placeholder),
      help_text: toOptionalString(form.help_text),
      validation_json: null,
      options: form.field_type === "select" ? parseOptionsText(form.options_text) : [],
    };

    try {
      if (editingItem) {
        await updateTicketCustomField(token, editingItem.id, payload);
      } else {
        await createTicketCustomField(token, payload);
      }
      closeModal();
      await loadData();
    } catch (error: unknown) {
      setFormError(getErrorMessage(error, "Nao foi possivel salvar o campo personalizado."));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="space-y-6">
      <div className="flex justify-end">
        <Button variant="primary" type="button" onClick={openCreateModal}>
          Novo campo
        </Button>
      </div>

      <section className="panel">
        <FilterBar columns={4}>
          <Input
            label="Busca"
            value={filters.search || ""}
            onChange={(event) => setFilters((current) => ({ ...current, page: 1, search: event.target.value }))}
            placeholder="Nome, rotulo ou descricao"
          />

          <Select
            label="Categoria"
            value={String(filters.category_id ?? "")}
            onChange={(event) =>
              setFilters((current) => ({
                ...current,
                page: 1,
                category_id: event.target.value ? Number(event.target.value) : "",
                subcategory_id: "",
              }))
            }
          >
            <option value="">Todas</option>
            {categoryOptions.map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </Select>

          <Select
            label="Subcategoria"
            value={String(filters.subcategory_id ?? "")}
            onChange={(event) =>
              setFilters((current) => ({
                ...current,
                page: 1,
                subcategory_id: event.target.value ? Number(event.target.value) : "",
              }))
            }
            disabled={!filters.category_id || subcategoryOptions.length === 0}
          >
            <option value="">Todas</option>
            {subcategoryOptions.map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </Select>

          <Select
            label="Status"
            value={String(filters.is_active ?? "")}
            onChange={(event) =>
              setFilters((current) => ({
                ...current,
                page: 1,
                is_active: parseStatusValue(event.target.value),
              }))
            }
          >
            <option value="">Todos</option>
            <option value="true">Ativos</option>
            <option value="false">Inativos</option>
          </Select>
        </FilterBar>

        {isLoading ? <LoadingState title="Carregando campos personalizados" /> : null}
        {!isLoading && errorMessage ? <ErrorState description={errorMessage} /> : null}
        {!isLoading && !errorMessage && data.items.length === 0 ? (
          <EmptyState
            title="Nenhum campo personalizado encontrado"
            description="Configure campos extras por categoria ou subcategoria sem criar novas telas."
          />
        ) : null}

        {!isLoading && !errorMessage && data.items.length > 0 ? (
          <>
            <Table minWidth={1040}>
              <thead>
                <tr>
                  <th>Campo</th>
                  <th>Escopo</th>
                  <th>Tipo</th>
                  <th>Regras</th>
                  <th>Ordem</th>
                  <th>Status</th>
                  <th>Acoes</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((item) => (
                  <tr key={item.id}>
                    <td>
                      <div className="space-y-1">
                        <strong className="block max-w-[280px] truncate text-slate-900" title={item.label}>
                          {item.label}
                        </strong>
                        <span className="block max-w-[280px] truncate text-xs text-slate-500" title={item.name}>
                          {item.name}
                        </span>
                      </div>
                    </td>
                    <td className="text-sm text-slate-600">
                      <span className="block max-w-[260px] truncate" title={item.category_name}>
                        {item.category_name}
                      </span>
                      <span className="block max-w-[260px] truncate text-xs text-slate-500" title={item.subcategory_name || "Todas as subcategorias"}>
                        {item.subcategory_name || "Todas as subcategorias"}
                      </span>
                    </td>
                    <td>{customFieldTypeLabel(item.field_type)}</td>
                    <td className="text-sm text-slate-600">
                      {item.is_required ? "Obrigatorio" : "Opcional"}
                      {item.field_type === "select" ? ` · ${item.options.filter((option) => option.is_active).length} opcoes` : ""}
                    </td>
                    <td>{item.display_order}</td>
                    <td>{statusBadge(item.is_active)}</td>
                    <td>
                      <button className="ui-link-button" type="button" onClick={() => openEditModal(item)}>
                        Editar
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>

            <Pagination
              total={data.total}
              label="campo(s)"
              page={data.page}
              pages={data.pages}
              onPrevious={() => setFilters((current) => ({ ...current, page: Math.max(1, (current.page || 1) - 1) }))}
              onNext={() => setFilters((current) => ({ ...current, page: (current.page || 1) + 1 }))}
            />
          </>
        ) : null}
      </section>

      {isModalOpen ? (
        <Modal
          title={editingItem ? "Editar campo personalizado" : "Novo campo personalizado"}
          subtitle="Define perguntas adicionais para uma categoria ou subcategoria especifica."
          onClose={closeModal}
        >
          <form className="form-grid" onSubmit={handleSubmit}>
            <Select
              label="Categoria"
              value={form.category_id}
              onChange={(event) => updateFormCategory(event.target.value)}
              required
            >
              <option value="">Selecione</option>
              {categoryOptions.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </Select>

            <Select
              label="Subcategoria"
              value={form.subcategory_id}
              onChange={(event) => setForm((current) => ({ ...current, subcategory_id: event.target.value }))}
              disabled={!form.category_id || subcategoryOptions.length === 0}
            >
              <option value="">Todas</option>
              {subcategoryOptions.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </Select>

            <Input
              label="Nome tecnico"
              value={form.name}
              onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
              placeholder="ex.: pressao_linha"
              required
            />

            <Input
              label="Rotulo"
              value={form.label}
              onChange={(event) => setForm((current) => ({ ...current, label: event.target.value }))}
              placeholder="Pressao da linha"
              required
            />

            <Select
              label="Tipo"
              value={form.field_type}
              onChange={(event) =>
                setForm((current) => ({ ...current, field_type: event.target.value as TicketCustomFieldType }))
              }
              required
            >
              <option value="text">Texto curto</option>
              <option value="textarea">Texto longo</option>
              <option value="number">Numero</option>
              <option value="boolean">Sim/Nao</option>
              <option value="select">Selecao</option>
              <option value="date">Data</option>
            </Select>

            <Input
              label="Ordem"
              type="number"
              min={0}
              value={form.display_order}
              onChange={(event) => setForm((current) => ({ ...current, display_order: event.target.value }))}
              required
            />

            <Input
              label="Placeholder"
              value={form.placeholder}
              onChange={(event) => setForm((current) => ({ ...current, placeholder: event.target.value }))}
            />

            <Input
              label="Texto de ajuda"
              value={form.help_text}
              onChange={(event) => setForm((current) => ({ ...current, help_text: event.target.value }))}
            />

            <Textarea
              label="Descricao"
              containerClassName="field field--full"
              value={form.description}
              onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))}
              rows={3}
            />

            {form.field_type === "select" ? (
              <Textarea
                label="Opcoes"
                containerClassName="field field--full"
                value={form.options_text}
                onChange={(event) => setForm((current) => ({ ...current, options_text: event.target.value }))}
                hint="Uma opcao por linha. Use Label|valor quando o valor tecnico precisar ser diferente."
                rows={5}
                required
              />
            ) : null}

            <div className="field field--full grid gap-3 sm:grid-cols-2">
              <label className="flex items-center gap-2 text-sm text-slate-700">
                <input
                  type="checkbox"
                  checked={form.is_required}
                  onChange={(event) => setForm((current) => ({ ...current, is_required: event.target.checked }))}
                />
                Campo obrigatorio
              </label>
              <label className="flex items-center gap-2 text-sm text-slate-700">
                <input
                  type="checkbox"
                  checked={form.is_active}
                  onChange={(event) => setForm((current) => ({ ...current, is_active: event.target.checked }))}
                />
                Registro ativo
              </label>
            </div>

            {formError ? <ErrorState description={formError} /> : null}

            <div className="field field--full flex justify-end gap-3">
              <Button variant="secondary" type="button" onClick={closeModal} disabled={isSubmitting}>
                Cancelar
              </Button>
              <Button variant="primary" type="submit" disabled={isSubmitting}>
                {isSubmitting ? "Salvando..." : editingItem ? "Salvar ajustes" : "Criar campo"}
              </Button>
            </div>
          </form>
        </Modal>
      ) : null}
    </section>
  );
}

function TicketWorkflowSection({ token }: { token: string }) {
  const [filters, setFilters] = useState<TicketConfigurationFilters>(initialStatusFilters);
  const [statuses, setStatuses] = useState<TicketStatusListResponse>(emptyStatusState);
  const [transitions, setTransitions] = useState<TicketStatusTransitionListResponse>(emptyTransitionState);
  const [statusForm, setStatusForm] = useState<StatusFormState>(initialStatusForm);
  const [transitionForm, setTransitionForm] = useState<TransitionFormState>(initialTransitionForm);
  const [editingStatus, setEditingStatus] = useState<TicketStatusItem | null>(null);
  const [editingTransition, setEditingTransition] = useState<TicketStatusTransitionItem | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let isActive = true;
    setIsLoading(true);
    setErrorMessage(null);

    Promise.all([
      listAdminTicketStatuses(token, filters),
      listAdminTicketStatusTransitions(token, { page: 1, page_size: 100 }),
    ])
      .then(([statusResponse, transitionResponse]) => {
        if (!isActive) return;
        setStatuses(statusResponse);
        setTransitions(transitionResponse);
      })
      .catch((error: unknown) => {
        if (!isActive) return;
        setErrorMessage(getErrorMessage(error, "Nao foi possivel carregar status e transicoes."));
      })
      .finally(() => {
        if (isActive) setIsLoading(false);
      });

    return () => {
      isActive = false;
    };
  }, [token, filters.page, filters.page_size, filters.search, filters.is_active, reloadKey]);

  function resetStatusForm() {
    setEditingStatus(null);
    setStatusForm(initialStatusForm);
  }

  function resetTransitionForm() {
    setEditingTransition(null);
    setTransitionForm(initialTransitionForm);
  }

  function submitStatus(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const request = editingStatus
      ? updateTicketStatus(token, editingStatus.id, buildStatusPayload(statusForm))
      : createTicketStatus(token, buildStatusPayload(statusForm));

    request
      .then(() => {
        resetStatusForm();
        setReloadKey((current) => current + 1);
      })
      .catch((error: unknown) => setErrorMessage(getErrorMessage(error, "Nao foi possivel salvar o status.")));
  }

  function submitTransition(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const request = editingTransition
      ? updateTicketStatusTransition(token, editingTransition.id, buildTransitionPayload(transitionForm))
      : createTicketStatusTransition(token, buildTransitionPayload(transitionForm));

    request
      .then(() => {
        resetTransitionForm();
        setReloadKey((current) => current + 1);
      })
      .catch((error: unknown) => setErrorMessage(getErrorMessage(error, "Nao foi possivel salvar a transicao.")));
  }

  function startEditStatus(status: TicketStatusItem) {
    setEditingStatus(status);
    setStatusForm({
      name: status.name,
      legacy_value: status.legacy_value ?? "",
      description: status.description ?? "",
      color: status.color,
      is_initial: status.is_initial,
      is_final: status.is_final,
      pauses_sla: status.pauses_sla,
      allows_reopen: status.allows_reopen,
      is_active: status.is_active,
      display_order: String(status.display_order),
    });
  }

  function startEditTransition(transition: TicketStatusTransitionItem) {
    setEditingTransition(transition);
    setTransitionForm({
      from_status_id: String(transition.from_status_id),
      to_status_id: String(transition.to_status_id),
      requires_comment: transition.requires_comment,
      requires_attachment: transition.requires_attachment,
      allowed_roles: (transition.allowed_roles_json ?? []).join(", "),
      is_active: transition.is_active,
    });
  }

  return (
    <div className="space-y-6">
      {errorMessage ? <ErrorState description={errorMessage} /> : null}

      <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <form className="grid gap-4 lg:grid-cols-12" onSubmit={submitStatus}>
          <div className="lg:col-span-3">
            <Input
              label="Nome"
              value={statusForm.name}
              onChange={(event) => setStatusForm((current) => ({ ...current, name: event.target.value }))}
              required
            />
          </div>
          <div className="lg:col-span-2">
            <Input
              label="Legado"
              value={statusForm.legacy_value}
              onChange={(event) => setStatusForm((current) => ({ ...current, legacy_value: event.target.value }))}
              placeholder="open"
            />
          </div>
          <div className="lg:col-span-2">
            <Input
              label="Cor"
              type="color"
              value={statusForm.color}
              onChange={(event) => setStatusForm((current) => ({ ...current, color: event.target.value }))}
            />
          </div>
          <div className="lg:col-span-2">
            <Input
              label="Ordem"
              type="number"
              value={statusForm.display_order}
              onChange={(event) => setStatusForm((current) => ({ ...current, display_order: event.target.value }))}
            />
          </div>
          <div className="lg:col-span-3">
            <Textarea
              label="Descricao"
              value={statusForm.description}
              onChange={(event) => setStatusForm((current) => ({ ...current, description: event.target.value }))}
              rows={2}
            />
          </div>
          <div className="flex flex-wrap gap-4 lg:col-span-9">
            {[
              ["Inicial", "is_initial"],
              ["Final", "is_final"],
              ["Pausa SLA", "pauses_sla"],
              ["Permite reabrir", "allows_reopen"],
              ["Ativo", "is_active"],
            ].map(([label, key]) => (
              <label key={key} className="flex items-center gap-2 text-sm text-slate-700">
                <input
                  type="checkbox"
                  checked={Boolean(statusForm[key as keyof StatusFormState])}
                  onChange={(event) =>
                    setStatusForm((current) => ({ ...current, [key]: event.target.checked }))
                  }
                />
                {label}
              </label>
            ))}
          </div>
          <div className="flex items-end gap-2 lg:col-span-3">
            <Button type="submit">{editingStatus ? "Salvar status" : "Criar status"}</Button>
            {editingStatus ? (
              <Button type="button" variant="secondary" onClick={resetStatusForm}>
                Cancelar
              </Button>
            ) : null}
          </div>
        </form>
      </section>

      <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <form className="grid gap-4 lg:grid-cols-12" onSubmit={submitTransition}>
          <div className="lg:col-span-3">
            <Select
              label="De"
              value={transitionForm.from_status_id}
              onChange={(event) => setTransitionForm((current) => ({ ...current, from_status_id: event.target.value }))}
              required
            >
              <option value="">Selecione</option>
              {statuses.items.map((status) => (
                <option key={status.id} value={status.id}>{status.name}</option>
              ))}
            </Select>
          </div>
          <div className="lg:col-span-3">
            <Select
              label="Para"
              value={transitionForm.to_status_id}
              onChange={(event) => setTransitionForm((current) => ({ ...current, to_status_id: event.target.value }))}
              required
            >
              <option value="">Selecione</option>
              {statuses.items.map((status) => (
                <option key={status.id} value={status.id}>{status.name}</option>
              ))}
            </Select>
          </div>
          <div className="lg:col-span-3">
            <Input
              label="Perfis permitidos"
              value={transitionForm.allowed_roles}
              onChange={(event) => setTransitionForm((current) => ({ ...current, allowed_roles: event.target.value }))}
              placeholder="admin, engineering"
            />
          </div>
          <div className="flex flex-wrap items-end gap-4 lg:col-span-3">
            <label className="flex items-center gap-2 text-sm text-slate-700">
              <input
                type="checkbox"
                checked={transitionForm.requires_comment}
                onChange={(event) =>
                  setTransitionForm((current) => ({ ...current, requires_comment: event.target.checked }))
                }
              />
              Comentario
            </label>
            <label className="flex items-center gap-2 text-sm text-slate-700">
              <input
                type="checkbox"
                checked={transitionForm.requires_attachment}
                onChange={(event) =>
                  setTransitionForm((current) => ({ ...current, requires_attachment: event.target.checked }))
                }
              />
              Anexo
            </label>
            <label className="flex items-center gap-2 text-sm text-slate-700">
              <input
                type="checkbox"
                checked={transitionForm.is_active}
                onChange={(event) =>
                  setTransitionForm((current) => ({ ...current, is_active: event.target.checked }))
                }
              />
              Ativa
            </label>
          </div>
          <div className="flex gap-2 lg:col-span-12">
            <Button type="submit">{editingTransition ? "Salvar transicao" : "Criar transicao"}</Button>
            {editingTransition ? (
              <Button type="button" variant="secondary" onClick={resetTransitionForm}>
                Cancelar
              </Button>
            ) : null}
          </div>
        </form>
      </section>

      {isLoading ? <LoadingState title="Carregando fluxo" description="Atualizando status e transicoes." /> : null}

      {!isLoading ? (
        <div className="grid gap-6 xl:grid-cols-2">
          <section className="rounded-xl border border-slate-200 bg-white shadow-sm">
            <div className="border-b border-slate-100 px-5 py-4">
              <h3 className="text-base font-semibold text-slate-900">Status</h3>
            </div>
            {statuses.items.length === 0 ? (
              <EmptyState title="Ainda nao ha registros" description="Nenhum status configurado." />
            ) : (
              <Table minWidth={760}>
                <thead>
                  <tr>
                    <th>Nome</th>
                    <th>Legado</th>
                    <th>Marcadores</th>
                    <th>Status</th>
                    <th>Acoes</th>
                  </tr>
                </thead>
                <tbody>
                  {statuses.items.map((status) => (
                    <tr key={status.id}>
                      <td>
                        <span className="inline-flex items-center gap-2">
                          <span className="h-3 w-3 rounded-full" style={{ backgroundColor: status.color }} />
                          {status.name}
                        </span>
                      </td>
                      <td>{status.legacy_value ?? "Sem legado"}</td>
                      <td className="space-x-1">
                        {status.is_initial ? <Badge tone="info">Inicial</Badge> : null}
                        {status.is_final ? <Badge tone="neutral">Final</Badge> : null}
                        {status.pauses_sla ? <Badge tone="warning">Pausa SLA</Badge> : null}
                      </td>
                      <td>{statusBadge(status.is_active)}</td>
                      <td>
                        <Button type="button" variant="secondary" size="sm" onClick={() => startEditStatus(status)}>
                          Editar
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            )}
          </section>

          <section className="rounded-xl border border-slate-200 bg-white shadow-sm">
            <div className="border-b border-slate-100 px-5 py-4">
              <h3 className="text-base font-semibold text-slate-900">Transicoes</h3>
            </div>
            {transitions.items.length === 0 ? (
              <EmptyState title="Ainda nao ha registros" description="Nenhuma transicao configurada." />
            ) : (
              <Table minWidth={760}>
                <thead>
                  <tr>
                    <th>Origem</th>
                    <th>Destino</th>
                    <th>Regras</th>
                    <th>Status</th>
                    <th>Acoes</th>
                  </tr>
                </thead>
                <tbody>
                  {transitions.items.map((transition) => (
                    <tr key={transition.id}>
                      <td>{transition.from_status_name}</td>
                      <td>{transition.to_status_name}</td>
                      <td className="space-x-1">
                        {transition.requires_comment ? <Badge tone="info">Comentario</Badge> : null}
                        {transition.requires_attachment ? <Badge tone="warning">Anexo</Badge> : null}
                        {transition.allowed_roles_json?.length ? (
                          <Badge tone="neutral">{transition.allowed_roles_json.join(", ")}</Badge>
                        ) : null}
                      </td>
                      <td>{statusBadge(transition.is_active)}</td>
                      <td>
                        <Button
                          type="button"
                          variant="secondary"
                          size="sm"
                          onClick={() => startEditTransition(transition)}
                        >
                          Editar
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            )}
          </section>
        </div>
      ) : null}
    </div>
  );
}

export default function TicketSettingsPage() {
  const { token, user } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const activeTab = parseTab(searchParams.get("tab"));
  const [referenceCategories, setReferenceCategories] = useState<TicketCategoryItem[]>([]);
  const [referenceTypes, setReferenceTypes] = useState<TicketTypeItem[]>([]);
  const [referenceError, setReferenceError] = useState<string | null>(null);

  const isAdmin = user?.role === "admin";

  async function loadReferenceData() {
    if (!token || !isAdmin) {
      return;
    }

    setReferenceError(null);

    try {
      const [categoriesResponse, typesResponse] = await Promise.all([
        listAdminTicketCategories(token, { page: 1, page_size: 100, sort: "name_asc" }),
        listAdminTicketTypes(token, { page: 1, page_size: 100, sort: "name_asc" }),
      ]);

      setReferenceCategories(categoriesResponse.items);
      setReferenceTypes(typesResponse.items);
    } catch (error: unknown) {
      setReferenceError(getErrorMessage(error, "Nao foi possivel carregar as referencias dos cadastros."));
    }
  }

  useEffect(() => {
    void loadReferenceData();
  }, [token, isAdmin]);

  const activeTabLabel = useMemo(
    () => settingsTabs.find((tab) => tab.id === activeTab)?.label ?? "Categorias",
    [activeTab],
  );

  if (!token || !isAdmin) {
    return (
      <section className="space-y-6">
        <ErrorState description="Seu perfil nao pode acessar os cadastros configuraveis de chamados." />
      </section>
    );
  }

  return (
    <section className="space-y-6">
      <PageHeader
        eyebrow="Configuracoes"
        title="Chamados"
        description="Centraliza categorias, subcategorias, tipos e prioridades sem criar uma nova area administrativa."
      />

      <section className="min-w-0 rounded-xl border border-slate-200 bg-white px-3 py-2 shadow-sm">
        <nav className="flex max-w-full gap-1 overflow-x-auto overscroll-x-contain" aria-label="Abas internas de chamados">
          {settingsTabs.map((tab) => (
            <button
              key={tab.id}
              className={[
                "whitespace-nowrap rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                activeTab === tab.id
                  ? "bg-teal-50 text-teal-700 ring-1 ring-inset ring-teal-200"
                  : "text-slate-500 hover:bg-slate-50 hover:text-slate-700",
              ]
                .filter(Boolean)
                .join(" ")}
              type="button"
              onClick={() => setSearchParams({ tab: tab.id })}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </section>

      <section className="rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
        <div className="flex flex-wrap items-center gap-3">
          <Badge tone="accent">{activeTabLabel}</Badge>
          <span className="text-sm text-slate-500">
            Cadastros configuraveis mantidos dentro de <strong>/settings/tickets</strong>.
          </span>
        </div>
      </section>

      {referenceError ? <ErrorState description={referenceError} /> : null}

      {activeTab === "categories" ? (
        <TicketCategoriesSection
          token={token}
          typeOptions={referenceTypes}
          onReferencesChanged={loadReferenceData}
        />
      ) : null}

      {activeTab === "subcategories" ? (
        <TicketSubcategoriesSection
          token={token}
          categoryOptions={referenceCategories}
        />
      ) : null}

      {activeTab === "types" ? (
        <TicketTypesSection
          token={token}
          onReferencesChanged={loadReferenceData}
        />
      ) : null}

      {activeTab === "priorities" ? <TicketPrioritiesSection token={token} /> : null}

      {activeTab === "workflow" ? <TicketWorkflowSection token={token} /> : null}

      {activeTab === "custom_fields" ? (
        <TicketCustomFieldsSection
          token={token}
          categoryOptions={referenceCategories}
        />
      ) : null}
    </section>
  );
}
