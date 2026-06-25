import { Navigate, Outlet, Route, Routes, useLocation } from "react-router-dom";

import AppLayout from "./components/layout/AppLayout";
import LoadingState from "./components/ui/LoadingState";
import { AuthProvider, useAuth } from "./hooks/useAuth";
import ApprovalLevelsPage from "./pages/ApprovalLevelsPage";
import CreateTicketPage from "./pages/CreateTicketPage";
import DashboardPage from "./pages/DashboardPage";
import EngineeringQueuePage from "./pages/EngineeringQueuePage";
import HomePage from "./pages/HomePage";
import LoginPage from "./pages/LoginPage";
import AlertsPage from "./pages/AlertsPage";
import AuditLogsPage from "./pages/AuditLogsPage";
import ReportsPage from "./pages/ReportsPage";
import SuppliersPage from "./pages/SuppliersPage";
import TicketDetailPage from "./pages/TicketDetailPage";
import TicketsPage from "./pages/TicketsPage";
import UnitsPage from "./pages/UnitsPage";
import UsersPage from "./pages/UsersPage";

function ProtectedShell() {
  const location = useLocation();
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="screen-state">
        <LoadingState
          title="Validando sessao"
          description="Aguarde enquanto o token atual eh conferido no backend."
        />
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
        <LoadingState
          title="Preparando acesso"
          description="Carregando o contexto da sessao autenticada."
        />
      </div>
    );
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
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
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/approval-levels" element={<ApprovalLevelsPage />} />
          <Route path="/engineering" element={<EngineeringQueuePage />} />
          <Route path="/tickets" element={<TicketsPage />} />
          <Route path="/tickets/new" element={<CreateTicketPage />} />
          <Route path="/tickets/:ticketId" element={<TicketDetailPage />} />
          <Route path="/reports" element={<ReportsPage />} />
          <Route path="/alerts" element={<AlertsPage />} />
          <Route path="/audit-logs" element={<AuditLogsPage />} />
          <Route path="/suppliers" element={<SuppliersPage />} />
          <Route path="/units" element={<UnitsPage />} />
          <Route path="/users" element={<UsersPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  );
}
