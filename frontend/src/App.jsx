import { useState } from "react";
import "./App.css";
import { AuthProvider, useAuth } from "./context/AuthContext";
import Navbar from "./components/Navbar";
import Dashboard from "./pages/Dashboard";
import FoodsPage from "./pages/FoodsPage";
import RecommendPage from "./pages/RecommendPage";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import ProfilePage from "./pages/ProfilePage";
import HistoryPage from "./pages/HistoryPage";

function AppInner() {
  const [activePage, setActivePage] = useState("dashboard");
  const { user } = useAuth();

  function renderPage() {
    switch (activePage) {
      case "foods":
        return <FoodsPage />;
      case "recommend":
        return <RecommendPage />;
      case "login":
        return <LoginPage onNavigate={setActivePage} />;
      case "register":
        return <RegisterPage onNavigate={setActivePage} />;
      case "profile":
        return user ? <ProfilePage /> : <LoginPage onNavigate={setActivePage} />;
      case "history":
        return user ? <HistoryPage /> : <LoginPage onNavigate={setActivePage} />;
      default:
        return <Dashboard onNavigate={setActivePage} />;
    }
  }

  return (
    <div className="app">
      <Navbar activePage={activePage} onNavigate={setActivePage} />
      <main className="main-content">{renderPage()}</main>
      <footer className="footer">
        <p>NutriLogic &copy; 2025 — MOH Kenya Nutrient Profile Model</p>
      </footer>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppInner />
    </AuthProvider>
  );
}
