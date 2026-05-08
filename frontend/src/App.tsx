import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Gallery from './pages/Gallery';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Supervisor from './pages/Supervisor';

function PrivateRoute({ children, role }: { children: React.ReactNode; role?: string }) {
  const { isAuthenticated, loading, user } = useAuth();
  if (loading) return <div className="loading">Loading…</div>;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  // Si un supervisor intenta entrar al dashboard de usuario normal, redirigir a su panel
  if (!role && user?.role === 'supervisor') return <Navigate to="/supervisor" replace />;
  if (role && user?.role !== role) return <Navigate to="/dashboard" replace />;
  return <>{children}</>;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/"           element={<Gallery />} />
      <Route path="/login"      element={<Login />} />
      <Route path="/register"   element={<Register />} />
      <Route path="/dashboard"  element={<PrivateRoute><Dashboard /></PrivateRoute>} />
      <Route path="/supervisor" element={<PrivateRoute role="supervisor"><Supervisor /></PrivateRoute>} />
      <Route path="*"           element={<Navigate to="/" replace />} />
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
