# PanelAssist vs. baseline vs. human panel (dev set, 10 cases)

## Per-submission totals (out of 100)

| Submission | Human panel | Simple baseline | PanelAssist (full) |
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

| Metric | Simple baseline | PanelAssist (full) |
|---|---|---|
| Mean absolute error vs. human total (lower is better) | 11.2 | 7.8 |
| Spearman rank correlation vs. human (higher is better) | 0.857 | 0.875 |
| Recall on planted defects | 0.0 (no mechanism) | 1.0 |
| Precision (flags on honest submissions) | n/a | 1.0 |
| False-alarm rate (honest submissions with any original-check flag) | n/a | 0.0 |
| LLM calls per submission | 1.0 | 7.0 |
| Total cost, all 10 submissions (est., see common/llm.py rates) | $0.0059 | $0.0571 |
| Wall-clock time, all 10 submissions | 111.7s | 932.1s |

Lean mode: **not run** - no `results/lean_scores.json` (needs a working LLM key: `python agent/run_agent.py --mode lean`). For an offline *estimate* from saved outputs, clearly not a measurement, see `eval/LEAN_REPLAY.md`.

Human time per task is not measured here (that needs a real judging session). As a proxy: the baseline returns one rationale paragraph with zero structured citations, so a human has to re-find the evidence before trusting a score; the full pipeline returns 148 cited pieces of evidence across 6 criteria x 10 submissions. This is a citation count, not a minutes-saved number.

## Per-criterion mean absolute error vs. human (lower is better)

| Criterion | Simple baseline | PanelAssist (full) |
|---|---|---|
| Problem & User Value | 2.5 | 3.3 |
| Agent Solution & Engineering | 2.8 | 2.7 |
| End to End Quality | 2.2 | 2.0 |
| Measured Improvement | 2.0 | 1.7 |
| Reproducibility | 1.3 | 1.6 |
| Hot Take / Insights | 0.6 | 0.7 |

## Planted-defect detection (the case the baseline structurally cannot handle)

### PanelAssist (full)

- **fabricated_claims**: expected to trip `claims_have_evidence` -> caught
- **broken_repro**: expected to trip `repro_paths_exist` -> caught
- **thin_hot_take**: expected to trip `hot_take_grounded` -> caught
- **strong_baseline_done_right** (honest): no false alarms
- **good_project_bad_writeup** (honest): no false alarms
- **real_gains_no_changelog** (honest): no false alarms
- **overengineered_but_honest** (honest): no false alarms
- **scope_mismatch** (honest): no false alarms
- write-up check: not in this run. This run pre-dates the write-up check; see eval/WRITEUP_CHECK.md for the offline evaluation.
