import { useMemo, useState } from "react";
import { api } from "../api";
import type { Criterion, Report } from "../types";

interface Props {
  report: Report;
  shownAt: number;
}

const SOURCE_LABEL: Record<Report["source"], string> = {
  live: "LIVE",
  offline_demo: "OFFLINE DEMO - stored result, not live",
  deterministic_only: "NO MODEL KEY - scores unavailable",
};

export default function ReportView({ report, shownAt }: Props) {
  const [judge, setJudge] = useState<Record<string, string>>({});
  const [notes, setNotes] = useState<Record<string, string>>({});
  const [rated, setRated] = useState<Record<string, boolean>>({});
  const [saved, setSaved] = useState<number | null>(null);
  const [msg, setMsg] = useState<string | null>(null);

  const problems = useMemo(() => {
    const out: Record<string, string> = {};
    for (const c of report.criteria) {
      const raw = judge[c.id];
      if (raw === undefined || raw === "") continue;
      const n = Number(raw);
      if (!Number.isInteger(n) || n < 0 || n > c.max_points) out[c.id] = `Enter a whole number from 0 to ${c.max_points}.`;
    }
    return out;
  }, [judge, report.criteria]);

  const complete = report.criteria.every((c) => judge[c.id] !== undefined && judge[c.id] !== "") &&
    Object.keys(problems).length === 0;
  const judgeTotal = complete ? report.criteria.reduce((sum, c) => sum + Number(judge[c.id]), 0) : null;
  const attention = report.criteria.filter((c) => report.low_confidence_criteria.includes(c.id));
  const failed = report.flags.filter((f) => !f.passed);

  async function rateFlag(check: string, useful: boolean) {
    setRated((r) => ({ ...r, [check]: useful }));
    try {
      await api.rateFlag(report.review_id, check, useful);
    } catch (e) {
      setMsg((e as Error).message);
    }
  }

  function startFromAdvisory() {
    const next: Record<string, string> = {};
    for (const c of report.criteria) if (c.advisory_score !== null) next[c.id] = String(c.advisory_score);
    setJudge(next);
  }

  async function save() {
    setMsg(null);
    try {
      const res = await api.saveJudge(
        report.review_id,
        report.criteria.map((c) => ({ criterion_id: c.id, judge_score: Number(judge[c.id]), note: notes[c.id] ?? "" })),
        Math.round((Date.now() - shownAt) / 1000),
      );
      setSaved(res.judge_total);
    } catch (e) {
      setMsg((e as Error).message);
    }
  }

  return (
    <div>
      <div className={`banner source-${report.source}`} role="status">
        <strong>{SOURCE_LABEL[report.source]}.</strong> {report.source_note}
      </div>

      {report.input_warnings.length > 0 && (
        <div className="banner banner-warn" role="alert">
          <strong>{report.input_warnings.length} line(s) of the submission looked like instructions to the scorer and
            were removed before any model saw them:</strong>
          <ul>
            {report.input_warnings.map((w, i) => (
              <li key={i}>{w.where}: <code>{w.excerpt}</code></li>
            ))}
          </ul>
        </div>
      )}

      <div className="score-tiles">
        <div className="tile">
          <span className="tile-label">Advisory score (model)</span>
          <span className="tile-value">{report.advisory_total ?? "-"}<small>{report.advisory_total !== null ? " / 100" : ""}</small></span>
          <span className="tile-note">A suggestion. Not a decision.</span>
        </div>
        <div className={saved !== null ? "tile judge saved" : "tile judge"}>
          <span className="tile-label">Judge score (yours)</span>
          <span className="tile-value">{judgeTotal ?? "-"}<small>{judgeTotal !== null ? " / 100" : ""}</small></span>
          <span className="tile-note">{saved !== null ? `Saved: ${saved} / 100` : complete ? "Not saved yet" : "Enter all six scores below"}</span>
        </div>
      </div>

      <h3>Needs your attention</h3>
      {failed.length === 0 && attention.length === 0 ? (
        <p className="empty">Nothing flagged. That does not mean nothing is wrong - the checks are narrow.</p>
      ) : (
        <ul className="attention">
          {failed.map((f) => <li key={f.check}><strong>{f.title}</strong>{f.bears_on.length > 0 && <> (affects {f.bears_on.join(", ")})</>}</li>)}
          {attention.map((c) => <li key={c.id}><strong>{c.name}</strong>: the model reported low confidence</li>)}
        </ul>
      )}

      <h3>Checks</h3>
      <ul className="flags">
        {report.flags.map((f) => (
          <li key={f.check} className={f.passed ? "flag ok" : "flag bad"}>
            <div className="flag-head">
              <span className={f.passed ? "pill ok" : "pill bad"}>{f.passed ? "passed" : "flagged"}</span>
              <strong>{f.title}</strong>
              {f.computed_now && <span className="pill note">computed now, not part of the stored run</span>}
            </div>
            <p>{f.detail}</p>
            <div className="rate" role="group" aria-label={`Was the ${f.title} check useful?`}>
              <span>Was this useful?</span>
              <button type="button" className="btn small" aria-pressed={rated[f.check] === true}
                onClick={() => rateFlag(f.check, true)}>Useful</button>
              <button type="button" className="btn small" aria-pressed={rated[f.check] === false}
                onClick={() => rateFlag(f.check, false)}>Not useful</button>
            </div>
          </li>
        ))}
      </ul>

      <h3>Scores by criterion</h3>
      {report.advisory_total !== null && (
        <p><button type="button" className="btn secondary small" onClick={startFromAdvisory}>
          Start from the advisory scores</button>{" "}
          <span className="hint">Optional. Starting blank avoids anchoring on the model's numbers.</span></p>
      )}
      <div className="table-wrap">
        <table>
          <thead>
            <tr><th scope="col">Criterion</th><th scope="col">Advisory</th><th scope="col">Your score</th></tr>
          </thead>
          <tbody>
            {report.criteria.map((c) => (
              <CriterionRow key={c.id} c={c} value={judge[c.id] ?? ""} note={notes[c.id] ?? ""}
                problem={problems[c.id]}
                onValue={(v) => setJudge((j) => ({ ...j, [c.id]: v }))}
                onNote={(v) => setNotes((n) => ({ ...n, [c.id]: v }))} />
            ))}
          </tbody>
        </table>
      </div>

      {msg && <p className="error" role="alert">{msg}</p>}
      <p>
        <button type="button" className="btn primary" disabled={!complete || saved !== null} onClick={save}>
          {saved !== null ? "Saved" : "Save my review"}
        </button>{" "}
        <span className="hint">Saves your scores and notes, and how long this review took. Not the submission text.</span>
      </p>
      <p className="disclaimer">{report.disclaimer}</p>
    </div>
  );
}

