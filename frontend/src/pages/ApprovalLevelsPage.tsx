import { type FormEvent, useEffect, useState } from "react";

import { createApprovalLevel, listApprovalLevels, updateApprovalLevel } from "../api/approvalLevelApi";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import EmptyState from "../components/ui/EmptyState";
import ErrorState from "../components/ui/ErrorState";
import FilterBar from "../components/ui/FilterBar";
import Input from "../components/ui/Input";
import LoadingState from "../components/ui/LoadingState";
import Modal from "../components/ui/Modal";
import Pagination from "../components/ui/Pagination";
import Select from "../components/ui/Select";
import { ROLE_LABELS } from "../components/ui/statusOptions";
import Table from "../components/ui/Table";
import { useAuth } from "../hooks/useAuth";
import type { ApprovalLevel, ApprovalLevelFilters, ApprovalLevelPayload } from "../types/approvalLevel";
import type { UserRole } from "../types/auth";
import { getErrorMessage, LIST_EMPTY_MESSAGES } from "../utils/messages";

const initialFilters: ApprovalLevelFilters = {
  page: 1,
  page_size: 20,
  search: "",
  is_active: "",
};

const initialForm: ApprovalLevelPayload = {
  name: "",
  min_amount: "0.00",
  max_amount: null,
  allowed_roles: ["engineering", "admin"],
  is_active: true,
};

const roleOptions: UserRole[] = ["engineering", "director", "admin"];

