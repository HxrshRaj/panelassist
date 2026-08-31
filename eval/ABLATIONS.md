# Ablation: what each change actually contributed

| Stage | MAE vs. human (lower better) | Spearman vs. human (higher better) |
|---|---|---|
| baseline (raw text, 1 call) | 8.6 | 0.85 |
| + evidence ledger (1 combined call) | 11.2 | 0.905 |
| + specialist split, no verification | 10.8 | 0.875 |
| + verification (final) | 6.4 | 0.863 |

## Per-submission totals across every stage

| Submission | Human | Baseline | +Ledger | +Split | Final |
|---|---|---|---|---|---|
| broken_repro | 63 | 72 | 70 | 81 | 60 |
| cosmetic_orchestration | 38 | 42 | 57 | 52 | 35 |
| fabricated_claims | 36 | 34 | 62 | 51 | 44 |
| good_project_bad_writeup | 78 | 97 | 94 | 91 | 93 |
| overengineered_but_honest | 84 | 97 | 96 | 93 | 92 |
| real_gains_no_changelog | 78 | 92 | 84 | 88 | 88 |
| scope_mismatch | 76 | 92 | 90 | 90 | 80 |
| strong_baseline_done_right | 92 | 95 | 98 | 91 | 90 |
| thin_hot_take | 82 | 84 | 84 | 87 | 86 |
| weak_single_prompt | 25 | 21 | 29 | 34 | 32 |
