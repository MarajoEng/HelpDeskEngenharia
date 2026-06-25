export default function HomePage() {
  return (
    <section className="hero">
      <div className="hero__eyebrow">Fundacao tecnica</div>
      <h1>Portal de Chamados Engenharia</h1>
      <p className="hero__lead">
        Base inicial pronta para evoluir abertura, triagem e acompanhamento de
        chamados criticos com backend em FastAPI e frontend em React.
      </p>

      <div className="hero__grid">
        <article className="panel">
          <h2>Fase atual</h2>
          <p>
            Estrutura organizada para crescimento incremental, sem regras de
            negocio, autenticacao ou persistencia nesta etapa.
          </p>
        </article>

        <article className="panel">
          <h2>Preparado para</h2>
          <p>
            Integracao com API real, roteamento de paginas e camadas
            reutilizaveis para os proximos modulos do portal.
          </p>
        </article>
      </div>
    </section>
  );
}
