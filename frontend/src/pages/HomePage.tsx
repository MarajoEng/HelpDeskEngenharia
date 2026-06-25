import { useAuth } from "../hooks/useAuth";

export default function HomePage() {
  const { user } = useAuth();

  return (
    <section className="page">
      <div className="page__header">
        <div>
          <p className="eyebrow">Base autenticada</p>
          <h2 className="page__title">Acesso inicial liberado para o portal.</h2>
        </div>
        <span className="priority-badge priority-badge--medium">JWT ativo</span>
      </div>

      <div className="page__grid">
        <article className="panel panel--feature">
          <h3>Sessao atual</h3>
          <p className="panel__lead">
            Usuario autenticado no frontend a partir de `/auth/login` e
            validado novamente por `/auth/me`.
          </p>
          <dl className="details-list">
            <div>
              <dt>Nome</dt>
              <dd>{user?.name}</dd>
            </div>
            <div>
              <dt>Email</dt>
              <dd>{user?.email}</dd>
            </div>
            <div>
              <dt>Perfil</dt>
              <dd>{user?.role}</dd>
            </div>
            <div>
              <dt>Unidade</dt>
              <dd>{user?.unit_id ?? "Nao vinculada"}</dd>
            </div>
          </dl>
        </article>

        <article className="panel">
          <h3>Escopo desta fase</h3>
          <ul className="list">
            <li>Abertura de chamados com status inicial `open` e numero unico gerado no backend.</li>
            <li>Permissoes por perfil para criar, listar e detalhar chamados.</li>
            <li>Triagem tecnica com responsavel, ajuste de prioridade/severidade, SLA e comentario auditavel.</li>
            <li>Fila dedicada da engenharia, alçadas configuraveis e aprovacao de orcamento no detalhe sem mock fixo.</li>
          </ul>
        </article>

        <article className="panel">
          <h3>Limites preservados</h3>
          <ul className="list">
            <li>Sem execucao, encerramento, anexos ou dashboard operacional.</li>
            <li>Sem dashboard, relatorios, upload ou automacoes assincronas.</li>
            <li>Sem Celery ou qualquer fluxo da FASE 9 em diante.</li>
          </ul>
        </article>
      </div>
    </section>
  );
}