export default function ApprovalLevelsPage() {
  const { token, user } = useAuth();
  const [filters, setFilters] = useState<ApprovalLevelFilters>(initialFilters);
  const [data, setData] = useState<{ items: ApprovalLevel[]; total: number; page: number; page_size: number; pages: number }>({
    items: [],
    total: 0,
    page: 1,
    page_size: 10,
    pages: 0,
  });
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingLevel, setEditingLevel] = useState<ApprovalLevel | null>(null);
  const [form, setForm] = useState<ApprovalLevelPayload>(initialForm);
  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const isAdmin = user?.role === "admin";

  async function loadApprovalLevels() {
    if (!token || !isAdmin) {
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);

    try {
      const response = await listApprovalLevels(token, filters);
      setData(response);
    } catch (error: unknown) {
      setErrorMessage(getErrorMessage(error, "Nao foi possivel carregar as alcadas."));
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadApprovalLevels();
  }, [token, isAdmin, filters.page, filters.page_size, filters.search, filters.is_active, filters.sort]);

  function openCreateModal() {
    setEditingLevel(null);
    setForm(initialForm);
    setFormError(null);
    setIsModalOpen(true);
  }

  function openEditModal(level: ApprovalLevel) {
    setEditingLevel(level);
    setForm({
      name: level.name,
      min_amount: level.min_amount,
      max_amount: level.max_amount,
      allowed_roles: level.allowed_roles,
      is_active: level.is_active,
    });
    setFormError(null);
    setIsModalOpen(true);
  }

  function closeModal() {
    setIsModalOpen(false);
    setEditingLevel(null);
    setFormError(null);
  }

  function toggleRole(role: UserRole) {
    setForm((current) => {
      const exists = current.allowed_roles.includes(role);
      return {
        ...current,
        allowed_roles: exists
          ? current.allowed_roles.filter((item) => item !== role)
          : [...current.allowed_roles, role],
      };
    });
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token) return;

    if (!form.name.trim()) {
      setFormError("Informe um nome para a alcada.");
      return;
    }
    if (Number(form.min_amount) < 0) {
      setFormError("O valor minimo nao pode ser negativo.");
      return;
    }
    if (form.max_amount && Number(form.max_amount) < Number(form.min_amount)) {
      setFormError("O valor maximo deve ser maior ou igual ao minimo.");
      return;
    }
    if (form.allowed_roles.length === 0) {
      setFormError("Selecione ao menos um perfil aprovador.");
      return;
    }

    setIsSubmitting(true);
    setFormError(null);

    try {
      if (editingLevel) {
        await updateApprovalLevel(token, editingLevel.id, form);
      } else {
        await createApprovalLevel(token, form);
      }
      closeModal();
      await loadApprovalLevels();
    } catch (error: unknown) {
      setFormError(getErrorMessage(error, "Nao foi possivel salvar a alcada."));
    } finally {
      setIsSubmitting(false);
    }
  }

  if (!isAdmin) {
    return (
      <section className="space-y-6">
        <ErrorState description="Seu perfil nao pode acessar as alcadas." />
      </section>
    );
  }

  return (
    <section className="space-y-6">
      <div className="flex justify-end">
        <Button variant="primary" type="button" onClick={openCreateModal}>
          Nova alcada
        </Button>
      </div>

      <section className="panel">
        <FilterBar columns={2}>
          <Input
            label="Busca"
            value={filters.search || ""}
            onChange={(event) => setFilters((current) => ({ ...current, page: 1, search: event.target.value }))}
            placeholder="Nome da alcada"
          />
          <Select
            label="Status"
            value={String(filters.is_active ?? "")}
            onChange={(event) =>
              setFilters((current) => ({
                ...current,
                page: 1,
                is_active: event.target.value === "" ? "" : event.target.value === "true",
              }))
            }
          >
            <option value="">Todos</option>
            <option value="true">Ativas</option>
            <option value="false">Inativas</option>
          </Select>
        </FilterBar>

        {isLoading ? <LoadingState title="Carregando alcadas" /> : null}
        {!isLoading && errorMessage ? <ErrorState description={errorMessage} /> : null}
        {!isLoading && !errorMessage && data.items.length === 0 ? (
          <EmptyState title="Nenhuma alcada encontrada" description={LIST_EMPTY_MESSAGES.approvals} />
        ) : null}

        {!isLoading && !errorMessage && data.items.length > 0 ? (
          <>
            <Table minWidth={860}>
              <thead>
                <tr>
                  <th>Nome</th>
                  <th>Faixa</th>
                  <th>Perfis</th>
                  <th>Status</th>
                  <th>Acoes</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((level) => (
                  <tr key={level.id}>
                    <td>{level.name}</td>
                    <td>
                      {level.max_amount
                        ? `R$ ${level.min_amount} ate R$ ${level.max_amount}`
                        : `A partir de R$ ${level.min_amount}`}
                    </td>
                    <td>{level.allowed_roles.map((role) => ROLE_LABELS[role]).join(", ")}</td>
                    <td>
                      <Badge tone={level.is_active ? "success" : "neutral"}>
                        {level.is_active ? "Ativa" : "Inativa"}
                      </Badge>
                    </td>
                    <td>
                      <button className="ui-link-button" type="button" onClick={() => openEditModal(level)}>
                        Editar
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>

            <Pagination
              total={data.total}
              label="alcada(s)"
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
          title={editingLevel ? "Editar alcada" : "Nova alcada"}
          subtitle="Configuracao de limites financeiros e perfis aprovadores."
          onClose={closeModal}
        >
          <form className="form-grid" onSubmit={handleSubmit}>
            <Input
              label="Nome"
              value={form.name}
              onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
              disabled={isSubmitting}
              required
            />

            <div className="ticket-triage-grid">
              <Input
                label="Valor minimo"
                type="number"
                min="0"
                step="0.01"
                value={form.min_amount}
                onChange={(event) => setForm((current) => ({ ...current, min_amount: event.target.value }))}
                disabled={isSubmitting}
                required
              />

              <Input
                label="Valor maximo"
                type="number"
                min="0"
                step="0.01"
                value={form.max_amount ?? ""}
                onChange={(event) =>
                  setForm((current) => ({ ...current, max_amount: event.target.value || null }))
                }
                placeholder="Deixe vazio para topo aberto"
                disabled={isSubmitting}
              />
            </div>

            <div className="field field--full">
              <span>Perfis permitidos *</span>
              <div className="checkbox-grid">
                {roleOptions.map((role) => (
                  <label className="field field--checkbox" key={role}>
                    <input
                      type="checkbox"
                      checked={form.allowed_roles.includes(role)}
                      onChange={() => toggleRole(role)}
                      disabled={isSubmitting}
                    />
                    <span>{ROLE_LABELS[role]}</span>
                  </label>
                ))}
              </div>
            </div>

            <label className="field field--checkbox">
              <input
                type="checkbox"
                checked={form.is_active}
                onChange={(event) => setForm((current) => ({ ...current, is_active: event.target.checked }))}
                disabled={isSubmitting}
              />
              <span>Alcada ativa</span>
            </label>

            {formError ? <div className="form-message form-message--error">{formError}</div> : null}

            <div className="form-actions">
              <Button variant="secondary" type="button" onClick={closeModal} disabled={isSubmitting}>
                Cancelar
              </Button>
              <Button variant="primary" type="submit" disabled={isSubmitting}>
                {isSubmitting ? "Salvando..." : "Salvar alcada"}
              </Button>
            </div>
          </form>
        </Modal>
      ) : null}
    </section>
  );
}
