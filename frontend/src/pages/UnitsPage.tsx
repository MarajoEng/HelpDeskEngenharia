import { useEffect, useState } from "react";

import { createUnit, listUnits, updateUnit } from "../api/unitApi";
import { useAuth } from "../hooks/useAuth";
import type { Unit, UnitFilters, UnitPayload } from "../types/unit";

const initialFilters: UnitFilters = {
  page: 1,
  page_size: 10,
  search: "",
  is_active: "",
  state: "",
  region: "",
  sort: "name_asc",
};

const initialForm: UnitPayload = {
  code: "",
  name: "",
  city: "",
  state: "",
  region: "",
  is_active: true,
};

export default function UnitsPage() {
  const { token, user } = useAuth();
  const [filters, setFilters] = useState<UnitFilters>(initialFilters);
  const [data, setData] = useState<{ items: Unit[]; total: number; page: number; page_size: number; pages: number }>({
    items: [],
    total: 0,
    page: 1,
    page_size: 10,
    pages: 0,
  });
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingUnit, setEditingUnit] = useState<Unit | null>(null);
  const [form, setForm] = useState<UnitPayload>(initialForm);
  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function loadUnits() {
    if (!token) {
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);

    try {
      const response = await listUnits(token, filters);
      setData(response);
    } catch (error: unknown) {
      setErrorMessage(error instanceof Error ? error.message : "Nao foi possivel carregar unidades.");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadUnits();
  }, [token, filters.page, filters.page_size, filters.search, filters.is_active, filters.state, filters.region, filters.sort]);

  function openCreateModal() {
    setEditingUnit(null);
    setForm(initialForm);
    setFormError(null);
    setIsModalOpen(true);
  }

  function openEditModal(unit: Unit) {
    setEditingUnit(unit);
    setForm({
      code: unit.code,
      name: unit.name,
      city: unit.city,
      state: unit.state,
      region: unit.region,
      is_active: unit.is_active,
    });
    setFormError(null);
    setIsModalOpen(true);
  }

  function closeModal() {
    setIsModalOpen(false);
    setEditingUnit(null);
    setFormError(null);
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token) {
      return;
    }

    setIsSubmitting(true);
    setFormError(null);

    try {
      if (editingUnit) {
        await updateUnit(token, editingUnit.id, form);
      } else {
        await createUnit(token, form);
      }
      closeModal();
      await loadUnits();
    } catch (error: unknown) {
      setFormError(error instanceof Error ? error.message : "Nao foi possivel salvar a unidade.");
    } finally {
      setIsSubmitting(false);
    }
  }

  const canManage = user?.role === "admin";

  return (
    <section className="page">
      <div className="page__header">
        <div>
          <p className="eyebrow">Cadastro base</p>
          <h2 className="page__title">Unidades</h2>
          <p className="page__description">
            Cadastro administrativo com filtros, paginacao e controle de ativacao.
          </p>
        </div>
        {canManage ? (
          <button className="button-primary" type="button" onClick={openCreateModal}>
            Nova unidade
          </button>
        ) : null}
      </div>

      <section className="panel">
        <div className="filters">
          <label className="field">
            <span>Busca</span>
            <input
              value={filters.search || ""}
              onChange={(event) =>
                setFilters((current) => ({ ...current, page: 1, search: event.target.value }))
              }
              placeholder="Code, nome, cidade ou regiao"
            />
          </label>

          <label className="field">
            <span>UF</span>
            <input
              value={filters.state || ""}
              onChange={(event) =>
                setFilters((current) => ({ ...current, page: 1, state: event.target.value.toUpperCase() }))
              }
              placeholder="SP"
              maxLength={2}
            />
          </label>

          <label className="field">
            <span>Regiao</span>
            <input
              value={filters.region || ""}
              onChange={(event) =>
                setFilters((current) => ({ ...current, page: 1, region: event.target.value }))
              }
              placeholder="Sudeste"
            />
          </label>

          <label className="field">
            <span>Status</span>
            <select
              value={String(filters.is_active ?? "")}
              onChange={(event) => {
                const value = event.target.value;
                setFilters((current) => ({
                  ...current,
                  page: 1,
                  is_active: value === "" ? "" : value === "true",
                }));
              }}
            >
              <option value="">Todos</option>
              <option value="true">Ativas</option>
              <option value="false">Inativas</option>
            </select>
          </label>
        </div>

        {isLoading ? <div className="state-card">Carregando unidades...</div> : null}
        {!isLoading && errorMessage ? <div className="state-card state-card--error">{errorMessage}</div> : null}
        {!isLoading && !errorMessage && data.items.length === 0 ? (
          <div className="state-card">Nenhuma unidade encontrada para os filtros atuais.</div>
        ) : null}

        {!isLoading && !errorMessage && data.items.length > 0 ? (
          <>
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Code</th>
                    <th>Nome</th>
                    <th>Cidade</th>
                    <th>UF</th>
                    <th>Regiao</th>
                    <th>Status</th>
                    <th>Acoes</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((unit) => (
                    <tr key={unit.id}>
                      <td>{unit.code}</td>
                      <td>{unit.name}</td>
                      <td>{unit.city}</td>
                      <td>{unit.state}</td>
                      <td>{unit.region}</td>
                      <td>
                        <span className={unit.is_active ? "status-badge status-badge--success" : "status-badge status-badge--muted"}>
                          {unit.is_active ? "Ativa" : "Inativa"}
                        </span>
                      </td>
                      <td>
                        {canManage ? (
                          <button className="button-link" type="button" onClick={() => openEditModal(unit)}>
                            Editar
                          </button>
                        ) : (
                          <span className="text-muted">Somente leitura</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="pagination-bar">
              <span>
                {data.total} registro(s) · pagina {data.page} de {Math.max(data.pages, 1)}
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
        <div className="modal-backdrop" role="presentation" onClick={closeModal}>
          <div className="modal-card" role="dialog" aria-modal="true" onClick={(event) => event.stopPropagation()}>
            <div className="modal-card__header">
              <div>
                <p className="eyebrow">Unidades</p>
                <h3>{editingUnit ? "Editar unidade" : "Nova unidade"}</h3>
              </div>
              <button className="button-secondary" type="button" onClick={closeModal}>
                Fechar
              </button>
            </div>

            <form className="form-grid" onSubmit={handleSubmit}>
              <label className="field">
                <span>Code</span>
                <input
                  value={form.code}
                  onChange={(event) => setForm((current) => ({ ...current, code: event.target.value.toUpperCase() }))}
                  required
                />
              </label>
              <label className="field">
                <span>Nome</span>
                <input
                  value={form.name}
                  onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
                  required
                />
              </label>
              <label className="field">
                <span>Cidade</span>
                <input
                  value={form.city}
                  onChange={(event) => setForm((current) => ({ ...current, city: event.target.value }))}
                  required
                />
              </label>
              <label className="field">
                <span>UF</span>
                <input
                  value={form.state}
                  maxLength={2}
                  onChange={(event) => setForm((current) => ({ ...current, state: event.target.value.toUpperCase() }))}
                  required
                />
              </label>
              <label className="field">
                <span>Regiao</span>
                <input
                  value={form.region}
                  onChange={(event) => setForm((current) => ({ ...current, region: event.target.value }))}
                  required
                />
              </label>
              <label className="field field--checkbox">
                <input
                  checked={form.is_active}
                  type="checkbox"
                  onChange={(event) => setForm((current) => ({ ...current, is_active: event.target.checked }))}
                />
                <span>Unidade ativa</span>
              </label>

              {formError ? <div className="form-message form-message--error">{formError}</div> : null}

              <div className="form-actions">
                <button className="button-secondary" type="button" onClick={closeModal}>
                  Cancelar
                </button>
                <button className="button-primary" type="submit" disabled={isSubmitting}>
                  {isSubmitting ? "Salvando..." : editingUnit ? "Salvar alteracoes" : "Criar unidade"}
                </button>
              </div>
            </form>
          </div>
        </div>
      ) : null}
    </section>
  );
}
