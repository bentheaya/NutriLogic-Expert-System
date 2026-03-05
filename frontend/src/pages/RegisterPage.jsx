/**
 * RegisterPage.jsx
 * ----------------
 * Allows a new user to create an account.
 * On success, navigates to the login page with a confirmation message.
 */

import { useState } from "react";
import { registerUser } from "../api/nutrilogicApi";

export default function RegisterPage({ onNavigate }) {
  const [form, setForm] = useState({
    username: "",
    email: "",
    password: "",
    password2: "",
  });
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [loading, setLoading] = useState(false);

  function handleChange(e) {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    if (form.password !== form.password2) {
      setError("Passwords do not match.");
      return;
    }
    setLoading(true);
    try {
      const data = await registerUser(form);
      setSuccess(data.detail || "Account created! You can now log in.");
      setTimeout(() => onNavigate("login"), 2000);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page auth-page">
      <div className="auth-card card">
        <h2>Create Account</h2>
        <p className="subtitle">Join NutriLogic to save recommendations and track your nutrition.</p>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="reg-username">Username</label>
            <input
              id="reg-username"
              name="username"
              type="text"
              value={form.username}
              onChange={handleChange}
              required
              autoComplete="username"
            />
          </div>
          <div className="form-group">
            <label htmlFor="reg-email">Email (optional)</label>
            <input
              id="reg-email"
              name="email"
              type="email"
              value={form.email}
              onChange={handleChange}
              autoComplete="email"
            />
          </div>
          <div className="form-group">
            <label htmlFor="reg-password">Password</label>
            <input
              id="reg-password"
              name="password"
              type="password"
              value={form.password}
              onChange={handleChange}
              required
              minLength={8}
              autoComplete="new-password"
            />
          </div>
          <div className="form-group">
            <label htmlFor="reg-password2">Confirm Password</label>
            <input
              id="reg-password2"
              name="password2"
              type="password"
              value={form.password2}
              onChange={handleChange}
              required
              minLength={8}
              autoComplete="new-password"
            />
          </div>
          {error && <p className="status-msg error">{error}</p>}
          {success && <p className="status-msg success">{success}</p>}
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? "Creating account…" : "Register"}
          </button>
        </form>
        <p className="auth-switch">
          Already have an account?{" "}
          <button className="link-btn" onClick={() => onNavigate("login")}>
            Sign In
          </button>
        </p>
      </div>
    </div>
  );
}
