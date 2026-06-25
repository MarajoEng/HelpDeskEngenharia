import type { PropsWithChildren } from "react";

export default function AppLayout({ children }: PropsWithChildren) {
  return (
    <div className="shell">
      <header className="shell__header">
        <div>
          <p className="shell__kicker">Engenharia e Manutencao</p>
          <strong>Portal de Chamados</strong>
        </div>
        <span className="shell__badge">Base inicial</span>
      </header>

      <main className="shell__content">{children}</main>

      <footer className="shell__footer">
        Estrutura inicial pronta para as proximas fases do projeto.
      </footer>
    </div>
  );
}
