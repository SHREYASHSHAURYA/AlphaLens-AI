import { Link, useLocation } from "react-router-dom";
import { useData } from "../context/DataContext";

const links = [
  { to: "/", label: "Dashboard" },
  { to: "/portfolio", label: "Portfolio" },
  { to: "/simulator", label: "Simulator" },
  { to: "/robustness", label: "Robustness" },
  { to: "/system", label: "System" },
];

export default function Navbar() {
  const location = useLocation();
  const { fetchData, loading, lastUpdated } = useData();

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-[#1E293B] bg-opacity-95 backdrop-blur-sm border-b border-slate-700 px-6 py-3 flex items-center justify-between">
      <span className="text-accent font-bold text-lg tracking-wide">
        AlphaLens AI
      </span>
      <div className="flex gap-6">
        {links.map((l) => (
          <Link
            key={l.to}
            to={l.to}
            className={`text-sm font-medium transition-colors ${location.pathname === l.to ? "text-accent" : "text-slate-400 hover:text-text"}`}
          >
            {l.label}
          </Link>
        ))}
      </div>
      <div className="flex items-center gap-3">
        {lastUpdated && (
          <span className="text-xs text-slate-500">
            Updated: {lastUpdated.toLocaleTimeString()}
          </span>
        )}
        <button
          onClick={fetchData}
          disabled={loading}
          className="bg-accent text-bg text-sm font-semibold px-4 py-2 rounded-lg hover:opacity-90 disabled:opacity-50"
        >
          {loading ? "Scanning..." : "Scan Market"}
        </button>
      </div>
    </nav>
  );
}
