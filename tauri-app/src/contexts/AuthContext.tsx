import { createContext, useContext, useState, useCallback, type ReactNode } from 'react';
import type { User } from '../types';
import * as api from '../api/client';

interface AuthState {
  token: string | null;
  user: User | null;
  isAuthenticated: boolean;
  login: (code: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setTokenState] = useState<string | null>(
    localStorage.getItem('access_token')
  );
  const [user, setUser] = useState<User | null>(null);

  const login = useCallback(async (code: string) => {
    const data = await api.login(code);
    setTokenState(data.access_token);
    setUser(data.user);
  }, []);

  const logout = useCallback(() => {
    api.clearToken();
    setTokenState(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        token,
        user,
        isAuthenticated: !!token,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return ctx;
}
