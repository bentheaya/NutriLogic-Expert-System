/**
 * LoginPage.jsx
 * -------------
 * Allows an existing user to log in with username + password.
 * On success, stores tokens via AuthContext and redirects to the dashboard.
 */

import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { obtainToken } from "../api/nutrilogicApi";

export default function LoginPage({ onNavigate }) {
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const { access, refresh } = await obtainToken(username, password);
      login(access, refresh);
      onNavigate("dashboard");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page auth-page">
      <div className="auth-card card">
        <h2>Sign In</h2>
        <p className="subtitle">Log in to save your recommendations and manage your profile.</p>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="login-username">Username</label>
            <input
              id="login-username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              autoComplete="username"
            />
          </div>
          <div className="form-group">
            <label htmlFor="login-password">Password</label>
            <input
              id="login-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
            />
          </div>
          {error && <p className="status-msg error">{error}</p>}
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? "Signing in…" : "Sign In"}
          </button>
        </form>
        <p className="auth-switch">
          Don&apos;t have an account?{" "}
          <button className="link-btn" onClick={() => onNavigate("register")}>
            Register
          </button>
        </p>
      </div>
    </div>
  );
}
