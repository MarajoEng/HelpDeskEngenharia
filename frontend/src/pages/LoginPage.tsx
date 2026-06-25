import { useState, type FormEvent } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";

import Button from "../components/ui/Button";
import Input from "../components/ui/Input";
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
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        {/* Logo area */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-teal-600 mb-4">
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          </div>
          <h1 className="text-xl font-bold text-white">Portal de Chamados</h1>
          <p className="text-sm text-slate-400 mt-1">Engenharia e Manutencao Estrutural</p>
        </div>

        {/* Login card */}
        <div className="bg-white rounded-2xl shadow-2xl p-8">
          <div className="mb-6">
            <p className="text-xs font-semibold text-teal-600 uppercase tracking-wider mb-1">Acesso seguro</p>
            <h2 className="text-2xl font-bold text-slate-900">Entrar</h2>
            <p className="text-sm text-slate-500 mt-1">
              Use um usuario existente para acessar o sistema.
            </p>
          </div>

          <form className="space-y-4" onSubmit={handleSubmit}>
            <Input
              autoComplete="email"
              label="Email"
              name="email"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="admin@local.test"
              required
            />

            <Input
              autoComplete="current-password"
              label="Senha"
              name="password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Sua senha"
              required
            />

            {errorMessage ? (
              <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-3 text-sm">
                {errorMessage}
              </div>
            ) : null}

            <Button block variant="primary" type="submit" disabled={isLoading} size="lg">
              {isLoading ? "Validando acesso..." : "Entrar"}
            </Button>
          </form>

          {import.meta.env.DEV && (
            <div className="mt-6 p-4 bg-slate-50 border border-slate-200 rounded-lg text-xs">
              <p className="font-semibold text-slate-700 mb-2">Credenciais de Demo (Apenas Local)</p>
              <ul className="space-y-1 text-slate-500">
                <li><strong className="text-slate-700">admin@local.test</strong> / admin123</li>
                <li><strong className="text-slate-700">engenharia@local.test</strong> / admin123</li>
                <li><strong className="text-slate-700">diretor@local.test</strong> / admin123</li>
                <li><strong className="text-slate-700">gerente0101@local.test</strong> / admin123</li>
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
