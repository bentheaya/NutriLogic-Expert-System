/**
 * Dashboard.jsx
 * -------------
 * Landing page for NutriLogic: shows a summary and quick-access cards.
 */

export default function Dashboard({ onNavigate }) {
  const cards = [
    {
      icon: "🥘",
      title: "Food Knowledge Base",
      description:
        "Browse 20+ catalogued Kenyan foods with nutritional data based on MOH 2025 Kenya Nutrient Profile Model.",
      action: "foods",
      actionLabel: "Browse Foods",
    },
    {
      icon: "🤖",
      title: "AI Recommendations",
      description:
        "Get personalised meal recommendations powered by SWI-Prolog backward chaining inference.",
      action: "recommend",
      actionLabel: "Get Recommendations",
    },
  ];

  return (
    <div className="page dashboard">
      <div className="hero">
        <h1>NutriLogic Expert System</h1>
        <p>
          A hybrid Neuro-Symbolic Expert System for personalised nutrition and fitness in
          Kenya. Combining symbolic logic (Prolog) with modern web technology to deliver
          culturally-sensitive, explainable health recommendations.
        </p>
      </div>

      <div className="card-grid">
        {cards.map((card) => (
          <div className="feature-card" key={card.action}>
            <div className="feature-icon">{card.icon}</div>
            <h3>{card.title}</h3>
            <p>{card.description}</p>
            <button
              className="btn-primary"
              onClick={() => onNavigate(card.action)}
            >
              {card.actionLabel}
            </button>
          </div>
        ))}
      </div>

      <div className="card system-info">
        <h2>System Architecture</h2>
        <ul className="arch-list">
          <li>
            <strong>Frontend:</strong> ReactJS + Vite — responsive dashboard
          </li>
          <li>
            <strong>Backend:</strong> Django (Python) — authentication, PostgreSQL
            storage, REST API gateway
          </li>
          <li>
            <strong>Expert Core:</strong> SWI-Prolog — backward chaining inference engine
            with explainable recommendations
          </li>
          <li>
            <strong>Bridge:</strong> pyswip — integrates Django with the Prolog engine
          </li>
          <li>
            <strong>Knowledge Base:</strong> MOH 2025 Kenya Nutrient Profile Model covering
            Hypertension, Type 2 Diabetes, Anaemia, and micronutrient deficiencies
          </li>
        </ul>
      </div>
    </div>
  );
}
