import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Dashboard from './pages/Dashboard';
import Gallery from './pages/Gallery';
import Login from './pages/Login';
import Register from './pages/Register';
import Supervisor from './pages/Supervisor';

function PrivateRoute({ children, role }: { children: React.ReactNode; role?: string | string[] }) {
  const { isAuthenticated, loading, user } = useAuth();
  if (loading) return <div className="loading">Cargando...</div>;
  if (!isAuthenticated) return <Navigate to="/login" replace />;

  if (role) {
    const allowedRoles = Array.isArray(role) ? role : [role];
    const hasAccess = !!user && allowedRoles.includes(user.role);
    if (!hasAccess) return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Gallery />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/dashboard" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
      <Route path="/supervisor" element={<PrivateRoute role={['supervisor', 'admin']}><Supervisor /></PrivateRoute>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}
