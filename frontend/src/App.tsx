import { ShieldCheck } from "lucide-react";
import Dashboard from "./pages/Dashboard";
import Gallery from "./pages/Gallery";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Supervisor from "./pages/Supervisor";
import { useAuth } from "./context/AuthContext";

export default function App() {
  const { isAuthenticated, isReviewer, logout, user } = useAuth();

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand">
          <ShieldCheck size={24} />
          <span>SecureFrame Gallery</span>
        </div>
        {isAuthenticated && (
          <div className="session">
            <span>{user?.username} - {user?.role}</span>
            <button type="button" onClick={logout}>Salir</button>
          </div>
        )}
      </header>

      <Gallery />
      {isAuthenticated ? (
        <>
          <Dashboard />
          {isReviewer && <Supervisor />}
        </>
      ) : (
        <section className="auth-grid">
          <Login />
          <Register />
        </section>
      )}
    </main>
  );
}
