# PanelAssist vs. baseline vs. human panel

## Per-submission totals (out of 100)

| Submission | Human panel | Baseline | PanelAssist |
|---|---|---|---|
| broken_repro | 63 | 72 | 60 |
| cosmetic_orchestration | 38 | 42 | 35 |
| fabricated_claims | 36 | 34 | 44 |
| good_project_bad_writeup | 78 | 97 | 93 |
| overengineered_but_honest | 84 | 97 | 92 |
| real_gains_no_changelog | 78 | 92 | 88 |
| scope_mismatch | 76 | 92 | 80 |
| strong_baseline_done_right | 92 | 95 | 90 |
| thin_hot_take | 82 | 84 | 86 |
| weak_single_prompt | 25 | 21 | 32 |

## Summary metrics

| Metric | Simple baseline | PanelAssist agent | Change |
|---|---|---|---|
| Mean absolute error vs. human total score (lower is better) | 8.6 | 6.4 | +2.2 pts |
| Spearman rank correlation vs. human ranking (higher is better) | 0.85 | 0.863 | +0.013 |
| Recall on seeded issues (fabricated claim / broken repro / thin hot take) | 0.0 (no mechanism) | 1.0 | n/a |
| Precision on seeded-issue flags (no false alarms on the clean submission) | n/a | 0.75 | n/a |
| LLM calls per submission | 1 | 7 | +6 |
| Total cost, all 10 submissions (est., see common/llm.py rates) | $0.0058 | $0.0586 | +$0.0528 |
| Wall-clock time, all 10 submissions | 104.4s | 905.8s | +801.4s |

Human time per task is not directly measured here (that needs a real judging session to time). As a proxy: the baseline returns one rationale paragraph with zero structured citations per submission, so a human still has to go re-find the evidence themselves before trusting a score; PanelAssist returns 144 total cited pieces of evidence across the 6 criteria x 6 submissions, one per sub-score. We're stating that as a citation count, not converting it into a minutes-saved number we can't actually back up.

## Per-criterion mean absolute error vs. human (lower is better)

| Criterion | Baseline MAE | Agent MAE |
|---|---|---|
| Problem & User Value | 2.1 | 3.5 |
| Agent Solution & Engineering | 2.2 | 2.5 |
| End to End Quality | 2.2 | 2.1 |
| Measured Improvement | 1.5 | 1.4 |
| Reproducibility | 1.2 | 2.3 |
| Hot Take / Insights | 0.6 | 0.6 |

## Seeded-issue detection (the case the baseline structurally cannot handle)

- **fabricated_claims**: expected to trip `claims_have_evidence` -> caught
- **broken_repro**: expected to trip `repro_paths_exist` -> caught
- **thin_hot_take**: expected to trip `hot_take_grounded` -> caught
- **strong_baseline_done_right** (should stay clean): no false alarms
- **good_project_bad_writeup** (should stay clean): no false alarms
- **real_gains_no_changelog** (should stay clean): no false alarms
- **overengineered_but_honest** (should stay clean): no false alarms
- **scope_mismatch** (should stay clean): false positive on ['repro_paths_exist']
