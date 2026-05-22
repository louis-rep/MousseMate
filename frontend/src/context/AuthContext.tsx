import { createContext, useContext, useState } from "react";
import * as authApi from "../api/auth";

const TOKEN_KEY = "access_token";

interface AuthContextValue {
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(
    () => localStorage.getItem(TOKEN_KEY) !== null,
  );

  async function login(username: string, password: string): Promise<void> {
    const token = await authApi.login(username, password);
    localStorage.setItem(TOKEN_KEY, token.access_token);
    setIsAuthenticated(true);
  }

  async function register(username: string, password: string): Promise<void> {
    await authApi.register(username, password);
    await login(username, password);
  }

  function logout(): void {
    localStorage.removeItem(TOKEN_KEY);
    setIsAuthenticated(false);
  }

  return (
    <AuthContext.Provider value={{ isAuthenticated, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
