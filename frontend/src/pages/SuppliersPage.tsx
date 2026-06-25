import { useEffect, useState } from "react";

import { createSupplier, listSuppliers, updateSupplier } from "../api/supplierApi";
import { useAuth } from "../hooks/useAuth";
import type { Supplier, SupplierCreatePayload, SupplierUpdatePayload } from "../types/supplier";

const initialForm: SupplierCreatePayload = {
  name: "",
  document: "",
  phone: "",
  email: "",
  specialty: "",
  is_active: true,
};

function formatDate(value: string) {
  return new Date(value).toLocaleDateString("pt-BR");
}

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

  function handleChange(e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) {
    const { name, value, type } = e.target;
    setForm((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? (e.target as HTMLInputElement).checked : value,
    }));
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    const promise = editing
      ? updateSupplier(token, editing.id, form as SupplierUpdatePayload)
      : createSupplier(token, form);

    promise
      .then(() => onSaved())
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Erro ao salvar fornecedor.");
        setIsSubmitting(false);
      });
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal__header">
          <h2>{editing ? "Editar fornecedor" : "Novo fornecedor"}</h2>
          <button className="modal__close" type="button" onClick={onClose}>
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className="modal__body">
          {error ? <div className="state-card state-card--error">{error}</div> : null}

          <div className="field">
            <label htmlFor="sup-name">Nome *</label>
            <input
              id="sup-name"
              name="name"
              className="input"
              value={form.name}
              onChange={handleChange}
              required
              maxLength={255}
            />
          </div>

          <div className="field">
            <label htmlFor="sup-document">CNPJ / Documento *</label>
            <input
              id="sup-document"
              name="document"
              className="input"
              value={form.document}
              onChange={handleChange}
              required
              maxLength={50}
            />
          </div>

          <div className="field">
            <label htmlFor="sup-phone">Telefone *</label>
            <input
              id="sup-phone"
              name="phone"
              className="input"
              value={form.phone}
              onChange={handleChange}
              required
              maxLength={50}
            />
          </div>

          <div className="field">
            <label htmlFor="sup-email">E-mail *</label>
            <input
              id="sup-email"
              name="email"
              type="email"
              className="input"
              value={form.email}
              onChange={handleChange}
              required
              maxLength={255}
            />
          </div>

          <div className="field">
            <label htmlFor="sup-specialty">Especialidade *</label>
            <input
              id="sup-specialty"
              name="specialty"
              className="input"
              value={form.specialty}
              onChange={handleChange}
              required
              maxLength={255}
            />
          </div>

          <div className="field">
            <label>
              <input
                type="checkbox"
                name="is_active"
                checked={form.is_active}
                onChange={handleChange}
                style={{ marginRight: "8px" }}
              />
              Ativo
            </label>
          </div>

          <div className="modal__footer">
            <button className="button-secondary" type="button" onClick={onClose} disabled={isSubmitting}>
              Cancelar
            </button>
            <button className="button-primary" type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Salvando..." : "Salvar"}
            </button>
          </div>
        </form>
      </div>
    </div>
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
      .then((res) => {
        setSuppliers(res.items);
        setTotal(res.total);
        setPages(res.pages);
        setPage(currentPage);
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Erro ao carregar fornecedores.");
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
      <div className="page__header">
        <div>
          <p className="eyebrow">Cadastro</p>
          <h2 className="page__title">Fornecedores</h2>
          <p className="page__description">{total} fornecedor{total !== 1 ? "es" : ""} encontrado{total !== 1 ? "s" : ""}</p>
        </div>
        {isAdmin ? (
          <button className="button-primary" type="button" onClick={openCreate}>
            Novo fornecedor
          </button>
        ) : null}
      </div>

      <div className="filter-bar">
        <input
          className="input"
          type="text"
          placeholder="Buscar por nome, documento ou especialidade..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select
          className="input"
          value={isActiveFilter}
          onChange={(e) => setIsActiveFilter(e.target.value as "" | "true" | "false")}
        >
          <option value="">Todos</option>
          <option value="true">Ativos</option>
          <option value="false">Inativos</option>
        </select>
      </div>

      {error ? <div className="state-card state-card--error">{error}</div> : null}

      {isLoading ? (
        <div className="state-card">Carregando fornecedores...</div>
      ) : suppliers.length === 0 ? (
        <div className="state-card">Nenhum fornecedor encontrado.</div>
      ) : (
        <div className="table-wrapper">
          <table className="table">
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
                    <span className={supplier.is_active ? "status-badge status-badge--success" : "status-badge status-badge--muted"}>
                      {supplier.is_active ? "Ativo" : "Inativo"}
                    </span>
                  </td>
                  <td>{formatDate(supplier.created_at)}</td>
                  {isAdmin ? (
                    <td>
                      <button className="button-secondary" type="button" onClick={() => openEdit(supplier)}>
                        Editar
                      </button>
                    </td>
                  ) : null}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {pages > 1 ? (
        <div className="pagination">
          <button
            className="button-secondary"
            type="button"
            disabled={page <= 1}
            onClick={() => load(page - 1)}
          >
            Anterior
          </button>
          <span>
            {page} / {pages}
          </span>
          <button
            className="button-secondary"
            type="button"
            disabled={page >= pages}
            onClick={() => load(page + 1)}
          >
            Proxima
          </button>
        </div>
      ) : null}

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
