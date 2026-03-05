/**
 * ProfilePage.jsx
 * ---------------
 * Shows the authenticated user's profile and lets them update basic health
 * metrics: age, weight, height, activity level, and county.
 */

import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { getProfile, updateProfile } from "../api/nutrilogicApi";

const ACTIVITY_OPTIONS = [
  { value: "sedentary", label: "Sedentary" },
  { value: "light", label: "Lightly Active" },
  { value: "moderate", label: "Moderately Active" },
  { value: "active", label: "Active" },
  { value: "very_active", label: "Very Active" },
];

export default function ProfilePage() {
  const { accessToken, user } = useAuth();
  const [profile, setProfile] = useState(null);
  const [form, setForm] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  useEffect(() => {
    if (!accessToken) return;
    getProfile(accessToken)
      .then((data) => {
        setProfile(data);
        setForm({
          age: data.age ?? "",
          weight_kg: data.weight_kg ?? "",
          height_cm: data.height_cm ?? "",
          activity_level: data.activity_level ?? "moderate",
          county: data.county ?? "",
        });
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [accessToken]);

  function handleChange(e) {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setSaving(true);
    try {
      const updated = await updateProfile(form, accessToken);
      setProfile(updated);
      setSuccess("Profile updated successfully.");
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <p className="status-msg">Loading profile…</p>;

  return (
    <div className="page">
      <div className="card">
        <h2>My Profile</h2>
        {user && <p className="subtitle">Logged in as <strong>{user.username}</strong></p>}

        <form onSubmit={handleSubmit}>
          <div className="profile-grid">
            <div className="form-group">
              <label htmlFor="age">Age (years)</label>
              <input
                id="age"
                name="age"
                type="number"
                min="1"
                max="120"
                value={form.age}
                onChange={handleChange}
                placeholder="e.g. 28"
              />
            </div>
            <div className="form-group">
              <label htmlFor="weight_kg">Weight (kg)</label>
              <input
                id="weight_kg"
                name="weight_kg"
                type="number"
                min="1"
                step="0.01"
                value={form.weight_kg}
                onChange={handleChange}
                placeholder="e.g. 65.5"
              />
            </div>
            <div className="form-group">
              <label htmlFor="height_cm">Height (cm)</label>
              <input
                id="height_cm"
                name="height_cm"
                type="number"
                min="50"
                step="0.1"
                value={form.height_cm}
                onChange={handleChange}
                placeholder="e.g. 170"
              />
            </div>
            <div className="form-group">
              <label htmlFor="county">County</label>
              <input
                id="county"
                name="county"
                type="text"
                value={form.county}
                onChange={handleChange}
                placeholder="e.g. Nairobi"
                maxLength={100}
              />
            </div>
            <div className="form-group">
              <label htmlFor="activity_level">Activity Level</label>
              <select
                id="activity_level"
                name="activity_level"
                value={form.activity_level}
                onChange={handleChange}
              >
                {ACTIVITY_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>
          </div>

          {error && <p className="status-msg error">{error}</p>}
          {success && <p className="status-msg success">{success}</p>}

          <button type="submit" className="btn-primary" disabled={saving}>
            {saving ? "Saving…" : "Save Profile"}
          </button>
        </form>

        {profile?.conditions?.length > 0 && (
          <div className="conditions-section">
            <h3>Registered Health Conditions</h3>
            <ul className="conditions-list">
              {profile.conditions.map((c) => (
                <li key={c.id}>{c.condition}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
