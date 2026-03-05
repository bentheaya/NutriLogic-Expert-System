/**
 * FoodList.jsx
 * ------------
 * Displays all Kenyan foods from the NutriLogic knowledge base in a table.
 */

import { useEffect, useState } from "react";
import { getFoods } from "../api/nutrilogicApi";

export default function FoodList() {
  const [foods, setFoods] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    getFoods()
      .then(setFoods)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="status-msg">Loading foods…</p>;
  if (error) return <p className="status-msg error">Error: {error}</p>;

  return (
    <section className="card">
      <h2>Kenyan Foods Knowledge Base</h2>
      <p className="subtitle">
        {foods.length} foods catalogued per MOH 2025 Kenya Nutrient Profile Model
      </p>
      <div className="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>Food</th>
              <th>Group</th>
              <th>Cal (per 100 g)</th>
              <th>Protein (g)</th>
              <th>Carbs (g)</th>
              <th>Fat (g)</th>
              <th>Fibre (g)</th>
            </tr>
          </thead>
          <tbody>
            {foods.map((f) => (
              <tr key={f.name}>
                <td>{f.name.replace(/_/g, " ")}</td>
                <td>{f.food_group.replace(/_/g, " ")}</td>
                <td>{f.calories_per_100g}</td>
                <td>{f.protein_g}</td>
                <td>{f.carbs_g}</td>
                <td>{f.fat_g}</td>
                <td>{f.fibre_g}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
