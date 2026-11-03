export type Source = "live" | "offline_demo" | "deterministic_only";

export interface Health {
  status: string;
  llm_configured: boolean;
  mode: "live" | "offline";
  message: string;
}

export interface SampleInfo {
  slug: string;
  set: "dev" | "held-out";
  title: string;
  has_stored_run: boolean;
  synthetic: boolean;
}

export interface SampleText {
  slug: string;
  title: string;
  readme: string;
  reproduce: string;
  trajectory: string;
  files: string;
  synthetic: boolean;
}

export interface Criterion {
  id: string;
  name: string;
  max_points: number;
  advisory_score: number | null;
  confidence: "low" | "medium" | "high" | null;
  rationale: string;
  evidence_citations: string[];
  weaknesses_deducted_for: string[];
  source: string;
}

export interface Flag {
  check: string;
  passed: boolean;
  title: string;
  detail: string;
  bears_on: string[];
  computed_now?: boolean;
}

export interface InputWarning {
  kind: string;
  where: string;
  excerpt: string;
}

export interface Report {
  review_id: number;
  source: Source;
  source_note: string;
  title: string;
  advisory_total: number | null;
  criteria: Criterion[];
  flags: Flag[];
  needs_human_attention: boolean;
  low_confidence_criteria: string[];
  input_warnings: InputWarning[];
  disclaimer: string;
}

export type Job =
  | { status: "queued" | "running"; elapsed_seconds: number }
  | { status: "done"; report: Report; elapsed_seconds: number }
  | { status: "error"; error: string; elapsed_seconds: number };

export interface Stats {
  has_data: boolean;
  reviews_opened: number;
  offline_demo_reviews: number;
  reviews_by_source: Record<string, number>;
  reviews_completed: number;
  completion_rate: number | null;
  median_seconds_to_review: number | null;
  flags_rated: number;
  flags_marked_useful: number;
  helpful_rate: number | null;
  criteria_reviewed: number;
  criteria_overridden: number;
  override_rate: number | null;
  mean_abs_override_points: number | null;
}

export interface ReviewInput {
  title: string;
  readme: string;
  reproduce: string;
  trajectory: string;
  files: string;
  mode: "lean" | "full";
  sample_slug: string | null;
}
