/**
 * AuthContext.jsx
 * ---------------
 * Provides JWT-based authentication state and helpers throughout the app.
 *
 * Stores the access token in memory (React state) and the refresh token in
 * localStorage so the session survives a page reload.
 */

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { refreshToken as apiRefreshToken } from "../api/nutrilogicApi";

const TOKEN_KEY = "nutrilogic_refresh";

const AuthContext = createContext(null);

function decodePayload(token) {
  try {
    const payloadB64 = token.split(".")[1];
    const padded = payloadB64 + "=".repeat((4 - (payloadB64.length % 4)) % 4);
    return JSON.parse(atob(padded.replace(/-/g, "+").replace(/_/g, "/")));
  } catch {
    return null;
  }
}

function userFromAccessToken(access) {
  const payload = decodePayload(access);
  if (!payload) return null;
  // Backend embeds username via NutriLogicTokenObtainPairSerializer.
  if (payload.username) {
    return { username: payload.username, userId: payload.user_id };
  }
  return { username: null, userId: payload.user_id };
}

export function AuthProvider({ children }) {
  const [accessToken, setAccessToken] = useState(null);
  const [user, setUser] = useState(null);

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setAccessToken(null);
    setUser(null);
  }, []);

  useEffect(() => {
    const stored = localStorage.getItem(TOKEN_KEY);
    if (!stored) return;

    apiRefreshToken(stored)
      .then((data) => {
        const access = data?.access;
        if (!access) {
          localStorage.removeItem(TOKEN_KEY);
          return;
        }
        // SimpleJWT with ROTATE_REFRESH_TOKENS returns a new refresh token.
        if (data.refresh) {
          localStorage.setItem(TOKEN_KEY, data.refresh);
        }
        setAccessToken(access);
        setUser(userFromAccessToken(access));
      })
      .catch(() => {
        localStorage.removeItem(TOKEN_KEY);
      });
  }, []);

  function login(accessTok, refreshTok) {
    localStorage.setItem(TOKEN_KEY, refreshTok);
    setAccessToken(accessTok);
    setUser(userFromAccessToken(accessTok));
  }

  return (
    <AuthContext.Provider value={{ accessToken, user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  return useContext(AuthContext);
}
