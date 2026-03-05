import { useState } from "react";
import "./App.css";
import Navbar from "./components/Navbar";
import Dashboard from "./pages/Dashboard";
import FoodsPage from "./pages/FoodsPage";
import RecommendPage from "./pages/RecommendPage";

export default function App() {
  const [activePage, setActivePage] = useState("dashboard");

  function renderPage() {
    switch (activePage) {
      case "foods":
        return <FoodsPage />;
      case "recommend":
        return <RecommendPage />;
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
