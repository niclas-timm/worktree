import { createContext, useContext, useState, useEffect } from "react";
import { authApi } from "@/services/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem("token"));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initAuth = async () => {
      if (token) {
        try {
          const response = await authApi.getUser();
          setUser(response.data);
        } catch {
          localStorage.removeItem("token");
          setToken(null);
        }
      }
      setLoading(false);
    };
    initAuth();
  }, [token]);

  const login = async (email, password) => {
    const response = await authApi.login(email, password);
    const newToken = response.data.key;
    localStorage.setItem("token", newToken);
    setToken(newToken);

    const userResponse = await authApi.getUser();
    setUser(userResponse.data);

    return response;
  };

  const register = async (name, email, password) => {
    // Registration requires email verification, so don't auto-login
    const response = await authApi.register(name, email, password);
    return response;
  };

  const logout = async () => {
    try {
      await authApi.logout();
    } finally {
      localStorage.removeItem("token");
      setToken(null);
      setUser(null);
    }
  };

  const setAuthToken = async (newToken) => {
    localStorage.setItem("token", newToken);
    setToken(newToken);

    const userResponse = await authApi.getUser();
    setUser(userResponse.data);
  };

  const value = {
    user,
    token,
    loading,
    isAuthenticated: !!token,
    login,
    register,
    logout,
    setAuthToken,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
