# Ablation: what each change actually contributed

| Stage | MAE vs. human (lower better) | Spearman vs. human (higher better) |
|---|---|---|
| baseline (raw text, 1 call) | 11.2 | 0.857 |
| + evidence ledger (1 combined call) | 12.2 | 0.893 |
| + specialist split, no verification | 11.2 | 0.894 |
| + verification (final) | 7.8 | 0.875 |

## Per-submission totals across every stage

| Submission | Human | Baseline | +Ledger | +Split | Final |
|---|---|---|---|---|---|
| broken_repro | 63 | 77 | 79 | 82 | 60 |
| cosmetic_orchestration | 38 | 48 | 54 | 49 | 35 |
| fabricated_claims | 36 | 42 | 65 | 56 | 50 |
| good_project_bad_writeup | 78 | 98 | 95 | 93 | 94 |
| overengineered_but_honest | 84 | 98 | 95 | 94 | 92 |
| real_gains_no_changelog | 78 | 96 | 88 | 88 | 88 |
| scope_mismatch | 76 | 93 | 88 | 91 | 88 |
| strong_baseline_done_right | 92 | 97 | 98 | 96 | 95 |
| thin_hot_take | 82 | 81 | 84 | 85 | 84 |
| weak_single_prompt | 25 | 18 | 28 | 30 | 32 |
