import { useEffect, useState } from "react";
import { api } from "./api";
import type { Health } from "./types";
import ReviewPage from "./components/ReviewPage";
import StatsPage from "./components/StatsPage";

type Tab = "review" | "stats";

export default function App() {
  const [tab, setTab] = useState<Tab>("review");
  const [health, setHealth] = useState<Health | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);

  useEffect(() => {
    api.health().then(setHealth).catch((e: Error) => setHealthError(e.message));
  }, []);

  return (
    <>
      <a className="skip" href="#main">Skip to content</a>
      <header className="site-header">
        <div className="wrap header-row">
          <div>
            <h1>PanelAssist</h1>
            <p className="tagline">Advisory pre-screening for hackathon judges</p>
          </div>
          <nav aria-label="Primary">
            <button className={tab === "review" ? "tab active" : "tab"} aria-current={tab === "review" ? "page" : undefined}
              onClick={() => setTab("review")}>Review</button>
            <button className={tab === "stats" ? "tab active" : "tab"} aria-current={tab === "stats" ? "page" : undefined}
              onClick={() => setTab("stats")}>Usage stats</button>
          </nav>
        </div>
        <div className="advisory-bar" role="note">
          <div className="wrap">
            <strong>Advisory only.</strong> PanelAssist suggests scores with evidence. It never accepts, rejects,
            ranks or awards anything. The score that counts is yours.
          </div>
        </div>
      </header>

      <main id="main" className="wrap">
        {healthError && (
          <div className="banner banner-error" role="alert">
            Cannot reach the PanelAssist API ({healthError}). Start it with{" "}
            <code>uvicorn webapp.backend.app:app</code> from the repository root.
          </div>
        )}
        {health && (
          <div className={health.llm_configured ? "banner banner-live" : "banner banner-offline"} role="status">
            <strong>{health.llm_configured ? "Live mode." : "Offline mode."}</strong> {health.message}
          </div>
        )}
        {tab === "review" ? <ReviewPage /> : <StatsPage />}
      </main>

      <footer className="wrap site-footer">
        <p>
          All bundled samples are synthetic and written to test the tool. Nothing here is a real submission or a real
          judging result.
        </p>
      </footer>
    </>
  );
}
