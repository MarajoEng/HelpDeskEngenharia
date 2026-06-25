import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { getTicketById } from "../api/ticketApi";
import { useAuth } from "../hooks/useAuth";
import type { Ticket } from "../types/ticket";

function moneyLabel(value: string | null) {
  if (!value) {
    return "Nao informado";
  }

  const parsed = Number(value);
  return Number.isNaN(parsed)
    ? value
    : new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(parsed);
}

function labelFromValue(value: string | null | undefined) {
  if (!value) {
    return "Nao informado";
  }
  return value.split("_").join(" ");
}

function statusClass(status: string) {
  if (status === "open") {
    return "status-badge status-badge--info";
  }
  return "status-badge status-badge--muted";
}

export default function TicketDetailPage() {
  const { ticketId } = useParams();
  const { token } = useAuth();
  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!token || !ticketId) {
      return;
    }

    let isActive = true;
    setIsLoading(true);
    setErrorMessage(null);

    getTicketById(token, Number(ticketId))
      .then((response) => {
        if (!isActive) {
          return;
        }
        setTicket(response);
      })
      .catch((error: unknown) => {
        if (!isActive) {
          return;
        }
        setErrorMessage(error instanceof Error ? error.message : "Nao foi possivel carregar o chamado.");
      })
      .finally(() => {
        if (isActive) {
          setIsLoading(false);
        }
      });

    return () => {
      isActive = false;
    };
  }, [ticketId, token]);

  if (isLoading) {
    return <div className="state-card">Carregando chamado...</div>;
  }

  if (errorMessage) {
    return <div className="state-card state-card--error">{errorMessage}</div>;
  }

  if (!ticket) {
    return <div className="state-card">Chamado nao encontrado.</div>;
  }

  return (
    <section className="page">
      <div className="page__header">
        <div>
          <p className="eyebrow">Detalhe do chamado</p>
          <h2 className="page__title">{ticket.ticket_number}</h2>
          <p className="page__description">
            Registro inicial aberto na FASE 5. Triagem, aprovacao e execucao entram em fases futuras.
          </p>
        </div>
        <Link className="button-primary button-primary--link" to="/tickets">
          Voltar para chamados
        </Link>
      </div>

      <section className="panel panel--stack">
        <div className="ticket-summary">
          <div>
            <p className="eyebrow">Status atual</p>
            <h3>{ticket.title}</h3>
            <p>{ticket.unit_code || "Unidade"} · {ticket.unit_name || `#${ticket.unit_id}`}</p>
          </div>
          <div className="ticket-summary__meta">
            <span className={statusClass(ticket.status)}>{labelFromValue(ticket.status)}</span>
            <span className={`priority-badge priority-badge--${ticket.priority}`}>{labelFromValue(ticket.priority)}</span>
            <span className={`severity-badge severity-badge--${ticket.severity}`}>{labelFromValue(ticket.severity)}</span>
          </div>
        </div>

        <dl className="details-list">
          <div>
            <dt>Categoria</dt>
            <dd>{labelFromValue(ticket.category)}</dd>
          </div>
          <div>
            <dt>Tipo do problema</dt>
            <dd>{ticket.problem_type}</dd>
          </div>
          <div>
            <dt>Solicitante</dt>
            <dd>{ticket.opened_by_user_name || `Usuario #${ticket.opened_by_user_id}`}</dd>
          </div>
          <div>
            <dt>Data de abertura</dt>
            <dd>{new Date(ticket.opened_at).toLocaleString("pt-BR")}</dd>
          </div>
          <div>
            <dt>Bicos parados</dt>
            <dd>{ticket.fuel_nozzles_stopped ?? "Nao informado"}</dd>
          </div>
          <div>
            <dt>Exige aprovacao</dt>
            <dd>{ticket.requires_approval ? "Sim" : "Nao"}</dd>
          </div>
          <div>
            <dt>Perda diaria</dt>
            <dd>{moneyLabel(ticket.estimated_daily_loss)}</dd>
          </div>
          <div>
            <dt>Perda total inicial</dt>
            <dd>{moneyLabel(ticket.estimated_loss_total)}</dd>
          </div>
          <div>
            <dt>Custo estimado</dt>
            <dd>{moneyLabel(ticket.estimated_cost)}</dd>
          </div>
          <div>
            <dt>Impacto operacional</dt>
            <dd>{ticket.operational_impact || "Nao informado"}</dd>
          </div>
        </dl>

        <article className="info-card">
          <h2>Descricao</h2>
          <p>{ticket.description}</p>
        </article>

        <article className="state-card">
          Triagem da engenharia, comentarios, anexos e mudanca de status ainda nao fazem parte desta fase.
        </article>
      </section>
    </section>
  );
}
