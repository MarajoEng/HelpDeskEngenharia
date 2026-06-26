import { useEffect, useState } from "react";

import { createUnit, listUnits, updateUnit } from "../api/unitApi";
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
import Table from "../components/ui/Table";
import { useAuth } from "../hooks/useAuth";
import type { Unit, UnitFilters, UnitPayload } from "../types/unit";
import { getErrorMessage, LIST_EMPTY_MESSAGES } from "../utils/messages";

const initialFilters: UnitFilters = {
  page: 1,
  page_size: 10,
  search: "",
  is_active: "",
  state: "",
  region: "",
};

const initialForm: UnitPayload = {
  group_code: "",
  branch_code: "",
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
      setErrorMessage(getErrorMessage(error, "Nao foi possivel carregar unidades."));
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
      group_code: unit.group_code ?? "",
      branch_code: unit.branch_code ?? "",
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
      setFormError(getErrorMessage(error, "Nao foi possivel salvar a unidade."));
    } finally {
      setIsSubmitting(false);
    }
  }

  const canManage = user?.role === "admin";

  return (
    <section className="space-y-6">
      {canManage ? (
        <div className="flex justify-end">
          <Button variant="primary" type="button" onClick={openCreateModal}>
            Nova filial
          </Button>
        </div>
      ) : null}

      <section className="panel">
        <FilterBar columns={4}>
          <Input
            label="Busca"
            value={filters.search || ""}
            onChange={(event) =>
              setFilters((current) => ({ ...current, page: 1, search: event.target.value }))
            }
            placeholder="Grupo, filial, nome, cidade ou região"
          />

          <Input
            label="UF"
            value={filters.state || ""}
            onChange={(event) =>
              setFilters((current) => ({ ...current, page: 1, state: event.target.value.toUpperCase() }))
            }
            placeholder="SP"
            maxLength={2}
          />

          <Input
            label="Regiao"
            value={filters.region || ""}
            onChange={(event) =>
              setFilters((current) => ({ ...current, page: 1, region: event.target.value }))
            }
            placeholder="Sudeste"
          />

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
            <option value="true">Ativas</option>
            <option value="false">Inativas</option>
          </Select>
        </FilterBar>

        {isLoading ? <LoadingState title="Carregando filiais" /> : null}
        {!isLoading && errorMessage ? <ErrorState description={errorMessage} /> : null}
        {!isLoading && !errorMessage && data.items.length === 0 ? (
          <EmptyState title="Nenhuma filial encontrada" description={LIST_EMPTY_MESSAGES.units} />
        ) : null}

        {!isLoading && !errorMessage && data.items.length > 0 ? (
          <>
            <Table minWidth={960}>
              <thead>
                <tr>
                  <th>Grupo</th>
                  <th>Filial</th>
                  <th>Nome</th>
                  <th>Cidade</th>
                  <th>UF</th>
                  <th>Região</th>
                  <th>Status</th>
                  <th>Ações</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((unit) => (
                  <tr key={unit.id}>
                    <td>{unit.group_code ?? "—"}</td>
                    <td>{unit.branch_code ?? unit.code}</td>
                    <td>{unit.name}</td>
                    <td>{unit.city}</td>
                    <td>{unit.state}</td>
                    <td>{unit.region}</td>
                    <td>
                      <Badge tone={unit.is_active ? "success" : "neutral"}>
                        {unit.is_active ? "Ativa" : "Inativa"}
                      </Badge>
                    </td>
                    <td>
                      {canManage ? (
                        <button className="ui-link-button" type="button" onClick={() => openEditModal(unit)}>
                          Editar
                        </button>
                      ) : (
                        <span className="text-muted">Somente leitura</span>
                      )}
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
          title={editingUnit ? "Editar filial" : "Nova filial"}
          subtitle="Cadastro administrativo de filial operacional."
          onClose={closeModal}
        >
          <form className="form-grid" onSubmit={handleSubmit}>
            <Input
              label="Grupo"
              value={form.group_code}
              onChange={(event) => setForm((current) => ({ ...current, group_code: event.target.value }))}
              placeholder="02"
              required
            />
            <Input
              label="Filial"
              value={form.branch_code}
              onChange={(event) => setForm((current) => ({ ...current, branch_code: event.target.value }))}
              placeholder="4301"
              required
            />
            <Input
              label="Nome"
              value={form.name}
              onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
              required
            />
            <Input
              label="Cidade"
              value={form.city}
              onChange={(event) => setForm((current) => ({ ...current, city: event.target.value }))}
              required
            />
            <Input
              label="UF"
              value={form.state}
              maxLength={2}
              onChange={(event) => setForm((current) => ({ ...current, state: event.target.value.toUpperCase() }))}
              required
            />
            <Input
              label="Regiao"
              value={form.region}
              onChange={(event) => setForm((current) => ({ ...current, region: event.target.value }))}
              required
            />
            <label className="field field--checkbox">
              <input
                checked={form.is_active}
                type="checkbox"
                onChange={(event) => setForm((current) => ({ ...current, is_active: event.target.checked }))}
              />
              <span>Filial ativa</span>
            </label>

            {formError ? <div className="form-message form-message--error">{formError}</div> : null}

            <div className="form-actions">
              <Button variant="secondary" type="button" onClick={closeModal}>
                Cancelar
              </Button>
              <Button variant="primary" type="submit" disabled={isSubmitting}>
                {isSubmitting ? "Salvando..." : editingUnit ? "Salvar alteracoes" : "Criar filial"}
              </Button>
            </div>
          </form>
        </Modal>
      ) : null}
    </section>
  );
}
