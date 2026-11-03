import type { Health, Job, ReviewInput, SampleInfo, SampleText, Stats } from "./types";

const BASE = (import.meta.env.VITE_API_BASE as string | undefined) ?? "";

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, init);
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") detail = body.detail;
      else if (Array.isArray(body.detail)) detail = body.detail.map((d: { msg?: string }) => d.msg).join("; ");
    } catch {
      /* keep the status text */
    }
    throw new Error(detail);
  }
  return (await res.json()) as T;
}

const json = (body: unknown): RequestInit => ({
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

export const api = {
  health: () => call<Health>("/api/health"),
  samples: () => call<SampleInfo[]>("/api/samples"),
  sample: (slug: string) => call<SampleText>(`/api/samples/${encodeURIComponent(slug)}`),
  stats: () => call<Stats>("/api/stats"),
  startReview: (input: ReviewInput) => call<{ job_id: string }>("/api/review", json(input)),
  startUpload: (file: File, title: string, mode: string) => {
    const form = new FormData();
    form.append("file", file);
    form.append("title", title);
    form.append("mode", mode);
    return call<{ job_id: string }>("/api/review/upload", { method: "POST", body: form });
  },
  job: (id: string) => call<Job>(`/api/jobs/${id}`),
  rateFlag: (reviewId: number, check: string, useful: boolean) =>
    call<{ ok: boolean }>(`/api/reviews/${reviewId}/flags`, json({ check, useful })),
  saveJudge: (
    reviewId: number,
    scores: { criterion_id: string; judge_score: number; note: string }[],
    secondsToReview: number,
  ) =>
    call<{ ok: boolean; judge_total: number }>(
      `/api/reviews/${reviewId}/judge`,
      json({ scores, seconds_to_review: secondsToReview }),
    ),
};
