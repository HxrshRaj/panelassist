# PanelAssist vs. baseline vs. human panel

## Per-submission totals (out of 100)

| Submission | Human panel | Baseline | PanelAssist |
|---|---|---|---|
| broken_repro | 63 | 77 | 60 |
| cosmetic_orchestration | 38 | 48 | 35 |
| fabricated_claims | 36 | 42 | 50 |
| good_project_bad_writeup | 78 | 98 | 94 |
| overengineered_but_honest | 84 | 98 | 92 |
| real_gains_no_changelog | 78 | 96 | 88 |
| scope_mismatch | 76 | 93 | 88 |
| strong_baseline_done_right | 92 | 97 | 95 |
| thin_hot_take | 82 | 81 | 84 |
| weak_single_prompt | 25 | 18 | 32 |

## Summary metrics

| Metric | Simple baseline | PanelAssist agent | Change |
|---|---|---|---|
| Mean absolute error vs. human total score (lower is better) | 11.2 | 7.8 | +3.4 pts |
| Spearman rank correlation vs. human ranking (higher is better) | 0.857 | 0.875 | +0.018 |
| Recall on seeded issues (fabricated claim / broken repro / thin hot take) | 0.0 (no mechanism) | 1.0 | n/a |
| Precision on seeded-issue flags (no false alarms on the clean submission) | n/a | 1.0 | n/a |
| LLM calls per submission | 1 | 7 | +6 |
| Total cost, all 10 submissions (est., see common/llm.py rates) | $0.0059 | $0.0571 | +$0.0512 |
| Wall-clock time, all 10 submissions | 111.7s | 932.1s | +820.4s |

Human time per task is not directly measured here (that needs a real judging session to time). As a proxy: the baseline returns one rationale paragraph with zero structured citations per submission, so a human still has to go re-find the evidence themselves before trusting a score; PanelAssist returns 148 total cited pieces of evidence across the 6 criteria x 10 submissions, one per sub-score. We're stating that as a citation count, not converting it into a minutes-saved number we can't actually back up.

## Per-criterion mean absolute error vs. human (lower is better)

| Criterion | Baseline MAE | Agent MAE |
|---|---|---|
| Problem & User Value | 2.5 | 3.3 |
| Agent Solution & Engineering | 2.8 | 2.7 |
| End to End Quality | 2.2 | 2.0 |
| Measured Improvement | 2.0 | 1.7 |
| Reproducibility | 1.3 | 1.6 |
| Hot Take / Insights | 0.6 | 0.7 |

## Seeded-issue detection (the case the baseline structurally cannot handle)

- **fabricated_claims**: expected to trip `claims_have_evidence` -> caught
- **broken_repro**: expected to trip `repro_paths_exist` -> caught
- **thin_hot_take**: expected to trip `hot_take_grounded` -> caught
- **strong_baseline_done_right** (should stay clean): no false alarms
- **good_project_bad_writeup** (should stay clean): no false alarms
- **real_gains_no_changelog** (should stay clean): no false alarms
- **overengineered_but_honest** (should stay clean): no false alarms
- **scope_mismatch** (should stay clean): no false alarms
