/**
 * Navbar.jsx
 * ----------
 * Top navigation bar for the NutriLogic dashboard.
 * Shows auth-aware links: profile & history when logged in, login/register otherwise.
 */

import { Link, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const links = [
    { path: "/", label: "Dashboard" },
    { path: "/foods", label: "Foods" },
    { path: "/recommend", label: "Recommendations" },
    ...(user
      ? [
          { path: "/profile", label: "Profile" },
          { path: "/history", label: "History" },
        ]
      : []),
  ];

  function handleLogout() {
    logout();
    navigate("/");
  }

  return (
    <nav className="navbar">
      <Link to="/" className="navbar-brand" style={{ textDecoration: "none" }}>
        <span className="brand-icon">🥗</span>
        <span className="brand-name">NutriLogic</span>
        <span className="brand-tagline">Expert System</span>
      </Link>
      <ul className="nav-links">
        {links.map((link) => (
          <li key={link.path}>
            <NavLink
              to={link.path}
              end={link.path === "/"}
              className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}
            >
              {link.label}
            </NavLink>
          </li>
        ))}
        {user ? (
          <li>
            <button className="nav-link nav-link-auth" onClick={handleLogout}>
              Sign Out{user.username ? ` (${user.username})` : ""}
            </button>
          </li>
        ) : (
          <>
            <li>
              <NavLink
                to="/login"
                className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}
              >
                Sign In
              </NavLink>
            </li>
            <li>
              <NavLink
                to="/register"
                className={({ isActive }) => (isActive ? "nav-link active" : "nav-link nav-link-register")}
              >
                Register
              </NavLink>
            </li>
          </>
        )}
      </ul>
    </nav>
  );
}
