import { NavLink, Route, Routes } from "react-router-dom";

import Home from "./pages/Home";
import Results from "./pages/Results";
import History from "./pages/History";
import NotFound from "./pages/NotFound";

export default function App() {
  return (
    <div className="min-h-screen bg-[var(--bg-primary)] text-[var(--text-primary)]">
      <header className="border-b border-[var(--border)] bg-[rgba(10,15,30,0.88)] backdrop-blur">
        <div className="mx-auto flex w-full max-w-7xl items-center justify-between px-6 py-5">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-[var(--text-primary)]">
              SentiScope
            </h1>
            <p className="text-sm text-[var(--text-muted)]">
              Sentiment analysis for text and articles
            </p>
          </div>
          <nav className="flex items-center gap-5 text-sm font-medium" aria-label="Main navigation">
            <NavLink
              to="/"
              end
              className={({ isActive }) =>
                isActive ? "text-[var(--accent)]" : "text-[var(--text-muted)] transition hover:text-[var(--accent)]"
              }
            >
              Analyze
            </NavLink>
            <NavLink
              to="/history"
              className={({ isActive }) =>
                isActive ? "text-[var(--accent)]" : "text-[var(--text-muted)] transition hover:text-[var(--accent)]"
              }
            >
              History
            </NavLink>
          </nav>
        </div>
      </header>

      <main className="mx-auto w-full max-w-7xl px-6 py-10">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/results" element={<Results />} />
          <Route path="/history" element={<History />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
    </div>
  );
}
