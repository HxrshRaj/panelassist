# Removed experiment: LLM-based verification vs. deterministic verification

Setup: evidence ledger built once per submission (shared by both approaches). Deterministic checks run once (they are pure functions). LLM checks run 3x per submission to measure reproducibility. Extra cost of the LLM approach over the full 6-submission set: **18 LLM calls** (3 per submission x 6), vs. **0** for the deterministic checks.

## Did each approach catch the seeded issue?

| Submission | Seeded check | Deterministic | LLM (per run) |
|---|---|---|---|
| fabricated_claims | `claims_have_evidence` | caught | caught, caught, caught |
| broken_repro | `repro_paths_exist` | caught | caught, caught, caught |
| thin_hot_take | `hot_take_grounded` | caught | caught, caught, caught |

## False positives on the clean control

- **Deterministic:** none
- **LLM run 1:** none
- **LLM run 2:** none
- **LLM run 3:** none

## Run-to-run reproducibility of the LLM approach

No verdict changed between runs in this sample (still not *guaranteed* stable - it is a sampled model).

## Verdict

Kept the deterministic `verify.py`. The LLM version adds a call per submission, is not reproducible by construction, and its extra flexibility did not buy a catch the deterministic checks missed. A flag that a judge is meant to act on should be one they can re-derive by hand; `p in manifest_files` is that, a sampled model verdict is not.
