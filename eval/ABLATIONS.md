# Ablation: what each change actually contributed

| Stage | MAE vs. human (lower better) | Spearman vs. human (higher better) |
|---|---|---|
| baseline (raw text, 1 call) | 5.33 | 1.0 |
| + evidence ledger (1 combined call) | 10.17 | 0.943 |
| + specialist split, no verification | 8.67 | 0.943 |
| + verification (final) | 6.33 | 0.943 |

## Per-submission totals across every stage

| Submission | Human | Baseline | +Ledger | +Split | Final |
|---|---|---|---|---|---|
| broken_repro | 63 | 73 | 73 | 86 | 72 |
| cosmetic_orchestration | 38 | 44 | 50 | 39 | 35 |
| fabricated_claims | 36 | 38 | 64 | 41 | 39 |
| strong_baseline_done_right | 92 | 98 | 98 | 97 | 99 |
| thin_hot_take | 82 | 84 | 85 | 92 | 91 |
| weak_single_prompt | 25 | 19 | 27 | 17 | 18 |
