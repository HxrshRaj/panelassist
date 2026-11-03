import { useEffect, useState } from "react";
import { api } from "../api";
import type { Stats } from "../types";

const dash = (v: number | null, suffix = "") => (v === null ? "-" : `${v}${suffix}`);
const pct = (v: number | null) => (v === null ? "-" : `${Math.round(v * 100)}%`);

export default function StatsPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.stats().then(setStats).catch((e: Error) => setError(e.message));
  }, []);

  if (error) return <p className="error" role="alert">{error}</p>;
  if (!stats) return <p className="running">Loading...</p>;

  return (
    <section className="card" aria-labelledby="stats-h">
      <h2 id="stats-h">Usage stats</h2>
      <p className="hint">
        Everything on this page is computed from the reviews logged by this server and nothing else. There is no seeded
        or example data.
      </p>

      {!stats.has_data ? (
        <div className="empty-state">
          <h3>No reviews logged yet</h3>
          <p>
            When a judge opens a review, rates a check, or saves their scores, the counts appear here: how long
            reviews take, how often a check is called useful, and how often the judge's score differs from the
            advisory one.
          </p>
          <p>Go to the Review tab and run one to see this fill in.</p>
        </div>
      ) : (
        <>
          <dl className="stat-grid">
            <Stat label="Reviews opened" value={String(stats.reviews_opened)}
              note={stats.offline_demo_reviews > 0 ? `${stats.offline_demo_reviews} were offline-demo replays, not live` : undefined} />
            <Stat label="Reviews completed by a judge" value={`${stats.reviews_completed}`}
              note={`completion ${pct(stats.completion_rate)}`} />
            <Stat label="Median time to review" value={dash(stats.median_seconds_to_review, " s")}
              note="from report shown to Save" />
            <Stat label="Checks rated" value={String(stats.flags_rated)} note={`${stats.flags_marked_useful} marked useful`} />
            <Stat label="Helpful rate" value={pct(stats.helpful_rate)} note="of rated checks" />
            <Stat label="Judge changed the score" value={pct(stats.override_rate)}
              note={`${stats.criteria_overridden} of ${stats.criteria_reviewed} criterion scores`} />
            <Stat label="Mean size of a change" value={dash(stats.mean_abs_override_points, " pts")}
              note="when the judge differed" />
          </dl>
          <p className="hint">
            Small numbers move a lot. A single judge reviewing a few samples is not evidence about judges in general.
          </p>
        </>
      )}
    </section>
  );
}

function Stat({ label, value, note }: { label: string; value: string; note?: string }) {
  return (
    <div className="stat">
      <dt>{label}</dt>
      <dd>{value}</dd>
      {note && <dd className="stat-note">{note}</dd>}
    </div>
  );
}
