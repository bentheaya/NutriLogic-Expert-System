/**
 * Shared meal recommendation card (used on Recommend + History pages).
 */

export default function MealCard({ recommendation }) {
  const rec = recommendation || {};
  return (
    <li className="meal-card">
      <div className="meal-items">
        <span className="meal-tag staple">
          🌽 {rec.staple?.replace(/_/g, " ")}
        </span>
        <span className="meal-tag protein">
          🥩 {rec.protein?.replace(/_/g, " ")}
        </span>
        <span className="meal-tag vegetable">
          🥬 {rec.vegetable?.replace(/_/g, " ")}
        </span>
      </div>
      {rec.explanation && <p className="explanation">{rec.explanation}</p>}
    </li>
  );
}
