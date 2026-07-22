/**
 * HistoryPage.jsx
 * ---------------
 * Displays the authenticated user's last 20 recommendation logs.
 */

import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { getRecommendationHistory } from "../api/nutrilogicApi";
import MealCard from "../components/MealCard";

export default function HistoryPage() {
  const { accessToken } = useAuth();
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!accessToken) return;
    getRecommendationHistory(accessToken)
      .then(setLogs)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [accessToken]);

  if (loading) return <p className="status-msg">Loading history…</p>;
  if (error) return <p className="status-msg error">Error: {error}</p>;

  return (
    <div className="page">
      <div className="card">
        <h2>Recommendation History</h2>
        <p className="subtitle">
          Your last {logs.length} recommendation{logs.length !== 1 ? "s" : ""}.
        </p>

        {logs.length === 0 ? (
          <p>
            No recommendations saved yet. Use the Recommendations page and they will appear here.
          </p>
        ) : (
          <ul className="history-list">
            {logs.map((log) => (
              <li key={log.id} className="history-item card">
                <div className="history-meta">
                  <span className="history-date">
                    {new Date(log.created_at).toLocaleString("en-KE", {
                      dateStyle: "medium",
                      timeStyle: "short",
                    })}
                  </span>
                  {log.condition ? (
                    <span className="history-badge condition">
                      Condition: {log.condition.replace(/_/g, " ")}
                    </span>
                  ) : (
                    <span className="history-badge symptoms">
                      Symptoms: {log.symptoms.join(", ").replace(/_/g, " ")}
                    </span>
                  )}
                </div>
                {log.recommendations.length > 0 ? (
                  <ul className="meal-list">
                    {log.recommendations.map((rec, i) => (
                      <MealCard key={i} recommendation={rec} />
                    ))}
                  </ul>
                ) : (
                  <p>No meals returned for this query.</p>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
