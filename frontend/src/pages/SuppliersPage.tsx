import { useEffect, useState } from "react";

import { createSupplier, listSuppliers, updateSupplier } from "../api/supplierApi";
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
import { useAuth } from "../hooks/useAuth";
import type { Supplier, SupplierCreatePayload, SupplierUpdatePayload } from "../types/supplier";
import { formatShortDate } from "../utils/formatters";
import { getErrorMessage, LIST_EMPTY_MESSAGES } from "../utils/messages";

const initialForm: SupplierCreatePayload = {
  name: "",
  document: "",
  phone: "",
  email: "",
  specialty: "",
  is_active: true,
};

interface SupplierModalProps {
  token: string;
  editing: Supplier | null;
  onClose: () => void;
  onSaved: () => void;
}

function SupplierModal({ token, editing, onClose, onSaved }: SupplierModalProps) {
  const [form, setForm] = useState<SupplierCreatePayload>(
    editing
      ? {
          name: editing.name,
          document: editing.document,
          phone: editing.phone,
          email: editing.email,
          specialty: editing.specialty,
          is_active: editing.is_active,
        }
      : initialForm,
  );
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function handleChange(
    name: keyof SupplierCreatePayload,
    value: SupplierCreatePayload[keyof SupplierCreatePayload],
  ) {
    setForm((prev) => ({
      ...prev,
      [name]: value,
    }));
  }

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);

    const promise = editing
      ? updateSupplier(token, editing.id, form as SupplierUpdatePayload)
      : createSupplier(token, form);

    promise
      .then(() => onSaved())
      .catch((requestError: unknown) => {
        setError(getErrorMessage(requestError, "Erro ao salvar fornecedor."));
        setIsSubmitting(false);
      });
  }

  return (
    <Modal
      title={editing ? "Editar fornecedor" : "Novo fornecedor"}
      subtitle="Cadastro de parceiro homologado para atendimento da engenharia."
      onClose={onClose}
    >
      <form onSubmit={handleSubmit} className="form-grid">
        {error ? <div className="state-card state-card--error">{error}</div> : null}

        <Input
          label="Nome"
          value={form.name}
          onChange={(event) => handleChange("name", event.target.value)}
          required
          maxLength={255}
        />
        <Input
          label="CNPJ / Documento"
          value={form.document}
          onChange={(event) => handleChange("document", event.target.value)}
          required
          maxLength={50}
        />
        <Input
          label="Telefone"
          value={form.phone}
          onChange={(event) => handleChange("phone", event.target.value)}
          required
          maxLength={50}
        />
        <Input
          label="E-mail"
          type="email"
          value={form.email}
          onChange={(event) => handleChange("email", event.target.value)}
          required
          maxLength={255}
        />
        <Input
          label="Especialidade"
          value={form.specialty}
          onChange={(event) => handleChange("specialty", event.target.value)}
          required
          maxLength={255}
        />
        <label className="field field--checkbox">
          <input
            type="checkbox"
            checked={form.is_active}
            onChange={(event) => handleChange("is_active", event.target.checked)}
          />
          <span>Fornecedor ativo</span>
        </label>

        <div className="form-actions">
          <Button variant="secondary" type="button" onClick={onClose} disabled={isSubmitting}>
            Cancelar
          </Button>
          <Button variant="primary" type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Salvando..." : "Salvar"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}

export default function SuppliersPage() {
  const { token, user } = useAuth();
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [search, setSearch] = useState("");
  const [isActiveFilter, setIsActiveFilter] = useState<"" | "true" | "false">("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editingSupplier, setEditingSupplier] = useState<Supplier | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const isAdmin = user?.role === "admin";

  function load(currentPage = 1) {
    if (!token) return;
    setIsLoading(true);
    setError(null);
    listSuppliers(token, {
      page: currentPage,
      page_size: 20,
      search: search || undefined,
      is_active: isActiveFilter === "" ? undefined : isActiveFilter === "true",
    })
      .then((response) => {
        setSuppliers(response.items);
        setTotal(response.total);
        setPages(response.pages);
        setPage(currentPage);
      })
      .catch((requestError: unknown) => {
        setError(getErrorMessage(requestError, "Erro ao carregar fornecedores."));
      })
      .finally(() => setIsLoading(false));
  }

  useEffect(() => {
    load(1);
  }, [token, search, isActiveFilter]);

  function openCreate() {
    setEditingSupplier(null);
    setIsModalOpen(true);
  }

  function openEdit(supplier: Supplier) {
    setEditingSupplier(supplier);
    setIsModalOpen(true);
  }

  function handleSaved() {
    setIsModalOpen(false);
    load(page);
  }

  return (
    <section className="page">
      <PageHeader
        eyebrow="Cadastro"
        title="Fornecedores"
        description={`${total} fornecedor${total !== 1 ? "es" : ""} encontrado${total !== 1 ? "s" : ""}`}
        actions={
          isAdmin ? (
            <Button variant="primary" type="button" onClick={openCreate}>
              Novo fornecedor
            </Button>
          ) : null
        }
      />

      <section className="panel panel--stack">
        <FilterBar columns={2}>
          <Input
            label="Busca"
            type="text"
            placeholder="Nome, documento ou especialidade..."
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
          <Select
            label="Status"
            value={isActiveFilter}
            onChange={(event) => setIsActiveFilter(event.target.value as "" | "true" | "false")}
          >
            <option value="">Todos</option>
            <option value="true">Ativos</option>
            <option value="false">Inativos</option>
          </Select>
        </FilterBar>

        {error ? <ErrorState description={error} /> : null}

        {isLoading ? (
          <LoadingState title="Carregando fornecedores" />
        ) : suppliers.length === 0 ? (
          <EmptyState title="Nenhum fornecedor encontrado" description={LIST_EMPTY_MESSAGES.suppliers} />
        ) : (
          <>
            <Table minWidth={940}>
              <thead>
                <tr>
                  <th>Nome</th>
                  <th>Documento</th>
                  <th>Telefone</th>
                  <th>E-mail</th>
                  <th>Especialidade</th>
                  <th>Status</th>
                  <th>Cadastro</th>
                  {isAdmin ? <th>Acao</th> : null}
                </tr>
              </thead>
              <tbody>
                {suppliers.map((supplier) => (
                  <tr key={supplier.id}>
                    <td>{supplier.name}</td>
                    <td>{supplier.document}</td>
                    <td>{supplier.phone}</td>
                    <td>{supplier.email}</td>
                    <td>{supplier.specialty}</td>
                    <td>
                      <Badge tone={supplier.is_active ? "success" : "neutral"}>
                        {supplier.is_active ? "Ativo" : "Inativo"}
                      </Badge>
                    </td>
                    <td>{formatShortDate(supplier.created_at)}</td>
                    {isAdmin ? (
                      <td>
                        <Button variant="secondary" size="sm" type="button" onClick={() => openEdit(supplier)}>
                          Editar
                        </Button>
                      </td>
                    ) : null}
                  </tr>
                ))}
              </tbody>
            </Table>

            {pages > 1 ? (
              <Pagination
                total={total}
                label="fornecedor(es)"
                page={page}
                pages={pages}
                onPrevious={() => load(page - 1)}
                onNext={() => load(page + 1)}
              />
            ) : null}
          </>
        )}
      </section>

      {isModalOpen && token ? (
        <SupplierModal
          token={token}
          editing={editingSupplier}
          onClose={() => setIsModalOpen(false)}
          onSaved={handleSaved}
        />
      ) : null}
    </section>
  );
}
