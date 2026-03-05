/**
 * AuthContext.jsx
 * ---------------
 * Provides JWT-based authentication state and helpers throughout the app.
 *
 * Stores the access token in memory (React state) and the refresh token in
 * localStorage so the session survives a page reload.
 */

import { createContext, useCallback, useContext, useEffect, useState } from "react";

const TOKEN_KEY = "nutrilogic_refresh";
const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

const AuthContext = createContext(null);

// ---------------------------------------------------------------------------
// Module-level helpers (no component state dependency)
// ---------------------------------------------------------------------------

function decodePayload(token) {
  try {
    return JSON.parse(atob(token.split(".")[1]));
  } catch {
    return null;
  }
}

async function refreshAccessToken(refreshToken) {
  const resp = await fetch(`${BASE_URL}/auth/token/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh: refreshToken }),
  });
  if (!resp.ok) return null;
  const data = await resp.json();
  return data.access || null;
}

export function AuthProvider({ children }) {
  const [accessToken, setAccessToken] = useState(null);
  const [user, setUser] = useState(null); // { username, ... } decoded from token

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setAccessToken(null);
    setUser(null);
  }, []);

  // ---------------------------------------------------------------------------
  // On mount: restore session from stored refresh token
  // ---------------------------------------------------------------------------
  useEffect(() => {
    const stored = localStorage.getItem(TOKEN_KEY);
    if (!stored) return;

    refreshAccessToken(stored).then((access) => {
      if (access) {
        setAccessToken(access);
        const payload = decodePayload(access);
        if (payload) setUser({ username: payload.username });
      } else {
        localStorage.removeItem(TOKEN_KEY);
      }
    });
  }, []); // refreshAccessToken is module-level; no closure over state

  // ---------------------------------------------------------------------------
  // login — called after obtaining token pair from the backend
  // ---------------------------------------------------------------------------
  function login(accessTok, refreshTok) {
    localStorage.setItem(TOKEN_KEY, refreshTok);
    setAccessToken(accessTok);
    const payload = decodePayload(accessTok);
    if (payload) setUser({ username: payload.username });
  }

  return (
    <AuthContext.Provider value={{ accessToken, user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
