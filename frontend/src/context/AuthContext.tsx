import React, { createContext, useContext, useReducer, useEffect } from 'react';
import type { AuthUser, Role } from '../types';
import { authApi } from '../services/api';

// ── State ─────────────────────────────────────────────────────────────────
interface AuthState {
  user: AuthUser | null;
  loading: boolean;
}

type AuthAction =
  | { type: 'SET_USER'; payload: AuthUser }
  | { type: 'CLEAR_USER' }
  | { type: 'SET_LOADING'; payload: boolean };

function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case 'SET_USER':   return { ...state, user: action.payload, loading: false };
    case 'CLEAR_USER': return { user: null, loading: false };
    case 'SET_LOADING':return { ...state, loading: action.payload };
    default:           return state;
  }
}

// ── Context ───────────────────────────────────────────────────────────────
interface AuthContextValue {
  user: AuthUser | null;
  loading: boolean;
  role: Role | 'visitor';
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

// ── Provider ──────────────────────────────────────────────────────────────
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(authReducer, { user: null, loading: true });

  // Restaurar sesión al cargar
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) { dispatch({ type: 'SET_LOADING', payload: false }); return; }

    authApi.me()
      .then((res) => dispatch({ type: 'SET_USER', payload: res.data }))
      .catch(() => {
        localStorage.removeItem('access_token');
        dispatch({ type: 'CLEAR_USER' });
      });
  }, []);

  const login = async (username: string, password: string) => {
    await authApi.login(username, password);
    const res = await authApi.me();
    dispatch({ type: 'SET_USER', payload: res.data });
  };

  const logout = () => {
    void authApi.logout();
    dispatch({ type: 'CLEAR_USER' });
  };

  const value: AuthContextValue = {
    user: state.user,
    loading: state.loading,
    role: state.user?.role ?? 'visitor',
    isAuthenticated: !!state.user,
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// ── Hook ──────────────────────────────────────────────────────────────────
export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>');
  return ctx;
}
