import { type FormEvent, useEffect, useState } from "react";

import { createApprovalLevel, listApprovalLevels, updateApprovalLevel } from "../api/approvalLevelApi";
import { useAuth } from "../hooks/useAuth";
import type { UserRole } from "../types/auth";
import type { ApprovalLevel, ApprovalLevelFilters, ApprovalLevelPayload } from "../types/approvalLevel";
import { ROLE_LABELS } from "../components/tickets/ticketUi";

const initialFilters: ApprovalLevelFilters = {
  page: 1,
  page_size: 10,
  search: "",
  is_active: "",
  sort: "name_asc",
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
      setErrorMessage(error instanceof Error ? error.message : "Nao foi possivel carregar as alcadas.");
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
      setFormError(error instanceof Error ? error.message : "Nao foi possivel salvar a alcada.");
    } finally {
      setIsSubmitting(false);
    }
  }

  if (!isAdmin) {
    return (
      <section className="page">
        <div className="page__header">
          <div>
            <p className="eyebrow">Administracao</p>
            <h2 className="page__title">Acesso indisponivel</h2>
            <p className="page__description">A configuracao de alcadas fica disponivel apenas para admin.</p>
          </div>
        </div>
        <div className="state-card state-card--error">Seu perfil nao pode acessar as alcadas.</div>
      </section>
    );
  }

  return (
    <section className="page">
      <div className="page__header">
        <div>
          <p className="eyebrow">Administracao</p>
          <h2 className="page__title">Alcadas</h2>
          <p className="page__description">
            Configuracao paginada das faixas de aprovacao por valor e perfis autorizados.
          </p>
        </div>
        <button className="button-primary" type="button" onClick={openCreateModal}>
          Nova alcada
        </button>
      </div>

      <section className="panel">
        <div className="filters">
          <label className="field">
            <span>Busca</span>
            <input
              value={filters.search || ""}
              onChange={(event) => setFilters((current) => ({ ...current, page: 1, search: event.target.value }))}
              placeholder="Nome da alcada"
            />
          </label>
          <label className="field">
            <span>Status</span>
            <select
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
            </select>
          </label>
        </div>

        {isLoading ? <div className="state-card">Carregando alcadas...</div> : null}
        {!isLoading && errorMessage ? <div className="state-card state-card--error">{errorMessage}</div> : null}
        {!isLoading && !errorMessage && data.items.length === 0 ? (
          <div className="state-card">Nenhuma alcada encontrada para os filtros informados.</div>
        ) : null}

        {!isLoading && !errorMessage && data.items.length > 0 ? (
          <>
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Nome</th>
                    <th>Faixa</th>
                    <th>Perfis</th>
                    <th>Status</th>
                    <th></th>
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
                        <span className={level.is_active ? "status-badge status-badge--success" : "status-badge status-badge--muted"}>
                          {level.is_active ? "Ativa" : "Inativa"}
                        </span>
                      </td>
                      <td>
                        <button className="button-link" type="button" onClick={() => openEditModal(level)}>
                          Editar
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="pagination-bar">
              <span style={{ fontSize: "0.9rem" }}>
                {data.total} alcada(s) · pagina {data.page} de {Math.max(data.pages, 1)}
              </span>
              <div className="pagination-actions">
                <button
                  className="button-secondary"
                  type="button"
                  disabled={data.page <= 1}
                  onClick={() => setFilters((current) => ({ ...current, page: Math.max(1, (current.page || 1) - 1) }))}
                >
                  Anterior
                </button>
                <button
                  className="button-secondary"
                  type="button"
                  disabled={data.pages === 0 || data.page >= data.pages}
                  onClick={() => setFilters((current) => ({ ...current, page: (current.page || 1) + 1 }))}
                >
                  Proxima
                </button>
              </div>
            </div>
          </>
        ) : null}
      </section>

      {isModalOpen ? (
        <div className="modal-backdrop" role="presentation">
          <div className="modal-card">
            <div className="modal-card__header">
              <div>
                <p className="eyebrow">Configuracao de alcada</p>
                <h3>{editingLevel ? "Editar alcada" : "Nova alcada"}</h3>
              </div>
              <button className="button-secondary" type="button" onClick={closeModal}>
                Fechar
              </button>
            </div>

            <form className="form-grid" onSubmit={handleSubmit}>
              <label className="field">
                <span>Nome *</span>
                <input
                  value={form.name}
                  onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
                  disabled={isSubmitting}
                />
              </label>

              <div className="ticket-triage-grid">
                <label className="field">
                  <span>Valor minimo *</span>
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    value={form.min_amount}
                    onChange={(event) => setForm((current) => ({ ...current, min_amount: event.target.value }))}
                    disabled={isSubmitting}
                  />
                </label>

                <label className="field">
                  <span>Valor maximo</span>
                  <input
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
                </label>
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
                <button className="button-secondary" type="button" onClick={closeModal} disabled={isSubmitting}>
                  Cancelar
                </button>
                <button className="button-primary" type="submit" disabled={isSubmitting}>
                  {isSubmitting ? "Salvando..." : "Salvar alcada"}
                </button>
              </div>
            </form>
          </div>
        </div>
      ) : null}
    </section>
  );
}
