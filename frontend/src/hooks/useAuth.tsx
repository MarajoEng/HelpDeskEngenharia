import {
  createContext,
  useContext,
  useEffect,
  useState,
  type PropsWithChildren,
} from "react";

import { getCurrentUser, loginRequest } from "../api/authApi";
import type { CurrentUser, LoginRequest } from "../types/auth";

const storageKey = "portal_chamados_auth_token";

interface AuthContextValue {
  user: CurrentUser | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  errorMessage: string | null;
  login: (payload: LoginRequest) => Promise<void>;
  logout: () => void;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function getStoredToken() {
  if (typeof window === "undefined") {
    return null;
  }

  return window.localStorage.getItem(storageKey);
}

function persistToken(token: string | null) {
  if (typeof window === "undefined") {
    return;
  }

  if (token) {
    window.localStorage.setItem(storageKey, token);
    return;
  }

  window.localStorage.removeItem(storageKey);
}

export function AuthProvider({ children }: PropsWithChildren) {
  const [token, setToken] = useState<string | null>(() => getStoredToken());
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(Boolean(getStoredToken()));
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      setUser(null);
      setIsLoading(false);
      return;
    }

    if (user) {
      setIsLoading(false);
      return;
    }

    let isActive = true;
    setIsLoading(true);

    getCurrentUser(token)
      .then((currentUser) => {
        if (!isActive) {
          return;
        }

        setUser(currentUser);
        setErrorMessage(null);
      })
      .catch((error: unknown) => {
        if (!isActive) {
          return;
        }

        persistToken(null);
        setToken(null);
        setUser(null);
        setErrorMessage(
          error instanceof Error ? error.message : "Sessao invalida. Faca login novamente.",
        );
      })
      .finally(() => {
        if (isActive) {
          setIsLoading(false);
        }
      });

    return () => {
      isActive = false;
    };
  }, [token, user]);

  async function login(payload: LoginRequest) {
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const tokenResponse = await loginRequest(payload);
      persistToken(tokenResponse.access_token);

      const currentUser = await getCurrentUser(tokenResponse.access_token);
      setToken(tokenResponse.access_token);
      setUser(currentUser);
    } catch (error: unknown) {
      persistToken(null);
      setToken(null);
      setUser(null);
      setErrorMessage(
        error instanceof Error ? error.message : "Nao foi possivel autenticar.",
      );
      throw error;
    } finally {
      setIsLoading(false);
    }
  }

  function logout() {
    persistToken(null);
    setToken(null);
    setUser(null);
    setErrorMessage(null);
  }

  function clearError() {
    setErrorMessage(null);
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: Boolean(token && user),
        isLoading,
        errorMessage,
        login,
        logout,
        clearError,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used within AuthProvider.");
  }

  return context;
}
