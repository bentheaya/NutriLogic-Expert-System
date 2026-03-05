/**
 * Navbar.jsx
 * ----------
 * Top navigation bar for the NutriLogic dashboard.
 * Shows auth-aware links: profile & history when logged in, login/register otherwise.
 */

import { useAuth } from "../context/AuthContext";

export default function Navbar({ activePage, onNavigate }) {
  const { user, logout } = useAuth();

  const links = [
    { key: "dashboard", label: "Dashboard" },
    { key: "foods", label: "Foods" },
    { key: "recommend", label: "Recommendations" },
    ...(user
      ? [
          { key: "profile", label: "Profile" },
          { key: "history", label: "History" },
        ]
      : []),
  ];

  function handleLogout() {
    logout();
    onNavigate("dashboard");
  }

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
        {user ? (
          <li>
            <button className="nav-link nav-link-auth" onClick={handleLogout}>
              Sign Out ({user.username})
            </button>
          </li>
        ) : (
          <>
            <li>
              <button
                className={activePage === "login" ? "nav-link active" : "nav-link"}
                onClick={() => onNavigate("login")}
              >
                Sign In
              </button>
            </li>
            <li>
              <button
                className={activePage === "register" ? "nav-link active" : "nav-link nav-link-register"}
                onClick={() => onNavigate("register")}
              >
                Register
              </button>
            </li>
          </>
        )}
      </ul>
    </nav>
  );
}

