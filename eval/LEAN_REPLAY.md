# Lean mode - offline replay estimate

> **This is not a measured result for lean mode.** It replays saved outputs (see `eval/replay_lean.py` for exactly how and why it can differ from a live run). Nothing here may be quoted as lean mode's MAE. A live run is `python agent/run_agent.py --mode lean` followed by `python eval/run_eval.py`.

Cases: 10 (dev set). Same stored runs as `eval/RESULTS.md`.

| | Baseline (stored run) | Full pipeline (stored run) | Lean (replay estimate) |
|---|---|---|---|
| MAE vs. human (lower better) | 11.2 | 7.8 | 9.6 |
| Spearman vs. human | 0.857 | 0.875 | 0.845 |
| LLM calls per submission | 1 | 7 | 2.8 (expected: 2 + criteria re-scored) |

## Per case

| Submission | Human | Baseline | Full | Lean replay | Criteria re-scored |
|---|---|---|---|---|---|
| broken_repro | 63 | 77 | 60 | 73 | reproducibility |
| cosmetic_orchestration | 38 | 48 | 35 | 38 | reproducibility, hot_take_insights |
| fabricated_claims | 36 | 42 | 50 | 42 | measured_improvement, hot_take_insights |
| good_project_bad_writeup | 78 | 98 | 94 | 98 | - |
| overengineered_but_honest | 84 | 98 | 92 | 98 | - |
| real_gains_no_changelog | 78 | 96 | 88 | 96 | - |
| scope_mismatch | 76 | 93 | 88 | 93 | - |
| strong_baseline_done_right | 92 | 97 | 95 | 97 | - |
| thin_hot_take | 82 | 81 | 84 | 81 | hot_take_insights |
| weak_single_prompt | 25 | 18 | 32 | 20 | measured_improvement, hot_take_insights |

Mean criteria re-scored per submission: 0.8.
