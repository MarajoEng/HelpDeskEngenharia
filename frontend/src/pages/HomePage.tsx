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
            <li>CRUD administrativo de unidades com paginação e filtros.</li>
            <li>CRUD administrativo de usuarios com hash de senha e vinculo de unidade.</li>
            <li>Permissao de backend por perfil para leitura e gestao.</li>
            <li>Frontend simples para operacao base sem mock fixo.</li>
          </ul>
        </article>

        <article className="panel">
          <h3>Limites preservados</h3>
          <ul className="list">
            <li>Sem chamados, dashboard, upload ou aprovacao nesta etapa.</li>
            <li>Sem exclusao fisica de unidades.</li>
            <li>Sem relatorios, refresh token ou fluxo publico.</li>
          </ul>
        </article>
      </div>
    </section>
  );
}
