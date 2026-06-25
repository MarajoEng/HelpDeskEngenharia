import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { createTicket } from "../api/ticketApi";
import { getUnitById, listUnits } from "../api/unitApi";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import ErrorState from "../components/ui/ErrorState";
import Input from "../components/ui/Input";
import PageHeader from "../components/ui/PageHeader";
import Select from "../components/ui/Select";
import Textarea from "../components/ui/Textarea";
import { useAuth } from "../hooks/useAuth";
import type { Ticket, TicketCategory, TicketCreatePayload, TicketPriority, TicketSeverity } from "../types/ticket";
import type { Unit } from "../types/unit";
import { getErrorMessage } from "../utils/messages";

const categoryOptions: Array<{ value: TicketCategory; label: string }> = [
  { value: "fuel_pump", label: "Bomba de combustivel" },
  { value: "fuel_nozzle", label: "Bico de abastecimento" },
  { value: "electrical", label: "Eletrica" },
  { value: "plumbing", label: "Hidraulica" },
  { value: "leak", label: "Vazamento" },
  { value: "structure", label: "Estrutura" },
  { value: "roof", label: "Cobertura" },
  { value: "pavement", label: "Pavimento" },
  { value: "environmental_risk", label: "Risco ambiental" },
  { value: "other", label: "Outro" },
];

const priorityOptions: Array<{ value: TicketPriority; label: string }> = [
  { value: "low", label: "Baixa" },
  { value: "medium", label: "Media" },
  { value: "high", label: "Alta" },
  { value: "critical", label: "Critica" },
];

const severityOptions: Array<{ value: TicketSeverity; label: string }> = [
  { value: "low", label: "Baixa" },
  { value: "medium", label: "Media" },
  { value: "high", label: "Alta" },
  { value: "critical", label: "Critica" },
];

type TicketFormState = {
  unit_id: string;
  category: TicketCategory;
  problem_type: string;
  title: string;
  description: string;
  priority: TicketPriority;
  severity: TicketSeverity;
  operational_impact: string;
  fuel_nozzles_stopped: string;
  estimated_daily_loss: string;
  estimated_cost: string;
  requires_approval: boolean;
};

const initialForm: TicketFormState = {
  unit_id: "",
  category: "fuel_pump",
  problem_type: "",
  title: "",
  description: "",
  priority: "high",
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

function unitLabel(unit: Unit) {
  return `${unit.code} · ${unit.name}`;
}

export default function CreateTicketPage() {
  const { token, user } = useAuth();
  const [units, setUnits] = useState<Unit[]>([]);
  const [form, setForm] = useState<TicketFormState>(initialForm);
  const [createdTicket, setCreatedTicket] = useState<Ticket | null>(null);
  const [isLoadingUnits, setIsLoadingUnits] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const isSupplier = user?.role === "supplier";
  const isManager = user?.role === "manager";

  useEffect(() => {
    if (!token || !user) {
      return;
    }

    let isActive = true;
    setIsLoadingUnits(true);
    setErrorMessage(null);

    const loadUnits = async () => {
      try {
        if (user.role === "manager" && user.unit_id) {
          const currentUnit = await getUnitById(token, user.unit_id);
          if (!isActive) {
            return;
          }
          setUnits([currentUnit]);
          setForm((current) => ({ ...current, unit_id: String(currentUnit.id) }));
          return;
        }

        const response = await listUnits(token, {
          page: 1,
          page_size: 100,
          is_active: true,
          sort: "name_asc",
        });
        if (!isActive) {
          return;
        }
        setUnits(response.items);
      } catch (error: unknown) {
        if (!isActive) {
          return;
        }
        setErrorMessage(getErrorMessage(error, "Nao foi possivel carregar as unidades."));
      } finally {
        if (isActive) {
          setIsLoadingUnits(false);
        }
      }
    };

    void loadUnits();

    return () => {
      isActive = false;
    };
  }, [token, user]);

  const selectedUnit = useMemo(
    () => units.find((unit) => String(unit.id) === form.unit_id) || null,
    [form.unit_id, units],
  );

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || isSupplier) {
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);
    setCreatedTicket(null);

    try {
      const payload: TicketCreatePayload = {
        unit_id: Number(form.unit_id),
        category: form.category,
        problem_type: form.problem_type.trim(),
        title: form.title.trim(),
        description: form.description.trim(),
        priority: form.priority,
        severity: form.severity,
        operational_impact: form.operational_impact.trim() || null,
        fuel_nozzles_stopped: toOptionalInteger(form.fuel_nozzles_stopped),
        estimated_daily_loss: toOptionalDecimal(form.estimated_daily_loss),
        estimated_cost: toOptionalDecimal(form.estimated_cost),
        requires_approval: form.requires_approval,
      };

      const response = await createTicket(token, payload);
      setCreatedTicket(response);
      setForm((current) => ({
        ...initialForm,
        unit_id: isManager ? current.unit_id : "",
      }));
    } catch (error: unknown) {
      setErrorMessage(getErrorMessage(error, "Nao foi possivel abrir o chamado."));
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

      {errorMessage ? <ErrorState description={errorMessage} /> : null}

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
              disabled={isLoadingUnits || isManager}
              required
            >
              <option value="">{isLoadingUnits ? "Carregando..." : "Selecione"}</option>
              {units.map((unit) => (
                <option key={unit.id} value={unit.id}>
                  {unitLabel(unit)}
                </option>
              ))}
            </Select>

            <Select
              label="Categoria"
              value={form.category}
              onChange={(event) =>
                setForm((current) => ({ ...current, category: event.target.value as TicketCategory }))
              }
            >
              {categoryOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
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
              value={form.priority}
              onChange={(event) =>
                setForm((current) => ({ ...current, priority: event.target.value as TicketPriority }))
              }
            >
              {priorityOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
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

          <div className="form-actions">
            <Button variant="primary" type="submit" disabled={isSubmitting || isLoadingUnits || !form.unit_id}>
              {isSubmitting ? "Criando chamado..." : "Criar chamado"}
            </Button>
          </div>
        </form>
      </section>
    </section>
  );
}
