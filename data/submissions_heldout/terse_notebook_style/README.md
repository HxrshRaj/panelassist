# dedup-notes

> Synthetic example written for evaluating a judging tool. Not a real product.

- user: research assistants merging literature-review spreadsheets from 3-5 people
- pain: duplicate papers (same DOI, or same title with different punctuation) survive merges; cleaning 400 rows by hand = ~40 min (timed once, `data/timing.txt`)
- tool: agent proposes duplicate pairs with a one-line reason; human accepts or rejects each pair; nothing is deleted automatically
- data: 8 synthetic spreadsheets, 1,200 rows, 140 true duplicates marked in `eval/true_dupes.csv`
- baseline: exact-DOI match only (`src/baseline_doi.py`)

| | recall of true dupes | wrong pairs proposed |
|---|---|---|
| baseline | 51% | 0 |
| dedup-notes | 89% | 6 |

numbers from `eval/results.md`, produced by `eval/score.py`.

changelog
- v0 DOI only: 51%
- v1 normalised titles (lowercase, strip punctuation): 74%
- v2 model judges near-matches, shows reason: 89%, 6 wrong pairs (all shown to the human)

hot take: the model only needed to judge the ambiguous pairs; normalising first meant it saw a tenth of the rows.
