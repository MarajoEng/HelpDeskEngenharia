import { Navigate, Outlet, Route, Routes, useLocation } from "react-router-dom";

import AppLayout from "./components/layout/AppLayout";
import { AuthProvider, useAuth } from "./hooks/useAuth";
import HomePage from "./pages/HomePage";
import LoginPage from "./pages/LoginPage";
import UnitsPage from "./pages/UnitsPage";
import UsersPage from "./pages/UsersPage";

function ProtectedShell() {
  const location = useLocation();
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="screen-state">
        <div className="screen-state__card panel">
          <p className="eyebrow">Autenticacao</p>
          <h2>Validando sessao</h2>
          <p>Aguarde enquanto o token atual eh conferido no backend.</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  return (
    <AppLayout>
      <Outlet />
    </AppLayout>
  );
}

function LoginRoute() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="screen-state">
        <div className="screen-state__card panel">
          <p className="eyebrow">Autenticacao</p>
          <h2>Preparando acesso</h2>
          <p>Carregando contexto do usuario.</p>
        </div>
      </div>
    );
  }

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return <LoginPage />;
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginRoute />} />
        <Route element={<ProtectedShell />}>
          <Route path="/" element={<HomePage />} />
          <Route path="/units" element={<UnitsPage />} />
          <Route path="/users" element={<UsersPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  );
}
