import { useEffect, useState } from "react";

import { listUnits } from "../api/unitApi";
import { createUser, listUsers, updateUser } from "../api/userApi";
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
import type { UserRole } from "../types/auth";
import type { Unit } from "../types/unit";
import type { UserFilters, UserItem, UserPayload } from "../types/user";
import { getErrorMessage, LIST_EMPTY_MESSAGES } from "../utils/messages";

const initialFilters: UserFilters = {
  page: 1,
  page_size: 10,
  search: "",
  role: "",
  unit_id: "",
  is_active: "",
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

    void listUnits(token, { page: 1, page_size: 100 })
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
      setErrorMessage(getErrorMessage(error, "Nao foi possivel carregar usuarios."));
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
      setFormError(getErrorMessage(error, "Nao foi possivel salvar o usuario."));
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
    <section className="space-y-6">
      <div className="flex justify-end">
        <Button variant="primary" type="button" onClick={openCreateModal}>
          Novo usuario
        </Button>
      </div>

      <section className="panel">
        <FilterBar columns={4}>
          <Input
            label="Busca"
            value={filters.search || ""}
            onChange={(event) =>
              setFilters((current) => ({ ...current, page: 1, search: event.target.value }))
            }
            placeholder="Nome ou email"
          />
          <Select
            label="Perfil"
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
                {ROLE_LABELS[role]}
              </option>
            ))}
          </Select>
          <Select
            label="Unidade"
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
          </Select>
          <Select
            label="Status"
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
          </Select>
        </FilterBar>

        {isLoading ? <LoadingState title="Carregando usuarios" /> : null}
        {!isLoading && errorMessage ? <ErrorState description={errorMessage} /> : null}
        {!isLoading && !errorMessage && data.items.length === 0 ? (
          <EmptyState title="Nenhum usuario encontrado" description={LIST_EMPTY_MESSAGES.users} />
        ) : null}

        {!isLoading && !errorMessage && data.items.length > 0 ? (
          <>
            <Table minWidth={900}>
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
                    <td>{ROLE_LABELS[item.role]}</td>
                    <td>{unitLabel(item.unit_id)}</td>
                    <td>
                      <Badge tone={item.is_active ? "success" : "neutral"}>
                        {item.is_active ? "Ativo" : "Inativo"}
                      </Badge>
                    </td>
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
          title={editingUser ? "Editar usuario" : "Novo usuario"}
          subtitle="Cadastro administrativo com perfil, unidade e status."
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
              label="Email"
              type="email"
              value={form.email}
              onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))}
              required
            />
            <Select
              label="Perfil"
              value={form.role}
              onChange={(event) =>
                setForm((current) => ({ ...current, role: event.target.value as UserRole }))
              }
            >
              {roleOptions.map((role) => (
                <option key={role} value={role}>
                  {ROLE_LABELS[role]}
                </option>
              ))}
            </Select>
            <Select
              label="Unidade"
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
            </Select>
            <Input
              label={`Senha ${editingUser ? "(opcional)" : ""}`}
              type="password"
              value={form.password || ""}
              onChange={(event) => setForm((current) => ({ ...current, password: event.target.value }))}
              required={!editingUser}
            />
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
              <Button variant="secondary" type="button" onClick={closeModal}>
                Cancelar
              </Button>
              <Button variant="primary" type="submit" disabled={isSubmitting}>
                {isSubmitting ? "Salvando..." : editingUser ? "Salvar alteracoes" : "Criar usuario"}
              </Button>
            </div>
          </form>
        </Modal>
      ) : null}
    </section>
  );
}
