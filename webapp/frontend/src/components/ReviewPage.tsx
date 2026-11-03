import { useEffect, useRef, useState } from "react";
import { api } from "../api";
import type { Report, ReviewInput, SampleInfo } from "../types";
import ReportView from "./ReportView";

type Phase =
  | { kind: "idle" }
  | { kind: "running"; elapsed: number }
  | { kind: "error"; message: string }
  | { kind: "done"; report: Report; shownAt: number };

const EMPTY: ReviewInput = {
  title: "", readme: "", reproduce: "", trajectory: "", files: "", mode: "lean", sample_slug: null,
};

export default function ReviewPage() {
  const [form, setForm] = useState<ReviewInput>(EMPTY);
  const [zip, setZip] = useState<File | null>(null);
  const [samples, setSamples] = useState<SampleInfo[]>([]);
  const [pick, setPick] = useState("fabricated_claims");
  const [phase, setPhase] = useState<Phase>({ kind: "idle" });
  const [formError, setFormError] = useState<string | null>(null);
  const timer = useRef<number | null>(null);

  useEffect(() => {
    api.samples().then(setSamples).catch(() => setSamples([]));
    return () => {
      if (timer.current) window.clearInterval(timer.current);
    };
  }, []);

  const set = <K extends keyof ReviewInput>(key: K, value: ReviewInput[K]) =>
    setForm((f) => ({ ...f, [key]: value, ...(key === "readme" ? { sample_slug: null } : {}) }));

  async function loadSample() {
    setFormError(null);
    try {
      const s = await api.sample(pick);
      setForm({ ...form, title: s.title, readme: s.readme, reproduce: s.reproduce, trajectory: s.trajectory,
        files: s.files, sample_slug: s.slug });
      setZip(null);
      setPhase({ kind: "idle" });
    } catch (e) {
      setFormError((e as Error).message);
    }
  }

  async function submit(ev: React.FormEvent) {
    ev.preventDefault();
    setFormError(null);
    if (!zip && !form.readme.trim()) {
      setFormError("Paste a README, load a sample, or choose a zip first.");
      return;
    }
    setPhase({ kind: "running", elapsed: 0 });
    try {
      const { job_id } = zip
        ? await api.startUpload(zip, form.title, form.mode)
        : await api.startReview(form);
      if (timer.current) window.clearInterval(timer.current);
      timer.current = window.setInterval(async () => {
        try {
          const job = await api.job(job_id);
          if (job.status === "done") {
            window.clearInterval(timer.current as number);
            setPhase({ kind: "done", report: job.report, shownAt: Date.now() });
          } else if (job.status === "error") {
            window.clearInterval(timer.current as number);
            setPhase({ kind: "error", message: job.error });
          } else {
            setPhase({ kind: "running", elapsed: Math.round(job.elapsed_seconds) });
          }
        } catch (e) {
          window.clearInterval(timer.current as number);
          setPhase({ kind: "error", message: (e as Error).message });
        }
      }, 1200);
    } catch (e) {
      setPhase({ kind: "idle" });
      setFormError((e as Error).message);
    }
  }

  return (
    <div className="two-col">
      <section aria-labelledby="in-h" className="card">
        <h2 id="in-h">1. The submission</h2>

        <div className="sample-row">
          <label htmlFor="sample">Try a synthetic sample</label>
          <div className="inline">
            <select id="sample" value={pick} onChange={(e) => setPick(e.target.value)}>
              {samples.map((s) => (
                <option key={s.slug} value={s.slug}>
                  {s.slug.replace(/_/g, " ")} ({s.set}{s.has_stored_run ? ", stored run" : ""})
                </option>
              ))}
              {samples.length === 0 && <option value="fabricated_claims">fabricated claims</option>}
            </select>
            <button type="button" className="btn secondary" onClick={loadSample}>Load sample</button>
          </div>
          <p className="hint">Samples are synthetic. Those marked "stored run" replay a real earlier result when no model
            key is configured, clearly labelled as such.</p>
        </div>

        <form onSubmit={submit} noValidate>
          <label htmlFor="title">Title (optional)</label>
          <input id="title" value={form.title} maxLength={120} onChange={(e) => set("title", e.target.value)} />

          <label htmlFor="readme">README *</label>
          <textarea id="readme" rows={9} value={form.readme} onChange={(e) => set("readme", e.target.value)}
            aria-describedby="readme-hint" />
          <p id="readme-hint" className="hint">Up to 60,000 characters. Instruction-like text inside a submission is
            removed before any model sees it, and listed in the report.</p>

          <details>
            <summary>More inputs (reproduction guide, trajectory, file list)</summary>
            <label htmlFor="repro">REPRODUCE.md</label>
            <textarea id="repro" rows={5} value={form.reproduce} onChange={(e) => set("reproduce", e.target.value)} />
            <label htmlFor="traj">Trajectory (JSON or text)</label>
            <textarea id="traj" rows={4} value={form.trajectory} onChange={(e) => set("trajectory", e.target.value)} />
            <label htmlFor="files">Files in the submission (one per line)</label>
            <textarea id="files" rows={4} value={form.files} onChange={(e) => set("files", e.target.value)} />
          </details>

          <label htmlFor="zip">Or upload a zip (max 2 MB)</label>
          <input id="zip" type="file" accept=".zip,application/zip"
            onChange={(e) => setZip(e.target.files?.[0] ?? null)} />

          <fieldset>
            <legend>Review mode</legend>
            <label className="radio"><input type="radio" name="mode" checked={form.mode === "lean"}
              onChange={() => set("mode", "lean")} /> Lean - one holistic score, re-score only flagged criteria (fewer calls)</label>
            <label className="radio"><input type="radio" name="mode" checked={form.mode === "full"}
              onChange={() => set("mode", "full")} /> Full - six specialist scorers (7 calls)</label>
          </fieldset>

          {formError && <p className="error" role="alert">{formError}</p>}
          <button type="submit" className="btn primary" disabled={phase.kind === "running"}>
            {phase.kind === "running" ? "Reviewing..." : "Review submission"}
          </button>
        </form>
      </section>

      <section aria-labelledby="out-h" className="card" aria-live="polite">
        <h2 id="out-h">2. The advisory report</h2>
        {phase.kind === "idle" && <p className="empty">Load a sample or paste a README, then choose Review. Nothing is
          scored until you do.</p>}
        {phase.kind === "running" && (
          <p className="running"><span className="spinner" aria-hidden="true" /> Working... {phase.elapsed}s elapsed.
            A live full review can take a minute or two.</p>
        )}
        {phase.kind === "error" && <p className="error" role="alert">{phase.message}</p>}
        {phase.kind === "done" && <ReportView report={phase.report} shownAt={phase.shownAt} />}
      </section>
    </div>
  );
}
