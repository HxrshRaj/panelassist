# QuoteCheck

> Synthetic example written for evaluating a judging tool. Not a real product.

## User
Copy editors at a regional news desk checking that every direct quote in a draft
matches the transcript. A 1,200-word story has 4-7 quotes; checking against a
transcript takes about 10 minutes per story (`data/editor_timing.csv`).

## Approach
The agent finds each quoted passage in the draft, locates the closest span in
the transcript, and reports exact / paraphrased / not-found with both texts
side by side. The editor decides; the tool changes no text.

## Evaluation
50 synthetic stories with 262 quotes, 41 of them deliberately altered
(`eval/altered_quotes.csv`). Baseline: exact string match (`src/baseline_exact.py`).

| | Altered quotes caught (of 41) | Clean quotes wrongly flagged (of 221) |
|---|---|---|
| Exact match | 29 | 14 |
| QuoteCheck | 39 | 5 |

Results: `eval/results.md`.

## Changelog
| Stage | Change | Caught |
|---|---|---|
| v0 | Exact match | 29 |
| v1 | Fuzzy span alignment in code | 34 |
| v2 | Model classifies exact / paraphrased / altered | 39 |
| v3 | Model rewrites the quote | removed: it changed meaning twice |

## Hot take
Alignment in code, judgement in the model: the model never sees the whole transcript.
