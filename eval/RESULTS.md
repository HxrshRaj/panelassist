# PanelAssist vs. baseline vs. human panel

## Per-submission totals (out of 100)

| Submission | Human panel | Baseline | PanelAssist |
|---|---|---|---|
| broken_repro | 63 | 73 | 72 |
| cosmetic_orchestration | 38 | 44 | 35 |
| fabricated_claims | 36 | 38 | 39 |
| strong_baseline_done_right | 92 | 98 | 99 |
| thin_hot_take | 82 | 84 | 91 |
| weak_single_prompt | 25 | 19 | 18 |

## Summary metrics

| Metric | Simple baseline | PanelAssist agent | Change |
|---|---|---|---|
| Mean absolute error vs. human total score (lower is better) | 5.33 | 6.33 | -1.0 pts |
| Spearman rank correlation vs. human ranking (higher is better) | 1.0 | 0.943 | -0.057 |
| Recall on seeded issues (fabricated claim / broken repro / thin hot take) | 0.0 (no mechanism) | 1.0 | n/a |
| Precision on seeded-issue flags (no false alarms on the clean submission) | n/a | 1.0 | n/a |
| LLM calls per submission | 1 | 7 | +6 |
| Total cost, all 6 submissions (est., see common/llm.py rates) | $0.0034 | $0.0259 | +$0.0225 |
| Wall-clock time, all 6 submissions | 73.6s | 482.2s | +408.6s |

Human time per task is not directly measured here (that needs a real judging session to time). As a proxy: the baseline returns one rationale paragraph with zero structured citations per submission, so a human still has to go re-find the evidence themselves before trusting a score; PanelAssist returns 91 total cited pieces of evidence across the 6 criteria x 6 submissions, one per sub-score. We're stating that as a citation count, not converting it into a minutes-saved number we can't actually back up.

## Per-criterion mean absolute error vs. human (lower is better)

| Criterion | Baseline MAE | Agent MAE |
|---|---|---|
| Problem & User Value | 1.33 | 2.5 |
| Agent Solution & Engineering | 1.5 | 2.17 |
| End to End Quality | 1.33 | 1.83 |
| Measured Improvement | 0.83 | 1.33 |
| Reproducibility | 1.17 | 0.67 |
| Hot Take / Insights | 0.5 | 0.83 |

## Seeded-issue detection (the case the baseline structurally cannot handle)

- **fabricated_claims**: expected to trip `claims_have_evidence` -> caught
- **broken_repro**: expected to trip `repro_paths_exist` -> caught
- **thin_hot_take**: expected to trip `hot_take_grounded` -> caught
- **strong_baseline_done_right** (should stay clean): no false alarms
