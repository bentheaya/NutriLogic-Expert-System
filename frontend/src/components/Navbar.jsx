/**
 * Navbar.jsx
 * ----------
 * Top navigation bar for the NutriLogic dashboard.
 */

export default function Navbar({ activePage, onNavigate }) {
  const links = [
    { key: "dashboard", label: "Dashboard" },
    { key: "foods", label: "Foods" },
    { key: "recommend", label: "Recommendations" },
  ];

  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <span className="brand-icon">🥗</span>
        <span className="brand-name">NutriLogic</span>
        <span className="brand-tagline">Expert System</span>
      </div>
      <ul className="nav-links">
        {links.map((link) => (
          <li key={link.key}>
            <button
              className={activePage === link.key ? "nav-link active" : "nav-link"}
              onClick={() => onNavigate(link.key)}
            >
              {link.label}
            </button>
          </li>
        ))}
      </ul>
    </nav>
  );
}
