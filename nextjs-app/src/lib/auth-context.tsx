"use client";

import { createContext, useContext, useReducer, useEffect, useCallback, type ReactNode } from "react";
import { User } from "@/types/user";
import { apiLogin, apiGetMe, apiRefreshToken } from "./api";

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

type AuthAction =
  | { type: "SET_LOADING" }
  | { type: "LOGIN_SUCCESS"; user: User }
  | { type: "LOGOUT" }
  | { type: "AUTH_CHECK_COMPLETE"; user: User | null };

function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case "SET_LOADING":
      return { ...state, isLoading: true };
    case "LOGIN_SUCCESS":
      return { user: action.user, isAuthenticated: true, isLoading: false };
    case "LOGOUT":
      return { user: null, isAuthenticated: false, isLoading: false };
    case "AUTH_CHECK_COMPLETE":
      return {
        user: action.user,
        isAuthenticated: action.user !== null,
        isLoading: false,
      };
    default:
      return state;
  }
}

interface AuthContextType extends AuthState {
  login: (username: string, password: string) => Promise<boolean>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(authReducer, {
    user: null,
    isAuthenticated: false,
    isLoading: true,
  });

  const logout = useCallback(() => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    dispatch({ type: "LOGOUT" });
  }, []);

  const checkAuth = useCallback(async () => {
    const accessToken = localStorage.getItem("access_token");
    const refreshToken = localStorage.getItem("refresh_token");

    if (!accessToken || !refreshToken) {
      dispatch({ type: "AUTH_CHECK_COMPLETE", user: null });
      return;
    }

    try {
      const user = await apiGetMe();
      dispatch({ type: "AUTH_CHECK_COMPLETE", user });
    } catch {
      // Token expired, try refresh
      try {
        const tokens = await apiRefreshToken(refreshToken);
        localStorage.setItem("access_token", tokens.access_token);
        localStorage.setItem("refresh_token", tokens.refresh_token);
        const user = await apiGetMe();
        dispatch({ type: "AUTH_CHECK_COMPLETE", user });
      } catch {
        logout();
      }
    }
  }, [logout]);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  const login = async (username: string, password: string): Promise<boolean> => {
    dispatch({ type: "SET_LOADING" });
    try {
      const tokens = await apiLogin(username, password);
      localStorage.setItem("access_token", tokens.access_token);
      localStorage.setItem("refresh_token", tokens.refresh_token);
      const user = await apiGetMe();
      dispatch({ type: "LOGIN_SUCCESS", user });
      return true;
    } catch {
      dispatch({ type: "AUTH_CHECK_COMPLETE", user: null });
      return false;
    }
  };

  return (
    <AuthContext.Provider value={{ ...state, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
