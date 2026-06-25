import { useEffect, useState } from "react";

import { listUnits } from "../api/unitApi";
import { createUser, listUsers, updateUser } from "../api/userApi";
import { useAuth } from "../hooks/useAuth";
import type { Unit } from "../types/unit";
import type { UserFilters, UserItem, UserPayload } from "../types/user";
import type { UserRole } from "../types/auth";

const initialFilters: UserFilters = {
  page: 1,
  page_size: 10,
  search: "",
  role: "",
  unit_id: "",
  is_active: "",
  sort: "name_asc",
};

const initialForm: UserPayload = {
  name: "",
  email: "",
  role: "manager",
  unit_id: null,
  is_active: true,
  password: "",
};

const roleOptions: UserRole[] = ["admin", "manager", "engineering", "director", "supplier"];

export default function UsersPage() {
  const { token } = useAuth();
  const [filters, setFilters] = useState<UserFilters>(initialFilters);
  const [data, setData] = useState<{ items: UserItem[]; total: number; page: number; page_size: number; pages: number }>({
    items: [],
    total: 0,
    page: 1,
    page_size: 10,
    pages: 0,
  });
  const [units, setUnits] = useState<Unit[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<UserItem | null>(null);
  const [form, setForm] = useState<UserPayload>(initialForm);
  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (!token) {
      return;
    }

    void listUnits(token, { page: 1, page_size: 100, sort: "name_asc" })
      .then((response) => setUnits(response.items))
      .catch(() => setUnits([]));
  }, [token]);

  async function loadUsers() {
    if (!token) {
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);

    try {
      const response = await listUsers(token, filters);
      setData(response);
    } catch (error: unknown) {
      setErrorMessage(error instanceof Error ? error.message : "Nao foi possivel carregar usuarios.");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadUsers();
  }, [token, filters.page, filters.page_size, filters.search, filters.role, filters.unit_id, filters.is_active, filters.sort]);

  function openCreateModal() {
    setEditingUser(null);
    setForm(initialForm);
    setFormError(null);
    setIsModalOpen(true);
  }

  function openEditModal(user: UserItem) {
    setEditingUser(user);
    setForm({
      name: user.name,
      email: user.email,
      role: user.role,
      unit_id: user.unit_id,
      is_active: user.is_active,
      password: "",
    });
    setFormError(null);
    setIsModalOpen(true);
  }

  function closeModal() {
    setIsModalOpen(false);
    setEditingUser(null);
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
      if (editingUser) {
        await updateUser(token, editingUser.id, {
          name: form.name,
          email: form.email,
          role: form.role,
          unit_id: form.unit_id,
          is_active: form.is_active,
          ...(form.password ? { password: form.password } : {}),
        });
      } else {
        await createUser(token, form);
      }
      closeModal();
      await loadUsers();
    } catch (error: unknown) {
      setFormError(error instanceof Error ? error.message : "Nao foi possivel salvar o usuario.");
    } finally {
      setIsSubmitting(false);
    }
  }

  function unitLabel(unitId: number | null) {
    if (unitId === null) {
      return "Nao vinculada";
    }
    const unit = units.find((item) => item.id === unitId);
    return unit ? `${unit.code} · ${unit.name}` : `Unidade #${unitId}`;
  }

  return (
    <section className="page">
      <div className="page__header">
        <div>
          <p className="eyebrow">Administracao</p>
          <h2 className="page__title">Usuarios</h2>
          <p className="page__description">
            Gestao administrativa com filtros, papel, vinculo de unidade e ativacao.
          </p>
        </div>
        <button className="button-primary" type="button" onClick={openCreateModal}>
          Novo usuario
        </button>
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
              placeholder="Nome ou email"
            />
          </label>
          <label className="field">
            <span>Perfil</span>
            <select
              value={filters.role || ""}
              onChange={(event) =>
                setFilters((current) => ({
                  ...current,
                  page: 1,
                  role: (event.target.value as UserRole | "") || "",
                }))
              }
            >
              <option value="">Todos</option>
              {roleOptions.map((role) => (
                <option key={role} value={role}>
                  {role}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>Unidade</span>
            <select
              value={String(filters.unit_id ?? "")}
              onChange={(event) => {
                const value = event.target.value;
                setFilters((current) => ({
                  ...current,
                  page: 1,
                  unit_id: value === "" ? "" : Number(value),
                }));
              }}
            >
              <option value="">Todas</option>
              {units.map((unit) => (
                <option key={unit.id} value={unit.id}>
                  {unit.code} · {unit.name}
                </option>
              ))}
            </select>
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
              <option value="true">Ativos</option>
              <option value="false">Inativos</option>
            </select>
          </label>
        </div>

        {isLoading ? <div className="state-card">Carregando usuarios...</div> : null}
        {!isLoading && errorMessage ? <div className="state-card state-card--error">{errorMessage}</div> : null}
        {!isLoading && !errorMessage && data.items.length === 0 ? (
          <div className="state-card">Nenhum usuario encontrado para os filtros atuais.</div>
        ) : null}

        {!isLoading && !errorMessage && data.items.length > 0 ? (
          <>
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Nome</th>
                    <th>Email</th>
                    <th>Perfil</th>
                    <th>Unidade</th>
                    <th>Status</th>
                    <th>Acoes</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((item) => (
                    <tr key={item.id}>
                      <td>{item.name}</td>
                      <td>{item.email}</td>
                      <td>{item.role}</td>
                      <td>{unitLabel(item.unit_id)}</td>
                      <td>
                        <span className={item.is_active ? "status-badge status-badge--success" : "status-badge status-badge--muted"}>
                          {item.is_active ? "Ativo" : "Inativo"}
                        </span>
                      </td>
                      <td>
                        <button className="button-link" type="button" onClick={() => openEditModal(item)}>
                          Editar
                        </button>
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
                <p className="eyebrow">Usuarios</p>
                <h3>{editingUser ? "Editar usuario" : "Novo usuario"}</h3>
              </div>
              <button className="button-secondary" type="button" onClick={closeModal}>
                Fechar
              </button>
            </div>

            <form className="form-grid" onSubmit={handleSubmit}>
              <label className="field">
                <span>Nome</span>
                <input
                  value={form.name}
                  onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
                  required
                />
              </label>
              <label className="field">
                <span>Email</span>
                <input
                  type="email"
                  value={form.email}
                  onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))}
                  required
                />
              </label>
              <label className="field">
                <span>Perfil</span>
                <select
                  value={form.role}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, role: event.target.value as UserRole }))
                  }
                >
                  {roleOptions.map((role) => (
                    <option key={role} value={role}>
                      {role}
                    </option>
                  ))}
                </select>
              </label>
              <label className="field">
                <span>Unidade</span>
                <select
                  value={form.unit_id ?? ""}
                  onChange={(event) =>
                    setForm((current) => ({
                      ...current,
                      unit_id: event.target.value === "" ? null : Number(event.target.value),
                    }))
                  }
                >
                  <option value="">Sem unidade</option>
                  {units.map((unit) => (
                    <option key={unit.id} value={unit.id}>
                      {unit.code} · {unit.name}
                    </option>
                  ))}
                </select>
              </label>
              <label className="field">
                <span>Senha {editingUser ? "(opcional)" : ""}</span>
                <input
                  type="password"
                  value={form.password || ""}
                  onChange={(event) => setForm((current) => ({ ...current, password: event.target.value }))}
                  required={!editingUser}
                />
              </label>
              <label className="field field--checkbox">
                <input
                  checked={form.is_active}
                  type="checkbox"
                  onChange={(event) => setForm((current) => ({ ...current, is_active: event.target.checked }))}
                />
                <span>Usuario ativo</span>
              </label>

              {formError ? <div className="form-message form-message--error">{formError}</div> : null}

              <div className="form-actions">
                <button className="button-secondary" type="button" onClick={closeModal}>
                  Cancelar
                </button>
                <button className="button-primary" type="submit" disabled={isSubmitting}>
                  {isSubmitting ? "Salvando..." : editingUser ? "Salvar alteracoes" : "Criar usuario"}
                </button>
              </div>
            </form>
          </div>
        </div>
      ) : null}
    </section>
  );
}
