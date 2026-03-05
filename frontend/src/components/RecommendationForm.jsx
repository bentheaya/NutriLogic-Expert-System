/**
 * RecommendationForm.jsx
 * ----------------------
 * Allows the user to request personalised meal recommendations either by
 * selecting a known health condition OR by ticking applicable symptoms.
 * Results are displayed with the Prolog-generated explanation.
 */

import { useState } from "react";
import { recommendByCondition, recommendBySymptoms } from "../api/nutrilogicApi";

const CONDITIONS = [
  { value: "healthy", label: "Healthy (general)" },
  { value: "hypertension", label: "Hypertension" },
  { value: "type2_diabetes", label: "Type 2 Diabetes" },
  { value: "anaemia", label: "Anaemia" },
  { value: "vitA_deficiency", label: "Vitamin A Deficiency" },
  { value: "rickets", label: "Rickets / Vitamin D Deficiency" },
];

const SYMPTOMS = [
  { value: "fatigue", label: "Fatigue / tiredness" },
  { value: "pale_skin", label: "Pale skin" },
  { value: "night_blindness", label: "Night blindness" },
  { value: "dry_skin", label: "Dry skin" },
  { value: "frequent_infections", label: "Frequent infections" },
  { value: "bone_pain", label: "Bone pain" },
  { value: "muscle_weakness", label: "Muscle weakness" },
  { value: "rickets", label: "Rickets (bowing of legs)" },
  { value: "mouth_sores", label: "Mouth sores" },
  { value: "muscle_cramps", label: "Muscle cramps" },
];

export default function RecommendationForm() {
  const [mode, setMode] = useState("condition"); // "condition" | "symptoms"
  const [condition, setCondition] = useState("healthy");
  const [selectedSymptoms, setSelectedSymptoms] = useState([]);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  function toggleSymptom(value) {
    setSelectedSymptoms((prev) =>
      prev.includes(value) ? prev.filter((s) => s !== value) : [...prev, value]
    );
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResults(null);
    try {
      let data;
      if (mode === "condition") {
        data = await recommendByCondition(condition);
        setResults({ label: `Condition: ${condition}`, ...data });
      } else {
        if (selectedSymptoms.length === 0) {
          setError("Please select at least one symptom.");
          return;
        }
        data = await recommendBySymptoms(selectedSymptoms);
        setResults({ label: `Symptoms: ${selectedSymptoms.join(", ")}`, ...data });
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="card">
      <h2>Get Personalised Meal Recommendations</h2>

      {/* Mode toggle */}
      <div className="mode-toggle">
        <button
          className={mode === "condition" ? "active" : ""}
          onClick={() => setMode("condition")}
          type="button"
        >
          By Condition
        </button>
        <button
          className={mode === "symptoms" ? "active" : ""}
          onClick={() => setMode("symptoms")}
          type="button"
        >
          By Symptoms
        </button>
      </div>

      <form onSubmit={handleSubmit}>
        {mode === "condition" ? (
          <div className="form-group">
            <label htmlFor="condition-select">Health Condition</label>
            <select
              id="condition-select"
              value={condition}
              onChange={(e) => setCondition(e.target.value)}
            >
              {CONDITIONS.map((c) => (
                <option key={c.value} value={c.value}>
                  {c.label}
                </option>
              ))}
            </select>
          </div>
        ) : (
          <fieldset className="symptoms-grid">
            <legend>Select symptoms you are experiencing</legend>
            {SYMPTOMS.map((s) => (
              <label key={s.value} className="checkbox-label">
                <input
                  type="checkbox"
                  checked={selectedSymptoms.includes(s.value)}
                  onChange={() => toggleSymptom(s.value)}
                />
                {s.label}
              </label>
            ))}
          </fieldset>
        )}

        <button type="submit" className="btn-primary" disabled={loading}>
          {loading ? "Thinking…" : "Get Recommendations"}
        </button>
      </form>

      {error && <p className="status-msg error">Error: {error}</p>}

      {results && (
        <div className="results">
          <h3>Results — {results.label}</h3>
          {results.recommendations.length === 0 ? (
            <p>No recommendations found. Try a different condition or symptoms.</p>
          ) : (
            <ul className="meal-list">
              {results.recommendations.map((rec, i) => (
                <li key={i} className="meal-card">
                  <div className="meal-items">
                    <span className="meal-tag staple">
                      🌽 {rec.staple.replace(/_/g, " ")}
                    </span>
                    <span className="meal-tag protein">
                      🥩 {rec.protein.replace(/_/g, " ")}
                    </span>
                    <span className="meal-tag vegetable">
                      🥬 {rec.vegetable.replace(/_/g, " ")}
                    </span>
                  </div>
                  <p className="explanation">{rec.explanation}</p>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </section>
  );
}
