# CourseCheck

> Synthetic example written for evaluating a judging tool. Not a real product.

## Who has this problem
University instructors writing syllabi. A department of 30 courses must show
that each course's weekly topics cover its published learning outcomes. A
curriculum committee member reads about 8 syllabi per term and, by their own
count in `data/committee_timing.csv`, spends 35 minutes per syllabus tracing
outcomes to weeks.

## Bottleneck
Outcome-to-week tracing is manual and inconsistent: two committee members given
the same syllabus disagreed on coverage for 31% of outcomes (`eval/inter_rater.csv`).

## What CourseCheck does
It maps each outcome to the weeks that address it and quotes the syllabus line
as evidence. If the quote is not in the syllabus the mapping is discarded. The
committee member confirms or edits every mapping; nothing is submitted
automatically.

## Evaluation
45 synthetic syllabi with outcome maps by two raters who reconciled
disagreements (`eval/gold_maps.json`). Baseline 1: keyword overlap
(`src/baseline_keywords.py`). Baseline 2: one prompt (`src/baseline_prompt.py`).

| Method | Outcomes mapped correctly | Wrong-evidence quotes |
|---|---|---|
| Keyword overlap | 61.0% | n/a |
| Single prompt | 78.5% | 14 |
| CourseCheck | **90.2%** | 0 |

Per-syllabus detail: `eval/results.md`; outputs in `results/`.

## Improvement Changelog
| Stage | Change | Mapped correctly | Decision |
|---|---|---|---|
| Baseline 1 | keyword overlap | 61.0% | start |
| Baseline 2 | single prompt | 78.5% | start |
| 1 | split syllabus by week, map per week | 85.1% | kept |
| 2 | require a verbatim quote, verify in code | 90.2% (0 wrong quotes) | kept, biggest change |
| 3 | ask for a confidence score | 90.0% | removed: scores were uncalibrated, no gain |

## Main failure mode
Outcomes covered only implicitly (a project that exercises an outcome without
naming it) are missed about 40% of the time.

## Hot take
Requiring a quote the code can verify did more than any prompt change, and it
turned the model's confident wrong answers into visible refusals.