function CriterionRow(props: {
  c: Criterion; value: string; note: string; problem?: string;
  onValue: (v: string) => void; onNote: (v: string) => void;
}) {
  const { c } = props;
  const inputId = `score-${c.id}`;
  return (
    <tr>
      <th scope="row">
        <span>{c.name}</span>
        <span className="max">max {c.max_points}</span>
        {c.rationale && (
          <details>
            <summary>Why</summary>
            <p>{c.rationale}</p>
            {c.weaknesses_deducted_for.length > 0 && (
              <><strong>Deducted for</strong><ul>{c.weaknesses_deducted_for.map((w, i) => <li key={i}>{w}</li>)}</ul></>
            )}
            {c.evidence_citations.length > 0 && (
              <><strong>Evidence cited</strong><ul>{c.evidence_citations.map((w, i) => <li key={i}>{w}</li>)}</ul></>
            )}
          </details>
        )}
      </th>
      <td>
        {c.advisory_score === null ? <span className="muted">-</span> : (
          <><span className="advisory-score">{c.advisory_score}</span>
            {c.confidence && <span className={`conf conf-${c.confidence}`}>{c.confidence} confidence</span>}</>
        )}
      </td>
      <td>
        <label htmlFor={inputId} className="sr-only">{`Your score for ${c.name}, 0 to ${c.max_points}`}</label>
        <input id={inputId} className="score-input" type="number" inputMode="numeric" min={0} max={c.max_points}
          step={1} value={props.value} aria-invalid={props.problem ? true : undefined}
          aria-describedby={props.problem ? `${inputId}-err` : undefined}
          onChange={(e) => props.onValue(e.target.value)} />
        {props.problem && <span id={`${inputId}-err`} className="error small">{props.problem}</span>}
        <label htmlFor={`note-${c.id}`} className="sr-only">{`Note for ${c.name}`}</label>
        <input id={`note-${c.id}`} className="note-input" placeholder="Note (optional)" maxLength={2000}
          value={props.note} onChange={(e) => props.onNote(e.target.value)} />
      </td>
    </tr>
  );
}
