import { useState, type FormEvent } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../hooks/useAuth";

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { clearError, errorMessage, isAuthenticated, isLoading, login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const redirectTo =
    typeof location.state === "object" &&
    location.state !== null &&
    "from" in location.state &&
    typeof location.state.from === "string"
      ? location.state.from
      : "/";

  if (isAuthenticated) {
    return <Navigate to={redirectTo} replace />;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    clearError();

    try {
      await login({ email, password });
      navigate(redirectTo, { replace: true });
    } catch {
      return;
    }
  }

  return (
    <div className="auth-shell">
      <section className="auth-hero panel">
        <p className="eyebrow">Portal de Chamados Engenharia</p>
        <h1>Acesso seguro para operacao e engenharia.</h1>
        <p className="auth-hero__lead">
          Entre com um usuario valido para consultar o contexto inicial da
          plataforma e validar as permissoes no backend.
        </p>

        <div className="auth-hero__highlights">
          <article className="info-card">
            <h2>Controle no backend</h2>
            <p>JWT com expiracao, usuario ativo e bloqueio por perfil.</p>
          </article>
          <article className="info-card">
            <h2>Base para as proximas fases</h2>
            <p>Sem cadastro publico, sem refresh token e sem CRUD liberado.</p>
          </article>
        </div>
      </section>

      <section className="auth-panel panel">
        <div className="auth-panel__header">
          <p className="eyebrow">Login</p>
          <h2>Entrar</h2>
          <p>
            Use um usuario existente. Para ambiente local, o admin dev pode ser
            criado pelo script documentado.
          </p>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label className="field">
            <span>Email</span>
            <input
              autoComplete="email"
              name="email"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="admin@local.test"
              required
            />
          </label>

          <label className="field">
            <span>Senha</span>
            <input
              autoComplete="current-password"
              name="password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Sua senha"
              required
            />
          </label>

          {errorMessage ? (
            <div className="form-message form-message--error">{errorMessage}</div>
          ) : null}

          <button className="button-primary" type="submit" disabled={isLoading}>
            {isLoading ? "Validando acesso..." : "Entrar"}
          </button>
        </form>
      </section>
    </div>
  );
}
