import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { fetchMe, login as loginRequest, logoutRequest, setAccessToken, api } from "../services/api";
import type { Role, User } from "../types";

interface AuthContextValue {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isReviewer: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isInitializing, setIsInitializing] = useState(true);

  useEffect(() => {
    // Attempt silent refresh on mount
    const initAuth = async () => {
      try {
        const { data } = await api.post("/auth/refresh");
        setAccessToken(data.access_token);
        setToken(data.access_token);
        const userData = await fetchMe();
        setUser(userData);
      } catch (err) {
        // No valid session
        setAccessToken(null);
        setToken(null);
        setUser(null);
      } finally {
        setIsInitializing(false);
      }
    };
    initAuth();
  }, []);

  // Update setAccessToken if token changes via login
  useEffect(() => {
    setAccessToken(token);
  }, [token]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      token,
      isAuthenticated: Boolean(token && user),
      isReviewer: user ? ["supervisor", "admin"].includes(user.role as Role) : false,
      login: async (username: string, password: string) => {
        const response = await loginRequest(username, password);
        setToken(response.access_token);
        setUser(response.user);
      },
      logout: async () => {
        try {
          if (token) await logoutRequest();
        } catch {
          // ignore network errors on logout
        } finally {
          setToken(null);
          setUser(null);
        }
      },
    }),
    [token, user],
  );

  if (isInitializing) {
    return <div>Cargando sesión...</div>; // Opcional: reemplazar con un spinner bonito
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth debe usarse dentro de AuthProvider");
  }
  return context;
}
